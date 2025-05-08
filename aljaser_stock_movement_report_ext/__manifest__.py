# -*- coding: utf-8 -*-

{
    'name': 'Inventory Movement Report',
    'category': 'Inventory',
    'version': '15.0.1.0.1',
    'description':'Stock movement report',
	'author': 'Mast-IT Bahrain',
    'summary': 'Inventory Report',
    'depends': ['report_xlsx', 'stock','product','stock_account'],
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'views/production_report_view.xml',

    ],
    'qweb': [],
}
