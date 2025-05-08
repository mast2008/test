# -*- coding: utf-8 -*-
import collections
from odoo import api, fields, models, _
import time
from collections import OrderedDict
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar


class CashFlowReport(models.TransientModel):
    _name = "cash.flow.report"
    _description = "Cash Flow Report"

    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                              ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
                              ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')],
                             string='Month', required="True")
    year = fields.Integer(string='Year', required="True")

    def check_report_cash_flow_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'cash.flow.report'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('cash_flow_report.action_report_cash_flow_xlx').report_action(self, data=datas)

    def check_report_cash_flow(self):

        self.get_report_values_cash_flow()
        return self.env.ref('cash_flow_report.action_report_cash_flow').report_action(self)

    def get_report_values_cash_flow(self):
        code = self._fields['month'].selection
        code_dict = dict(code)
        selected_name = code_dict.get(self.month)
        print("selected_name", selected_name)
        month = self.month
        year = self.year
        print("month==", month)

        date_from = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d").date()
        print("date_from==", date_from)

        periods = {}
        bank_data = {}
        cash_data = {}
        start = datetime.strptime(f"{year}-{month}-1", "%Y-%m-%d")
        pp = 12
        print("pp---", pp)

        mm = self.month
        datef = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d").date()
        print("mm--", mm)
        for i in range(pp)[::-1]:
            start = datef
            res = calendar.monthrange(start.year, start.month)[1]
            period_stop = datetime.strptime(f"{start.year}-{start.month}-{res}", "%Y-%m-%d").date()
            period_name = str(period_stop)

            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (start or False),
            }
            datef = start + relativedelta(months=1)
            print("datef===", datef)
        print("periods==", periods)
        print("period_stop==", period_stop)
        customer = []
        total_customer = []
        in_process = []
        total_in_process = []
        ven = []
        total_ven = []
        total = []
        cr = self.env.cr
        user_company = self.env.user.company_id
        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        company_ids = self._context.get('company_ids') or [user_company.id]

        customer_acc_ids = self.env.company.customer_acc.ids
        print("customer_acc_ids===", customer_acc_ids)
        if customer_acc_ids:
            # periods query for creating the labels and periods ranges
            arg_list = (tuple(customer_acc_ids),tuple(company_ids))

            query = '''
                                 SELECT DISTINCT aml.partner_id, UPPER(res_partner.name)
                                 FROM account_move_line AS aml left join res_partner on aml.partner_id = res_partner.id, account_move move
                                  WHERE (aml.account_id IN %s)
                                     AND (aml.move_id = move.id)
                                     AND (move.state = 'posted')
                                     AND aml.company_id = %s
                                 ORDER BY UPPER(res_partner.name)'''

            cr.execute(query, arg_list)

            partners = cr.dictfetchall()
            print("partners", partners)
            # put a total of 0

            for i in range(pp + 2):
                total.append(0)

            # Build a string like (1,2,3) for easy use in SQL query
            partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
            print("partner_ids", partner_ids)
            lines = dict((partner['partner_id'] or False, []) for partner in partners)

            if not partner_ids:
                partner_ids = [0, -1]

            history = []
            ll = []

            for i in range(pp)[::-1]:
                args_list = (tuple(customer_acc_ids), tuple(partner_ids),)
                dates_query = '(COALESCE(am.invoice_date_due)'
                if i == int(len(range(pp)) - 1):
                    print("FAAAA")
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                elif periods[str(i)]['start'] and periods[str(i)]['stop']:
                    dates_query += ' BETWEEN %s AND %s)'
                    args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
                elif periods[str(i)]['start']:
                    dates_query += ' >= %s)'
                    args_list += (periods[str(i)]['start'],)
                else:
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                args_list += (tuple(company_ids))

                query = '''SELECT aml.id
                                FROM account_move_line aml, account_move am
                               WHERE (aml.move_id = am.id)
                                   AND (am.state = 'posted')
                                   AND (aml.account_id IN %s)
                                   AND ((aml.partner_id IN %s) OR (aml.partner_id IS NULL))
                                   AND ''' + dates_query + '''

                                AND aml.company_id = %s
                                ORDER BY am.invoice_date_due desc


                       '''

                cr.execute(query, args_list)
                partners_amount = {}
                partners_line = {}
                aml_ids = cr.fetchall()
                print("aml_ids22==", aml_ids)
                move_ids_used = []
                aml_ids = aml_ids and [x[0] for x in aml_ids] or []
                for line in self.env['account.move.line'].browse(aml_ids):
                    if line.move_id.id in move_ids_used:
                        continue
                    partner_id = line.partner_id.id or False
                    if partner_id not in partners_amount:
                        partners_amount[partner_id] = {'amount': 0.0,
                                                       'date': line.move_id.invoice_date_due,
                                                       }
                        partners_line[partner_id] = line.id
                        print("fff", partners_line[partner_id])
                    line_amount = line.move_id.amount_residual
                    '''
                    line_amount = line.currency_id._convert(line.move_id.amount_residual, self.env.company.currency_id,
                                                            line.company_id,
                                                            line.date or fields.Date.today(),
                                                            round=False)
                    '''
                    print("line_line_amountamount", line_amount)

                    if user_currency.is_zero(line_amount):
                        continue

                    if not self.env.user.company_id.currency_id.is_zero(line_amount):
                        move_ids_used.append(line.move_id.id)
                        partners_amount[partner_id]['amount'] += line.move_id.amount_residual
                        # partners_amount[partner_id]['date'] = line.move_id.invoice_date_due


                        lines[partner_id].append({
                            'line': line,
                            'amount': line_amount,
                            'period': i + 1,
                        })
                print("move_ids_used====", move_ids_used)
                history.append(partners_amount)
                ll.append(partners_line)
            print("history==", history)
            print("ll==", ll)
            totalresult_c = {}
            total_column_c = {}
            for partner in partners:
                if partner['partner_id'] is None:
                    partner['partner_id'] = False
                at_least_one_amount = False
                values = {}

                total[pp + 1] = total[pp + 1]
                column = {}

                for i in range(pp)[::-1]:
                    during = False
                    print("history[i]:", history[i])
                    if partner['partner_id'] in history[i]:
                        during = [history[i][partner['partner_id']]]
                        print("during===", during[0]['amount'])
                        print("during date===", during[0]['date'])

                    # Adding counter
                    column[str(i)] = {'amount': during and during[0]['amount'] or 0.0,
                                      'date': during and during[0]['date'] or False}
                    print("column[str(i)]===", column[str(i)])
                    print("column[str(i)][0]['amount']", column[str(i)]['amount'])

                    if not total_column_c.get(i):
                        total_column_c[i] = 0

                    total_column_c[i] = total_column_c[i] + (during and during[0]['amount'] or 0)

                    if not float_is_zero(column[str(i)]['amount'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                        at_least_one_amount = True
                print("column====", column)
                values['col'] = column
                values['partner_id'] = partner['partner_id']
                for j in range(pp):
                    if partner['partner_id'] in ll[j]:
                        print("ll[j]==", ll[j])
                        browsed_aml = self.env['account.move.line'].browse(ll[j][partner['partner_id']])
                        # print("browsed_aml", browsed_aml.move_id.invoice_line_ids.sale_line_ids.order_id.validity_date)
                        values['aml'] = browsed_aml.date
                if partner['partner_id']:
                    browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                    values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 \
                                     and browsed_partner.name[0:40] + '...' or browsed_partner.name
                    values['trust'] = browsed_partner.trust
                else:
                    values['name'] = _('Unknown Partner')
                    values['trust'] = False

                if at_least_one_amount or (
                        self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                    customer.append(values)
            print("total_column_c", total_column_c)
            totalresult_c['t_col'] = total_column_c
            total_customer.append(totalresult_c)
            print("customer==", customer)
            print("total_customer==", total_customer)

        # Bank line
        bank_acc_ids = self.env.company.bank_acc.ids
        print("bank_acc_ids===", bank_acc_ids)
        if bank_acc_ids:
            bank_value = 0
            date_f = f"{date_from} 23:59:59"
            date_t = f"{period_stop} 23:59:59"
            #account_type = ['Bank and Cash']
            arg_list = (tuple(bank_acc_ids), str(date_f), tuple(company_ids))
            print("arg_list=====", arg_list)
            query = '''
                                               SELECT l.account_id AS id, SUM(l.debit) AS debit, SUM(l.credit) AS credit, 
                                               (SUM(l.debit) - SUM(l.credit)) AS balance
                                               FROM account_move_line AS l 
                                               JOIN account_move move ON l.move_id = move.id
                                               WHERE l.account_id IN %s
                                                   AND (move.state = 'posted')
                                                   AND (l.date < %s)
                                                   AND l.company_id = %s
                                               GROUP BY l.account_id'''
            cr.execute(query, arg_list)

            bank = cr.dictfetchall()
            print("bank==", bank)
            i = 0
            for bb in bank:
                bank_value = bank_value + bb['balance']
            print("bank_value==", bank_value)

        # in process table
        in_process_ids = self.env.company.in_process_acc.ids
        print("in_process_ids===", in_process_ids)
        if in_process_ids:
            arg_list = (tuple(in_process_ids), tuple(company_ids))
            query = '''
                                      SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
                                      FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_move move
                                      WHERE (l.account_id IN %s)
                                        AND (l.move_id = move.id)
                                        AND (move.state = 'posted')
                                        AND l.company_id = %s
                                      ORDER BY UPPER(res_partner.name)'''
            cr.execute(query, arg_list)

            partners_so = cr.dictfetchall()
            print("partners_so", partners_so)

            # Build a string like (1,2,3) for easy use in SQL query
            partner_ids_so = [partner['partner_id'] for partner in partners_so if partner['partner_id']]
            print("partner_ids_so", partner_ids_so)
            lines_so = dict((partner['partner_id'] or False, []) for partner in partners_so)

            if not partner_ids_so:
                partner_ids_so = [0, -1]

            historyso = []
            llso = []
            for i in range(pp)[::-1]:
                print("stopppp", date_t)
                args_list = (tuple(in_process_ids), tuple(partner_ids_so),)
                dates_query = '(COALESCE(am.invoice_date_due)'
                if i == int(len(range(pp)) - 1):
                    print("FAAAA process")
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                elif periods[str(i)]['start'] and periods[str(i)]['stop']:
                    dates_query += ' BETWEEN %s AND %s)'
                    args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
                elif periods[str(i)]['start']:
                    dates_query += ' >= %s)'
                    args_list += (periods[str(i)]['start'],)
                else:
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                args_list += (tuple(company_ids))
                query = '''SELECT l.id
                                       FROM account_move_line AS l, account_move am
                                       WHERE (l.move_id = am.id)
                                          AND (am.state = 'posted')
                                          AND (l.account_id IN %s)
                                          AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                                          AND ''' + dates_query + '''

                                           AND l.company_id = %s
                                       ORDER BY am.invoice_date_due desc
                               '''
                cr.execute(query, args_list)

                sol_ids = cr.fetchall()
                print("sol_ids==", sol_ids)
                partners_amount_so = {}
                partners_line_so = {}
                move_ids_used = []

                sol_ids = sol_ids and [x[0] for x in sol_ids] or []
                for line in self.env['account.move.line'].browse(sol_ids):
                    if line.move_id.id in move_ids_used:
                        continue
                    partner_id = line.partner_id.id or False
                    if partner_id not in partners_amount_so:
                        partners_amount_so[partner_id] = {'amount': 0.0,
                                                          'date': line.move_id.invoice_date_due,
                                                          }
                        partners_line_so[partner_id] = line.id
                    line_amount = line.move_id.amount_residual

                    if user_currency.is_zero(line_amount):
                        continue

                    if not self.env.user.company_id.currency_id.is_zero(line_amount):
                        move_ids_used.append(line.move_id.id)
                        partners_amount_so[partner_id]['amount'] += line.move_id.amount_residual

                historyso.append(partners_amount_so)
                llso.append(partners_line_so)
            print("historyso==", historyso)
            totalresult_so = {}
            total_column_so = {}
            t_col_row = 0.0
            for partner in partners_so:
                if partner['partner_id'] is None:
                    partner['partner_id'] = False
                at_least_one_amount = False
                values_so = {}
                total[pp + 1] = total[pp + 1]

                column_so = {}
                # t_row = 0.0

                for i in range(pp)[::-1]:
                    during = False
                    dur = False
                    if partner['partner_id'] in historyso[i]:
                        during = [historyso[i][partner['partner_id']]]
                        # dur = historyso[i][partner['partner_id']]

                    # Adding counter
                    total[(i)] = total[(i)] + (during and during[0]['amount'] or 0)
                    column_so[str(i)] = {'amount': during and during[0]['amount'] or 0.0,
                                         'date': during and during[0]['date'] or False}
                    # t_row = t_row + dur
                    if not total_column_so.get(i):
                        total_column_so[i] = 0

                    total_column_so[i] = total_column_so[i] + (during and during[0]['amount'] or 0)

                    if not float_is_zero(column_so[str(i)]['amount'],
                                         precision_rounding=self.env.user.company_id.currency_id.rounding):
                        at_least_one_amount = True
                print("process column==", column_so)
                # t_col_row = t_col_row + t_row
                # print("column_so", column_so, t_row)
                values_so['col'] = column_so

                values_so['partner_id'] = partner['partner_id']
                for j in range(pp):
                    if partner['partner_id'] in llso[j]:
                        browsed_aml = self.env['account.move.line'].browse(llso[j][partner['partner_id']])
                        values_so['aml'] = browsed_aml.date
                if partner['partner_id']:
                    browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                    values_so['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 \
                                        and browsed_partner.name[0:40] + '...' or browsed_partner.name
                    values_so['trust'] = browsed_partner.trust
                else:
                    values_so['name'] = _('Unknown Partner')
                    values_so['trust'] = False

                if at_least_one_amount or (
                        self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                    in_process.append(values_so)
            print("total_column_so", total_column_so, t_col_row)
            totalresult_so['t_col'] = total_column_so
            total_in_process.append(totalresult_so)
            print("in_process==", in_process)
            print("total_in_process==", total_in_process)

        # Vendor Table
        vendor_ids = self.env.company.vendor_acc.ids
        print("vendor_ids===", vendor_ids)
        if vendor_ids:
            arg_list = (tuple(vendor_ids), tuple(company_ids))

            query = '''
                                SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
                                 FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_move move 
                                 WHERE (l.account_id IN %s)
                                    AND (l.move_id = move.id)
                                    AND (move.state = 'posted')
                                    AND l.company_id = %s
                                 ORDER BY UPPER(res_partner.name)'''

            cr.execute(query, arg_list)

            partners_ven = cr.dictfetchall()
            print("partners_ven", partners_ven)
            partner_ids_v = [partner['partner_id'] for partner in partners_ven if partner['partner_id']]
            print("partner_ids_v", partner_ids_v)
            lines = dict((partner['partner_id'] or False, []) for partner in partners_ven)

            if not partner_ids_v:
                partner_ids_v = [0, -1]

            historyven = []
            ll_ven = []
            for i in range(pp)[::-1]:
                args_list = (tuple(vendor_ids), tuple(partner_ids_v),)
                dates_query = '(COALESCE(am.invoice_date_due)'
                if i == int(len(range(pp)) - 1):
                    print("FAAAA")
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                elif periods[str(i)]['start'] and periods[str(i)]['stop']:
                    dates_query += ' BETWEEN %s AND %s)'
                    args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
                elif periods[str(i)]['start']:
                    dates_query += ' >= %s)'
                    args_list += (periods[str(i)]['start'],)
                else:
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                args_list += (tuple(company_ids))
                query = '''SELECT l.id
                                  FROM account_move_line l, account_move am
                                  WHERE (l.move_id = am.id)
                                      AND (am.state = 'posted')
                                      AND (l.account_id IN %s)
                                      AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                                      AND ''' + dates_query + '''
                                      AND l.company_id = %s
                                  ORDER BY am.invoice_date_due desc
                         '''

                cr.execute(query, args_list)
                partners_amount_ven = {}
                partners_line_ven = {}
                aml_ids = cr.fetchall()
                print("aml_ids4==", aml_ids)
                move_ids_used = []

                aml_ids = aml_ids and [x[0] for x in aml_ids] or []
                for line in self.env['account.move.line'].browse(aml_ids):
                    if line.move_id.id in move_ids_used:
                        continue
                    partner_id = line.partner_id.id or False
                    if partner_id not in partners_amount_ven:
                        partners_amount_ven[partner_id] = {'amount': 0.0,
                                                           'date': line.move_id.invoice_date_due,
                                                           }
                        partners_line_ven[partner_id] = line.id
                    line_amount = line.move_id.amount_residual

                    # line_amount = (-line_amount)
                    if user_currency.is_zero(line_amount):
                        continue

                    if not self.env.user.company_id.currency_id.is_zero(line_amount):
                        move_ids_used.append(line.move_id.id)
                        partners_amount_ven[partner_id]['amount'] += line.move_id.amount_residual

                historyven.append(partners_amount_ven)
                ll_ven.append(partners_line_ven)

            print("historyven==", historyven)
            totalresult_v = {}
            total_column_v = {}
            for partner in partners_ven:
                if partner['partner_id'] is None:
                    partner['partner_id'] = False
                at_least_one_amount = False
                values_ven = {}

                total[pp + 1] = total[pp + 1]

                column = {}

                for i in range(pp)[::-1]:
                    during = False
                    if partner['partner_id'] in historyven[i]:
                        during = [historyven[i][partner['partner_id']]]

                    # Adding counter
                    total[(i)] = total[(i)] + (during and during[0]['amount'] or 0)
                    column[str(i)] = {'amount': during and during[0]['amount'] or 0.0,
                                      'date': during and during[0]['date'] or False}
                    if not total_column_v.get(i):
                        total_column_v[i] = 0

                    total_column_v[i] = total_column_v[i] + (during and during[0]['amount'] or 0)

                    if not float_is_zero(column[str(i)]['amount'],
                                         precision_rounding=self.env.user.company_id.currency_id.rounding):
                        at_least_one_amount = True
                print("ven column==", column)

                values_ven['col'] = column

                values_ven['partner_id'] = partner['partner_id']
                for j in range(pp):
                    if partner['partner_id'] in ll_ven[j]:
                        browsed_aml_ven = self.env['account.move.line'].browse(ll_ven[j][partner['partner_id']])

                        # print("browsed_aml", browsed_aml.move_id.invoice_date)
                        values_ven['aml'] = browsed_aml_ven.date

                if partner['partner_id']:
                    browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                    values_ven['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 \
                                         and browsed_partner.name[0:40] + '...' or browsed_partner.name
                    values_ven['trust'] = browsed_partner.trust
                else:
                    values_ven['name'] = _('Unknown Partner')
                    values_ven['trust'] = False

                if at_least_one_amount or (
                        self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                    ven.append(values_ven)
            print("total_column_v", total_column_v)
            totalresult_v['t_col'] = total_column_v
            total_ven.append(totalresult_v)
            print("ven==", ven)
            print("total_ven==", total_ven)

        # bank data
        if vendor_ids and in_process_ids and customer_acc_ids:
            for i in range(pp - 1):
                if i == 0:
                    ff = bank_value
                else:
                    for val in bank_data:
                        ff = bank_data[val]['val']
                bank_data[str(i)] = {
                    'val': (ff + total_column_c[i]) + total_column_so[i] - total_column_v[i],

                }
                mm = int(mm) + 1
            print("bank_data==", bank_data)
        # cash flow data
        if vendor_ids and in_process_ids and customer_acc_ids:
            for i in range(pp):
                if i == 0:
                    ff = bank_value
                else:
                    for val in cash_data:
                        ff = bank_data[val]['val']
                        # print("ff===",ff)
                cash_data[str(i)] = {
                    'val': (ff + total_column_c[i]) + total_column_so[i] - total_column_v[i],

                }
                mm = int(mm) + 1
            print("cash_data==", cash_data)

        return periods, customer, in_process, ven, total_customer, total_in_process, total_ven, selected_name, bank_value, bank_data, cash_data
