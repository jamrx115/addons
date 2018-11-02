# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, AccessError

import logging
import time
import pytz
import math
import re

_logger = logging.getLogger(__name__)
HOURS_PER_DAY = 8
utc_time_zone = pytz.utc

#clase creada por alltic que modifica las ausencias
class HolidaysUpdated(models.Model):
    _inherit = 'hr.holidays'

    # override fields
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('delay', 'Postponed'),
        ('validate', 'Approved'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

    def _default_zero(self):
        today = datetime.now()
        user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        hour_zero_for_user = user_time_zone.localize(datetime(today.year, today.month, today.day, 0, 0, 0))
        hour_zero_utc = hour_zero_for_user.astimezone(utc_time_zone)
        return datetime(year=hour_zero_utc.year, month=hour_zero_utc.month, day=hour_zero_utc.day, hour=hour_zero_utc.hour, minute=hour_zero_utc.minute, second=hour_zero_utc.second)

    def _default_final(self):
        today = datetime.now()
        user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        hour_final_for_user = user_time_zone.localize(datetime(today.year, today.month, today.day, 23, 59, 59))
        hour_final_utc = hour_final_for_user.astimezone(utc_time_zone)
        return datetime(year=hour_final_utc.year, month=hour_final_utc.month, day=hour_final_utc.day, hour=hour_final_utc.hour, minute=hour_final_utc.minute, second=hour_final_utc.second)


    date_from = fields.Datetime('Start Date', readonly=True, index=True, copy=False,
                                states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                default=_default_zero)
    date_to = fields.Datetime('End Date', readonly=True, copy=False,
                              states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                default=_default_final)

    # new fields
    company_id = fields.Many2one('res.company', 'Compañía')
    date_return = fields.Datetime('Fecha de regreso', readonly=True, index=True, copy=False)

    #########################
    # para cálculo de días
    #########################

    # return holidays IN DICT
    def get_holidays_ids(self, date_from, date_to, country_emp_id):

        if date_from.year == date_to.year:
            holidays_ids = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', date_from), ('date', '<=', date_to),
                 ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_from.year),
                                                                         ('country_id', '=', country_emp_id)]).id)])
        else:
            holidays_ids1 = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', date_from),
                 ('date', '<=', datetime.strptime(str(date_from.year) + '-12-31', '%Y-%m-%d')),
                 ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_from.year),
                                                                         ('country_id', '=', country_emp_id)]).id)])
            holidays_ids = holidays_ids1 | self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', datetime.strptime(str(date_to.year) + '-01-01', '%Y-%m-%d')),
                 ('date', '<=', date_to),
                 ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_from.year),
                                                                         ('country_id', '=', country_emp_id)]).id)])
        return holidays_ids

    # return [a, b] with data for zero_hour and final_hour FOR A DAY
    def get_hours(self, first_date, last_date, date):

        utc_time_zone  = pytz.utc
        user_time_zone = pytz.timezone(self.env.user.partner_id.tz)

        hour_zero_for_user  = user_time_zone.localize(datetime(date.year, date.month, date.day, 0, 0, 0))
        hour_final_for_user = user_time_zone.localize(datetime(date.year, date.month, date.day, 23, 59, 59))

        hour_zero_utc  = hour_zero_for_user.astimezone(utc_time_zone)
        hour_final_utc = hour_final_for_user.astimezone(utc_time_zone)

        date = datetime(date.year, date.month, date.day, last_date.hour, last_date.minute, last_date.minute)

        if date.day == first_date.day:
            return [date,
                    datetime(hour_final_utc.year, hour_final_utc.month, hour_final_utc.day, hour_final_utc.hour, hour_final_utc.minute, hour_final_utc.second)]
        elif date.day == last_date.day:
            return [datetime(hour_zero_utc.year, hour_zero_utc.month, hour_zero_utc.day, hour_zero_utc.hour, hour_zero_utc.minute, hour_zero_utc.second),
                    date]
        else:
            return [datetime(hour_zero_utc.year, hour_zero_utc.month, hour_zero_utc.day, hour_zero_utc.hour, hour_zero_utc.minute, hour_zero_utc.second),
                    datetime(hour_final_utc.year, hour_final_utc.month, hour_final_utc.day, hour_final_utc.hour, hour_final_utc.minute, hour_final_utc.second)]

    # override
    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            resource = employee.resource_id.sudo()

            if resource and resource.calendar_id:
                country_emp_id = employee.company_id.country_id.id
                deduct_saturday = True
                deduct_sunday = True
                holidays_ids = self.get_holidays_ids(from_dt, to_dt, country_emp_id)
                subtrahend = 0.0

                date = from_dt
                delta = timedelta(days=1)
                while date <= to_dt:
                    date_str = str(date.date())
                    holiday_obj = holidays_ids.filtered(lambda r: r.date == date_str)

                    if holiday_obj:
                        f = self.get_hours(from_dt, to_dt, date)
                        h_f = resource.calendar_id.get_working_hours(f[0], f[1], resource_id=resource.id, compute_leaves=True)
                        subtrahend += h_f
                    elif date.weekday() == 5 and deduct_saturday:
                        s = self.get_hours(from_dt, to_dt, date)
                        h_s = resource.calendar_id.get_working_hours(s[0], s[1], resource_id=resource.id, compute_leaves=True)
                        subtrahend += h_s
                    elif date.weekday() == 6 and deduct_sunday:
                        d = self.get_hours(from_dt, to_dt, date)
                        h_d = resource.calendar_id.get_working_hours(d[0], d[1], resource_id=resource.id, compute_leaves=True)
                        subtrahend += h_d

                    date += delta

                hours = resource.calendar_id.get_working_hours(from_dt, to_dt, resource_id=resource.id, compute_leaves=True)
                hours = hours - subtrahend
                uom_hour = resource.calendar_id.uom_id
                uom_day = self.env.ref('product.product_uom_day')
                if uom_hour and uom_day:
                    return uom_hour._compute_quantity(hours, uom_day)

        time_delta = to_dt - from_dt
        return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)

    #########################
    # para botones
    #########################
    def _check_state_access_right(self, vals):
        is_approver = self.env['res.users'].has_group('hr_holidays.group_hr_holidays_user') or\
                      self.env['res.users'].has_group(
            'hr_holidays.group_hr_holidays_manager')
        if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'cancel'] and not is_approver:
            return False
        return True

    @api.multi
    def action_postponed(self):
        is_approver = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        if self.filtered(lambda holiday: holiday.state != 'validate1'):
            raise UserError('La solicitud de ausencia debe estar en estado "pre aprobada" para poder aplazarla.')
        template = self.env.ref('ciberc_holidays.postponed_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        return self.write({'state': 'delay'})

    @api.multi
    def action_confirm(self):
        is_approver = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError('La solicitud de ausencia debe estar en estado "Borrador" para enviarla.')
        template = self.env.ref('ciberc_holidays.confirm_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        return self.write({'state': 'confirm'})

    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        is_approver = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr_holidays.group_hr_holidays_manager')

        if not is_approver:
            raise UserError('Solamente un jefe de departamento o superior  puede aprobar la solicitud.')

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'confirm':
                raise UserError('La solicitud de ausencia debe estar enviada ("Pendiente de aprobación") para aprobarla.')

            # writing return_date
            to_dt = fields.Datetime.from_string(self.date_to)
            employee = self.employee_id
            resource = employee.resource_id.sudo()
            to_dt_zero_utc  = pytz.timezone(self.env.user.partner_id.tz).localize(datetime(to_dt.year, to_dt.month, to_dt.day, 0, 0, 0)).astimezone(pytz.utc)
            to_dt_hours_t = resource.calendar_id.working_hours_on_day(to_dt)
            to_dt_hours_w = resource.calendar_id.get_working_hours(datetime(to_dt_zero_utc.year, to_dt_zero_utc.month, to_dt_zero_utc.day, 0, 0, 0), to_dt, resource_id=resource.id, compute_leaves=True)
            date_return = to_dt if to_dt_hours_w < to_dt_hours_t else self.write_return_day(to_dt, employee.company_id.country_id.id)
            self.write({ 'date_return': date_return, })

            if holiday.double_validation:
                template = self.env.ref('ciberc_holidays.approve_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id)
                return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
            else:
                holiday.action_validate()

    @api.multi
    def action_validate(self):
        is_approver = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        if not is_approver:
            raise UserError('Solamente un jefe de departamento o superior puede aprobar la solicitud.')

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError('La solicitud de ausencia debe estar enviada ("Pendiente de aprobación") para aprobarla.')
            if holiday.state == 'validate1' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError('Solamente un jefe de departamento puede aplicar la segunda aprobación en solicitudes de ausencia.')

            holiday.write({'state': 'validate'})
            if holiday.double_validation:
                holiday.write({'manager_id2': manager.id})
                template = self.env.ref('ciberc_holidays.validate_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id)
            else:
                holiday.write({'manager_id': manager.id})
                template = self.env.ref('ciberc_holidays.validate_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id)
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                meeting_values = {
                    'name': holiday.display_name,
                    'categ_ids': [(6, 0, [holiday.holiday_status_id.categ_id.id])] if holiday.holiday_status_id.categ_id else [],
                    'duration': holiday.number_of_days_temp * HOURS_PER_DAY,
                    'description': holiday.notes,
                    'user_id': holiday.user_id.id,
                    'start': holiday.date_from,
                    'stop': holiday.date_to,
                    'allday': False,
                    'state': 'open',            # to block that meeting date in the calendar
                    'privacy': 'confidential'
                }
                #Add the partner_id (if exist) as an attendee
                if holiday.user_id and holiday.user_id.partner_id:
                    meeting_values['partner_ids'] = [(4, holiday.user_id.partner_id.id)]

                meeting = self.env['calendar.event'].with_context(no_mail_to_attendees=True).create(meeting_values)
                holiday._create_resource_leave()
                holiday.write({'meeting_id': meeting.id})
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                for employee in holiday.category_id.employee_ids:
                    values = holiday._prepare_create_by_category(employee)
                    leaves += self.with_context(mail_notify_force_send=False).create(values)
                # TODO is it necessary to interleave the calls?
                leaves.action_approve()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True

    @api.multi
    def action_refuse(self):
        is_approver = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        if not is_approver:
            raise UserError('Solamente  un jefe de departamento o superior puede rechazar la solicitud.')

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate', 'validate1', 'delay']:
                raise UserError(
                    'La solicitud de ausencia debe estar enviada ("Pendiente Aprobación" ), aplazada ("Aplazada") o aprobada ("Aprobada y Confirmada") para poder rechazarla.')

            if holiday.state == 'validate1':
                holiday.write({'state': 'refuse', 'manager_id': manager.id})
            else:
                holiday.write({'state': 'refuse', 'manager_id2': manager.id})
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
            
            template = self.env.ref('ciberc_holidays.refuse_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id)

        self._remove_resource_leave()
        return True

    #########################
    # para día de retorno
    #########################

    # return True if date is holiday, saturday or sunday
    def is_special_day(self, date, country_emp_id):
        answer = False
        date_str = str(date.date())
        is_holiday = self.get_holidays_ids(date-timedelta(days=1), date, country_emp_id).filtered(lambda r: r.date == date_str)
        if (len(is_holiday) == 1) or (date.weekday() == 5) or (date.weekday() == 6): answer = True
        return answer

    # return return_day
    def write_return_day(self, to_dt, country_emp_id):
        day = to_dt+timedelta(days=1)
        control = self.is_special_day(day, country_emp_id)

        while (control):
            if day.weekday() == 5:
                day = day+timedelta(days=2)
            else:
                day = day+timedelta(days=1)
            control = self.is_special_day(day, country_emp_id)

        answer = datetime(year=day.year, month=day.month, day=day.day)
        return answer

#clase creada por alltic que agrega fecha fin para reporte
class ReportLeavesnewFieldbyDepartment(models.TransientModel):
    _inherit = 'hr.holidays.summary.dept'

    date_to = fields.Date(string='Hasta', required=True, default=lambda *a: time.strftime('%Y-%m-01'))

#clase creada por alltic que calcula datos para reporte de ausencias por fechas
class ReportLeavesbyDepartment(models.AbstractModel):
    _inherit = 'report.hr_holidays.report_holidayssummary'

    def _get_header_info(self, start_date, end_date, holiday_type):
        st_date = fields.Date.from_string(start_date)
        en_date = fields.Date.from_string(end_date)
        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(en_date), # 59
            'holiday_type': 'Confirmed and Approved' if holiday_type == 'both' else holiday_type
        }

    def _get_day(self, start_date, end_date):
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        number_days = ((end_date-start_date).days)+1
        for x in range(0, number_days): # 60
            color = '#ababab' if start_date.strftime('%a') == 'Sat' or start_date.strftime('%a') == 'Sun' else ''
            res.append({'day_str': start_date.strftime('%a'), 'day': start_date.day , 'color': color})
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_months(self, start_date, end_date):
        # it works for geting month name between two dates.
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date) # 59
        while start_date <= end_date:
            last_date = start_date + relativedelta(day=1, months=+1, days=-1)
            if last_date > end_date:
                last_date = end_date
            month_days = (last_date - start_date).days + 1
            res.append({'month_name': start_date.strftime('%B'), 'days': month_days})
            start_date += relativedelta(day=1, months=+1)
        return res

    def _get_leaves_summary(self, start_date, end_date, empid, holiday_type):
        res = []
        count = 0
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date) # 59
        number_days = ((end_date-start_date).days)+1
        for index in range(0, number_days): # 60
            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': ''})
            if current.strftime('%a') == 'Sat' or current.strftime('%a') == 'Sun':
                res[index]['color'] = '#ababab'
        # count and get leave summary details.
        holiday_type = ['confirm','validate'] if holiday_type == 'both' else ['confirm'] if holiday_type == 'Confirmed' else ['validate']
        holidays = self.env['hr.holidays'].search([
            ('employee_id', '=', empid), ('state', 'in', holiday_type),
            ('type', '=', 'remove'), ('date_from', '<=', str(end_date)),
            ('date_to', '>=', str(start_date))
        ])
        for holiday in holidays:
            # Convert date to user timezone, otherwise the report will not be consistent with the
            # value displayed in the interface.
            date_from = fields.Datetime.from_string(holiday.date_from)
            date_from = fields.Datetime.context_timestamp(holiday, date_from).date()
            date_to = fields.Datetime.from_string(holiday.date_to)
            date_to = fields.Datetime.context_timestamp(holiday, date_to).date()
            for index in range(0, ((date_to - date_from).days + 1)): # 60
                if date_from >= start_date and date_from <= end_date:
                    res[(date_from-start_date).days]['color'] = holiday.holiday_status_id.color_name
                    count += 1
                date_from += timedelta(1)
            # count += abs(holiday.number_of_days)
        self.sum = count
        return res

    def _get_data_from_report(self, data):
        res = []
        Employee = self.env['hr.employee']
        if 'depts' in data:
            for department in self.env['hr.department'].browse(data['depts']):
                res.append({'dept' : department.name, 'data': [], 'color': self._get_day(data['date_from'], data['date_to'])})
                for emp in Employee.search([('department_id', '=', department.id)]):
                    res[len(res)-1]['data'].append({
                        'emp': emp.name,
                        'display': self._get_leaves_summary(data['date_from'], data['date_to'], emp.id, data['holiday_type']),
                        'sum': self.sum
                    })
        elif 'emp' in data:
            res.append({'data':[]})
            for emp in Employee.browse(data['emp']):
                res[0]['data'].append({
                    'emp': emp.name,
                    'display': self._get_leaves_summary(data['date_from'], data['date_to'], emp.id, data['holiday_type']),
                    'sum': self.sum
                })
        return res

    @api.model
    def render_html(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        Report = self.env['report']
        holidays_report = Report._get_report_from_name('hr_holidays.report_holidayssummary')
        holidays = self.env['hr.holidays'].browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': holidays_report.model,
            'docs': holidays,
            'get_header_info': self._get_header_info(data['form']['date_from'], data['form']['date_to'], data['form']['holiday_type']),
            'get_day': self._get_day(data['form']['date_from'], data['form']['date_to']),
            'get_months': self._get_months(data['form']['date_from'], data['form']['date_to']),
            'get_data_from_report': self._get_data_from_report(data['form']),
            'get_holidays_status': self._get_holidays_status(),
        }
        return Report.render('hr_holidays.report_holidayssummary', docargs)

#clase creada por alltic que crea codigo para regla salarial desde tipo de ausencia
class CodeLeaveType(models.Model):
    _inherit = 'hr.holidays.status'

    code = fields.Char('Código para regla salarial')

    @api.multi
    @api.onchange('code')
    def _check_code(self):
        if self.code:
            pattern = "^[A-Z0-9]{3,6}$"
            if re.match(pattern, self.code) == None:
                self.code = ""
                return {
                    'warning': {'title': 'Error',
                                'message': 'Formato de código no valido, debe incluir términos alfanúmeros y guion (si aplica), longitud 3 a 6 caracteres', }
                }

#clase creada por alltic que trabaja con el codigo para regla salarial
class CodeLeaveTypePayroll(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """

        def was_on_leave_interval(employee_id, date_from, date_to):
            date_from = fields.Datetime.to_string(date_from)
            date_to = fields.Datetime.to_string(date_to)
            return self.env['hr.holidays'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', date_from),
                ('date_to', '>=', date_to)
            ], limit=1)

        res = []
        # fill only if the contract as a working schedule linked
        uom_day = self.env.ref('product.product_uom_day', raise_if_not_found=False)
        for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
            uom_hour = contract.employee_id.resource_id.calendar_id.uom_id or self.env.ref('product.product_uom_hour',
                                                                                           raise_if_not_found=False)
            interval_data = []
            holidays = self.env['hr.holidays']
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }
            leaves = {}
            day_from = fields.Datetime.from_string(date_from)
            day_to = fields.Datetime.from_string(date_to)
            nb_of_days = (day_to - day_from).days + 1

            # Gather all intervals and holidays
            for day in range(0, nb_of_days):
                working_intervals_on_day = contract.working_hours.get_working_intervals_of_day(
                    start_dt=day_from + timedelta(days=day))
                for interval in working_intervals_on_day:
                    interval_data.append(
                        (interval, was_on_leave_interval(contract.employee_id.id, interval[0], interval[1])))

            # Extract information from previous data. A working interval is considered:
            # - as a leave if a hr.holiday completely covers the period
            # - as a working period instead
            for interval, holiday in interval_data:
                holidays |= holiday
                hours = (interval[1] - interval[0]).total_seconds() / 3600.0
                if holiday:
                    # if he was on leave, fill the leaves dict
                    if holiday.holiday_status_id.name in leaves:
                        leaves[holiday.holiday_status_id.name]['number_of_hours'] += hours
                    else:
                        leaves[holiday.holiday_status_id.name] = {
                            'name': holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.code,
                            'number_of_days': 0.0,
                            'number_of_hours': hours,
                            'contract_id': contract.id,
                        }
                else:
                    # add the input vals to tmp (increment if existing)
                    attendances['number_of_hours'] += hours

            # Clean-up the results
            leaves = [value for key, value in leaves.items()]
            for data in [attendances] + leaves:
                data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'], uom_day) \
                    if uom_day and uom_hour \
                    else data['number_of_hours'] / 8.0
                res.append(data)
        return res

#clase creada por alltic que crea valor anual para job
class CodeHoliday(models.Model):
    _inherit = 'hr.contract'

    annual_holiday = fields.Integer('Días libres anuales', help='Vacaciones para contrato laboral y días libres para prestación de servicios')
