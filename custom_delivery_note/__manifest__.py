# -*- coding: utf-8 -*-
{
    'name': "Custom Delivery Note",
    'version': '15.0.0.1',
    'summary': """
        Custom Invoice Report
        """,
    'description': """
        This is a customized delivery note print out...
    """,

    'author': "MAST IT",
    'website': "https://www.mast-it.com",

    'category': 'Inventory',
    'version': '0.1',

    'depends': ['stock'],

    'data': [
            'reports/report_deliveryslip.xml',
            'reports/report_stockpicking_operations.xml'
    ],
    'license': 'LGPL-3'
}
