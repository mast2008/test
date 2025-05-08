from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    print_out_logo = fields.Image('Printout Logo', copy=False)
