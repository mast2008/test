# -*- coding: utf-8 -*-
from odoo import fields, models

class AccountInvoice(models.Model):
    _inherit = "account.move"

    date_supply = fields.Date(string='Date of Supply', readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False, tracking=True)
    #added fayyas - 07/08/19
    date_lpo = fields.Date(string='LPO Date', readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False, tracking=True)
    lpo_no = fields.Char(string="LPO No", readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False, tracking=True)

    def get_pack_qty_details(self):
        uom_list = []
        uom_dict = {}
        uom_name = []
        uom_qty = []
        row_count = 0
        for line in self.invoice_line_ids:
            if line.product_uom_id:
                if line.product_uom_id not in uom_list:
                    uom_list.append(line.product_uom_id)
                    uom_dict[line.product_uom_id] = 0
                uom_dict[line.product_uom_id] += line.quantity
        if uom_dict:
            for key, qty in uom_dict.items():
                uom_name.append(key.name)
                uom_qty.append(qty)
                row_count += 1
        return [row_count,uom_name,uom_qty]

class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    def get_reference_uom(self):
        """if self.uom_id.uom_type == 'reference':
            return self.uom_id.name
        else:
            categ = self.uom_id.category_id
            uom_id = self.env['uom.uom'].search([('category_id', '=', categ.id),('uom_type', '=', 'reference')],limit=1)
            return uom_id.name"""
        pdt_bom_uom = ""
        if self.product_id:
            product = self.product_id
            product_bom_uom = self.env['mrp.bom'].search(
                ['|', ('product_id', '=', product.id), '&', ('product_id', '=', False),
                 ('product_tmpl_id', '=', product.product_tmpl_id.id)])
            if product_bom_uom:
                if product_bom_uom[-1].code:
                    pdt_bom_uom = product_bom_uom[-1].code
                else:
                    pdt_bom_uom = self.product_uom_id.name
            else:
                pdt_bom_uom = self.product_uom_id.name
        return pdt_bom_uom