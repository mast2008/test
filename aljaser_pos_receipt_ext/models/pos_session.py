# -*- coding: utf-8 -*-

import re

from odoo import models, fields, api
import math




class PosOrder(models.Model):
    _inherit = 'pos.order'


    @api.model
    def get_invoice(self, id):
        pos_id = self.search([('pos_reference', '=', id)])
        print("get_invoice", id,pos_id,pos_id.name)
        invoice_id = self.env['account.move'].search([('ref', '=', pos_id.name)])
        return {
            'invoice_id': invoice_id.id,
            'invoice_name': invoice_id.name,
        }


