# -*- coding: utf-8 -*-
# Copyright 2018 Humanytek
# - Manuel Marquez <manuel@humanytek.com>
# - Ruben Bravo <rubenred18@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import openerp
from openerp import http
from openerp.http import request
from openerp import SUPERUSER_ID
import openerp.addons.website_sale.controllers.main
import logging
_logger = logging.getLogger(__name__)


class website_sale(openerp.addons.website_sale.controllers.main.website_sale):

    @http.route()
    def cart(self, **post):
        cr, uid, context, pool = \
            request.cr, request.uid, request.context, request.registry
        order = request.website.sale_get_order()

        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(
                cr, uid, from_currency, to_currency, price, context=context)
            _logger.debug('DEBUG ORDER BEFORE %s', order.carrier_id)
            order.button_dummy()
            _logger.debug('DEBUG ORDER AFTER %s', order.carrier_id)
            #order.write({'carrier_id': order.button_dummy()})
        else:
            compute_currency = lambda price: price

        values = {
            'website_sale_order': order,
            'compute_currency': compute_currency,
            'suggested_products': [],
        }
        if order:
            _order = order
            if not context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()

        if post.get('type') == 'popover':
            return request.website.render("website_sale.cart_popover", values)

        if post.get('code_not_available'):
            values['code_not_available'] = post.get('code_not_available')

        return request.website.render("website_sale.cart", values)


    def checkout_form_save(self, checkout):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        order = request.website.sale_get_order(force_create=1, context=context)

        orm_partner = registry.get('res.partner')
        orm_user = registry.get('res.users')
        order_obj = request.registry.get('sale.order')

        partner_lang = request.lang if request.lang in [lang.code for lang in request.website.language_ids] else None

        billing_info = {'customer': True}
        if partner_lang:
            billing_info['lang'] = partner_lang
        billing_info.update(self.checkout_parse('billing', checkout, True))

        # set partner_id
        partner_id = None
        if request.uid != request.website.user_id.id:
            partner_id = orm_user.browse(cr, SUPERUSER_ID, uid, context=context)[0].partner_id.id
        elif order.partner_id:
            user_ids = request.registry['res.users'].search(cr, SUPERUSER_ID,
                [("partner_id", "=", order.partner_id.id)], context=dict(context or {}, active_test=False))
            if not user_ids or request.website.user_id.id not in user_ids:
                partner_id = order.partner_id.id

        # save partner informations
        if partner_id and request.website.partner_id.id != partner_id:
            orm_partner.write(cr, SUPERUSER_ID, [partner_id], billing_info, context=context)
        else:
            # create partner
            billing_info['team_id'] = request.website.salesteam_id.id
            partner_id = orm_partner.create(cr, SUPERUSER_ID, billing_info, context=context)
        order.write({'partner_id': partner_id})
        order_obj.onchange_partner_id(cr, SUPERUSER_ID, [order.id], context=context)

        # create a new shipping partner
        if checkout.get('shipping_id') == -1:
            shipping_info = self._get_shipping_info(checkout)
            if partner_lang:
                shipping_info['lang'] = partner_lang
            shipping_info['parent_id'] = partner_id
            checkout['shipping_id'] = orm_partner.create(cr, SUPERUSER_ID, shipping_info, context)

        order_info = {
            'message_partner_ids': [(4, partner_id), (3, request.website.partner_id.id)],
            'partner_shipping_id': checkout.get('shipping_id') or partner_id,
        }
        order_obj.write(cr, SUPERUSER_ID, [order.id], order_info, context=context)

