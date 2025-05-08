# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re
import uuid

from odoo import _, fields, models

_logger = logging.getLogger(__name__)



class ResPartner(models.Model):
    _inherit = "res.partner"

    credit_days = fields.Integer(string="Credit Days")
    credit_limit = fields.Integer(string="Credit Limit")
