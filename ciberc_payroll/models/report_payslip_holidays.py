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

class IndividualReportHolidays(models.Model):
    _inherit = 'hr.payslip'

    def get_holidays_vacations(self, employee_obj, worked_days_line_ids, date_from_payslip, date_to_payslip):
        res = []
        for worked_day_id in worked_days_line_ids:
            code = worked_day_id.code
            if code.startswith('VAC') or code.startswith('DLI'):
                type_holiday_id = self.env['hr.holidays.status'].search([('code', '=', code)])
                holiday_id = self.env['hr.holidays'].search(
                    ['&', '&', '&', ('state', '=', 'validate'), ('type', '=', 'remove'),
                               '&', ('holiday_status_id', '=', type_holiday_id.id), ('employee_id', '=', employee_obj.id),
                          '|', ('date_from', '<=', date_from_payslip), ('date_to', '>=', date_to_payslip)])
                res.append(holiday_id)
        return res

    def get_vacations_period(self, worked_days_line_ids, employee_obj):
        res = []
        for worked_day_id in worked_days_line_ids:
            code = worked_day_id.code
            if code.startswith('VAC') or code.startswith('DLI'):
                aux_yearf = int(code[-2:])
                joining_employee = employee_obj.joining_date
                date_joining = datetime.strptime(joining_employee, '%Y-%m-%d')
                date_joining_aux = date_joining - dateutil.relativedelta.relativedelta(days=1)
                res.append([str(date_joining.day)+" de "+date_joining.strftime('%B')+" de 20"+str(aux_yearf-1)+" al "+str(date_joining_aux.day)+" de "+date_joining_aux.strftime('%B')+" de 20"+str(aux_yearf),
                            "20"+str(aux_yearf-1)+" - 20"+str(aux_yearf)])
        return res
