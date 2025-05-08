# -*- coding: utf-8 -*-
# This module is develop by Mast Information Technology
# Contact: +973-17382342, info@mast-it.com
{
    'name': 'Attendance Extra',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
Extra features for attendance
    """,
    'author':'Mast',
    'website': 'https://mast-it.com',
    'depends': ['base', 'hr_attendance'],
    'data': ['data/hr_attendance_custom_data.xml','security/ir.model.access.csv', 'views/hr_attendance_custom_view.xml'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
