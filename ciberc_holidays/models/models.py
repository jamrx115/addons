# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
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
    number_of_days_calendar = fields.Float('Días Calendario')

    # -override
    @api.model
    def create(self, vals):

        if vals['type'] == 'add':
            vals['date_from'] = None
            vals['date_to'] = None

        return super(HolidaysUpdated, self).create(vals)

    #########################
    # para cálculo de días
    #########################

    # return holidays IN DICT
    def get_holidays_ids(self, date_from, date_to, country_emp_id):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)

        date_from_tz_user = user_tz.fromutc(date_from)  # tz user
        date_to_tz_user = user_tz.fromutc(date_to)  # tz user

        if date_from_tz_user.year == date_to_tz_user.year:
            holidays_ids = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', date_from_tz_user), ('date', '<=', date_to_tz_user),
                 ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_from_tz_user.year),
                                                                         ('country_id', '=', country_emp_id)]).id)])
        else:
            holidays_ids1 = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', date_from_tz_user),
                 ('date', '<=', datetime.strptime(str(date_from_tz_user.year) + '-12-31', '%Y-%m-%d')),
                 ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_from_tz_user.year),
                                                                         ('country_id', '=', country_emp_id)]).id)])
            holidays_ids2 = self.env['hr.holidays.public.line'].search(
                ['&', '&', ('date', '>=', datetime.strptime(str(date_to_tz_user.year) + '-01-01', '%Y-%m-%d')),
                 ('date', '<=', date_to_tz_user),
                 ('year_id', '=', self.env['hr.holidays.public'].search(['&', ('year', '=', date_to_tz_user.year),
                                                                         ('country_id', '=', country_emp_id)]).id)])
            holidays_ids = holidays_ids1 | holidays_ids2
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
        tipo_ausencia = self.holiday_status_id.code
        guatemala = self.env['res.country'].search([['name', '=', 'Guatemala']])

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
                    hours_range = self.get_hours(from_dt, to_dt, date)
                    working_hours = resource.calendar_id.get_working_hours(hours_range[0], hours_range[1], resource_id=resource.id, compute_leaves=True)

                    if holiday_obj:
                        subtrahend += working_hours
                    elif date.weekday() == 5 and deduct_saturday:
                        subtrahend += working_hours
                    elif date.weekday() == 6 and deduct_sunday:
                        subtrahend += working_hours

                    if tipo_ausencia and country_emp_id == guatemala.id:
                        if tipo_ausencia[:3] == 'VAC' or tipo_ausencia[:3] == 'DLI':
                            if date.month == 12 and (date.day == 24 or date.day == 31):
                                subtrahend += working_hours / 2

                    date += delta

                hours = resource.calendar_id.get_working_hours(from_dt, to_dt, resource_id=resource.id, compute_leaves=True)
                hours = round(hours, 6)
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

        if self.type == 'remove':
            from_dt = fields.Datetime.from_string(self.date_from)
            to_dt = fields.Datetime.from_string(self.date_to)

            calendar_delta = to_dt - from_dt
            calendar_days = -1 * round(calendar_delta.total_seconds() / 86400 , 2)
            self.write({'number_of_days_calendar': calendar_days})
        else:
            self.write({'number_of_days_calendar': self.number_of_days})

        template = self.env.ref('ciberc_holidays.confirm_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

        return self.write({'state': 'confirm'})

    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        is_approver = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        user_tz = pytz.timezone(self.env.user.partner_id.tz)

        if not is_approver:
            raise UserError('Solamente un jefe de departamento o superior  puede aprobar la solicitud.')

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'confirm':
                raise UserError('La solicitud de ausencia debe estar enviada ("Pendiente de aprobación") para aprobarla.')

            if holiday.type == 'remove':
                # writing return_date
                to_dt = fields.Datetime.from_string(self.date_to)

                to_dt_tz_user = user_tz.fromutc(to_dt) # tz user
                to_dt_user    = datetime.combine(to_dt_tz_user.date(), to_dt_tz_user.time())
                to_dt_user_ztz = user_tz.localize(datetime(to_dt_user.year, to_dt_user.month, to_dt_user.day, 0, 0, 0)) # tz user
                to_dt_utcz_ztz = to_dt_user_ztz.astimezone(pytz.utc) # tz utczero
                to_dt_utcz_z = datetime.combine(to_dt_utcz_ztz.date(), to_dt_utcz_ztz.time())

                employee = self.employee_id
                resource = employee.resource_id.sudo()

                to_dt_hours_t = resource.calendar_id.working_hours_on_day(to_dt)
                to_dt_hours_w = resource.calendar_id.get_working_hours(to_dt_utcz_z, to_dt, resource_id=resource.id, compute_leaves=True)

                date_return = to_dt if to_dt_hours_w < to_dt_hours_t else self.write_return_day(to_dt, employee.company_id.country_id.id)
                self.write({ 'date_return': date_return, })

                if holiday.double_validation:
                    template = self.env.ref('ciberc_holidays.approve_template')
                    self.env['mail.template'].browse(template.id).send_mail(self.id)
                    return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
                else:
                    holiday.action_validate()
            else: # holiday.type == 'add'
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

            if holiday.type == 'remove':
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
                    #if holiday.user_id and holiday.user_id.partner_id:
                        #meeting_values['partner_ids'] = [(4, holiday.user_id.partner_id.id)]

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
            else: # holiday.type == 'add'
                template = self.env.ref('ciberc_holidays.approve_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id)
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
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        date_tz_user = user_tz.fromutc(to_dt)  # tz user
        date_user = datetime.combine(date_tz_user.date(), date_tz_user.time())

        day = date_user+timedelta(days=1)
        control = self.is_special_day(day, country_emp_id)

        while (control):
            if day.weekday() == 5:
                day = day+timedelta(days=2)
            else:
                day = day+timedelta(days=1)
            control = self.is_special_day(day, country_emp_id)

        answer_tz_user = user_tz.localize(datetime(day.year, day.month, day.day, 0, 0, 0))  # tz user
        answer_tz_zero = answer_tz_user.astimezone(pytz.utc)  # tz zero
        answer = datetime.combine(answer_tz_zero.date(), answer_tz_zero.time())
        return answer

    #########################
    # para constancia
    #########################

    # return remaining days (holiday_status_id es el tipo de ausencia)
    def get_remaining_days(self, holiday_status, employee):
        holiday_status_id = holiday_status.id
        employee_id = employee.id
        answer = 0

        aprobadas_y_confirmadas = self.env['hr.holidays'].search(
                ['&', '&', ('employee_id', '=', employee_id), ('holiday_status_id', '=', holiday_status_id),
                      ('state', '=', 'validate')])

        for registro in aprobadas_y_confirmadas:
            answer += registro.number_of_days_calendar

        return answer

#clase creada por alltic que agrega fecha fin para reporte
class ReportLeavesnewFieldbyDepartment(models.TransientModel):
    _inherit = 'hr.holidays.summary.dept'

    date_to = fields.Date(string='Hasta', required=True, default=lambda *a: time.strftime('%Y-%m-01'))

#clase creada por alltic que agrega fecha fin para reporte
class ReportLeavesnewFieldfromEmployee(models.TransientModel):
    _inherit = 'hr.holidays.summary.employee'

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