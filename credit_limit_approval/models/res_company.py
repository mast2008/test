from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    cl_approval = fields.Boolean("Credit Limit Exemption Approval", help="Allow to confirm sales until certain hours by getting approval from manager even if credit limit exceeded", default=True)
    cl_approval_user_ids = fields.Many2many('res.users', 'cl_approval_comp_user_rel', 'comp_id', 'user_id', string="Users to approve credit limit exemption")
    cl_approval_validity_hour = fields.Integer("Approval Validity (Hour)", default=4)