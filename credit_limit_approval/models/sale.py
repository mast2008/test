from odoo import fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def check_limit(self):
        self.ensure_one()
        company = self.company_id or self.env.user.company_id
        partner = self.partner_id.commercial_partner_id.with_company(company)
        if partner.date_cl_exempt_apvl and \
        company.cl_approval and \
        company.cl_approval_validity_hour > 0:
            if partner.date_cl_exempt_apvl + timedelta(hours=company.cl_approval_validity_hour) >= fields.Datetime.now():
                return True
        return super().check_limit()

    ptnr_cl_exempt_id = fields.Many2one('ptnr.cl.exempt', copy=False, string="Partner Credit Limit Exemption")

    def action_send_to_cl_exempt_approval(self):
        obj_ptnr_cl_exempt = self.env['ptnr.cl.exempt']
        for rec in self:
            partner = rec.partner_id.commercial_partner_id
            if rec.ptnr_cl_exempt_id and \
            rec.ptnr_cl_exempt_id.state == 'to_approve':
                raise ValidationError("Already sent for credit limit exemption approval")
            company = rec.company_id or self.env.user.company_id
            if not company.cl_approval:
                raise UserError("Please enable settings first.\n\nSales -> Configuration -> Settings -> Credit Limit Exemption Approval")
            approval_users = company.cl_approval_user_ids
            if not approval_users:
                raise UserError("Please set approval users.\n\nSales -> Configuration -> Settings -> Credit Limit Exemption Approval")
            if rec.ptnr_cl_exempt_id:
                rec.ptnr_cl_exempt_id.activity_unlink(['credit_limit_approval.mail_act_ptnr_cl_exempt_approval'])
                rec.ptnr_cl_exempt_id.unlink(force=True)
            vals_cl_exempt = {'company_id': company.id,
                              'partner_id': partner.id,
                              'sale_order_id': rec.id
                              }
            rec.ptnr_cl_exempt_id = obj_ptnr_cl_exempt.create(vals_cl_exempt).id
            # activity to notify
            for app_user in approval_users:
                rec.ptnr_cl_exempt_id.activity_schedule('credit_limit_approval.mail_act_ptnr_cl_exempt_approval',
                                      note=f'',
                                      user_id=app_user.id,
                                      date_deadline=datetime.now().date())