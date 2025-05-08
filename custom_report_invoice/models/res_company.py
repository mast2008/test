# -*- coding: utf-8 -*-

from odoo import models, fields

class res_company(models.Model):
    _inherit = "res.company"

    #footer_image = fields.Binary("Footer Image", attachment=True, help="This field holds the image used for the footer")
    header_image = fields.Binary("Header Image", attachment=True, help="This field holds the image used for the header")

class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    header_image = fields.Binary(related='company_id.header_image', readonly=False)