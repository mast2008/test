
from odoo import fields, models, api
import time


class PartnerLedgerWizard(models.TransientModel):
    
    _name = 'partner.ledger.wizard'
    _description = 'Partner Ledger Wizard'

    partner_ids = fields.Many2many('res.partner',
                                    'partner_ledger_wizard_rel',
                                    'partner',
                                    'wizard_id',
                                    string='Partners')
    from_date = fields.Date(string='From Date', default=time.strftime('%Y-01-01'))
    to_date = fields.Date(string='To Date', default=fields.Date.today)
    include_opening_balance = fields.Boolean(string='Include Opening Balances', default=True)
    show_zero_balance = fields.Boolean(string='Show Zero Balance', default=False)
    posted_entries_only = fields.Boolean(string='Posted Entries Only', default=True)
    summary_format = fields.Boolean(string='Summary Format',default=True)
    account_ids = fields.Many2many('account.account',
                                   'account_filter_ledger_wizard_rel',
                                   'account_id',
                                   'wizard_id',
                                   string='Accounts')
    
    include_movement_filter = fields.Boolean(string="Include Movement Filter",default=True)
    
    account_filter = fields.Selection([('receivable','Receivable'),('payable','Payable'),
                                       ('receivable_payable','Receivable and Payable')],
                                      default='receivable', string="Account Filter")



    

    #@api.multi
    def print_report(self):
        return self.env.ref('aljser_account_reports_xlsx.partner_ledger_report_id').report_action(self)

