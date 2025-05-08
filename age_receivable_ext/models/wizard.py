# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountReport(models.TransientModel):
    _name = "wizard.aged.receivable.history"
    _description = "Aged History"

    receivable = fields.Boolean(string='Recievable', default=True)
    payable = fields.Boolean(string='Payable')
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', default=fields.Date.today(), required=True)
    days = fields.Integer(string='Days', default=30, required=True)

    def _get_objs_for_report(self, docids, data):
        """
        Returns objects for xlx report.  From WebUI these
        are either as docids taken from context.active_ids or
        in the case of wizard are in data.  Manual calls may rely
        on regular context, setting docids, or setting data.

        :param docids: list of integers, typically provided by
            qwebactionmanager for regular Models.
        :param data: dictionary of data, if present typically provided
            by qwebactionmanager for TransientModels.
        :param ids: list of integers, provided by overrides.
        :return: recordset of active model for ids.
        """
        if docids:
            ids = docids
        elif data and 'context' in data:
            ids = data["context"].get('active_ids', [])
        else:
            ids = self.env.context.get('active_ids', [])
        return self.env[self.env.context.get('active_model')].browse(ids)

    def export_xls(self):
        if not self.receivable and not self.payable:
            raise UserError(_("You should select one type at least"))
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'account.move'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return {'type': 'ir.actions.report',
                'report_name': 'age_receivable_ext.xlsx_age_receivable',
                'context': dict(self.env.context, report_file='account_move'),
                'data': datas,
                'name': 'Age Report',
                'report_type': 'xlsx'
                }
