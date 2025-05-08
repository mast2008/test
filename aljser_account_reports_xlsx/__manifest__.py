

{
    'name': 'Aljser Accounting Reports XLSX',
    'version': '15.0.0',
    'summary': 'Partner ledger Reports in XLSX Format',
    'description': """
        Helps you to print accounting reports (Receivable Payable Reports) in xlsx Format.
        """,
    'category': 'Account',
    'author': 'Mast-IT Bahrain',
    'maintainer': 'Mast-IT Bahrain',
    'website': "https://mast-it.com/",
    'depends': [
        'account','report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/partner_ledger_wizard_view.xml',
        'views/report.xml',
        'views/menu.xml'
    ],
    'demo': [],
    'auto_install': False,
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
