{
    'name': 'Warning Print',
    'category': 'Accounting',
    'version': '17.0.0.1',
    'author': 'Mast Information Technology - Bahrain',
    'description': "Warning Letter (#2866)",
    'depends': ['hr','hr_warning11', 'base','hr_payroll'],
    # 'website': 'http://www.mast-it.com',
    'data': [
            'views/res_company_views.xml',
            'views/hr_warning_view.xml',

            'reports/report_templates.xml',
            'reports/reports.xml',

             ],
    'installable': True,
    'license': 'LGPL-3',
}
