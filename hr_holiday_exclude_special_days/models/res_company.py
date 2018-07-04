# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    deduct_saturday_in_leave =\
        fields.Boolean(string='Deduct Saturdays',
                       default=True)

    deduct_sunday_in_leave =\
        fields.Boolean(string='Deduct Sundays',
                       default=True)

    hours_per_day = fields.Float(string='Work hours per day', default=8.0)
