
from datetime import datetime, timedelta
from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import calendar
import base64
import io
import re
from . import user_tz_dtm


LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def excel_style(row, col):
    """ Convert given row and column number to an Excel-style cell name. """
    result = []
    while col:
        col, rem = divmod(col-1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result) + str(row)



class PartnerLedger(models.AbstractModel):
    _name = 'report.partner_ledger_report_xlsx'    
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, record):

        user_lang = user_tz_dtm.get_language(self)
        currency_num_format = f"#{user_lang.thousands_sep}##0{user_lang.decimal_point}{self.env.user.company_id.currency_id.decimal_places * '0'}"
        
        top_heading_left = workbook.add_format({'align': 'left',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 12})
        
        partner_heading_left = workbook.add_format({'align': 'left',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 11})
        
        op_heading_right = workbook.add_format({'align': 'right',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 11})
        
        op_bal_heading_left =  workbook.add_format({'num_format': currency_num_format,
                                                      'valign': 'vcenter', 'bold': True,
                                                      'align' : 'right', 'size': 11})
        
        shading_below = workbook.add_format({'bg_color': '#a8a9ad', 'size': 10})
        
        sub_heading_left = workbook.add_format({'align': 'left',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 10})
        
        sub_heading_center = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 10})
        
        sub_heading_right = workbook.add_format({'align': 'right',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 10})
        
        sub_total_right = workbook.add_format({'num_format': '#,##0.00', 
                                              'valign': 'vcenter', 'bold': True,
                                              'align' : 'right', 'size': 11})

        date_format_left = workbook.add_format({'num_format':  'dd/mm/yyyy',
                                           'align': 'left',
                                           'valign': 'vcenter',
                                           'size': 10})
        
        summary_heading_right = workbook.add_format({'align': 'right',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 12,'border':True})
        
        summary_heading_left = workbook.add_format({'align': 'left',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 12,'border':True})
        
        total_heading_left = workbook.add_format({'align': 'left',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 11})
        
        total_heading_right = workbook.add_format({'align': 'right',
                                              'num_format': '#,##0.00', 
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 11,'border':True})
        
        period_format = workbook.add_format({'num_format':  'dd/mm/yyyy',
                                           'align': 'left',
                                           'valign': 'vcenter',
                                           'bold': True,
                                           'size': 11})
        
        column_details_left = workbook.add_format({'align': 'left',
                                              'valign': 'vcenter',
                                              'text_wrap': True,
                                               'size': 10,'border':True})
        
        column_numbers_right =  workbook.add_format({'num_format': currency_num_format,
                                                      'valign': 'vcenter',
                                                      'align' : 'right', 'size': 10,'border':True})
        
        company_address_format = workbook.add_format({'align': 'left',
                                              'valign': 'vcenter',
                                              'font_color': '#4757c1',
                                              'bold': True, 'size': 11})
        format1 = workbook.add_format({'font_size': 12,'bold':True})
        format1.set_align('center')
        format21 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format10 = workbook.add_format({'font_size': 10, 'align': 'center','bold':True})

        worksheet = workbook.add_worksheet("Partner Ledger Report")
        
        row = 1
        
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 12)
        
        company_address_col = 6
        
        if record.summary_format:
            worksheet.set_column('A:A', 10)
            worksheet.set_column('B:B', 25)
            worksheet.set_column('C:C', 25)
            worksheet.set_column('D:D', 12)
            worksheet.set_column('E:E', 20)
            worksheet.set_column('F:F', 20)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 20)
            company_address_col = 7
            



        worksheet.merge_range(1, 0, 1, 9, str(self.env.user.company_id.name), format1)
        buf_image = io.BytesIO(base64.b64decode(self.env.user.company_id.logo))
        # sheet.set_column(1, 9, 15)
        worksheet.insert_image('B2', "any_name.png", {'image_data': buf_image, 'x_scale': 0.1, 'y_scale': 0.1})
        address_company = []
        if self.env.user.company_id.street:
            address_company.append('Flat/Shop No. ' + self.env.user.company_id.street)
        if self.env.user.company_id.street2:
            address_company.append('Building ' + self.env.user.company_id.street2)
        if self.env.user.company_id.city:
            address_company.append(self.env.user.company_id.city)
        if self.env.user.company_id.zip:
            address_company.append(self.env.user.company_id.zip)
        if self.env.user.company_id.country_id:
            address_company.append(self.env.user.company_id.country_id.name)
        worksheet.merge_range(2, 0, 2, 9, str(', '.join(address_company)), format21)
        row += 3
        from_date = record.from_date or False
        to_date = record.to_date or False
        if record.account_filter == 'receivable':
            worksheet.merge_range(3, 0, 3, 9, 'Account Receivables as on' + str(to_date), format10)
        if record.account_filter == 'payable':
            worksheet.merge_range(3, 0, 3, 9, 'Account  Payables  as on' + str(to_date), format10)
        if record.account_filter == 'receivable_payable':
            worksheet.merge_range(3, 0, 3, 9, 'Account Receivables and  Payables  as on' + str(to_date), format10)

        
        all_partner_objs = self.env['res.partner'].search([('active','=',True)], order="name asc")
        partner_ids = (record.partner_ids and record.partner_ids.ids) or (all_partner_objs and all_partner_objs.ids) or []
        include_opening_bal = record.include_opening_balance or False
        include_movement_filter = record.include_movement_filter or False
        account_filter = record.account_filter or False
        show_zero_balance = record.show_zero_balance or False
        posted_entries_only = record.posted_entries_only or False
        account_ids = record.account_ids and record.account_ids.ids or []
        summary_format = record.summary_format or False
        summary_added = False
        summary_grand_debit = 0.000
        summary_grand_credit = 0.000
        summary_grand_balance = 0.000
        
        if summary_format:
            row += 1
            worksheet.write(row, 0, 'Sl No', summary_heading_left)
            starting_col = excel_style(row + 1, 2)
            ending_col = excel_style(row + 1, 4)
            if record.account_filter == 'receivable':
                worksheet.merge_range('%s:%s'%(starting_col, ending_col), 'Customer Name', summary_heading_left)
            elif record.account_filter == 'payable':
                worksheet.merge_range('%s:%s'%(starting_col, ending_col), 'Supplier Name', summary_heading_left)
            else:
                worksheet.merge_range('%s:%s' % (starting_col, ending_col), 'Partner Name', summary_heading_left)

            worksheet.write(row, 4, 'Opening Balance', summary_heading_right)
            worksheet.write(row, 5, 'Debit', summary_heading_right)
            worksheet.write(row, 6, 'Credit', summary_heading_right)
            worksheet.write(row, 7, 'Closing Balance', summary_heading_right)
            #row += 1
            #starting_col = excel_style(row + 1, 1)
            #ending_col = excel_style(row + 1, 7)
            #worksheet.merge_range('%s:%s'%(starting_col, ending_col), '', shading_below)
            partner_sl_no = 1
        cr = self.env.cr
        for partner_id in partner_ids:
            partner_obj = self.env['res.partner'].browse(partner_id)
            if summary_format:
                if from_date:
                    opening_where_condition = """aml.date < '{0}'""".format(from_date)
                    opening_where_condition += """ AND (aml.partner_id = {0})""".format(partner_id)
                    if posted_entries_only:
                        opening_where_condition += """ AND am.state = 'posted'"""
                    if account_ids and not account_filter:
                        if len(account_ids) == 1:
                            opening_where_condition += ''' AND aml.account_id = %s''' % account_ids[0]
                        else:
                            opening_where_condition += ''' AND aml.account_id IN {0}'''.format(tuple(account_ids))

                    elif account_filter:
                        if account_filter == 'receivable':
                            opening_where_condition += """ AND aat.type = 'receivable'"""

                        elif account_filter == 'payable':
                            opening_where_condition += """ AND aat.type = 'payable'"""

                        else:
                            opening_where_condition += """ AND aat.type In ('payable','receivable')"""

                    cr.execute("""
                                        Select
                                            sum((aml.debit - aml.credit)) as balance 
                                        From 
                                            account_move_line aml 
                                        Left Join
                                            account_account aa 
                                        on 
                                            (aa.id = aml.account_id)
                                        Left Join 
                                            account_account_type aat
                                        on 
                                            (aat.id = aa.user_type_id)
                                        Left Join 
                                            account_move am 
                                        on 
                                            (am.id = aml.move_id) 
                                        Where 
                                            %s
                                        """ % opening_where_condition)
                    dict_val = cr.dictfetchall()
                    dict_val = dict_val and dict_val[0] or False
                    opening_balance = dict_val and dict_val.get('balance') is not None and dict_val.get('balance') or False
                    print("dict_val",dict_val)

                summary_where_condition = """(aml.partner_id = {0})""".format(partner_id)
                if not include_opening_bal and from_date:
                    summary_where_condition += """ AND aml.date >= '{0}'""".format(from_date)
                if to_date:
                    summary_where_condition += """ AND aml.date <= '{0}'""".format(to_date)
                if posted_entries_only:
                    summary_where_condition += """ AND am.state = 'posted'"""
                if not account_filter and account_ids:
                    if len(account_ids) == 1:
                        summary_where_condition += ''' AND aml.account_id = %s''' % account_ids[0]
                    else:
                        summary_where_condition += ''' AND aml.account_id IN {0}'''.format(tuple(account_ids))
                elif account_filter:
                    if account_filter == 'receivable':
                        summary_where_condition += """ AND aat.type = 'receivable'"""

                    elif account_filter == 'payable':
                        summary_where_condition += """ AND aat.type = 'payable'"""
                    else:
                        summary_where_condition += """ AND aat.type In ('payable','receivable')"""
                    
                cr.execute("""
                    Select
                        sum(aml.debit) as total_debit,
                        sum(aml.credit) as total_credit 
                    From 
                        account_move_line aml 
                    Left Join 
                        account_move am 
                    on 
                        (am.id = aml.move_id) 
                    Left Join
                        account_account aa 
                    on 
                        (aa.id = aml.account_id)
                    Left Join 
                        account_account_type aat
                    on 
                        (aat.id = aa.user_type_id)
                    Where 
                        %s
                    """ %summary_where_condition)
                
                dict_val = cr.dictfetchall()
                dict_val = dict_val and dict_val[0] or False
                total_debit = dict_val and dict_val.get('total_debit') is not None and [dict_val.get('total_debit')] or False
                total_credit = dict_val and dict_val.get('total_credit') is not None and [dict_val.get('total_credit')] or False
                    
                if total_debit or total_credit:
                    total_debit = total_debit and round(total_debit[0],2) or 0.00
                    total_credit = total_credit and round(total_credit[0],2) or 0.00
                    total_balance = total_debit - total_credit
                    if total_balance != 0.00:
                        row += 1
                        worksheet.write(row, 0, partner_sl_no, column_details_left)
                        starting_col = excel_style(row + 1, 2)
                        ending_col = excel_style(row + 1, 4)
                        partner_name = partner_obj.name or ''
                        worksheet.merge_range('%s:%s'%(starting_col, ending_col), partner_name, column_details_left)
                        worksheet.write(row, 4,   opening_balance, column_numbers_right)
                        worksheet.write(row, 5, total_debit, column_numbers_right)
                        worksheet.write(row, 6, total_credit, column_numbers_right)
                        worksheet.write(row, 7, total_balance, column_numbers_right)
                        summary_grand_debit += total_debit
                        summary_grand_credit += total_credit
                        summary_grand_balance += total_balance
                        summary_added = True
                        partner_sl_no += 1
                    elif total_balance == 0.00 and show_zero_balance:
                        row += 1
                        worksheet.write(row, 0, partner_sl_no, column_details_left)
                        starting_col = excel_style(row + 1, 2)
                        ending_col = excel_style(row + 1, 4)
                        partner_name = partner_obj.name or ''
                        worksheet.merge_range('%s:%s'%(starting_col, ending_col), partner_name, column_details_left)
                        worksheet.write(row, 4, opening_balance, op_bal_heading_left)
                        worksheet.write(row, 5, total_debit, column_numbers_right)
                        worksheet.write(row, 6, total_credit, column_numbers_right)
                        worksheet.write(row, 7, total_balance, column_numbers_right)
                        summary_grand_debit += total_debit
                        summary_grand_credit += total_credit
                        summary_grand_balance += total_balance
                        summary_added = True
                        partner_sl_no += 1
                elif not include_movement_filter:
                    row += 1
                    worksheet.write(row, 0, partner_sl_no, column_details_left)
                    starting_col = excel_style(row + 1, 2)
                    ending_col = excel_style(row + 1, 4)
                    partner_name = partner_obj.name or ''
                    worksheet.merge_range('%s:%s'%(starting_col, ending_col), partner_name, column_details_left)
                    worksheet.write(row, 4, 0.00, column_numbers_right)
                    worksheet.write(row, 5, 0.00, column_numbers_right)
                    worksheet.write(row, 6, 0.00, column_numbers_right)
                    worksheet.write(row, 7, 0.00, column_numbers_right)
                    summary_grand_debit += 0.00
                    summary_grand_credit += 0.00
                    summary_grand_balance += 0.00
                    summary_added = True
                    partner_sl_no += 1
            
#             else:
#                 opening_balance = False
#                 if from_date:
# #                     opening_where_condition = """aat.type In ('payable','receivable')"""
#                     opening_where_condition = """aml.date < '{0}'""".format(from_date)
#                     opening_where_condition += """ AND (aml.partner_id = {0})""".format(partner_id)
#                     if posted_entries_only:
#                         opening_where_condition += """ AND am.state = 'posted'"""
#
#                     if account_ids and not account_filter:
#                         if len(account_ids) == 1:
#                             opening_where_condition += ''' AND aml.account_id = %s''' % account_ids[0]
#                         else:
#                             opening_where_condition += ''' AND aml.account_id IN {0}'''.format(tuple(account_ids))
#
#                     elif account_filter:
#                         if account_filter == 'receivable':
#                             opening_where_condition += """ AND aat.type = 'receivable'"""
#
#                         elif account_filter == 'payable':
#                             opening_where_condition += """ AND aat.type = 'payable'"""
#
#                         else:
#                             opening_where_condition += """ AND aat.type In ('payable','receivable')"""
#
#
#                     cr.execute("""
#                         Select
#                             sum((aml.debit - aml.credit)) as balance
#                         From
#                             account_move_line aml
#                         Left Join
#                             account_account aa
#                         on
#                             (aa.id = aml.account_id)
#                         Left Join
#                             account_account_type aat
#                         on
#                             (aat.id = aa.user_type_id)
#                         Left Join
#                             account_move am
#                         on
#                             (am.id = aml.move_id)
#                         Where
#                             %s
#                         """ %opening_where_condition)
#                     dict_val = cr.dictfetchall()
#                     dict_val = dict_val and dict_val[0] or False
#                     opening_balance = dict_val and dict_val.get('balance') is not None and [dict_val.get('balance')] or False
#
# #                 where_condition = """aat.type In ('payable','receivable')"""
#                 where_condition = """(aml.partner_id = {0})""".format(partner_id)
#                 if from_date:
#                     where_condition += """ AND aml.date >= '{0}'""".format(from_date)
#                 if to_date:
#                     where_condition += """ AND aml.date <= '{0}'""".format(to_date)
#
#
#                 if posted_entries_only:
#                     where_condition += """ AND am.state = 'posted'"""
#
#                 if account_ids and not account_filter:
#                     if len(account_ids) == 1:
#                         where_condition += ''' AND aml.account_id = %s''' % account_ids[0]
#                     else:
#                         where_condition += ''' AND aml.account_id IN {0}'''.format(tuple(account_ids))
#
#                 elif account_filter:
#                     if account_filter == 'receivable':
#                         where_condition += """ AND aat.type = 'receivable'"""
#
#                     elif account_filter == 'payable':
#                         where_condition += """ AND aat.type = 'payable'"""
#
#                     else:
#                         where_condition += """ AND aat.type In ('payable','receivable')"""
#
#                 cr.execute("""
#                             Select
#                                 aml.date as date,
#                                 aml.name as label,
#                                 Case when
#                                     am.name is null
#                                 Then
#                                     aml.ref
#                                 else
#                                     am.name
#                                 End
#                                     as ref,
#                                 aml.debit as debit,
#                                 aml.credit as credit,
#                                 (aml.debit - aml.credit) as balance,
#                                 aa.code as account_code,
#                                 aa.name as account_name
#                             From
#                                 account_move_line aml
#                             Left Join
#                                 account_account aa
#                             on
#                                 (aa.id = aml.account_id)
#                             Left Join
#                                 account_account_type aat
#                             on
#                                 (aat.id = aa.user_type_id)
#                             Left Join
#                                 account_move am
#                             on
#                                 (am.id = aml.move_id)
#                             Where
#                                 %s
#                             Order by
#                                 aml.date
#                             """ %where_condition)
#
#                 trnacation_details = cr.dictfetchall()
#
#                 if trnacation_details or (opening_balance and include_opening_bal) or not include_movement_filter:
#                     partner_total = 0.0
#                     partner_credit_total = 0.0
#                     partner_debit_total = 0.0
#                     balance_log = 0.0
#                     row += 2
#                     worksheet.write(row, 0, 'Partner', partner_heading_left)
#                     starting_col = excel_style(row + 1, 2)
#                     ending_col = excel_style(row + 1, 7)
#                     worksheet.merge_range('%s:%s'%(starting_col, ending_col), partner_obj.name, partner_heading_left)
#
#                     if trnacation_details:
#                         row += 2
#                         worksheet.write(row, 0, 'Date', sub_heading_left)
#                         worksheet.write(row, 1, 'Reference', sub_heading_center)
#                         worksheet.write(row, 2, 'Description', sub_heading_center)
#                         worksheet.write(row, 3, 'Debit', sub_heading_right)
#                         worksheet.write(row, 4, 'Credit', sub_heading_right)
#                         worksheet.write(row, 5, 'Balance', sub_heading_right)
#
#
#                         if opening_balance and include_opening_bal:
#                             row += 1
#                             starting_col = excel_style(row + 1, 2)
#                             ending_col = excel_style(row + 1, 5)
#                             worksheet.merge_range('%s:%s'%(starting_col, ending_col), 'Opening Balance', op_heading_right)
#                             worksheet.write(row, 5, opening_balance[0], op_bal_heading_left)
#                             balance_log = opening_balance[0]
#
#                         for items in trnacation_details:
#                             row += 1
#                             date_string = ''
#                             if items.get('date'):
#                                 date_string = items.get('date').strftime('%d-%m-%Y')
#                             worksheet.write(row, 0, date_string, date_format_left)
#                             worksheet.write(row, 1, items.get('label'), column_details_left)
#                             worksheet.write(row, 2, items.get('ref'), column_details_left)
#                             worksheet.write(row, 3, items.get('debit'), column_numbers_right)
#                             worksheet.write(row, 4, items.get('credit'), column_numbers_right)
#                             balance_log += (items.get('debit') - items.get('credit'))
#                             worksheet.write(row, 5, balance_log, column_numbers_right)
#                             partner_credit_total += items.get('credit')
#                             partner_debit_total += items.get('debit')
#
#                     elif not include_movement_filter:
#                         row += 2
#                         worksheet.write(row, 0, 'Date', sub_heading_left)
#                         worksheet.write(row, 1, 'Reference', sub_heading_center)
#                         worksheet.write(row, 2, 'Description', sub_heading_center)
#                         worksheet.write(row, 3, 'Debit', sub_heading_right)
#                         worksheet.write(row, 4, 'Credit', sub_heading_right)
#                         worksheet.write(row, 5, 'Balance', sub_heading_right)
#
#
#                         if opening_balance and include_opening_bal:
#                             row += 1
#                             starting_col = excel_style(row + 1, 2)
#                             ending_col = excel_style(row + 1, 5)
#                             worksheet.merge_range('%s:%s'%(starting_col, ending_col), 'Opening Balance', op_heading_right)
#                             worksheet.write(row, 5, opening_balance[0], op_bal_heading_left)
#         #                     partner_total += opening_balance[0]
#                             balance_log = opening_balance[0]
#
#
#                         row += 1
#                         date_string = ''
#
#                         worksheet.write(row, 0, date_string, date_format_left)
#                         worksheet.write(row, 1, '', column_details_left)
#                         worksheet.write(row, 2, '', column_details_left)
#                         worksheet.write(row, 3, 0.00, column_numbers_right)
#                         worksheet.write(row, 4, 0.00, column_numbers_right)
#                         balance_log += 0.00
#                         worksheet.write(row, 5, balance_log, column_numbers_right)
#                         partner_credit_total += 0.00
#                         partner_debit_total += 0.00
#
#                     if partner_credit_total > 0.0 or partner_debit_total > 0.0:
#                         row += 1
#                         worksheet.write(row, 2, 'Total', sub_heading_right)
#                         worksheet.write(row, 3, partner_debit_total, sub_total_right)
#                         worksheet.write(row, 4, partner_credit_total, sub_total_right)
#     #                     worksheet.write(row, 8, partner_total, sub_total_right)
#                     elif not include_movement_filter:
#                         row += 1
#                         worksheet.write(row, 2, 'Total', sub_heading_right)
#                         worksheet.write(row, 3, 0.00, sub_total_right)
#                         worksheet.write(row, 4, 0.00, sub_total_right)
#
#                     row += 1
#                     starting_col = excel_style(row + 1, 1)
#                     ending_col = excel_style(row + 1, 6)
#                     worksheet.merge_range('%s:%s'%(starting_col, ending_col), '', shading_below)

        
        # if summary_format and summary_added:
        #     row += 1
        #     starting_col = excel_style(row + 1, 1)
        #     ending_col = excel_style(row + 1, 4)
        #     worksheet.merge_range('%s:%s'%(starting_col, ending_col), 'Total', total_heading_left)
        #     worksheet.write(row, 5, summary_grand_debit, total_heading_right)
        #     worksheet.write(row, 6, summary_grand_credit, total_heading_right)
        #     worksheet.write(row, 7, summary_grand_balance, total_heading_right)
        #
        #     #row += 1
        #     #starting_col = excel_style(row + 1, 1)
        #     #ending_col = excel_style(row + 1, 7)
        #     #worksheet.merge_range('%s:%s'%(starting_col, ending_col), '', shading_below)

PartnerLedger()

