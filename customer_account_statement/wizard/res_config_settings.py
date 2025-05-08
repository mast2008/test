from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    default_show_aging_buckets = fields.Boolean(
        string="Show Aging Buckets", default_model="customer.account.statement.wizard"
    )

    group_customer_account_statement = fields.Boolean(
        "Enable Customer Account Statements",
        group="account.group_account_invoice",
        implied_group="customer_account_statement.group_customer_account_statement",
    )

    def set_values(self):
        self = self.with_context(active_test=False)
        # default values fields
        IrDefault = self.env["ir.default"].sudo()
        for name, field in self._fields.items():
            if (
                name.startswith("default_")
                and field.default_model == "customer.account.statement.wizard"
            ):
                if isinstance(self[name], models.BaseModel):
                    if self._fields[name].type == "many2one":
                        value = self[name].id
                    else:
                        value = self[name].ids
                else:
                    value = self[name]
                IrDefault.set("customer.account.statement.wizard", name[8:], value)
        return super().set_values()
