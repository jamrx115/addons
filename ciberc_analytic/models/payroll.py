# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta, time as dtime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, AccessError

import calendar
import logging
import time
import pytz
import math
import re

_logger = logging.getLogger(__name__)
utc_cero = pytz.utc

class PayrollAnalytic(models.Model):
    _inherit = 'hr.payslip'

    # método que corta registros de parte de horas día por día y con límite de fechas
    def cut_analyticline_withrange(self, analytic_lines_tz0, fechai_tz0, fechaf_tz0, employee_tz):
    	fechai_tz0 = datetime.combine(fechai_tz0.date(), fechai_tz0.time())
    	fechaf_tz0 = datetime.combine(fechaf_tz0.date(), fechaf_tz0.time())
    	result = []
    	for analytic_line in analytic_lines_tz0:
    		# cortar desde fechai_tz0 si analytic_line empieza antes de fechai_tz0
    		empieza = fields.Datetime.from_string(analytic_line.date_from)
    		if empieza < fechai_tz0:
    			empieza = fechai_tz0
    		# cortar hasta fechaf_tz0 si analytic_line termina después de fechaf_tz0
    		fin = fields.Datetime.from_string(analytic_line.date_to)
    		if fin > fechaf_tz0:
    			fin = fechaf_tz0

    		# cortar por días (en utc employee)
    		empieza_e = (utc_cero.localize(empieza)).astimezone(employee_tz)
    		fin_e     = (utc_cero.localize(fin)).astimezone(employee_tz)

    		if (empieza_e.date()) == (fin_e.date()):
    			new_array = [datetime.combine(empieza_e.date(), empieza_e.time()), 
    						 datetime.combine(fin_e.date(), fin_e.time())]
    			result.append(new_array)
    		else:
    			# comparaciones y corte en utc employee
    			aux_i = datetime.combine(empieza_e.date(), empieza_e.time())
    			aux_f = datetime.combine(empieza_e.date(), dtime(hour=23, minute=59, second=59))
    			aux_lim = datetime.combine(fin_e.date(), fin_e.time())
    			while aux_i < aux_lim:
    				if aux_f > aux_lim:
    					aux_f = aux_lim
    				else:
    					aux_f = datetime.combine(aux_f.date()+timedelta(days=1), dtime())
    				new_array = [aux_i, aux_f]
    				result.append(new_array)
    				aux_i = datetime.combine(aux_i.date()+timedelta(days=1), dtime())
    				aux_f = datetime.combine(aux_i.date()+timedelta(days=1), dtime()) #
    	return result

    # método conteo : llena los objetos tipo custom.analytic_hours
    def get_divided_hours(self, contract, date_from_payslip, date_to_payslip, hi_cutstr, hf_cutstr):
        # 1. =====> fechas nómina a zona horaria usuario
        employee_tz = pytz.timezone(contract.employee_id.company_id.partner_id.tz)
        country_emp_id = contract.employee_id.company_id.country_id.id
        date_from_payslip_c = employee_tz.localize(fields.Datetime.from_string(date_from_payslip))
        date_to_aux       = fields.Datetime.from_string(date_to_payslip)
        date_to_payslip_c   = employee_tz.localize(datetime.combine(
        					date_to_aux.date(), dtime(hour=23, minute=59, second=59)))

        holidays_ids = self.env['hr.holidays'].get_holidays_ids(date_from_payslip_c, date_to_payslip_c, country_emp_id)

        # 2. consulta
        # 2.1. =====> fechas nómina a zona horaria utc cero
        date_from_payslip_c = date_from_payslip_c.astimezone(utc_cero)
        date_to_payslip_c   = date_to_payslip_c.astimezone(utc_cero)

        # 2.2. cortar zona horaria
        date_from_payslip = datetime.combine(date_from_payslip_c.date(), date_from_payslip_c.time())
        date_to_payslip   = datetime.combine(date_to_payslip_c.date(), date_to_payslip_c.time())

        # 2.3. consulta
        user_employee = contract.employee_id.user_id
        ph_consulta1 = self.env['account.analytic.line'].search(
            ['&', '&', '&', ('user_id', '=', user_employee.id), ('date_from', '<', str(date_from_payslip)), 
                       '&', ('date_to', '>', str(date_from_payslip)), ('date_to', '<', str(date_to_payslip)),
                   ('state', '=', 'aprobado') ],
            order='date_from')
        ph_consulta2 = self.env['account.analytic.line'].search(
            ['&', '&', ('date_from', '>=', str(date_from_payslip)), ('date_to', '<=', str(date_to_payslip)), 
                  '&', ('user_id', '=', user_employee.id), ('state', '=', 'aprobado')],
            order='date_from')
        ph_consulta3 = self.env['account.analytic.line'].search(
            ['&', '&', '&', ('user_id', '=', user_employee.id), ('date_to', '>', str(date_to_payslip)), 
                  '&', ('date_from', '>', str(date_from_payslip)), ('date_from', '<', str(date_to_payslip)),
                  ('state', '=', 'aprobado') ],
            order='date_from')

        # 2.4. dividir partes de horas
        ph_consulta1 = self.cut_analyticline_withrange(ph_consulta1, date_from_payslip, date_to_payslip, employee_tz)
        ph_consulta2 = self.cut_analyticline_withrange(ph_consulta2, date_from_payslip, date_to_payslip, employee_tz)
        ph_consulta3 = self.cut_analyticline_withrange(ph_consulta3, date_from_payslip, date_to_payslip, employee_tz)

        # 2.5. unir
        partes_horas = ph_consulta1 + ph_consulta2 + ph_consulta3
        
        # 3. cálculo        
        hi_cut = dtime(hour=int(hi_cutstr[:2]), minute=int(hi_cutstr[-2:]))
        hf_cut = dtime(hour=int(hf_cutstr[:2]), minute=int(hf_cutstr[-2:]))
        h_ordinarias  = [0,0]
        h_dominicales = [0,0]
        e_ordinarias  = [0,0]
        e_dominicales = [0,0]
        
        for registro_horas in partes_horas:
        	fecha = registro_horas[0].date()
        	corte_i = datetime.combine(fecha, hi_cut)
        	corte_f = datetime.combine(fecha, hf_cut)
        	holiday_obj = holidays_ids.filtered(lambda r: r.date == str(registro_horas[0].date()))

        	if (registro_horas[0].weekday() == 6) or holiday_obj:
	        	if registro_horas[0] < corte_i:
	        		h_dominicales[1] += ((corte_i-registro_horas[0]).total_seconds()/3600)
	        		if registro_horas[1] <= corte_f:
		        		h_dominicales[0] += ((registro_horas[1]-corte_i).total_seconds()/3600)
		        	else:
		        		h_dominicales[0] += ((corte_f-corte_i).total_seconds()/3600)
		        		h_dominicales[1] += ((registro_horas[1]-corte_f).total_seconds()/3600)
		        else:
		        	if corte_f < registro_horas[1]:
		        		h_dominicales[0] += ((corte_f-registro_horas[0]).total_seconds()/3600)
		        		h_dominicales[1] += ((registro_horas[1]-corte_f).total_seconds()/3600)
		        	else:
		        		h_dominicales[0] += ((registro_horas[1]-registro_horas[0]).total_seconds()/3600)
	        else:
	        	if registro_horas[0] < corte_i:
	        		h_ordinarias[1] += ((corte_i-registro_horas[0]).total_seconds()/3600)
	        		if registro_horas[1] <= corte_f:
		        		h_ordinarias[0] += ((registro_horas[1]-corte_i).total_seconds()/3600)
		        	else:
		        		h_ordinarias[0] += ((corte_f-corte_i).total_seconds()/3600)
		        		h_ordinarias[1] += ((registro_horas[1]-corte_f).total_seconds()/3600)
		        else:
		        	if corte_f < registro_horas[1]:
		        		h_ordinarias[0] += ((corte_f-registro_horas[0]).total_seconds()/3600)
		        		h_ordinarias[1] += ((registro_horas[1]-corte_f).total_seconds()/3600)
		        	else:
		        		h_ordinarias[0] += ((registro_horas[1]-registro_horas[0]).total_seconds()/3600)

        return [h_ordinarias, h_dominicales, e_ordinarias, e_dominicales]