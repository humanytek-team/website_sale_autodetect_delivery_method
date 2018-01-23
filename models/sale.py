# -*- coding: utf-8 -*-
import logging

from openerp import api, models
from openerp import SUPERUSER_ID


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # @api.v7
    # def _get_delivery_methods(self, cr, uid, order, context=None):
    #     #_logger.debug('DEBUG ORDER CARRIERRRRRRRRR %s', order.carrier_id.name)
    # return super(SaleOrder, self)._get_delivery_methods(cr, uid, order,
    # context=context)

    # @api.v7
    # def _check_carrier_quotation(self, cr, uid, order, force_carrier_id=None, context=None):
    #     carrier_obj = self.pool.get('delivery.carrier')

    #     # check to add or remove carrier_id
    #     if not order:
    #         return False
    #     if all(line.product_id.type in ("service", "digital") for line in order.website_order_line):
    #         order.write({'carrier_id': None})
    #         self.pool['sale.order']._delivery_unset(
    #             cr, SUPERUSER_ID, [order.id], context=context)
    #         return True
    #     else:
    #         _logger.debug('DEBUG CHECK CARRIERRRRRRRRR %s',
    #                       order.carrier_id.id)
    #         carrier_id = order.carrier_id.id or force_carrier_id
    #         carrier_ids = self._get_delivery_methods(
    #             cr, uid, order, context=context)
    #         if carrier_id:
    #             if carrier_id not in carrier_ids:
    #                 carrier_id = False
    #             else:
    #                 carrier_ids.remove(carrier_id)
    #                 carrier_ids.insert(0, carrier_id)
    #         if force_carrier_id or not carrier_id or not carrier_id in carrier_ids:
    #             _logger.debug('DEBUG ORDER %s',
    #                           order)
    #             order.button_dummy()
    #             # for delivery_id in carrier_ids:
    #             #     carrier = carrier_obj.verify_carrier(
    #             #         cr, SUPERUSER_ID, [delivery_id], order.partner_shipping_id)
    #             #     if carrier:
    #             #         carrier_id = delivery_id
    #             #         break
    #             # order.write({'carrier_id': carrier_id})
    #         if carrier_id:
    #             order.delivery_set()
    #         else:
    #             order._delivery_unset()

    #     return bool(carrier_id)

    @api.v7
    def _cart_update(self, cr, uid, ids, product_id=None, line_id=None, add_qty=0, set_qty=0, context=None, **kwargs):
        """ Override to update carrier quotation if quantity changed """

        self._delivery_unset(cr, uid, ids, context=context)

        # When you update a cart, it is not enouf to remove the "delivery cost" line
        # The carrier might also be invalid, eg: if you bought things that are too heavy
        # -> this may cause a bug if you go to the checkout screen, choose a carrier,
        #    then update your cart (the cart becomes uneditable)
        self.write(cr, uid, ids, {'carrier_id': False}, context=context)

        values = super(SaleOrder, self)._cart_update(
            cr, uid, ids, product_id, line_id, add_qty, set_qty, context, **kwargs)

        if add_qty or set_qty is not None:
            for sale_order in self.browse(cr, uid, ids, context=context):
                self._check_carrier_quotation(
                    cr, uid, sale_order, context=context)

        return values
