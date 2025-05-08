# -*- coding: utf-8 -*-
{
    'name': 'Export Aged Receivable in xls',
    'version': '1.0',
    'summary': "Export Aged Receivable in xls",
    'category': 'Account',
    'author': 'Mast',
    'license': 'LGPL-3',
    'company': 'Mast',
    'website': 'http://www.mast-it.com',
    'depends': ['account', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
