# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    
    uom_id = fields.Many2one('uom.uom', "Unit of Measure")
    
    @api.onchange('product_id','product_tmpl_id')
    def onchange_product_id_uom_id(self):
        self.uom_id = False
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
            return {'domain':{'uom_id':[('category_id','=',self.product_id.uom_id.category_id.id)]}}
        elif self.product_tmpl_id:
            self.uom_id = self.product_tmpl_id.uom_id.id
            return {'domain':{'uom_id':[('category_id','=',self.product_tmpl_id.uom_id.category_id.id)]}}

    def _compute_price(self, price, price_uom, product, quantity=1.0, partner=False):
        price = super(PricelistItem,self)._compute_price(price, price_uom, product,quantity,partner)
        if price_uom and \
        price_uom.id != product.uom_id.id and \
        self.uom_id and \
        self.uom_id.id == price_uom.id and \
        self.applied_on in ['0_product_variant','1_product']:
            #in org _compute_price func , they converted UNIT PRICE to product uom - convert_to_price_uom
            #next line we applied reverese
            price = price_uom._compute_price(price, product.uom_id)
        return price

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule_get_items(self, products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids):
        items = super(Pricelist,self)._compute_price_rule_get_items(products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids)
        if uom_id and (prod_tmpl_ids or prod_ids):
            #to remove other UOM items
            pricelist_item_ded = items.filtered(lambda l: l.uom_id and l.applied_on in ['0_product_variant','1_product'] and l.uom_id.id != uom_id)
            items -= pricelist_item_ded
        return items