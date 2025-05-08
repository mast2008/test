# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import date

from odoo import _, api, fields, models


def return_start_and_end(interval, ttype, inclusive, period_direction, compared_to="today", compared_to_value=1,
                         compared_to_type="months"):
    """
    Return start and end date based on interval parameters

    Args:
        interval (int): Number of time units
        ttype (str): Type of interval ('days', 'weeks', 'months', 'years')
        inclusive (bool): Whether to include current period
        period_direction (str): 'last' or 'next'
        compared_to (str): Reference point ('today', 'last', 'next')
        compared_to_value (int): Number of units to shift reference
        compared_to_type (str): Type of units for reference shift

    Returns:
        tuple: (start_date, end_date) as date objects
    """

    def _return_relative_delta(int_type, int_interval):
        """Helper to create relativedelta object"""
        return relativedelta(**{
            'days': int_interval if int_type == "days" else 0,
            'weeks': int_interval if int_type == "weeks" else 0,
            'months': int_interval if int_type == "months" else 0,
            'years': int_interval if int_type == "years" else 0,
        })

    today = date.today()

    # Calculate reference date if not today
    if compared_to != "today" and compared_to_value:
        delta = _return_relative_delta(
            compared_to_type,
            compared_to_value if compared_to == "next" else -compared_to_value
        )
        today += delta

    # Adjust interval based on inclusive flag
    the_next_interval = 0
    if period_direction == "next":
        if not inclusive:
            the_next_interval = 1
            interval += 1
    elif inclusive:
        the_next_interval = 1
        interval -= 1

    # Calculate date range
    period_delta = _return_relative_delta(ttype, interval)
    period_delta_2 = _return_relative_delta(ttype, the_next_interval)

    if period_direction == "next":
        return today + period_delta_2, today + period_delta
    return today - period_delta, today + period_delta_2


def return_the_first_month_or_year_date(calc_date, year=False):
    """
    Return first date of month or year

    Args:
        calc_date (date): Input date
        year (bool): Whether to return first of year

    Returns:
        date: First day of period
    """
    return date(
        year=calc_date.year,
        month=1 if year else calc_date.month,
        day=1
    )


class CloudDomainPeriod(models.Model):
    """Model to construct relative date domains for cloud operations"""
    _name = "cloud.domain.period"
    _description = "Cloud Relative Period"
    _order = "field_id, id"

    sync_model_id = fields.Many2one("sync.model", string="Sync Model")
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Date Field",
        required=True,
        ondelete="cascade",
        domain="[('ttype', 'in', ['date', 'datetime'])]",
        help="Date field to use for period calculation"
    )
    period_direction = fields.Selection(
        selection=[
            ("last", "The Last"),
            ("next", "The Next"),
        ],
        string="Period Direction",
        default="last",
        required=True,
    )
    period_value = fields.Integer(
        string="Interval Value",
        required=True,
        default=1,
    )
    period_type = fields.Selection(
        selection=[
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
            ("years", "Years"),
        ],
        string="Interval Type",
        required=True,
        default="months",
    )
    compared_to = fields.Selection(
        selection=[
            ("today", "Today"),
            ("last", "Past"),
            ("next", "Future")
        ],
        string="Reference Point",
        default="today",
        required=True,
    )
    compared_to_value = fields.Integer(
        string="Reference Shift",
        required=True,
        default=0,
    )
    compared_to_type = fields.Selection(
        selection=[
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
            ("years", "Years"),
        ],
        string="Reference Shift Type",
        required=True,
        default="months",
    )
    inclusive_this = fields.Boolean(
        string="Include Current Period",
        help="When checked, includes the current period in calculations. For example, if today is 25/11/2023 and "
             "selecting 'the last 2 months', unchecked would consider September-October, checked would consider "
             "October-November"
    )
    domain = fields.Text(
        string="Domain",
        compute="_compute_domain",
        help="Computed domain filter based on period parameters"
    )
    title = fields.Char(
        string="Period Title",
        compute="_compute_domain",
        help="Human-readable description of the period"
    )

    _sql_constraints = [
        ("period_value_check", "CHECK (period_value > 0)", _("Interval value must be positive!"))
    ]

    @api.depends(
        "field_id", "period_value", "period_type", "inclusive_this",
        "period_direction", "compared_to", "compared_to_type", "compared_to_value"
    )
    def _compute_domain(self):
        """Compute the domain filter and display title for the period"""
        for period in self:
            if not (period.field_id and period.period_value > 0 and period.period_type and period.period_direction):
                period.domain = "[]"
                period.title = False
                continue

            start, end = return_start_and_end(
                interval=period.period_value,
                ttype=period.period_type,
                inclusive=period.inclusive_this,
                period_direction=period.period_direction,
                compared_to=period.compared_to,
                compared_to_value=period.compared_to_value,
                compared_to_type=period.compared_to_type,
            )

            # Adjust for specific period types
            if period.period_type == "weeks":
                start -= relativedelta(days=start.weekday())
                end -= relativedelta(days=end.weekday())
            elif period.period_type in ["months", "years"]:
                start = return_the_first_month_or_year_date(start, year=(period.period_type == "years"))
                end = return_the_first_month_or_year_date(end, year=(period.period_type == "years"))

            period.domain = f"['&', ['{period.field_id.name}', '<', '{end}'], ['{period.field_id.name}', '>=', '{start}']]"
            period.title = f"{start} - {end - relativedelta(days=1)}"