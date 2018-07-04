# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, exceptions, fields, models


class GenerateHolidayWizard(models.TransientModel):
    _name = 'hr_holiday.generate_holiday_wizard'

    employee_ids = fields.Many2many('hr.employee', string='Impacted Employees')

    @api.model
    def get_public_holiday(self):
        """
        This methods retrive the public holiday from which we opened the
        wizard
        """
        return self.env['hr.public_holiday'].browse(self._context['active_id'])

    @api.multi
    def search_missing_employees(self):
        """
        This method search for employees that are in the company
        of the public leave but for which the leave is not created
        """
        self.ensure_one()

        public_holiday = self.get_public_holiday()

        date_from, date_to = \
            public_holiday.compensate_user_tz(
                public_holiday.date)

        domain = []

        if public_holiday.company_ids:
            domain.append(('company_id', 'in', public_holiday.company_ids.ids))
        if public_holiday.tag_ids:
            domain.append(('category_ids', 'in', public_holiday.tag_ids.ids))

        all_employee_ids = self.env['hr.employee'].search(
            domain)

        holiday_ids = self.env['hr.holidays'].search(
            [('holiday_status_id', '=', self.holiday_status_id.id),
             ('date_from', '>=', date_from),
             ('date_to', '<=', date_to),
             ('employee_id', 'in', all_employee_ids.ids)])

        # only keep employees that does not have the holiday
        new_employees =\
            all_employee_ids - holiday_ids.mapped('employee_id')

        if not new_employees:
            raise exceptions.ValidationError(
                'No missing employees found for the public holiday')

        self.employee_ids = new_employees

        # avoid the wizard from closing
        return {
            'type': 'ir.actions.do_nothing',
        }

    @api.multi
    def generate_leaves(self):
        """
        This methods generate the public leave for the selected
        employees in the wizard
        :return:
        """
        public_holiday = self.get_public_holiday()
        public_holiday.create_employee_leaves(self.employee_ids)
