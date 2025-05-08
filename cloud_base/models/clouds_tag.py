# -*- coding: utf-8 -*-

from odoo import fields, models


class clouds_tag(models.Model):
    """
    The model to systemize cloud tags
    """
    _name = "clouds.tag"
    _inherit = ["clouds.node"]
    _description = "Tag"

    parent_id = fields.Many2one("clouds.tag", string="Parent Tag")
    child_ids = fields.One2many("clouds.tag", "parent_id", string="Child Tags")
    color = fields.Integer(string="Color index", default=10)

    _order = "sequence, id"
