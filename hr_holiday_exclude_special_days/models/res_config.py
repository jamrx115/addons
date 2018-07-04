# -*- coding: utf-8 -*-
# © 2017 Tobias Zehntner
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HolidayConfigSettings(models.TransientModel):
    _name = 'holiday.config.settings'
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', 'Company', compute='_compute_company')
    deduct_saturday = fields.Boolean(
        default=True,
        related='company_id.deduct_saturday_in_leave',
        string='Deduct Saturdays *')
    deduct_sunday = fields.Boolean(
        default=True,
        related='company_id.deduct_sunday_in_leave',
        string='Deduct Sundays *')
    hours_per_day = fields.Float(related='company_id.hours_per_day',
                                 default=8.0,
                                 string='Work Hours per Day *')

    def _compute_company(self):
        self.company_id = self.env.user.company_id
