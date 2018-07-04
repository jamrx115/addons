# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat, Tobias Zehntner
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class PublicHoliday(models.Model):
    _name = 'hr.public_holiday'

    date = fields.Date('Public Holiday Date', required=True)
    name = fields.Char(string='Holiday Name', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft')

    company_ids = fields.Many2many('res.company', string='Companies')
    tag_ids = fields.Many2many('hr.employee.category', string='Tags')
    employee_ids = fields.Many2many('hr.employee', string='Impacted Employees',
                                    required=True)
    holiday_status_id = fields.Many2one(
        'hr.holidays.status', 'Leave Type', required=True,
        default=lambda self: self.get_default_holiday_status())

    def get_default_holiday_status(self):
        public_holidays = self.env['hr.holidays.status'].search([
            ('is_public_holiday', '=', True)])
        if public_holidays:
            return public_holidays[0].id

    @api.onchange('company_ids', 'tag_ids')
    def _onchange_function(self):
        domain = []
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))

        if self.tag_ids:
            domain.append(('category_ids', 'in', self.tag_ids.ids))

        if domain:
            employees = self.env['hr.employee'].search(domain)

            self.employee_ids = employees.ids
        else:
            self.employee_ids = False

    @api.multi
    def create_leaves(self):
        """
        This method will create a leave for all selected employees
        """
        self.ensure_one()
        if self.state != 'draft':
            raise exceptions.ValidationError('You can only create a leave '
                                             'from a public holiday in state '
                                             '"draft"')

        self.create_employee_leaves(self.employee_ids)
        self.state = 'done'

    @api.multi
    def create_employee_leaves(self, employee_ids):
        """
        This method will create a leave for the employees passed in parameter
        :param employee_ids: the employees to create the leave for
        """
        self.ensure_one()

        HRHolidays = self.env['hr.holidays']

        date_from, date_to = self.compensate_user_tz(self.date)

        if not self.holiday_status_id:
            raise exceptions.ValidationError(
                'No Leave Type has been configured as Public Holiday. Please '
                'go to Configuration > Leave Types and tick the box \'Public '
                'Holiday\' on the desired leave type.')

        values = {
            'name': self.name,
            'type': 'remove',
            'holiday_type': 'employee',
            'holiday_status_id': self.holiday_status_id.id,
            'date_from': date_from,
            'date_to': date_to,
            'number_of_days_temp': 1,
            'state': 'confirm',
            'is_batch': True,
        }

        context = {
            'mail_create_nosubscribe': True,
            'mail_create_nolog': True,
            'mail_notrack': True,
            'tracking_disable': True
        }

        # add the employee in case we generate for newcomers
        self.employee_ids += employee_ids

        for employee in employee_ids:
            values['employee_id'] = employee.id
            try:
                leave = HRHolidays.sudo().with_context(context).create(values)
                leave.with_context(context).action_validate()
            except exceptions.ValidationError, e:
                raise exceptions.ValidationError(
                    'The leave entries could not be generated as the '
                    'following error occurred:\n\n%s: %s'
                    % (employee.name, e.name))

    @api.multi
    def remove_leaves(self):
        """
        This method will remove the leave and its related
        analytic entries for all impacted employees
        """
        self.ensure_one()

        if self.state != 'done':
            raise exceptions.ValidationError('You can only delete a leave '
                                             'from a public holiday in state '
                                             '"done"')

        date_from, date_to = self.compensate_user_tz(self.date)
        holiday_ids = self.env['hr.holidays'].search(
            [('holiday_status_id', '=', self.holiday_status_id.id),
             ('date_from', '>=', date_from),
             ('date_to', '<=', date_to),
             ('employee_id', 'in', self.employee_ids.ids)])

        if self.env.user.has_group('base.group_system') \
                or self.env.user.has_group('hr.group_hr_manager'):
            holiday_ids.sudo().write({'state': 'draft'})
            holiday_ids.sudo().unlink()
        else:
            raise exceptions.ValidationError(
                'You do not have the rights to delete leave entries')

        self.state = 'draft'

    def compensate_user_tz(self, date):
        '''
        Return date compensated from user timezone
        :param date:
        :return:
        '''
        if not self.env.user.tz:
            raise exceptions.ValidationError('Please set a timezone in your '
                                             'user settings to assure a '
                                             'correct generation of leave '
                                             'entries.')

        date_obj = datetime.strptime(date, DF)
        date_from = datetime.combine(date_obj, datetime.min.time())
        date_to = datetime.combine(date_obj, datetime.max.time())
        user_tz_offset = fields.Datetime.context_timestamp(
            self.sudo(self._uid), date_from).tzinfo._utcoffset
        date_from_tz_comp = date_from - user_tz_offset
        date_to_tz_comp = date_to - user_tz_offset
        date_from_tz_comp_str = date_from_tz_comp.strftime(DTF)
        date_to_tz_comp_str = date_to_tz_comp.strftime(DTF)

        return date_from_tz_comp_str, date_to_tz_comp_str

    @api.multi
    def open_generate_wizard(self):
        """
        Open wizard to generate leave entry for newcomers
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr_holiday.generate_holiday_wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }


class HRHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    is_public_holiday = fields.Boolean('Public Holiday')
