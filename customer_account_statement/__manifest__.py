# Copyright 2022 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Customer Account Statement",
    "version": "15.0.1.0.1",
    "category": "Accounting & Finance",
    "summary": "Customer Account Statement",
    "author": "Mast-IT Bahrain",
    "license": "LGPL-3",
    "depends": ["account", "report_xlsx",'partner_credit_limit'],
    "data": [
        "security/ir.model.access.csv",
        "security/statement_security.xml",
        "views/customer_account_statement.xml",
        "views/res_config_settings.xml",
        "wizard/statement_wizard.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "/customer_account_statement/static/src/scss/layout_statement.scss",
        ],
    },
    "installable": True,
    "application": False,
}
