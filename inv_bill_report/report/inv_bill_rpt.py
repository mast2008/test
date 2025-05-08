# -*- coding: utf-8 -*-
from odoo import models
from .. import user_tz_dtm

class InvBillReportXls(models.AbstractModel):
    _name = 'report.inv_bill_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Sales & Purchase Report'
    
    def get_query_res(self,query):
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()   
    
    def generate_xlsx_report(self, workbook, datas, wiz_obj):
        obj_acc_move = self.env['account.move']
        #product_uom_dp = self.env.ref('product.decimal_product_uom')
        rec = wiz_obj
        user_lang = user_tz_dtm.get_language(self)
        currency_num_format = f"#{user_lang.thousands_sep}##0{user_lang.decimal_point}{rec.currency_id.decimal_places * '0'}"
        #uom_num_format = f"###0.{product_uom_dp.digits * '0'}"
        #col_right = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'right'})
        col_right_currency = workbook.add_format(
            {'bold': True, 'font_size': 10, 'align': 'right', 'num_format': currency_num_format,
             'border':1,'bg_color':'#e6e6e6'})
        #col_right_uom = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'right', 'num_format': uom_num_format})
        row_left = workbook.add_format({'font_size': 10, 'align': 'left'})
        #row_left_number = workbook.add_format({'font_size': 10,'align': 'left','num_format':currency_num_format})
        row_right = workbook.add_format({'font_size': 10, 'align': 'right'})
        row_center = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter'})
        row_right_currency = workbook.add_format({'font_size': 10, 'align': 'right', 'num_format': currency_num_format})
        col_center = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter'})
        col_center_main = workbook.add_format({'bold': True,'font_size': 10,'align': 'center','valign':'vcenter'})
        col_total = workbook.add_format({'bold': True, 'font_size': 10,
                                         'align': 'right', 'valign': 'vcenter',
                                         'border':1,'bg_color':'#e6e6e6'})
        #col_number = workbook.add_format({'bold': True,'font_size': 10,'align': 'center','num_format':currency_num_format})
        col_center_main.set_bg_color("#2481d2")
        col_center_main.set_font_color('#ffffff')
        col_center_main.set_border(1)
        sheet_purchase = workbook.add_worksheet("Purchase Report"[:31])
        sheet_sale = workbook.add_worksheet("Sales Report"[:31])
        col_center.set_border(1)
        col_center.set_bottom_color("#ffffff")
        row_center.set_border(1)
        row_center.set_bottom_color("#ffffff")
        row_center.set_top_color("#ffffff")
        filters = rec.get_report_filters()
        for rpt in ['purchase','sale']:
            sheet = rpt == 'purchase' and sheet_purchase or sheet_sale
            #titles
            row_count = 0
            sheet.merge_range(row_count, 0, row_count, 9, rec.company_id.name, col_center)
            address = []
            rec.company_id.street_name and address.append(rec.company_id.street_name)
            rec.company_id.street2 and address.append(rec.company_id.street2)
            if address:
                row_count += 1
                sheet.merge_range(row_count, 0, row_count, 9, ", ".join(address), row_center)
            address = []
            rec.company_id.zip and address.append(f"P.O. Box {rec.company_id.zip}")
            rec.company_id.company_registry and address.append(f"CR {rec.company_id.company_registry}")
            rec.company_id.city and address.append(rec.company_id.city)
            rec.company_id.country_id and address.append(rec.company_id.country_id.name)
            if address:
                row_count += 1
                sheet.merge_range(row_count, 0, row_count, 9, ", ".join(address), row_center)
            row_count += 1
            sheet.merge_range(row_count, 0, row_count, 9, rpt == 'purchase' and "TAX PURCHASE REPORT (Including Showroom Sales)" or "TAX SALES REPORT (Including Showroom Purchases)", col_center)
            if rec.date_from or rec.date_to:
                row_count += 1
                period_info = [rec.date_from and user_tz_dtm.get_date_str(self,rec.date_from) or '*',
                               rec.date_to and user_tz_dtm.get_date_str(self,rec.date_to) or '*']
                sheet.merge_range(row_count, 0, row_count, 9, f"For the period of {' to '.join(period_info)}", row_center)
            for filter in filters:
                value = f"{filter['label']} : {filter['value']}"
                if filter['label'] not in ['Customers', 'Vendors']:
                    row_count += 1
                    sheet.merge_range(row_count, 0, row_count, 9, value,row_center)
                elif (filter['label'] == 'Customers' and rpt == 'sale') or (filter['label'] == 'Vendors' and rpt == 'purchase'):
                    row_count += 1
                    sheet.merge_range(row_count, 0, row_count, 9, value, row_center)
            #cols
            row_count += 1
            sheet.set_row(row_count, 30)
            sheet.write(row_count, 0, rpt == 'purchase' and "Bill Number" or 'Invoice Number', col_center_main)
            sheet.set_column(0, 0, 20)
            sheet.write(row_count, 1, rpt == 'purchase' and "Bill Date" or 'Invoice Date', col_center_main)
            sheet.set_column(1, 1, 15)
            sheet.write(row_count, 2, "CR No.", col_center_main)
            sheet.set_column(2, 2, 15)
            sheet.write(row_count, 3, "VAT Account No.", col_center_main)
            sheet.set_column(3, 3, 20)
            sheet.write(row_count, 4, rpt == 'purchase' and "Supplier Name" or 'Client Name', col_center_main)
            sheet.set_column(4, 4, 25)
            sheet.write(row_count, 5, "Good/Service Description", col_center_main)
            sheet.set_column(5, 5, 23)
            sheet.write(row_count, 6, "VAT Rate", col_center_main)
            sheet.set_column(6, 6, 9)
            sheet.write(row_count, 7, f"Total {rec.currency_id.name}\n(Exclusive of VAT)", col_center_main)
            sheet.set_column(7, 7, 15)
            sheet.write(row_count, 8, "VAT Amount", col_center_main)
            sheet.set_column(8, 8, 12)
            sheet.write(row_count, 9, f"Total {rec.currency_id.name}\n(Inclusive of VAT)", col_center_main)
            sheet.set_column(9, 9, 15)
            #query
            domain = [('state','=','posted'),]
            rec.date_from and domain.append(('invoice_date', '>=', rec.date_from))
            rec.date_to and domain.append(('invoice_date', '<=', rec.date_to))
            move_type = [rpt == 'purchase' and 'in_invoice' or 'out_invoice']
            rpt == 'purchase' and rec.incl_bill_credit_note and move_type.append('in_refund')
            rpt == 'sale' and rec.incl_inv_credit_note and move_type.append('out_refund')
            domain.append(('move_type', 'in', move_type))
            rpt == 'purchase' and rec.vendor_ids and domain.append(('partner_id', 'in', rec.vendor_ids.ids))
            rpt == 'sale' and rec.customer_ids and domain.append(('partner_id', 'in', rec.customer_ids.ids))
            moves = obj_acc_move.search(domain)
            price_subtotal_start = "H"+str(row_count+2)
            price_tax_start = "I" + str(row_count + 2)
            price_total_start = "J" + str(row_count + 2)
            cell_default_height = 15 #as per documentation
            for move in moves:
                is_refund = move.move_type in ['out_refund','in_refund'] and True or False
                for line in move.invoice_line_ids:
                    row_count += 1
                    #cell height adjustment
                    line.name and len(line.name.split("\n")) > 1 and sheet.set_row(row_count, cell_default_height * len(line.name.split("\n")))
                    sheet.write(row_count, 0, move.name, row_left)
                    sheet.write(row_count, 1, move.invoice_date and user_tz_dtm.get_date_str(self,move.invoice_date) or '', row_right)
                    sheet.write(row_count, 2, move.partner_id.company_registry or '', row_left)
                    sheet.write(row_count, 3, move.partner_id.vat or '', row_left)
                    sheet.write(row_count, 4, move.partner_id.name or '', row_left)
                    sheet.write(row_count, 5, line.name or line.product_id.display_name or '', row_left)
                    sheet.write(row_count, 6, ", ".join(line.tax_ids.mapped('description')), row_right)
                    sheet.write_number(row_count, 7, is_refund and -line.price_subtotal or line.price_subtotal, row_right_currency)
                    sheet.write_number(row_count, 8, (is_refund and -line.price_total or line.price_total) - (is_refund and -line.price_subtotal or line.price_subtotal), row_right_currency)
                    sheet.write_number(row_count, 9, is_refund and -line.price_total or line.price_total, row_right_currency)
            price_subtotal_end = "H" + str(row_count + 1)
            price_tax_end = "I" + str(row_count + 1)
            price_total_end = "J" + str(row_count + 1)
            row_count += 1
            #totals
            sheet.merge_range(row_count,0,row_count,6,'',col_total)
            sheet.write(row_count, 7, f'=SUM({price_subtotal_start}:{price_subtotal_end})', col_right_currency)
            sheet.write(row_count, 8, f'=SUM({price_tax_start}:{price_tax_end})', col_right_currency)
            sheet.write(row_count, 9, f'=SUM({price_total_start}:{price_total_end})', col_right_currency)
        workbook.close()
