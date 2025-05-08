from odoo import models, fields
from datetime import datetime
from .. import user_tz_dtm
from odoo.exceptions import UserError

class InvBillReportWiz(models.TransientModel):
    _name = 'inv.bill.rpt.wiz'
    _description = 'Invoice & Bill Report Wizard'

    def get_query_res(self,query):
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall() or []
    
    def _get_is_module_installed(self, module_name):
        qry = f"select state from ir_module_module where name='{module_name}' and state ='installed'"
        qry_res = self.get_query_res(qry)  
        if qry_res:
            return True
        return False

    def get_record(self, model_name, domain=[]):
        return self.env[model_name].search(domain)
    
    def get_record_obj(self, model_name, ids):
        return self.env[model_name].browse(ids)
        
    def validate_report(self):
        user_tz_dtm.get_timezone(self)
        msg = []
        if self.date_from and self.date_to and self.date_from > self.date_to:
            msg.append(f"From Date must be less than To Date.")
        if msg:
            raise UserError("\n\n".join(msg))
    
    def generate_report(self):
        self.validate_report()
        return self.export_xls()

    date_from = fields.Date("From Date")
    date_to = fields.Date("To Date")
    customer_ids = fields.Many2many('res.partner','inv_bill_rpt_cust_rel','wiz_id','cust_id', string="Customer")
    vendor_ids = fields.Many2many('res.partner', 'inv_bill_rpt_vendor_rel', 'wiz_id', 'vendor_id', string="Vendor")
    incl_inv_credit_note = fields.Boolean("Include Invoice Credit Notes", default=True)
    incl_bill_credit_note = fields.Boolean("Include Bill Credit Notes", default=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.user.company_id.currency_id.id,
                                  string="Currency", required=True)
    company_id = fields.Many2one('res.company', 'Company', invisible=True, required=True,
                                 default=lambda self: self.env.user.company_id.id, copy=False, ondelete='cascade')
    user_id = fields.Many2one('res.users', 'Responsible', invisible=True, default=lambda self: self.env.user.id,
                              copy=False, required=True, ondelete='cascade')

    def export_xls(self):
        user_tz_dtm.get_timezone(self)
        datas = {'ids': self._context.get('active_ids', []),
                 'model': self._name,
                 'form': self.read()[0]
                 }
        self = self.with_context(discard_logo_check=True)
        return self.env.ref('inv_bill_report.report_xlsx_inv_bill').report_action(self, data=datas)

    def get_report_filters(self):
        filters = []
        now_str = user_tz_dtm.get_tz_date_time_str(self,datetime.now())
        filters.append({'label':'Printed By','value': f"{self.env.user.display_name} - {now_str}"})
        self.customer_ids and filters.append({'label':'Customers','value':", ".join(self.customer_ids.mapped('display_name'))})
        self.vendor_ids and filters.append({'label': 'Vendors', 'value': ", ".join(self.vendor_ids.mapped('display_name'))})
        return filters