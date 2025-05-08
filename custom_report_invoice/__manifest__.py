# -*- coding: utf-8 -*-
{
    'name': "custom_report_invoice",
    'version':'15.0.0.1',
    'summary': """
        Custom Invoice Report
        """,
    'description': """
        This is a customized invoice print out...
    """,

    'author': "MAST IT",
    'license': "LGPL-3",
    'website': "https://www.mast-it.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['web', 'account', 'point_of_sale', 'mrp'],

    'data': [
        'views/inherited_invoice_report.xml',
		'views/account_invoice.xml',
        'views/base_document_layout_views.xml',
    ],
    'assets':{
        'point_of_sale.assets': [
            'custom_report_invoice/static/src/js/models.js',
        ],
         'web.assets_qweb': [
                'custom_report_invoice/static/src/xml/**/*',
            ],
    }
    
}
