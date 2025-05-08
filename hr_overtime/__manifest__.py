# -*- coding: utf-8 -*-

{
    'name': 'HR Overtime Policy',
    'version': '1.0',
    'author': 'Mast',
    'category': 'Human Resource',
    'sequence': 20,
    'summary': 'Adding Overtime Policy',
    'depends': ['hr_attendance','hr_payroll'],
    'data': [
        'views/hr_overtime_view.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/hr_overtime_data.xml',
    ],
    'installable': True,
    'application': False,
    'website': 'https://www.mast-it.com',
    'auto_install': False,
    'license': 'LGPL-3'
}
