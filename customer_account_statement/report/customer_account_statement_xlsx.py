# Author: Christopher Ormaza
# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from datetime import date, datetime
import pytz
import base64
import io

#from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS
from .report_xlsx_format import FORMATS,XLS_HEADERS


class CustomerAccountStatementXslx(models.AbstractModel):
    _name = "report.p_s.report_customer_account_statement_xlsx"
    _description = "Customer Account Statement XLSL Report"
    _inherit = "report.report_xlsx.abstract"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Customer Account Statement")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name
    def _get_report_footer_info(self, company):
        footer1 = " "
        footer2 = " "
        address1 = []
        address2 = []
        if company:
            #company = self.env["res.company"].browse(company_id)
            if company.street_name:
                address1.append(company.street_name)
            if company.street_number:
                address1.append(company.street_number)
            if company.street_number2:
                address1.append(company.street_number2)
            if company.company_registry:
                address1.append('CR '+company.company_registry)
            if company.city:
                address1.append(company.city)
            if company.state_id:
                address1.append(company.state_id.name)
            if company.country_id:
                address1.append(company.country_id.name)
            if company.website:
                address2.append('Website: '+company.website)
            if company.email:
                address2.append('Email: '+company.email)
            if company.phone:
                address2.append('Tel: '+company.phone)
            if address1:
                footer1 = ', '.join(address1)
            if address2:
                footer2 = ', '.join(address2)

        return footer1,footer2
    def _get_report_customer_info(self,customer):
        customer1 = " "
        address1 = []
        if customer:
            if customer.street_name:
                address1.append(customer.street_name)
            if customer.street_number:
                address1.append(customer.street_number)
            if customer.street_number2:
                address1.append(customer.street_number2)
            if customer.city:
                address1.append(customer.city)
            if customer.state_id:
                address1.append(customer.state_id.name)
            if address1:
                customer1 = ', '.join(address1)
        return customer1


    def _write_currency_lines(self, row_pos, sheet, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        account_type = data.get("account_type", False)
        row_pos += 2
        statement_header = _("%(payable)sStatement up to %(end)s in %(currency)s") % {
            "payable": account_type == "payable" and _("Supplier ") or "",
            "end": partner_data.get("end"),
            "currency": currency.display_name,
        }

        sheet.merge_range(
            row_pos, 0, row_pos, 7, statement_header, FORMATS["format_right_bold"]
        )
        row_pos += 1
        sheet.write(row_pos, 0, _("Date"), FORMATS["format_theader_yellow_center"])
        sheet.write(
            row_pos, 1, _("Invoice No."), FORMATS["format_theader_yellow_center"]
        )
        sheet.write(
            row_pos, 2, _("Reference"), FORMATS["format_theader_yellow_center"]
        )
        sheet.write(row_pos, 3, _("Due Date"), FORMATS["format_theader_yellow_center"])
        sheet.write(row_pos, 4, _("Overduces Day"), FORMATS["format_theader_yellow_center"])
        sheet.write(row_pos, 5, _("Invoice Amount"), FORMATS["format_theader_yellow_center"])
        sheet.write(
            row_pos, 6, _("Received Amount"), FORMATS["format_theader_yellow_center"]
        )
        sheet.write(row_pos, 7, _("Pending Dues"), FORMATS["format_theader_yellow_center"])
        print("currency_data",currency_data)
        for line in currency_data.get("lines"):
            row_pos += 1
            name_to_show = (
                line.get("name", "") == "/" or not line.get("name", "")
            ) and line.get("ref", "")
            if line.get("name", "") != "/":
                if not line.get("ref", ""):
                    name_to_show = line.get("name", "")
                else:
                    if line.get("name", "") and ((line.get("ref", "") in line.get("name", "")) or (
                        line.get("name", "") == line.get("ref", "")
                    )):
                        name_to_show = line.get("name", "")
                    else:
                        name_to_show = line.get("ref", "")
            sheet.write(
                row_pos, 0, line.get("date", ""), FORMATS["format_tcell_date_left"]
            )
            sheet.write(
                row_pos, 1, line.get("move_id", ""), FORMATS["format_tcell_left"]
            )
            sheet.write(row_pos, 2, name_to_show, FORMATS["format_distributed"])
            sheet.write(
                row_pos,
                3,
                line.get("date_maturity", ""),
                FORMATS["format_tcell_date_left"],
            )
            if line.get("open_amount", "") and line.get("date_maturity", "") and line.get("move_line", ""):
                date_now = fields.Date.today()
                move_line_id = self.env['account.move.line'].browse(line.get("move_line", ""))
                delta = date_now - (move_line_id.date_maturity or move_line_id.date)
                sheet.write(
                    row_pos, 4, delta.days, FORMATS["format_tcell_right"]
                )
            else:
                sheet.write(
                    row_pos, 4, " ", FORMATS["format_tcell_right"]
                )
            sheet.write(
                row_pos, 5, line.get("amount", ""), FORMATS["current_money_format"]
            )
            sheet.write(
                row_pos, 6, line.get("amount", "")-line.get("open_amount", ""), FORMATS["current_money_format"]
            )
            sheet.write(
                row_pos, 7, line.get("balance", ""), FORMATS["current_money_format"]
            )
        row_pos += 1
        sheet.write(
            row_pos, 0, partner_data.get("end"), FORMATS["format_tcell_date_left"]
        )
        sheet.merge_range(
            row_pos, 2, row_pos, 4, _("Ending Balance"), FORMATS["format_tcell_left"]
        )
        sheet.write(
            row_pos, 7, currency_data.get("amount_due"), FORMATS["current_money_format"]
        )
        return row_pos

    def _write_currency_buckets(self, row_pos, sheet, partner, currency, data):
        report_model = self.env["report.customer_account_statement.customer_account_statement"]
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        if currency_data.get("buckets"):
            row_pos += 2
            buckets_header = _("Aging Report at %(end)s in %(currency)s") % {
                "end": partner_data.get("end"),
                "currency": currency.display_name,
            }

            sheet.merge_range(
                row_pos, 0, row_pos, 7, buckets_header, FORMATS["format_right_bold"]
            )
            buckets_data = currency_data.get("buckets")
            buckets_labels = report_model._get_bucket_labels(
                partner_data.get("end"), data.get("aging_type")
            )
            row_pos += 1
            for i in range(len(buckets_labels)):
                sheet.write(
                    row_pos,
                    i,
                    buckets_labels[i],
                    FORMATS["format_theader_yellow_center"],
                )
            row_pos += 1
            sheet.write(
                row_pos,
                0,
                buckets_data.get("b_0_30", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                1,
                buckets_data.get("b_30_60", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                2,
                buckets_data.get("b_60_90", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                3,
                buckets_data.get("b_90_120", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                4,
                buckets_data.get("b_120_150", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                5,
                buckets_data.get("b_150_180", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                6,
                buckets_data.get("b_over_180", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                7,
                buckets_data.get("balance", 0.0),
                FORMATS["current_money_format"],
            )
        return row_pos

    def _size_columns(self, sheet):
        for i in range(8):
            sheet.set_column(0, i, 20)

    def generate_xlsx_report(self, workbook, data, objects):
        report_model = self.env["report.customer_account_statement.customer_account_statement"]
        self._define_formats(workbook)
        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})

        FORMATS["format_distributed"] = workbook.add_format({"align": "vdistributed"})
        company_id = data.get("company_id", False)
        if company_id:
            company = self.env["res.company"].browse(company_id)
        else:
            company = self.env.user.company_id
        data.update(report_model._get_report_values(data.get("partner_ids"), data))
        partners = self.env["res.partner"].browse(data.get("partner_ids"))
        sheet = workbook.add_worksheet(_("Customer Account Statement"))
        sheet.set_landscape()
        row_pos = 0
        sheet.merge_range(
            row_pos,
            0,
            row_pos+2,
            5,
            company.display_name,
            FORMATS["format_ws_title"],
        )
        """sheet.merge_range(
            row_pos,
            4,
            row_pos,
            6,
            _("Statement of Account from %s") % (company.display_name),
            FORMATS["format_ws_title"],
        )"""
        buf_image = io.BytesIO(base64.b64decode(company.logo))
        sheet.insert_image(row_pos, 6, "company_logo.png",
                           {'image_data': buf_image, 'x_scale': 0.8, 'y_scale': 0.8})
        row_pos += 3
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            4,
            _("Customer Report As on %s") % (fields.Date.from_string(data.get("date_end"))),
            FORMATS["format_theader_yellow_center"],
        )

        row_pos += 1
        #sheet.write(row_pos, 1, _("Date:"), FORMATS["format_theader_yellow_right"])
        #sheet.write(
        #    row_pos,
        #    2,
        #    fields.Date.from_string(data.get("date_end")),
        #    FORMATS["format_date_left"],
        #)
        self._size_columns(sheet)
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 2, 20)
        sheet.set_column(3, 5, 15)
        sheet.set_column(6, 6, 18)
        sheet.set_column(7, 7, 15)
        for partner in partners:
            invoice_address = data.get(
                "get_inv_addr", lambda x: self.env["res.partner"]
            )(partner)
            row_pos += 1
            sheet.write(
                row_pos, 0, _("Customer:"), FORMATS["format_theader_yellow_right"]
            )
            sheet.merge_range(
                row_pos,
                1,
                row_pos,
                3,
                invoice_address.display_name,
                FORMATS["format_left"],
            )
            #if invoice_address.vat:
            #    sheet.write(
            #        row_pos,
            #        4,
            #        _("Printed Date:"),
            #        FORMATS["format_theader_yellow_right"],
            #    )
            #    sheet.write(
            #        row_pos,
            #        5,
            #        datetime.now(),
            #        FORMATS["format_left"],
            #    )
            row_pos += 1
            sheet.write(
                row_pos, 0, _("Address:"), FORMATS["format_theader_yellow_right"]
            )
            customer_address = self._get_report_customer_info(invoice_address)
            sheet.merge_range(
                row_pos,
                1,
                row_pos,
                3,
                _("%s") % (customer_address),
                FORMATS["format_left"],
            )
            #if company.vat:
            timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
            date_now = pytz.utc.localize(datetime.now()).astimezone(timezone)
            sheet.write(
                row_pos,
                5,
                _("Printed Date:"),
                FORMATS["format_theader_yellow_right"],
            )
            sheet.merge_range(
                row_pos,
                6,
                row_pos,
                7,
                fields.Datetime.to_string(date_now),
                FORMATS["format_left"],
            )

            row_pos += 1
            sheet.write(
                row_pos, 0, _("Credit Days:"), FORMATS["format_theader_yellow_right"]
            )
            sheet.merge_range(
                row_pos,
                1,
                row_pos,
                3,
                _("%s") % (partner.credit_days),
                FORMATS["format_left"],
            )
            row_pos += 1
            sheet.write(
                row_pos, 0, _("Credit Limit:"), FORMATS["format_theader_yellow_right"]
            )
            sheet.merge_range(
                row_pos,
                1,
                row_pos,
                3,
                _("%s") % (partner.credit_limit),
                FORMATS["format_left"],
            )


            partner_data = data.get("data", {}).get(partner.id)
            currencies = partner_data.get("currencies", {}).keys()
            if currencies:
                row_pos += 1
            for currency_id in currencies:
                currency = self.env["res.currency"].browse(currency_id)
                if currency.position == "after":
                    money_string = "#,##0.%s " % (
                        "0" * currency.decimal_places
                    ) + "[${}]".format(currency.symbol)
                elif currency.position == "before":
                    money_string = "[${}]".format(currency.symbol) + " #,##0.%s" % (
                        "0" * currency.decimal_places
                    )
                FORMATS["current_money_format"] = workbook.add_format(
                    {"align": "right", "num_format": money_string}
                )
                row_pos = self._write_currency_lines(
                    row_pos, sheet, partner, currency, data
                )
                row_pos = self._write_currency_buckets(
                    row_pos, sheet, partner, currency, data
                )
            row_pos += 2
        row_pos += 3
        sheet.merge_range(
            row_pos, 0,row_pos, 2, _("Prepared By:"), FORMATS["format_theader_yellow_left"]
        )
        sheet.merge_range(
            row_pos, 5,row_pos, 7, _("Received By:"), FORMATS["format_theader_yellow_left"]
        )
        row_pos += 1
        sheet.write(
            row_pos, 0, _("User Name:"), FORMATS["format_left"]
        )
        sheet.merge_range(
            row_pos, 1,row_pos, 2, self.env.user.name, FORMATS["format_left"]
        )
        sheet.write(
            row_pos, 5, _("Name:"), FORMATS["format_left"]
        )
        sheet.merge_range(
            row_pos, 6,row_pos, 7, " ", FORMATS["format_left"]
        )

        row_pos += 1
        sheet.write(
            row_pos, 0, _("Position:"), FORMATS["format_left"]
        )
        if self.env.user.partner_id.function:
            sheet.merge_range(
                row_pos, 1,row_pos, 2, self.env.user.partner_id.function, FORMATS["format_left"]
            )
        sheet.write(
            row_pos, 5, _("Position:"), FORMATS["format_left"]
        )
        sheet.merge_range(
            row_pos, 6,row_pos, 7, " ", FORMATS["format_left"]
        )
        footer1,footer2 = self._get_report_footer_info(company)
        row_pos += 3
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            7,
            footer1,
            FORMATS["format_center"],
        )
        row_pos += 1
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            7,
            footer2,
            FORMATS["format_center"],
        )

    def _define_xls_headers(self, workbook):
        """
        Predefined worksheet headers/footers.
        """
        hf_params = {
            "font_size": 8,
            "font_style": "I",  # B: Bold, I:  Italic, U: Underline
        }
        XLS_HEADERS["xls_headers"] = {"standard": ""}
        report_date = fields.Datetime.context_timestamp(
            self.env.user, datetime.now()
        ).strftime("%Y-%m-%d %H:%M")
        XLS_HEADERS["xls_footers"] = {
            "standard": (
                                "&L&%(font_size)s&%(font_style)s"
                                + report_date
                                + "&R&%(font_size)s&%(font_style)s&P / &N"
                        )
                        % hf_params
        }
    def _define_formats(self, workbook):
        """
        This section contains a number of pre-defined formats.
        It is recommended to use these in order to have a
        consistent look & feel between your XLSX reports.
        """
        self._define_xls_headers(workbook)

        border_grey = "#D3D3D3"
        border = {"border": True, "border_color": border_grey}
        theader = dict(border, bold=True)
        bg_grey = "#CCCCCC"
        bg_yellow = "#FFFFCC"
        bg_blue = "#CCFFFF"
        num_format = "#,##0.00"
        num_format_conditional = "{0};[Red]-{0};{0}".format(num_format)
        pct_format = "#,##0.00%"
        pct_format_conditional = "{0};[Red]-{0};{0}".format(pct_format)
        int_format = "#,##0"
        int_format_conditional = "{0};[Red]-{0};{0}".format(int_format)
        date_format = "YYYY-MM-DD"
        theader_grey = dict(theader, bg_color=bg_grey)
        theader_yellow = dict(theader, bg_color=bg_yellow)
        theader_blue = dict(theader, bg_color=bg_blue)

        # format for worksheet title
        FORMATS["format_ws_title"] = workbook.add_format(
            {"bold": True, "font_size": 14, "font_color": '#025839'}
        )

        # no border formats
        FORMATS["format_left"] = workbook.add_format({"align": "left"})
        FORMATS["format_center"] = workbook.add_format({"align": "center", "font_color": '#025839'})
        FORMATS["format_right"] = workbook.add_format({"align": "right"})
        FORMATS["format_amount_left"] = workbook.add_format(
            {"align": "left", "num_format": num_format}
        )
        FORMATS["format_amount_center"] = workbook.add_format(
            {"align": "center", "num_format": num_format}
        )
        FORMATS["format_amount_right"] = workbook.add_format(
            {"align": "right", "num_format": num_format}
        )
        FORMATS["format_amount_conditional_left"] = workbook.add_format(
            {"align": "left", "num_format": num_format_conditional}
        )
        FORMATS["format_amount_conditional_center"] = workbook.add_format(
            {"align": "center", "num_format": num_format_conditional}
        )
        FORMATS["format_amount_conditional_right"] = workbook.add_format(
            {"align": "right", "num_format": num_format_conditional}
        )
        FORMATS["format_percent_left"] = workbook.add_format(
            {"align": "left", "num_format": pct_format}
        )
        FORMATS["format_percent_center"] = workbook.add_format(
            {"align": "center", "num_format": pct_format}
        )
        FORMATS["format_percent_right"] = workbook.add_format(
            {"align": "right", "num_format": pct_format}
        )
        FORMATS["format_percent_conditional_left"] = workbook.add_format(
            {"align": "left", "num_format": pct_format_conditional}
        )
        FORMATS["format_percent_conditional_center"] = workbook.add_format(
            {"align": "center", "num_format": pct_format_conditional}
        )
        FORMATS["format_percent_conditional_right"] = workbook.add_format(
            {"align": "right", "num_format": pct_format_conditional}
        )
        FORMATS["format_integer_left"] = workbook.add_format(
            {"align": "left", "num_format": int_format}
        )
        FORMATS["format_integer_center"] = workbook.add_format(
            {"align": "center", "num_format": int_format}
        )
        FORMATS["format_integer_right"] = workbook.add_format(
            {"align": "right", "num_format": int_format}
        )
        FORMATS["format_integer_conditional_left"] = workbook.add_format(
            {"align": "right", "num_format": int_format_conditional}
        )
        FORMATS["format_integer_conditional_center"] = workbook.add_format(
            {"align": "center", "num_format": int_format_conditional}
        )
        FORMATS["format_integer_conditional_right"] = workbook.add_format(
            {"align": "right", "num_format": int_format_conditional}
        )
        FORMATS["format_date_left"] = workbook.add_format(
            {"align": "left", "num_format": date_format}
        )
        FORMATS["format_date_center"] = workbook.add_format(
            {"align": "center", "num_format": date_format}
        )
        FORMATS["format_date_right"] = workbook.add_format(
            {"align": "right", "num_format": date_format}
        )

        FORMATS["format_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True}
        )
        FORMATS["format_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True}
        )
        FORMATS["format_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True}
        )
        FORMATS["format_amount_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True, "num_format": num_format}
        )
        FORMATS["format_amount_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True, "num_format": num_format}
        )
        FORMATS["format_amount_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True, "num_format": num_format}
        )
        FORMATS["format_amount_conditional_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True, "num_format": num_format_conditional}
        )
        FORMATS["format_amount_conditional_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True, "num_format": num_format_conditional}
        )
        FORMATS["format_amount_conditional_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True, "num_format": num_format_conditional}
        )
        FORMATS["format_percent_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True, "num_format": pct_format}
        )
        FORMATS["format_percent_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True, "num_format": pct_format}
        )
        FORMATS["format_percent_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True, "num_format": pct_format}
        )
        FORMATS["format_percent_conditional_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True, "num_format": pct_format_conditional}
        )
        FORMATS["format_percent_conditional_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True, "num_format": pct_format_conditional}
        )
        FORMATS["format_percent_conditional_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True, "num_format": pct_format_conditional}
        )
        FORMATS["format_integer_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True, "num_format": int_format}
        )
        FORMATS["format_integer_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True, "num_format": int_format}
        )
        FORMATS["format_integer_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True, "num_format": int_format}
        )
        FORMATS["format_integer_conditional_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True, "num_format": int_format_conditional}
        )
        FORMATS["format_integer_conditional_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True, "num_format": int_format_conditional}
        )
        FORMATS["format_integer_conditional_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True, "num_format": int_format_conditional}
        )
        FORMATS["format_date_left_bold"] = workbook.add_format(
            {"align": "left", "bold": True, "num_format": date_format}
        )
        FORMATS["format_date_center_bold"] = workbook.add_format(
            {"align": "center", "bold": True, "num_format": date_format}
        )
        FORMATS["format_date_right_bold"] = workbook.add_format(
            {"align": "right", "bold": True, "num_format": date_format}
        )

        # formats for worksheet table column headers
        FORMATS["format_theader_grey_left"] = workbook.add_format(theader_grey)
        FORMATS["format_theader_grey_center"] = workbook.add_format(
            dict(theader_grey, align="center")
        )
        FORMATS["format_theader_grey_right"] = workbook.add_format(
            dict(theader_grey, align="right")
        )
        FORMATS["format_theader_grey_amount_left"] = workbook.add_format(
            dict(theader_grey, num_format=num_format, align="left")
        )
        FORMATS["format_theader_grey_amount_center"] = workbook.add_format(
            dict(theader_grey, num_format=num_format, align="center")
        )
        FORMATS["format_theader_grey_amount_right"] = workbook.add_format(
            dict(theader_grey, num_format=num_format, align="right")
        )

        FORMATS["format_theader_grey_amount_conditional_left"] = workbook.add_format(
            dict(theader_grey, num_format=num_format_conditional, align="left")
        )
        FORMATS["format_theader_grey_amount_conditional_center"] = workbook.add_format(
            dict(theader_grey, num_format=num_format_conditional, align="center")
        )
        FORMATS["format_theader_grey_amount_conditional_right"] = workbook.add_format(
            dict(theader_grey, num_format=num_format_conditional, align="right")
        )
        FORMATS["format_theader_grey_percent_left"] = workbook.add_format(
            dict(theader_grey, num_format=pct_format, align="left")
        )
        FORMATS["format_theader_grey_percent_center"] = workbook.add_format(
            dict(theader_grey, num_format=pct_format, align="center")
        )
        FORMATS["format_theader_grey_percent_right"] = workbook.add_format(
            dict(theader_grey, num_format=pct_format, align="right")
        )
        FORMATS["format_theader_grey_percent_conditional_left"] = workbook.add_format(
            dict(theader_grey, num_format=pct_format_conditional, align="left")
        )
        FORMATS["format_theader_grey_percent_conditional_center"] = workbook.add_format(
            dict(theader_grey, num_format=pct_format_conditional, align="center")
        )
        FORMATS["format_theader_grey_percent_conditional_right"] = workbook.add_format(
            dict(theader_grey, num_format=pct_format_conditional, align="right")
        )
        FORMATS["format_theader_grey_integer_left"] = workbook.add_format(
            dict(theader_grey, num_format=int_format, align="left")
        )
        FORMATS["format_theader_grey_integer_center"] = workbook.add_format(
            dict(theader_grey, num_format=int_format, align="center")
        )
        FORMATS["format_theader_grey_integer_right"] = workbook.add_format(
            dict(theader_grey, num_format=int_format, align="right")
        )
        FORMATS["format_theader_grey_integer_conditional_left"] = workbook.add_format(
            dict(theader_grey, num_format=int_format_conditional, align="left")
        )
        FORMATS["format_theader_grey_integer_conditional_center"] = workbook.add_format(
            dict(theader_grey, num_format=int_format_conditional, align="center")
        )
        FORMATS["format_theader_grey_integer_conditional_right"] = workbook.add_format(
            dict(theader_grey, num_format=int_format_conditional, align="right")
        )

        FORMATS["format_theader_yellow_left"] = workbook.add_format(theader_yellow)
        FORMATS["format_theader_yellow_center"] = workbook.add_format(
            dict(theader_yellow, align="center")
        )
        FORMATS["format_theader_yellow_right"] = workbook.add_format(
            dict(theader_yellow, align="right")
        )
        FORMATS["format_theader_yellow_amount_left"] = workbook.add_format(
            dict(theader_yellow, num_format=num_format, align="left")
        )
        FORMATS["format_theader_yellow_amount_center"] = workbook.add_format(
            dict(theader_yellow, num_format=num_format, align="center")
        )
        FORMATS["format_theader_yellow_amount_right"] = workbook.add_format(
            dict(theader_yellow, num_format=num_format, align="right")
        )

        FORMATS["format_theader_yellow_amount_conditional_left"] = workbook.add_format(
            dict(theader_yellow, num_format=num_format_conditional, align="left")
        )
        FORMATS[
            "format_theader_yellow_amount_conditional_center"
        ] = workbook.add_format(
            dict(theader_yellow, num_format=num_format_conditional, align="center")
        )
        FORMATS["format_theader_yellow_amount_conditional_right"] = workbook.add_format(
            dict(theader_yellow, num_format=num_format_conditional, align="right")
        )
        FORMATS["format_theader_yellow_percent_left"] = workbook.add_format(
            dict(theader_yellow, num_format=pct_format, align="left")
        )
        FORMATS["format_theader_yellow_percent_center"] = workbook.add_format(
            dict(theader_yellow, num_format=pct_format, align="center")
        )
        FORMATS["format_theader_yellow_percent_right"] = workbook.add_format(
            dict(theader_yellow, num_format=pct_format, align="right")
        )
        FORMATS["format_theader_yellow_percent_conditional_left"] = workbook.add_format(
            dict(theader_yellow, num_format=pct_format_conditional, align="left")
        )
        FORMATS[
            "format_theader_yellow_percent_conditional_center"
        ] = workbook.add_format(
            dict(theader_yellow, num_format=pct_format_conditional, align="center")
        )
        FORMATS[
            "format_theader_yellow_percent_conditional_right"
        ] = workbook.add_format(
            dict(theader_yellow, num_format=pct_format_conditional, align="right")
        )
        FORMATS["format_theader_yellow_integer_left"] = workbook.add_format(
            dict(theader_yellow, num_format=int_format, align="left")
        )
        FORMATS["format_theader_yellow_integer_center"] = workbook.add_format(
            dict(theader_yellow, num_format=int_format, align="center")
        )
        FORMATS["format_theader_yellow_integer_right"] = workbook.add_format(
            dict(theader_yellow, num_format=int_format, align="right")
        )
        FORMATS["format_theader_yellow_integer_conditional_left"] = workbook.add_format(
            dict(theader_yellow, num_format=int_format_conditional, align="left")
        )
        FORMATS[
            "format_theader_yellow_integer_conditional_center"
        ] = workbook.add_format(
            dict(theader_yellow, num_format=int_format_conditional, align="center")
        )
        FORMATS[
            "format_theader_yellow_integer_conditional_right"
        ] = workbook.add_format(
            dict(theader_yellow, num_format=int_format_conditional, align="right")
        )

        FORMATS["format_theader_blue_left"] = workbook.add_format(theader_blue)
        FORMATS["format_theader_blue_center"] = workbook.add_format(
            dict(theader_blue, align="center")
        )
        FORMATS["format_theader_blue_right"] = workbook.add_format(
            dict(theader_blue, align="right")
        )
        FORMATS["format_theader_blue_amount_left"] = workbook.add_format(
            dict(theader_blue, num_format=num_format, align="left")
        )
        FORMATS["format_theader_blue_amount_center"] = workbook.add_format(
            dict(theader_blue, num_format=num_format, align="center")
        )
        FORMATS["format_theader_blue_amount_right"] = workbook.add_format(
            dict(theader_blue, num_format=num_format, align="right")
        )
        FORMATS["format_theader_blue_amount_conditional_left"] = workbook.add_format(
            dict(theader_blue, num_format=num_format_conditional, align="left")
        )
        FORMATS["format_theader_blue_amount_conditional_center"] = workbook.add_format(
            dict(theader_blue, num_format=num_format_conditional, align="center")
        )
        FORMATS["format_theader_blue_amount_conditional_right"] = workbook.add_format(
            dict(theader_blue, num_format=num_format_conditional, align="right")
        )
        FORMATS["format_theader_blue_percent_left"] = workbook.add_format(
            dict(theader_blue, num_format=pct_format, align="left")
        )
        FORMATS["format_theader_blue_percent_center"] = workbook.add_format(
            dict(theader_blue, num_format=pct_format, align="center")
        )
        FORMATS["format_theader_blue_percent_right"] = workbook.add_format(
            dict(theader_blue, num_format=pct_format, align="right")
        )
        FORMATS["format_theader_blue_percent_conditional_left"] = workbook.add_format(
            dict(theader_blue, num_format=pct_format_conditional, align="left")
        )
        FORMATS["format_theader_blue_percent_conditional_center"] = workbook.add_format(
            dict(theader_blue, num_format=pct_format_conditional, align="center")
        )
        FORMATS["format_theader_blue_percent_conditional_right"] = workbook.add_format(
            dict(theader_blue, num_format=pct_format_conditional, align="right")
        )
        FORMATS["format_theader_blue_integer_left"] = workbook.add_format(
            dict(theader_blue, num_format=int_format, align="left")
        )
        FORMATS["format_theader_blue_integer_center"] = workbook.add_format(
            dict(theader_blue, num_format=int_format, align="center")
        )
        FORMATS["format_theader_blue_integer_right"] = workbook.add_format(
            dict(theader_blue, num_format=int_format, align="right")
        )
        FORMATS["format_theader_blue_integer_conditional_left"] = workbook.add_format(
            dict(theader_blue, num_format=int_format_conditional, align="left")
        )
        FORMATS["format_theader_blue_integer_conditional_center"] = workbook.add_format(
            dict(theader_blue, num_format=int_format_conditional, align="center")
        )
        FORMATS["format_theader_blue_integer_conditional_right"] = workbook.add_format(
            dict(theader_blue, num_format=int_format_conditional, align="right")
        )

        # formats for worksheet table cells
        FORMATS["format_tcell_left"] = workbook.add_format(dict(border, align="left"))
        FORMATS["format_tcell_center"] = workbook.add_format(
            dict(border, align="center")
        )
        FORMATS["format_tcell_right"] = workbook.add_format(dict(border, align="right"))
        FORMATS["format_tcell_amount_left"] = workbook.add_format(
            dict(border, num_format=num_format, align="left")
        )
        FORMATS["format_tcell_amount_center"] = workbook.add_format(
            dict(border, num_format=num_format, align="center")
        )
        FORMATS["format_tcell_amount_right"] = workbook.add_format(
            dict(border, num_format=num_format, align="right")
        )
        FORMATS["format_tcell_amount_conditional_left"] = workbook.add_format(
            dict(border, num_format=num_format_conditional, align="left")
        )
        FORMATS["format_tcell_amount_conditional_center"] = workbook.add_format(
            dict(border, num_format=num_format_conditional, align="center")
        )
        FORMATS["format_tcell_amount_conditional_right"] = workbook.add_format(
            dict(border, num_format=num_format_conditional, align="right")
        )
        FORMATS["format_tcell_percent_left"] = workbook.add_format(
            dict(border, num_format=pct_format, align="left")
        )
        FORMATS["format_tcell_percent_center"] = workbook.add_format(
            dict(border, num_format=pct_format, align="center")
        )
        FORMATS["format_tcell_percent_right"] = workbook.add_format(
            dict(border, num_format=pct_format, align="right")
        )
        FORMATS["format_tcell_percent_conditional_left"] = workbook.add_format(
            dict(border, num_format=pct_format_conditional, align="left")
        )
        FORMATS["format_tcell_percent_conditional_center"] = workbook.add_format(
            dict(border, num_format=pct_format_conditional, align="center")
        )
        FORMATS["format_tcell_percent_conditional_right"] = workbook.add_format(
            dict(border, num_format=pct_format_conditional, align="right")
        )
        FORMATS["format_tcell_integer_left"] = workbook.add_format(
            dict(border, num_format=int_format, align="left")
        )
        FORMATS["format_tcell_integer_center"] = workbook.add_format(
            dict(border, num_format=int_format, align="center")
        )
        FORMATS["format_tcell_integer_right"] = workbook.add_format(
            dict(border, num_format=int_format, align="right")
        )
        FORMATS["format_tcell_integer_conditional_left"] = workbook.add_format(
            dict(border, num_format=int_format_conditional, align="left")
        )
        FORMATS["format_tcell_integer_conditional_center"] = workbook.add_format(
            dict(border, num_format=int_format_conditional, align="center")
        )
        FORMATS["format_tcell_integer_conditional_right"] = workbook.add_format(
            dict(border, num_format=int_format_conditional, align="right")
        )
        FORMATS["format_tcell_date_left"] = workbook.add_format(
            dict(border, num_format=date_format, align="left")
        )
        FORMATS["format_tcell_date_center"] = workbook.add_format(
            dict(border, num_format=date_format, align="center")
        )
        FORMATS["format_tcell_date_right"] = workbook.add_format(
            dict(border, num_format=date_format, align="right")
        )

        FORMATS["format_tcell_left_bold"] = workbook.add_format(
            dict(border, align="left", bold=True)
        )
        FORMATS["format_tcell_center_bold"] = workbook.add_format(
            dict(border, align="center", bold=True)
        )
        FORMATS["format_tcell_right_bold"] = workbook.add_format(
            dict(border, align="right", bold=True)
        )
        FORMATS["format_tcell_amount_left_bold"] = workbook.add_format(
            dict(border, num_format=num_format, align="left", bold=True)
        )
        FORMATS["format_tcell_amount_center_bold"] = workbook.add_format(
            dict(border, num_format=num_format, align="center", bold=True)
        )
        FORMATS["format_tcell_amount_right_bold"] = workbook.add_format(
            dict(border, num_format=num_format, align="right", bold=True)
        )
        FORMATS["format_tcell_amount_conditional_left_bold"] = workbook.add_format(
            dict(border, num_format=num_format_conditional, align="left", bold=True)
        )
        FORMATS["format_tcell_amount_conditional_center_bold"] = workbook.add_format(
            dict(border, num_format=num_format_conditional, align="center", bold=True)
        )
        FORMATS["format_tcell_amount_conditional_right_bold"] = workbook.add_format(
            dict(border, num_format=num_format_conditional, align="right", bold=True)
        )
        FORMATS["format_tcell_percent_left_bold"] = workbook.add_format(
            dict(border, num_format=pct_format, align="left", bold=True)
        )
        FORMATS["format_tcell_percent_center_bold"] = workbook.add_format(
            dict(border, num_format=pct_format, align="center", bold=True)
        )
        FORMATS["format_tcell_percent_right_bold"] = workbook.add_format(
            dict(border, num_format=pct_format, align="right", bold=True)
        )
        FORMATS["format_tcell_percent_conditional_left_bold"] = workbook.add_format(
            dict(border, num_format=pct_format_conditional, align="left", bold=True)
        )
        FORMATS["format_tcell_percent_conditional_center_bold"] = workbook.add_format(
            dict(border, num_format=pct_format_conditional, align="center", bold=True)
        )
        FORMATS["format_tcell_percent_conditional_right_bold"] = workbook.add_format(
            dict(border, num_format=pct_format_conditional, align="right", bold=True)
        )
        FORMATS["format_tcell_integer_left_bold"] = workbook.add_format(
            dict(border, num_format=int_format, align="left", bold=True)
        )
        FORMATS["format_tcell_integer_center_bold"] = workbook.add_format(
            dict(border, num_format=int_format, align="center", bold=True)
        )
        FORMATS["format_tcell_integer_right_bold"] = workbook.add_format(
            dict(border, num_format=int_format, align="right", bold=True)
        )
        FORMATS["format_tcell_integer_conditional_left_bold"] = workbook.add_format(
            dict(border, num_format=int_format_conditional, align="left", bold=True)
        )
        FORMATS["format_tcell_integer_conditional_center_bold"] = workbook.add_format(
            dict(border, num_format=int_format_conditional, align="center", bold=True)
        )
        FORMATS["format_tcell_integer_conditional_right_bold"] = workbook.add_format(
            dict(border, num_format=int_format_conditional, align="right", bold=True)
        )
        FORMATS["format_tcell_date_left_bold"] = workbook.add_format(
            dict(border, num_format=date_format, align="left", bold=True)
        )
        FORMATS["format_tcell_date_center_bold"] = workbook.add_format(
            dict(border, num_format=date_format, align="center", bold=True)
        )
        FORMATS["format_tcell_date_right_bold"] = workbook.add_format(
            dict(border, num_format=date_format, align="right", bold=True)
        )