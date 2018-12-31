# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta

import logging
import calendar
import babel
import time
import pytz

_logger = logging.getLogger(__name__)

#
class PayslipWorkedDaysUpdated(models.Model):
    _inherit = 'hr.payslip.worked_days'

    number_of_days_calendar = fields.Float(string='Días Calendario')
    distance_from_holiday = fields.Integer(string='Distancia al inicio de la ausencia')


# clase creada por alltic que personaliza reglas salariales
class CodeLeaveTypePayroll(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def action_payslip_verify(self):
        return self.write({'state': 'verify'})

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        user_tz = pytz.timezone(self.env.user.partner_id.tz)

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
                'number_of_days_calendar': 0.0,  # empty
                'date_from': None,  # empty
                'date_to': None,  # empty
                'distance_from_holiday': 0,  # empty
            }
            leaves = {}
            day_from_contract = fields.Datetime.from_string(contract.date_start)
            day_from_payslip = fields.Datetime.from_string(date_from)
            day_to_contract = fields.Datetime.from_string(contract.date_end)
            day_to_payslip = fields.Datetime.from_string(date_to)
            if day_from_contract > day_from_payslip:
                day_from = day_from_contract
            else:
                day_from = day_from_payslip
            if day_to_contract:
                if day_to_contract < day_to_payslip:
                    day_to = day_to_contract
                else:
                    day_to = day_to_payslip
            else:
                day_to = day_to_payslip
            nb_of_days = (day_to - day_from).days + 1
            country_emp_id = contract.employee_id.company_id.country_id.id
            holidays_ids = holidays.get_holidays_ids(day_from, day_to, country_emp_id)
            # holidays_ids, day_from, day_to en UTC "usuario"
            for day in range(0, nb_of_days):
                working_intervals_on_day = contract.working_hours.get_working_intervals_of_day(
                    start_dt=day_from + timedelta(days=day))
                for interval in working_intervals_on_day:  # interval is tuple
                    tuple_to_list = list(interval)
                    aux_leaves = was_on_leave_interval(contract.employee_id.id, interval[0], interval[1])
                    aux_interv_i = user_tz.fromutc(interval[0])
                    tuple_to_list[0] = datetime.combine(aux_interv_i.date(), aux_interv_i.time())
                    aux_interv_f = user_tz.fromutc(interval[1])
                    tuple_to_list[1] = datetime.combine(aux_interv_f.date(), aux_interv_f.time())
                    interval_updated = tuple(tuple_to_list)
                    interval_data.append((interval_updated, aux_leaves))  # se cambia interval por interval_updated

            # Note: Here, the dates are in UTC-0
            for interval, ausencia in interval_data:
                holidays |= ausencia
                hours = (interval[1] - interval[0]).total_seconds() / 3600.0
                date_str = str(interval[0].date())
                holiday_obj = holidays_ids.filtered(lambda r: r.date == date_str)

                if ausencia:  # hay ausencia -> conteo ausencia
                    if ausencia.holiday_status_id.name in leaves:
                        leaves[ausencia.holiday_status_id.name]['date_to'] = interval[1].date()
                        if (interval[0].weekday() == 5) or (interval[0].weekday() == 6) or holiday_obj:
                            attendances['number_of_hours'] += hours
                        else:
                            leaves[ausencia.holiday_status_id.name]['number_of_hours'] += hours
                    else:
                        aux_df_utczero = fields.Datetime.from_string(ausencia.date_from)
                        aux_df_utc_user = user_tz.fromutc(aux_df_utczero)
                        ausencia_date_from = datetime.combine(aux_df_utc_user.date(), aux_df_utc_user.time())
                        leaves[ausencia.holiday_status_id.name] = {
                            'name': ausencia.holiday_status_id.name,
                            'sequence': 5,
                            'code': ausencia.holiday_status_id.code,
                            'number_of_days': 0.0,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,

                            'number_of_days_calendar': 0.0,
                            'date_from': interval[0].date(),
                            'date_to': interval[1].date(),
                            'distance_from_holiday': (ausencia_date_from - day_from).days,
                        }
                        if (interval[0].weekday() == 5) or (interval[0].weekday() == 6) or holiday_obj:
                            attendances['number_of_hours'] += hours
                        else:
                            leaves[ausencia.holiday_status_id.name]['number_of_hours'] += hours
                else:
                    # no hay ausencia -> conteo WORK100
                    attendances['number_of_hours'] += hours

            leaves = [value for key, value in leaves.items()]

            auxiliar_for_WORK100 = 0.00
            for data in [attendances] + leaves:
                data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'], uom_day) \
                    if uom_day and uom_hour \
                    else data['number_of_hours'] / 8.0

                if data['code'] != 'WORK100':
                    calendar_delta = data['date_to'] - data['date_from']
                    number_of_days_calendar = round(calendar_delta.days + float(calendar_delta.seconds) / 86400,
                                                    2) + 1.00
                    auxiliar_for_WORK100 += number_of_days_calendar
                    data['number_of_days_calendar'] = number_of_days_calendar

                res.append(data)

            res[0]['number_of_days_calendar'] = nb_of_days - auxiliar_for_WORK100
            # Se traslada solución a regla salarial
            # if day_to.day == 31:
            #     res[0]['number_of_days'] = res[0]['number_of_days'] - 1
            #     res[0]['number_of_days_calendar'] = res[0]['number_of_days_calendar'] - 1

        return res

    @api.onchange('employee_id', 'date_from', 'date_to', 'contract_id')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'es_CO'
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                self.contract_id = None
                self.worked_days_line_ids = None
                self.input_line_ids = None
                return
            if not self.contract_id:
                self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        # filter only for current contract
        contract_ids = [self.contract_id.id]

        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id

        # computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(contract_ids, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        input_line_ids = self.get_inputs(contract_ids, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return

    # obtener sumatoria salarios
    @api.multi
    def sum_wage(self, employee_p, date_from_payslip, date_to_payslip, rule, order):
        result = 0
        date_from_payslip = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_to_payslip = fields.Datetime.from_string(date_to_payslip)  # tipo datetime

        employee = self.env['hr.employee'].browse(employee_p)  # tipo hr_employee

        if rule == 'BONO14' or rule == 'AGUINALDO':
            meses1 = [mn for mn in range(date_from_payslip.month, 13)]
            meses2 = [mn for mn in range(1, date_to_payslip.month + 1)]
            meses = meses1 + meses2
        else:
            meses = [mn for mn in range(date_from_payslip.month, date_to_payslip.month + 1)]

        for mes in meses:
            date_from_mes = datetime(year=date_from_payslip.year, month=mes, day=1)  # tipo datetime
            date_to_mes = datetime(year=date_to_payslip.year, month=mes,
                                   day=calendar.monthrange(date_to_payslip.year, mes)[1])  # tipo datetime

            payslip_ids = self.env['hr.payslip'].search(
                ['&', '&', '&', ('date_from', '>=', date_from_mes), ('date_to', '<=', date_to_mes),
                 ('employee_id', '=', employee.id),
                 ('state', '=', 'done')])
            for nomina in payslip_ids:
                contract = self.env['hr.contract'].search([('id', '=', nomina.contract_id.id)])
                salario = contract.wage
                contract_start = fields.Datetime.from_string(contract.date_start)  # tipo datetime
                contract_end = False
                if contract.date_end:
                    contract_end = fields.Datetime.from_string(contract.date_end)  # tipo datetime

                if contract_start < date_from_mes:
                    if contract_end:
                        if date_to_mes < contract_end:
                            dias = ((date_to_mes - date_from_mes).days) + 1
                        else:
                            dias = ((contract_end - date_from_mes).days) + 1
                    else:
                        dias = ((date_to_mes - date_from_mes).days) + 1
                else:
                    if contract_end:
                        if date_to_mes < contract_end:
                            dias = ((date_to_mes - contract_start).days) + 1
                        else:
                            dias = ((contract_end - contract_start).days) + 1
                    else:
                        dias = ((date_to_mes - contract_start).days) + 1

                if order == 'WAGE':
                    result += (salario / 30) * dias
                else:
                    result += dias

        return result

    # obtener sumatoria comisiones
    @api.multi
    def sum_other(self, employee_p, date_from_payslip, date_to_payslip, rule, code):
        date_from_payslip = fields.Datetime.from_string(date_from_payslip) # tipo datetime
        date_to_payslip = fields.Datetime.from_string(date_to_payslip)  # tipo datetime

        if rule == 'BONO14':
            date_from_bono = datetime(year=(date_from_payslip.year) - 1, month=7, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=6, day=30)  # tipo datetime
        elif rule == 'AGUINALDO':
            date_from_bono = datetime(year=(date_from_payslip.year) - 1, month=12, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=11, day=30)  # tipo datetime
        elif rule == 'PRIMA1':
            date_from_bono = datetime(year=(date_from_payslip.year) - 1, month=1, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=6, day=30)  # tipo datetime
        else:
            date_from_bono = datetime(year=(date_from_payslip.year) - 1, month=7, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=12, day=31)  # tipo datetime

        result = 0.00
        employee = self.env['hr.employee'].browse(employee_p)  # tipo hr_employee
        contract_ids = self.get_contract(employee, date_from_bono, date_to_bono)  # tipo [int]
        payslip_ids = self.env['hr.payslip'].search(['&', ('contract_id', '=', None), ('state', '=', 'done')],
                                                    limit=0)  # recordset vacío para concatenar

        for contract_id in contract_ids:
            payslip_aux = self.env['hr.payslip'].search(
                ['&', '&', '&', ('date_from', '>=', date_from_bono), ('date_to', '<=', date_to_bono),
                 ('contract_id', '=', contract_id),
                 ('state', '=', 'done')])

            payslip_ids = payslip_ids + payslip_aux

        for payslip in payslip_ids:
            for input in payslip.line_ids:
                if input.code == code:
                    result += input.amount

        return result

    def get_lastfortnight(self, contract, date_from_payslip, code):
        date_from_payslip = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_from = datetime(day=1, month=date_from_payslip.month, year=date_from_payslip.year)
        date_to = date_from_payslip - timedelta(days=1)
        result = 0.00

        last_payslip = self.env['hr.payslip'].search(
            ['&', '&', '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to),
             ('contract_id', '=', contract.id),
             ('state', '=', 'done')])

        for input in last_payslip.line_ids:
            if input.code == code:
                result += input.amount

        return result

    def get_lastsixpaysplips(self, employee_p, code):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        hoy = datetime.now(tz=user_tz).date()
        date_to = datetime(year=hoy.year, month=hoy.month, day=calendar.monthrange(hoy.year, hoy.month)[1])
        employee = self.env['hr.employee'].browse(employee_p)  # tipo hr_employee

        guia = date_to - timedelta (days=180) # 30*6=180
        date_from = datetime(year=guia.year, month=guia.month, day=1)
        #_logger.debug('------------------------------- [%s, %s]', date_from, date_to)
        nominas = self.env['hr.payslip'].search(
            ['&', '&', '&', ('employee_id', '=', employee.id),
                            ('state', '=', 'done'),
                        ('date_from', '>=', date_from),
                   ('date_to', '<=', date_to)],
            order="date_from")
        sum_salaries = 0

        for nomina in nominas:
            line_ids = nomina.line_ids
            for line in line_ids:
                if line.code == code:
                    sum_salaries += line.total

        return sum_salaries

    def get_pending_holidays(self, employee_p):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        hoy = datetime.now(tz=user_tz).date()

        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])
        holiday_status_ids = self.env['hr.holidays.status'].search(
            ['|', ('code', '=like', 'VAC%'), ('code', '=like', 'DLI%')]).ids

        employee = self.env['hr.employee'].browse(employee_p)
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order = 'date_start desc')
        holidays = self.env['hr.holidays'].search(
            ['&', '&', ('employee_id', '=', employee.id), ('state', '=', 'validate'),
                  ('holiday_status_id', 'in', holiday_status_ids)], order = 'holiday_status_id')

        global_pending_holidays = 0
        aux_pending_holidays = 0
        pending_holidays = {}

        # contar vacaciones pendientes (agrupadas por bolsas de días)
        if len(holidays)>0:
            current_holiday_status = holidays[0].holiday_status_id
            for h in holidays:
                if h.holiday_status_id != current_holiday_status:
                    current_holiday_status = h.holiday_status_id
                    aux_pending_holidays = 0
                global_pending_holidays += h.number_of_days
                aux_pending_holidays += h.number_of_days
                pending_holidays[current_holiday_status] = aux_pending_holidays

        # si hoy > fecha de cumpleaños de contrato, calcular días adicionales de vacaciones generados
        for c in contracts:
            if c.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                date_start = fields.Datetime.from_string(c.date_start)
                fecha_aux = datetime(year=hoy.year, month=date_start.month, day=date_start.day).date()
                if hoy > fecha_aux:
                    date_delta = (hoy - fecha_aux).days + 1.0
                    global_pending_holidays += date_delta * 15.0 / 365.0
                    break

        # cerrar las vacaciones pendientes
        for ph in pending_holidays:
            pass

        return global_pending_holidays

    def get_pending_agui(self, employee_p):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        hoy = datetime.now(tz=user_tz).date() # tipo date
        last_year = hoy.year - 1
        inicio_aguinaldo = datetime(day=1, month=12, year=last_year).date()
        fin_aguinaldo = datetime(day=30, month=11, year=hoy.year).date()
        date_guia = hoy - timedelta(days=180)
        _logger.debug('---------------- date_guia %s', date_guia)
        start_contract = 1

        employee = self.env['hr.employee'].browse(employee_p)
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order='date_start desc')
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search(
            [('name', '=', 'Vinculación laboral')])

        for c in contracts:
            if c.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                start_contract = fields.Datetime.from_string(c.date_start).day
                date_guia = datetime(day=start_contract, month=date_guia.month, year=date_guia.year).date()
                break

        global_pending_agui = 0

        _logger.debug('---------------- inicio_aguinaldo %s', inicio_aguinaldo)
        _logger.debug('---------------- fin_aguinaldo %s', fin_aguinaldo)
        for i in range (6):
            _logger.debug('---------------- date_guia %s', date_guia)
            date_guia = date_guia + timedelta(days=30)
            date_guia = datetime(day=start_contract, month=date_guia.month, year=date_guia.year).date()
            #if date_guia >= inicio_aguinaldo and date_guia <= fin_aguinaldo:
            #    global_pending_agui += 0 #calendar.monthrange(date_guia.year, date_guia.month)[1]

        return global_pending_agui

# clase creada por alltic que permite obtener datos para reportes
class HrEmployeePayslip(models.Model):
    _inherit = 'hr.employee'

    payslip_count = fields.Integer(compute='_compute_payslip_count', string='Payslips')

    def is_leap_year(self):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        current_year = datetime.now(tz=user_tz).year

        if current_year % 4 == 0:
            if current_year % 100 == 0:
                if current_year % 400 == 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    def get_age(self):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        fecha_nacimiento = fields.Datetime.from_string(self.birthday).date()
        hoy = datetime.now(tz=user_tz).date()
        return (hoy - fecha_nacimiento).days / 365

    def get_filtered_lineid(self, code):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        last_year = (datetime.now(tz=user_tz).date().year) - 1
        aux = 0
        for m in range(12):
            mes = m + 1
            date_from = datetime(day=1, month=mes, year=last_year).date()
            date_to = datetime(day=calendar.monthrange(last_year, mes)[1], month=mes, year=last_year).date()
            pagos = self.env['hr.payslip'].search(
                ['&', '&', '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to),
                 ('employee_id', '=', self.id), ('state', '=', 'done')],
                order="date_from")
            for nomina in pagos:
                line_ids = nomina.line_ids
                for line in line_ids:
                    if line.code == code:
                        aux += line.total
        return aux

    def get_data(self):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        today = datetime.now(tz=user_tz).date()
        current_year = today.year
        answer = []
        struct_agui = self.env['hr.payroll.structure'].search([('code', '=', 'AGUINALDO GT')])
        struct_bono = self.env['hr.payroll.structure'].search([('code', '=', 'BONO14 GT')])
        for m in range(12):
            date_from = datetime(day=1, month=m + 1, year=current_year).date()
            date_to = datetime(day=calendar.monthrange(current_year, m + 1)[1], month=m + 1, year=current_year).date()
            pagos_nominas = self.env['hr.payslip'].search(
                ['&', '&', ('employee_id', '=', self.id), ('state', '=', 'done'),
                      '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to)],
                order="date_from")
            pagos_bonos = self.env['hr.payslip'].search(
                ['&', '&', ('employee_id', '=', self.id), ('state', '=', 'done'),
                      '|', ('struct_id', '=', struct_agui.id), ('struct_id', '=', struct_bono.id),
                      ('date_to', '=', date_to)],
                order="date_from")
            pagos = pagos_nominas + pagos_bonos

            locale = self.env.context.get('lang') or 'es_CO'
            nombre_mes = ('%s') % (tools.ustr(babel.dates.format_date(date=date_from, format='MMMM', locale=locale)))
            mes = m + 1
            salario_mensual = 0
            moneda = False
            # sección horas trabajadas
            h_normal = 0
            h_total = 0
            # sección salario devengado
            s_recibido = 0
            s_ordinario = 0
            s_vacaciones = 0
            d_vacaciones = 0
            d_total = 0
            # sección deducciones legales
            d_igss = 0
            d_otros = 0
            # sección final
            sum_agui = 0
            dec_372001 = 0

            for nomina in pagos:
                moneda = nomina.contract_id.x_currency_id
                salario_mensual = nomina.contract_id.wage

                worked_days_line_ids = nomina.worked_days_line_ids
                for wd in worked_days_line_ids:
                    h_total += wd.number_of_hours
                    if wd.code.startswith('VAC') or wd.code.startswith('DLI'):
                        d_vacaciones += wd.number_of_days_calendar

                line_ids = nomina.line_ids

                for line in line_ids:
                    if line.code == 'DIASTRABAJO':
                        d_total += line.total
                    if line.code == 'IGSS':
                        d_igss += line.total
                    if line.code == 'TOTALDED':
                        d_otros += line.total
                    if line.code == 'BON37':
                        dec_372001 += line.total
                    if line.code == 'NET':
                        s_recibido += line.total
                    if line.code == 'AGUI':
                        sum_agui += line.total
                        s_recibido += line.total
                    if line.code == 'BON14':
                        sum_agui += line.total
                        s_recibido += line.total

                s_ordinario = (salario_mensual / 30) * (d_total - d_vacaciones)
                s_vacaciones = (salario_mensual / 30) * d_vacaciones

            resource = self.resource_id.sudo()
            horas_diarias = resource.calendar_id.working_hours_on_day(datetime(day=1, month=mes, year=current_year))
            h_normal = horas_diarias * d_total

            row = [moneda, mes, nombre_mes, salario_mensual, d_total,
                   h_normal, 0.00,
                   s_ordinario, 0.00, 0.00, s_vacaciones, (s_ordinario + s_vacaciones),
                   d_igss, (d_otros - d_igss), d_otros,
                   sum_agui, dec_372001, s_recibido]
            answer.append(row)
        return answer