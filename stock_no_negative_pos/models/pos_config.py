from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_location_src_id = fields.Many2one(
        "stock.location", related="picking_type_id.default_location_src_id"
    )
    allow_negative_stock_location = fields.Boolean(related='default_location_src_id.allow_negative_stock')
