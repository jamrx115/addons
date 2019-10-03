# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta

import dateutil.relativedelta
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
        guatemala = self.env['res.country'].search([['name', '=', 'Guatemala']])

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
                'hours_half_holidays': 0,
                'hours_holiday_leaves': 0,
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
            calendar_days = (day_to - day_from).days + 1
            country_emp_id = contract.employee_id.company_id.country_id.id
            holidays_ids = holidays.get_holidays_ids(day_from, day_to, country_emp_id)
            # holidays_ids, day_from, day_to en UTC "usuario"
            for day in range(0, calendar_days):
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
                            leaves[ausencia.holiday_status_id.name]['hours_holiday_leaves'] += hours
                        else:
                            leaves[ausencia.holiday_status_id.name]['number_of_hours'] += hours

                            if country_emp_id == guatemala.id:
                                if ausencia.holiday_status_id.code[:3] == 'VAC' or ausencia.holiday_status_id.code[:3] == 'DLI':
                                    if interval[0].month == 12 and (interval[0].day == 24 or interval[0].day == 31):
                                        leaves[ausencia.holiday_status_id.name]['hours_half_holidays'] += hours / 2
                                        leaves[ausencia.holiday_status_id.name]['number_of_hours'] -= hours / 2
                                        attendances['number_of_hours'] += hours / 2
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
                            'hours_half_holidays': 0,
                            'hours_holiday_leaves': 0,
                        }
                        if (interval[0].weekday() == 5) or (interval[0].weekday() == 6) or holiday_obj:
                            attendances['number_of_hours'] += hours
                            leaves[ausencia.holiday_status_id.name]['hours_holiday_leaves'] += hours
                        else:
                            leaves[ausencia.holiday_status_id.name]['number_of_hours'] += hours
                            if country_emp_id == guatemala.id:
                                if ausencia.holiday_status_id.code[:3] == 'VAC' or ausencia.holiday_status_id.code[:3] == 'DLI':
                                    if interval[0].month == 12 and (interval[0].day == 24 or interval[0].day == 31):
                                        leaves[ausencia.holiday_status_id.name]['hours_half_holidays'] += hours / 2
                                        leaves[ausencia.holiday_status_id.name]['number_of_hours'] -= hours / 2
                                        attendances['number_of_hours'] += hours / 2
                else:
                    # no hay ausencia -> conteo WORK100
                    attendances['number_of_hours'] += hours

            days_holidays = 0.0
            leaves = [value for key, value in leaves.items()]
            
            for data in [attendances] + leaves:
                data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'], uom_day) if uom_day and uom_hour else data['number_of_hours'] / 8.0
                if str(data['code']) != 'WORK100':
                    hours_calendar = data['number_of_hours'] + data['hours_half_holidays'] + data['hours_holiday_leaves']
                    days_calendar = uom_hour._compute_quantity(hours_calendar, uom_day) if uom_day and uom_hour else hours_calendar / 8.0
                    data['number_of_days_calendar'] = days_calendar
                    days_holidays += days_calendar
                res.append(data)

            res[0]['number_of_days_calendar'] = calendar_days - days_holidays

        return res

    @api.onchange('employee_id', 'date_from', 'date_to', 'contract_id')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        tfyme = datetime.fromtimestamp(time.mktime(time.strptime(date_to, "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'es_CO'
        # inicia personalizacion nombre
        if self.struct_id:
            if 'Local' in self.struct_id.name:
                payslip_firstname = ('Nómina Local de %s para ').decode('utf8') % (employee.name)
            elif 'Servicios Profesionales' in self.struct_id.name:
                payslip_firstname = ('Honorarios profesionales de %s para ') % (employee.name)
            elif 'Aguinaldo' in self.struct_id.name:
                payslip_firstname = ('Aguinaldo de %s para ') % (employee.name)
            elif 'Bono 14' in self.struct_id.name:
                payslip_firstname = ('Bono 14 de %s para ') % (employee.name)
            else:
                payslip_firstname = ('Nómina de %s para ').decode('utf8') % (employee.name)

            self.name = payslip_firstname + ' ' + ('%s a %s') % (
                    tools.ustr(babel.dates.format_date(date=ttyme, format='d-MMMM-y', locale=locale)),
                    tools.ustr(babel.dates.format_date(date=tfyme, format='d-MMMM-y', locale=locale)) )

        else:
            self.name = _('Salary Slip of %s for %s') % (
                        employee.name, 
                        tools.ustr(babel.dates.format_date(date=ttyme, format='d-MMMM-y', locale=locale)))
        # fin personalizacion nombre
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

    @api.multi
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        #defaults
        res = {
            'value': {
                'line_ids': [],
                #delete old input lines
                'input_line_ids': map(lambda x: (2, x,), self.input_line_ids.ids),
                #delete old worked days lines
                'worked_days_line_ids': map(lambda x: (2, x,), self.worked_days_line_ids.ids),
                #'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        tfyme = datetime.fromtimestamp(time.mktime(time.strptime(date_to, "%Y-%m-%d")))
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'

        if not self.env.context.get('contract'):
            #fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                #set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                #if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })

        payslip_name = ''
        
        # inicia personalizacion nombre
        if res['value']['struct_id']:
            struct = self.env['hr.payroll.structure'].browse(res['value']['struct_id'])
            if 'Local' in struct.name:
                payslip_firstname = ('Nómina Local de %s para ').decode('utf8') % (employee.name)
            elif 'Servicios Profesionales' in struct.name:
                payslip_firstname = ('Honorarios profesionales de %s para ') % (employee.name)
            elif 'Aguinaldo' in struct.name:
                payslip_firstname = ('Aguinaldo de %s para ') % (employee.name)
            elif 'Bono 14' in struct.name:
                payslip_firstname = ('Bono 14 de %s para ') % (employee.name)
            else:
                payslip_firstname = ('Nómina de %s para ').decode('utf8') % (employee.name)

            payslip_name = payslip_firstname + ' ' + ('%s a %s') % (
                    tools.ustr(babel.dates.format_date(date=ttyme, format='d-MMMM-y', locale=locale)),
                    tools.ustr(babel.dates.format_date(date=tfyme, format='d-MMMM-y', locale=locale)) )

        else:
            payslip_name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))

        # fin personalizacion nombre
        res['value'].update({
            'name': payslip_name,
            'company_id': employee.company_id.id,
        })

        #computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(contract_ids, date_from, date_to)
        input_line_ids = self.get_inputs(contract_ids, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res

    # obtener sumatoria salarios o dias cancelados
    @api.multi
    def sum_wage(self, employee_p, date_from_payslip, date_to_payslip, rule, order):
        #_logger.debug('***************')
        #_logger.debug('rule %s', rule)
        #_logger.debug('order %s', order)

        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])
        employee = self.env['hr.employee'].browse(employee_p)  # tipo hr_employee
        date_from_payslip = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_to_payslip = fields.Datetime.from_string(date_to_payslip)  # tipo datetime
        aux_year = date_from_payslip.year
        aux_meses = 0
        result = 0
        dias = 0

        if rule == 'BONO14' or rule == 'AGUINALDO':
            meses1 = [mn for mn in range(date_from_payslip.month, 13)]
            meses2 = [mn for mn in range(1, date_to_payslip.month + 1)]
            meses = meses1 + meses2
        elif rule == 'PRIMA1':
            meses = [mn for mn in range(1, date_to_payslip.month + 1)]
        elif rule == 'PRIMA2':
            meses = [mn for mn in range(date_from_payslip.month, 13)]
        elif rule == 'PRIMALIQ':
            aux_year = date_to_payslip.year
            if date_to_payslip.month <= 6:
                meses = [mn for mn in range(1, date_to_payslip.month + 1)]
            else:
                meses = [mn for mn in range(7, date_to_payslip.month + 1)]
        elif rule == 'UANUAL_LAB':
            contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order = 'date_start desc')
            aux_cmeses = 0.0
            meses = []
            for c in contracts:
                if c.date_end:
                    temp = self.auxiliar_for_sum(c.date_start, c.date_end, 'MESES_EXACTOS_ROUND')
                    aux_cmeses += temp
                    fin = fields.Datetime.from_string(c.date_end)
                    if fin.day != calendar.monthrange(fin.year, fin.month)[1]:
                        fin = fin.replace(day=1) - dateutil.relativedelta.relativedelta(days=1)
                    #_logger.debug('aux_cmeses %s', aux_cmeses)
                    if aux_cmeses < 12:
                        inicia = fields.Datetime.from_string(c.date_start)
                        #_logger.debug('inicia 1 %s fin 1 %s', inicia, fin)
                        aux_year = inicia.year
                        if fin.year == aux_year:
                            aux_ameses = [mn for mn in range(inicia.month, fin.month + 1)]
                        else:
                            aux_ameses  = [mn for mn in range(inicia.month, 12 + 1)]
                            aux_ameses += [mn for mn in range(1, fin.month + 1)]
                        meses = aux_ameses + meses
                        #_logger.debug('meses p %s', meses)
                    else:
                        #_logger.debug('')
                        resto_round = int(12 - (aux_cmeses-temp))
                        aux_cmeses = 12
                        fecha_aux = datetime(day=1, month=meses[0], year=aux_year)
                        #_logger.debug('fecha_aux %s', fecha_aux)
                        inicia = fecha_aux - dateutil.relativedelta.relativedelta(months=resto_round)
                        #_logger.debug('inicia 2 %s fin %s', inicia, fin)
                        aux_year = inicia.year                    
                        aux_ameses = [mn for mn in range(inicia.month, fin.month + 1)]
                        meses = aux_ameses + meses
                        #_logger.debug('meses f %s', meses)
                        break
                        
                if c.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                    break
        elif rule == 'UANUAL':
            aux_year = date_to_payslip.year
            contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order = 'date_start desc')
            date_end_contract = fields.Datetime.from_string(contracts[0].date_end)
            aux_cmeses = self.auxiliar_for_sum(str(datetime(year=date_end_contract.year, month=1, day=1)), contracts[0].date_end, 'MESES')
            meses = [mn for mn in range(1, date_end_contract.month + 1)]
        else:
            aux_cmeses = self.auxiliar_for_sum(str(date_from_payslip), str(date_to_payslip), order)
            meses = [mn for mn in range(date_from_payslip.month, 13)]
            aux_year_con = (date_from_payslip.year) + 1
            aux_year_lim = date_to_payslip.year
            while aux_year_con <= aux_year_lim:
                if aux_year_con < aux_year_lim:
                    aux_ameses = [mn for mn in range(1, 13)]
                else:
                    aux_ameses = [mn for mn in range(1, date_to_payslip.month + 1)]
                meses = meses + aux_ameses
                aux_year_con = aux_year_con + 1

        if meses:
            aux_meses = meses[0]

        if order.startswith('MESES'):
            result = aux_cmeses
        else:
            for mes in meses:
                date_from_mes = datetime(year=aux_year, month=mes, day=1)  # tipo datetime
                date_to_mes   = datetime(year=aux_year, month=mes, day=calendar.monthrange(aux_year, mes)[1])  # tipo datetime

                payslip_ids = self.env['hr.payslip'].search(
                    ['&', '&', '&', ('date_from', '>=', date_from_mes), ('date_to', '<=', date_to_mes),
                     ('employee_id', '=', employee.id),
                     ('state', '=', 'done')])

                for nomina in payslip_ids:
                    contract = self.env['hr.contract'].search([('id', '=', nomina.contract_id.id)])
                    date_from_p = fields.Datetime.from_string(nomina.date_from)
                    date_to_p = fields.Datetime.from_string(nomina.date_to)

                    if contract:
                        salario = contract.wage
                        contract_start = fields.Datetime.from_string(contract.date_start)  # tipo datetime
                        contract_end = False
                        if contract.date_end:
                            contract_end = fields.Datetime.from_string(contract.date_end)  # tipo datetime

                        if contract_start < date_from_p:
                            if contract_end:
                                if date_to_p < contract_end:
                                    dias = ((date_to_p - date_from_p).days) + 1
                                else:
                                    dias = ((contract_end - date_from_p).days) + 1
                            else:
                                dias = ((date_to_p - date_from_p).days) + 1
                        else:
                            if contract_end:
                                if date_to_p < contract_end:
                                    dias = ((date_to_p - contract_start).days) + 1
                                else:
                                    dias = ((contract_end - contract_start).days) + 1
                            else:
                                dias = ((date_to_p - contract_start).days) + 1
                        
                        # correccion dias para redondear a 30
                        if date_from_p.month == 2:
                            if date_to_p.day == 28:
                                dias += 2
                            if date_to_p.day == 29:
                                dias += 1
                        if date_to_p.day == 31 and (dias >= 16):
                            dias -= 1
                        
                        # calculando resutado
                        if order == 'WAGE':
                            result += ((salario / 30) * dias)
                            #_logger.debug('')
                            #_logger.debug('fechas %s - %s salario %s', nomina.date_from, nomina.date_to, ((salario / 30) * dias))
                        else:
                            result += dias
                            #_logger.debug('')
                            #_logger.debug('fechas %s - %s valor dias %s', nomina.date_from, nomina.date_to, dias)

                        #_logger.debug('subtotal %s', result)

                aux_meses +=1
                if aux_meses%13 == 0:
                    aux_year = aux_year + 1

        #_logger.debug('***************')

        return result

    # obtener sumatoria comisiones y otros code definidos en la 2da pestana de nomina
    # se usa en aguinaldo GT bono14 GT, cesantias CO, primas CO
    @api.multi
    def sum_other(self, employee_p, date_from_payslip, date_to_payslip, rule, code):
        #_logger.debug('***************')
        #_logger.debug('rule %s', rule)
        #_logger.debug('code %s', code)
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])
        employee = self.env['hr.employee'].browse(employee_p)  # tipo hr_employee

        date_from_payslip = fields.Datetime.from_string(date_from_payslip) # tipo datetime
        date_to_payslip = fields.Datetime.from_string(date_to_payslip)  # tipo datetime

        if rule == 'BONO14':
            date_from_bono = datetime(year=(date_from_payslip.year), month=7, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=6, day=30)  # tipo datetime
        elif rule == 'AGUINALDO':
            date_from_bono = datetime(year=(date_from_payslip.year), month=12, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=11, day=30)  # tipo datetime
        elif (rule == 'PRIMA1') or (rule == 'PRIMALIQ' and date_to_payslip.month <= 6):
            date_from_bono = datetime(year=date_from_payslip.year, month=1, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=6, day=30)  # tipo datetime
        elif (rule == 'PRIMA2') or (rule == 'PRIMALIQ' and date_to_payslip.month > 6):
            date_from_bono = datetime(year=date_from_payslip.year, month=7, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=12, day=31)  # tipo datetime
        elif rule == 'UANUAL':
            contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order = 'date_start desc')            
            date_from_bono = datetime(year=date_to_payslip.year, month=1, day=1)  # tipo datetime
            date_to_bono = fields.Datetime.from_string(contracts[0].date_end)  # tipo datetime
        elif rule == 'UANUAL_LAB':
            contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order = 'date_start desc')
            aux_cmeses = 0.0
            rango = []
            for c in contracts:
                if c.date_end:
                    temp = self.auxiliar_for_sum(c.date_start, c.date_end, 'MESES_EXACTOS_ROUND')
                    aux_cmeses += temp
                    fin = fields.Datetime.from_string(c.date_end)
                    if fin.day != calendar.monthrange(fin.year, fin.month)[1]:
                        fin = fin.replace(day=1) - dateutil.relativedelta.relativedelta(days=1)
                    #_logger.debug('')
                    if aux_cmeses < 12:
                        inicia = fields.Datetime.from_string(c.date_start)
                        rango = [inicia, fin] + rango
                    else:
                        resto_round = int(12 - (aux_cmeses-temp))
                        aux_cmeses = 12
                        inicia = rango[0] - dateutil.relativedelta.relativedelta(months=resto_round)
                        rango = [inicia, fin] + rango
                        break
                if c.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                    break

            #_logger.debug('rango %s', rango)

            date_from_bono = datetime(year=rango[0].year,  month=rango[0].month,  day=1)  # tipo datetime
            date_to_bono   = datetime(year=rango[-1].year, month=rango[-1].month, day=calendar.monthrange(rango[-1].year, month=rango[-1].month)[1])  # tipo datetime
        else:
            date_from_bono = datetime(year=date_from_payslip.year, month=1, day=1)  # tipo datetime
            date_to_bono = datetime(year=date_to_payslip.year, month=12, day=31)  # tipo datetime

        #_logger.debug('date_from_bono %s', date_from_bono)
        #_logger.debug('date_to_bono %s', date_to_bono)
        #_logger.debug('')

        result = 0.00
        contract_ids = self.get_contract(employee, date_from_bono, date_to_bono)  # tipo [int]
        #_logger.debug('contract_ids %s', contract_ids)
        payslip_ids = self.env['hr.payslip'].search(
            ['&', ('contract_id', '=', None), ('state', '=', 'done')],
            limit=0)  # recordset vacío para concatenar

        for contract_id in contract_ids:
            c = self.env['hr.contract'].browse(contract_id)
            #_logger.debug('fechas c %s a %s', c.date_start, c.date_end)
            payslip_aux = self.env['hr.payslip'].search(
                ['&', '&', '&', ('date_from', '>=', date_from_bono), ('date_to', '<=', date_to_bono),
                 ('contract_id', '=', contract_id),
                 ('state', '=', 'done')])
            #_logger.debug('payslip_aux %s', payslip_aux)
            payslip_ids = payslip_aux + payslip_ids
            #_logger.debug('payslip_ids %s', payslip_ids)
        
        for payslip in payslip_ids:
            #_logger.debug('')
            #_logger.debug('fechas %s - %s', payslip.date_from, payslip.date_to)
            for input_line in payslip.line_ids:
                if input_line.code == code:
                    result += input_line.amount
                    #_logger.debug('valor %s', input_line.amount)
                    #_logger.debug('subtotal %s', result)

        #_logger.debug('***************')
        return result

    @api.multi
    def days_by_year(self, employee_p, date_from_payslip, date_to_payslip):
        #_logger.debug('***************')
        employee = self.env['hr.employee'].browse(employee_p)  # tipo hr_employee
        date_from_payslip = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_to_payslip = fields.Datetime.from_string(date_to_payslip)  # tipo datetime
        aux_year = date_from_payslip.year
        aux_meses = 0
        result = []
        dias_anual = 0
        dias = 0

        #_logger.debug('date_from_payslip %s', date_from_payslip)
        #_logger.debug('date_to_payslip %s', date_to_payslip)


        meses = [mn for mn in range(date_from_payslip.month, 13)]
        aux_year_con = (date_from_payslip.year) + 1
        aux_year_lim = date_to_payslip.year
        while aux_year_con <= aux_year_lim:
            if aux_year_con < aux_year_lim:
                aux_ameses = [mn for mn in range(1, 13)]
            else:
                aux_ameses = [mn for mn in range(1, date_to_payslip.month + 1)]
            meses = meses + aux_ameses
            aux_year_con = aux_year_con + 1

        if meses:
            aux_meses = meses[0]

        for mes in meses:
            date_from_mes = datetime(year=aux_year, month=mes, day=1)  # tipo datetime
            date_to_mes   = datetime(year=aux_year, month=mes, day=calendar.monthrange(aux_year, mes)[1])  # tipo datetime

            #_logger.debug('---')
            #_logger.debug('date_from_mes %s', date_from_mes)
            #_logger.debug('date_to_mes   %s', date_to_mes)
            
            payslip_ids = self.env['hr.payslip'].search(
                ['&', '&', '&', ('date_from', '>=', date_from_mes), ('date_to', '<=', date_to_mes),
                 ('employee_id', '=', employee.id),
                 ('state', '=', 'done')])

            for nomina in payslip_ids:
                contract = self.env['hr.contract'].search([('id', '=', nomina.contract_id.id)])
                date_from_p = fields.Datetime.from_string(nomina.date_from)
                date_to_p = fields.Datetime.from_string(nomina.date_to)

                if contract:
                    contract_start = fields.Datetime.from_string(contract.date_start)  # tipo datetime
                    contract_end = False
                    if contract.date_end:
                        contract_end = fields.Datetime.from_string(contract.date_end)  # tipo datetime

                    # conteo días
                    if contract_start < date_from_p:
                        if contract_end:
                            if date_to_p < contract_end:
                                dias = ((date_to_p - date_from_p).days) + 1
                            else:
                                dias = ((contract_end - date_from_p).days) + 1
                        else:
                            dias = ((date_to_p - date_from_p).days) + 1
                    else:
                        if contract_end:
                            if date_to_p < contract_end:
                                dias = ((date_to_p - contract_start).days) + 1
                            else:
                                dias = ((contract_end - contract_start).days) + 1
                        else:
                            dias = ((date_to_p - contract_start).days) + 1
                    
                    # correccion dias para redondear a 30
                    if date_from_p.month == 2:
                        if date_to_p.day == 28:
                            dias += 2
                        if date_to_p.day == 29:
                            dias += 1
                    if date_to_p.day == 31 and (dias >= 16):
                        dias -= 1
                    
                    # calculando resutado
                    dias_anual += dias
                    #_logger.debug('')
                    #_logger.debug('fechas %s - %s valor dias %s', nomina.date_from, nomina.date_to, dias)
                    #_logger.debug('acumulado %s', dias_anual)

            if (aux_meses%12 == 0) or (aux_meses == len(meses)+meses[0]-1):
                result = result + [dias_anual]
                dias_anual = 0

            aux_meses +=1

            if aux_meses%13 == 0:
                aux_year = aux_year + 1

        #_logger.debug('result   %s', result)
        #_logger.debug('***************')
        return result

    # obtener datos de pagos (line_ids) en ultima quincena
    def get_lastfortnight(self, contract, date_from_payslip, code):
        date_from_payslip = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_from = datetime(day=1, month=date_from_payslip.month, year=date_from_payslip.year)
        date_to = date_from_payslip - timedelta(days=1)
        result = 0.00

        #last_payslip = self.env['hr.payslip'].search(
            #['&', '&', '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to),
             #('contract_id', '=', contract.id),
             #('state', '=', 'done')])

        last_payslip = self.env['hr.payslip'].search(
            ['&', '&', '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to),
             ('employee_id', '=', contract.employee_id.id),
             ('state', '=', 'done')])

        for input in last_payslip.line_ids:
            if input.code == code:
                result += input.amount
        
        return result

    # auxiliar de conteo
    def auxiliar_for_sum(self, date_from_str, date_to_str, tiempo):
        date_from = fields.Datetime.from_string(date_from_str).date()
        date_to   = fields.Datetime.from_string(date_to_str).date()
        sub = 0.0
        if tiempo == 'DIAS':
            sub = ((date_to-date_from).days)+1
        elif tiempo == 'MESES_EXACTOS':
            delta = dateutil.relativedelta.relativedelta(date_to, date_from)
            sub = delta.months + round((delta.days * 1.0 / 30.0),2)
        elif tiempo == 'MESES_EXACTOS_ROUND':
            if date_from.day <= 15:
                # si inicia en quincena 1 -> pasa a iniciar el 1
                date_from = datetime(year=date_from.year, month=date_from.month, day=1)
            else:
                # si inicia en quincena 2 -> pasa a iniciar el 15
                date_from = datetime(year=date_from.year, month=date_from.month, day=15)

            if date_to.day <= 15:
                # si finaliza en quincena 1 -> pasa a finalizar el 15
                date_to = datetime(year=date_to.year, month=date_to.month, day=15).date()
            else:
                # si finaliza en quincena 2 -> pasa a finalizar el ultimo día del mes
                date_to = datetime(year=date_to.year, month=date_to.month, day=calendar.monthrange(date_to.year, date_to.month)[1]).date()

            delta = dateutil.relativedelta.relativedelta(date_to, date_from)
            dias = delta.days

            ult_dia_mes = calendar.monthrange(date_to.year, date_to.month)[1]
            if ult_dia_mes == 28:
                dias = dias + 2
            elif ult_dia_mes == 29:
                dias = dias + 1
            elif ult_dia_mes == 31:
                dias = dias - 1
            else:
                dias = dias

            if dias <= 15:
                if dias <= 0:
                    sub = delta.months
                else:
                    sub = delta.months + 0.5
            else:
                sub = delta.months + 1.0
        # default :: 'MESES' :: número de meses cubiertos
        else:
            sub = ((date_to.month-date_from.month)%12)+1
        return sub

    # obtener datos de fechas para liquidacion, tipo_sumatoria es "PARCIAL" o "TOTAL", tiempo es "MESES" o "DIAS"
    def get_time_forliq(self, employee_p, date_from_payslip, date_to_payslip, tipo_sumatoria, tiempo):
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])
        employee = self.env['hr.employee'].browse(employee_p)
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order = 'date_start desc')
        suma = 0.0
        date_end_str = date_to_payslip

        # resultado para 'liquidacion'
        if tipo_sumatoria == 'PARCIAL':
            suma = self.auxiliar_for_sum(date_from_payslip, date_to_payslip, tiempo)
        # resultado para 'total'
        else:
            for c in contracts:
                if c.date_end:
                    date_end_str = c.date_end
                suma += self.auxiliar_for_sum(c.date_start, date_end_str, tiempo)                
                if c.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                    break
        return suma

    # obtener sumatoria de salarios base (descomentar para descontar solamente vacaciones o dias libres)
    def get_sum_basicforliq(self, employee_p, date_from_payslip, date_to_payslip):
        holiday_status_codes = self.env['hr.holidays.status'].search(
            ['|', ('code', '=like', 'VAC%'), ('code', '=like', 'DLI%')]).code
        employee = self.env['hr.employee'].browse(employee_p)
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)],order = 'date_start desc')

        date_from   = fields.Datetime.from_string(date_from_payslip).date()
        date_to     = fields.Datetime.from_string(date_to_payslip).date()
        suma = 0.0

        nominas = self.env['hr.payslip'].search(
            ['&', '&', '&', ('employee_id', '=', employee.id),
                            ('state', '=', 'done'),
                        ('date_from', '>=', date_from),
                   ('date_to', '<=', date_to)],
            order="date_from")

        for n in nominas:
            date_from_c = fields.Datetime.from_string(n.contract_id.date_start).date()
            #date_to_c   = fields.Datetime.from_string(n.contract_id.date_end).date()
            date_from_n = fields.Datetime.from_string(n.date_from).date()
            date_to_n   = fields.Datetime.from_string(n.date_to).date()
            base_wage = n.contract_id.wage
            dias = 0.00
            if date_from_c < date_from:
                dias_aux = (date_to-date_from).days +1
                dias += dias_aux
            else:
                dias_aux = (date_to-date_from_c).days +1
                dias += dias_aux
            if date_from_n.month == 2:
                if date_to_n.day == 28:
                    dias += 2
                if date_to_n.day == 29:
                    dias += 1
            if date_to_n.day == 31 and (dias_aux == 16 or dias_aux == 31):
                dias -= 1
            '''for line in n.worked_days_line_ids:
                if line.code[:3] in holiday_status_codes:
                    dias -= line.number_of_days_calendar'''
            suma += (base_wage/30)*dias

        return suma

    # obtener datos de los ultimos 6 meses (para LIQ) segun el codigo de la 2da pestaña
    # NOTA: los 6 meses están definidos por las fechas de la nómina
    def get_datapaysplips(self, employee_p, date_from_payslip, date_to_payslip, code):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        hoy = datetime.now(tz=user_tz).date()
        date_from = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_to = fields.Datetime.from_string(date_to_payslip)  # tipo datetime
        employee = self.env['hr.employee'].browse(employee_p)  # tipo hr_employee

        nominas = self.env['hr.payslip'].search(
            ['&', '&', '&', ('employee_id', '=', employee.id),
                            ('state', '=', 'done'),
                        ('date_from', '>=', date_from),
                   ('date_to', '<=', date_to)],
            order="date_from")
        summation = 0

        for nomina in nominas:
            line_ids = nomina.line_ids
            for line in line_ids:
                if line.code == code:
                    summation += line.total

        return summation

    # obtener datos de las vacaciones pendientes (para LIQ)
    # PEND cerrar las vacaciones pendientes
    def get_pending_holidays(self, employee_p, contract_p):
        #_logger.debug('***************')
        user_tz = pytz.timezone(self.env.user.partner_id.tz)

        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])
        holiday_status_ids = self.env['hr.holidays.status'].search(
            ['|', ('code', '=like', 'VAC%'), ('code', '=like', 'DLI%')]).ids

        employee = self.env['hr.employee'].browse(employee_p)
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)], 
            order = 'date_start desc')
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

        # si date_end > fecha de cumpleaños de contrato, calcular días adicionales de vacaciones generados
        for i, c in enumerate(contracts):
            if i == 0:
                date_end = fields.Datetime.from_string(c.date_end).date()
            if c.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                date_start = fields.Datetime.from_string(c.date_start)
                fecha_aux = datetime(year=date_end.year, month=date_start.month, day=date_start.day).date()
                #_logger.debug('date_end %s', date_end)
                #_logger.debug('fecha_aux %s', fecha_aux)
                if date_end > fecha_aux:
                    date_delta = (date_end - fecha_aux).days + 1.0
                    global_pending_holidays += date_delta * 15.0 / 365.0
                break
        
        #_logger.debug('global_pending_holidays %s', global_pending_holidays)

        # cerrar las vacaciones pendientes
        for ph in pending_holidays:
            pass

        return global_pending_holidays

    # obtener aguinaldos pendientes (para LIQ) 
    # NOTA: actualmente el rango es dic a nov
    def get_dayspending_agui(self, employee_pid, date_from_payslip, date_to_payslip):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        date_from_n = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_to_n = fields.Datetime.from_string(date_to_payslip)  # tipo datetime
        global_pending_agui = 0

        employee = self.env['hr.employee'].browse(employee_pid)
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search(
            [('name', '=', 'Vinculación laboral')])
        estructura_aguinaldo = self.env['hr.payroll.structure'].search(
            [('name', 'like', '%Aguinaldo%')])

        # ultima nomina pagada
        ultima_nomina = self.env['hr.payslip'].search(
            ['&', '&', ('employee_id', '=', employee.id),
                       ('state', '=', 'done'),
                 ('struct_id', '=', estructura_aguinaldo.id)],
            order="date_from desc", limit=1)
        ultimo_contrato = self.env['hr.contract'].search(
            [('employee_id', '=', employee.id)],order = 'date_start desc', limit=1)

        if len(ultima_nomina)>0:
            # existe
            date_to_na = fields.Datetime.from_string(ultima_nomina.date_to)  # tipo datetime
            date_from = date_to_na + timedelta(days=1)
            date_to = fields.Datetime.from_string(ultimo_contrato.date_end)  # tipo datetime
        else:
            # no existe nominas de aguinaldo pagadas
            # debe existir contrato !!
            date_from = datetime(day=1, month=12, year=date_to_n.year-1)
            joining_date = fields.Datetime.from_string(employee.joining_date)
            if joining_date > date_from:
                date_from = joining_date
            date_to = fields.Datetime.from_string(ultimo_contrato.date_end)  # tipo datetime

        global_pending_agui = (date_to-date_from).days+1

        return global_pending_agui

    # obtener bono14 pendientes (para LIQ) MOD
    # NOTA: actualmente el rango es jul a jun
    def get_dayspending_bono14(self, employee_pid, date_from_payslip, date_to_payslip):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        date_from_n = fields.Datetime.from_string(date_from_payslip)  # tipo datetime
        date_to_n = fields.Datetime.from_string(date_to_payslip)  # tipo datetime
        global_pending_agui = 0
        employee = self.env['hr.employee'].browse(employee_pid)
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search(
            [('name', '=', 'Vinculación laboral')])
        estructura_bono14 = self.env['hr.payroll.structure'].search(
            [('name', 'like', '%Bono 14%')])

        ultima_nomina = self.env['hr.payslip'].search(
            ['&', '&', ('employee_id', '=', employee.id),
                       ('state', '=', 'done'),
                 ('struct_id', '=', estructura_bono14.id)],
            order="date_from desc", limit=1)
        ultimo_contrato = self.env['hr.contract'].search([('employee_id', '=', employee.id)],order = 'date_start desc', limit=1)
        
        # ultima nomina pagada
        if len(ultima_nomina)==1:
            # existe
            date_to_na = fields.Datetime.from_string(ultima_nomina.date_to)  # tipo datetime
            date_from = date_to_na + timedelta(days=1)
            date_to = fields.Datetime.from_string(ultimo_contrato.date_end)  # tipo datetime
        else:
            # no existe nominas de aguinaldo pagadas
            # debe existir contrato !!
            date_from = datetime(day=1, month=7, year=date_to_n.year-1)
            joining_date = fields.Datetime.from_string(employee.joining_date)
            if joining_date > date_from:
                date_from = joining_date
            date_to = fields.Datetime.from_string(ultimo_contrato.date_end)  # tipo datetime

        global_pending_agui = (date_to-date_from).days+1

        return global_pending_agui

    # trae valores de line_ids
    @api.multi
    def get_from_lineids(self, line_ids, code):
        valor = line_ids.filtered(lambda r: r.salary_rule_id.code == code).total
        if not valor:
            valor = 0.0
        return valor

    # trae days de worked_days_line_ids
    @api.multi
    def get_days_from_workeddays(self, worked_days_line_ids, code, days_str):
        if len(code) == 3:
            if days_str == 'number_of_days_calendar':
                valor = worked_days_line_ids.filtered(lambda r: r.code.startswith(code)).number_of_days_calendar
            else:
                valor = worked_days_line_ids.filtered(lambda r: r.code.startswith(code)).number_of_days
        else:
            if days_str == 'number_of_days_calendar':
                valor = worked_days_line_ids.filtered(lambda r: r.code == code).number_of_days_calendar
            else:
                valor = worked_days_line_ids.filtered(lambda r: r.code == code).number_of_days

        if not valor:
            valor = 0.0
        return valor

    # trae valores de line_ids
    @api.multi
    def get_currency(self, contract_obj):
        valor = contract_obj.x_currency_id
        return valor

    # para obtener los dias que tiene derecho anuales
    def get_annual_holiday(self, contract):
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])
        contratos = self.env['hr.contract'].search([('employee_id', '=', contract.employee_id.id)], order='date_start')
        for c in contratos:
            if c.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                return c.annual_holiday

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

    def get_worked_days_by_year(self, employee_id):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        year_p = (datetime.now(tz=user_tz).date().year) - 1
        days = 0.0
        for m in range(12):
            mes = m + 1
            date_from = datetime(day=1, month=mes, year=year_p)
            date_to = datetime(day=calendar.monthrange(year_p, mes)[1], month=mes, year=year_p)

            contract = self.env['hr.payslip'].get_contract(employee_id, date_from, date_to)
            if contract:
                days += self.env['hr.holidays']._get_number_of_days(str(date_from), str(date_to), self.id)
        return days

    def get_filtered_lineid(self, code):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        last_year = (datetime.now(tz=user_tz).date().year) - 1
        aux = 0
        struct_agui = self.env['hr.payroll.structure'].search([('code', '=', 'AGUINALDO GT')])
        struct_bono = self.env['hr.payroll.structure'].search([('code', '=', 'BONO14 GT')])

        for m in range(12):
            mes = m + 1
            date_from = datetime(day=1, month=mes, year=last_year).date()
            date_to = datetime(day=calendar.monthrange(last_year, mes)[1], month=mes, year=last_year).date()
            pagos_nominas = self.env['hr.payslip'].search(
                ['&', '&', '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to),
                 ('employee_id', '=', self.id), ('state', '=', 'done')],
                order="date_from")
            pagos_bonos = self.env['hr.payslip'].search(
                ['&', '&', ('employee_id', '=', self.id), ('state', '=', 'done'),
                      '|', ('struct_id', '=', struct_agui.id), ('struct_id', '=', struct_bono.id),
                      ('date_to', '=', date_to)],
                order="date_from")
            pagos = pagos_nominas + pagos_bonos
            for nomina in pagos:
                line_ids = nomina.line_ids
                for line in line_ids:
                    if line.code == code:
                        aux += line.total
        return aux

    def get_data(self, year_p):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        today = datetime.now(tz=user_tz).date()
        if year_p == 'ACTUAL':
            search_year = today.year
        else:
            search_year = (today.year) - 1
        answer = []
        struct_agui = self.env['hr.payroll.structure'].search([('code', '=', 'AGUINALDO GT')])
        struct_bono = self.env['hr.payroll.structure'].search([('code', '=', 'BONO14 GT')])
        struct_liq_ids = self.env['hr.payroll.structure'].search([('code', '=like', 'LIQUIDACION%')]).ids
        for m in range(12):
            date_from = datetime(day=1, month=m + 1, year=search_year).date()
            date_to = datetime(day=calendar.monthrange(search_year, m + 1)[1], month=m + 1, year=search_year).date()
            pagos_nominas = self.env['hr.payslip'].search(
                ['&', '&', ('employee_id', '=', self.id), ('state', '=', 'done'),
                      '&', ('date_from', '>=', date_from), ('date_to', '<=', date_to)],
                order="date_from")
            pago_indemnizacion = self.env['hr.payslip'].search(
                ['&', '&', '&', ('employee_id', '=', self.id), ('state', '=', 'done'),
                           '&', ('date_from', '<=', date_from), ('date_to', '<=', date_to),
                      ('struct_id', 'in', struct_liq_ids)],
                order="date_from")
            pagos_bonos = self.env['hr.payslip'].search(
                ['&', '&', ('employee_id', '=', self.id), ('state', '=', 'done'),
                      '|', ('struct_id', '=', struct_agui.id), ('struct_id', '=', struct_bono.id),
                      ('date_to', '=', date_to)],
                order="date_from")
            pagos = pagos_nominas + pagos_bonos + pago_indemnizacion

            locale = self.env.context.get('lang') or 'es_CO'
            nombre_mes = ('%s') % (tools.ustr(babel.dates.format_date(date=date_from, format='MMMM yyyy', locale=locale)))
            mes = m + 1
            salario_contrato = 0
            moneda = False
            # ---------- sección horas trabajadas
            horas_normal = 0
            # ---------- sección salario devengado
            dias_total = 0
            salario_ordinario = 0
            salario_comisiones = 0
            liq_vacpnd = 0
            # ---------- sección deducciones legales
            deducc_igss = 0
            deducc_total = 0
            # ---------- sección final
            suma_otros = 0    # aguinaldo + bono 14 + liq_indemn
            suma_bono7889 = 0 # bono 37-2001 + otros bonos = bono 78-89 y reformas
            subtotal = 0

            for nomina in pagos:
                moneda = nomina.contract_id.x_currency_id
                salario_contrato = nomina.contract_id.wage

                line_ids = nomina.line_ids

                for line in line_ids:

                    if line.code == 'DIASTRABAJO':
                        dias_total += line.total
                    if line.code == 'COM':
                        salario_comisiones += line.total
                    if line.code == 'IGSS':
                        deducc_igss += line.total
                    if line.code == 'TOTALDED':
                        deducc_total += line.total

                    if line.code == 'BON37':
                        suma_bono7889 += line.total
                    if line.code == 'BON':
                        suma_bono7889 += line.total

                    if line.code == 'AGUI':
                        suma_otros += line.total
                    if line.code == 'BON14':
                        suma_otros += line.total

                    if line.code == 'AGUIPE':
                        suma_otros += line.total
                    if line.code == 'BON14P':
                        suma_otros += line.total
                    if line.code == 'INDEMN':
                        suma_otros += line.total
                    if line.code == 'VACPND':
                        liq_vacpnd += line.total

                salario_ordinario = (salario_contrato / 30) * (dias_total)
                subtotal = salario_ordinario + salario_comisiones + liq_vacpnd

            resource = self.resource_id.sudo()
            horas_diarias = resource.calendar_id.working_hours_on_day(datetime(day=1, month=mes, year=search_year))
            horas_normal = horas_diarias * dias_total

            # 0. moneda 1. No. Orden 2. Periodo de trabajo 3. Salario en quetzales 4. Días Trabajados
            # 5. Horas Trabajadas / Ordinarias 6. HT / Extra ordinarias
            # 7. Salario Devengado / Ordinario 8. SD /  Extra ordinario 
            #     9. SD / Septimos y asuetos 10. SD / Vacaciones 11. Salario Total
            # 12. Deducciones Legales / IGSS 13. DL / Otras deducciones 14. DL / Total deducciones
            # 15. Bono 14 + Aguinaldo 16. Bonificación Dec. 37-2001 17. Líquido a recibir

            row = [moneda, mes, nombre_mes, salario_contrato, dias_total,
                   horas_normal, 0.00,
                   salario_ordinario, salario_comisiones, 0.00, liq_vacpnd, subtotal,
                   deducc_igss, (deducc_total - deducc_igss), deducc_total,
                   suma_otros, suma_bono7889, (subtotal+deducc_total+suma_otros+suma_bono7889)]
            answer.append(row)
        return answer

# clase creada por alltic que permite los pagos masivos desde estado "en espera"
class MultiPaySlipWizUpdated(models.TransientModel):
    _inherit = 'multi.payslip.wizard'

    @api.multi
    def multi_payslip(self):
        payslip_ids = self.env['hr.payslip'].browse(self._context.get('active_ids'))
        for payslip in payslip_ids:
            if payslip.state == 'verify':
                payslip.action_payslip_done()
