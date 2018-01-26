# -*- coding: utf-8 -*-
# Copyright 2018 Humanytek
# - Manuel Marquez <manuel@humanytek.com>
# - Ruben Bravo <rubenred18@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import openerp
from openerp import http
from openerp.http import request
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
