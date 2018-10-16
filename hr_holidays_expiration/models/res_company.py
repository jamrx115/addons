# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    notify_template_id = fields.Many2one(
        'mail.template',
        string='Notify Email Template'
    )
    expire_template_id = fields.Many2one(
        'mail.template',
        string='Expired Email Template'
    )
