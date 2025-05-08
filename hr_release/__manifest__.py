# -*- coding: utf-8 -*-

{
    'name': 'Employees Release',
    'category': 'Human Resources',
    'version': '1.0',
    'description':'',
	'author': 'Mast',
    'depends': ['hr', 'hr_payroll', 'hr_contract', 'hr_bahrain'],
    'auto_install': False,
    'data': ['data/hr_release_data.xml', 'security/security.xml', 'security/ir.model.access.csv', 'views/hr_release_view.xml'],
    'qweb': [],
    'license': 'LGPL-3'
}
