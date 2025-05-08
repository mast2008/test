# -*- coding: utf-8 -*-
{
    'name': 'Invoice & Bill (Tax) Report (Excel)',
    'version': '15.0.0.1',
    'category': 'Account',
    'author': 'Mast Information Technology - Bahrain',
    'description': "Ticket # 1061",
    'license': 'LGPL-3',
    'depends': ['report_xlsx', 'account','base_address_extended','partner_company_registry'],
    #'website': 'http://www.mast-it.com',
    'data': [
            'report/report.xml',
            'wizard/inv_bill_rpt_wiz_views.xml',
            'security/ir.model.access.csv',
             ],
    'installable': True,
}
