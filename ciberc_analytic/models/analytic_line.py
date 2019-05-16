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

# actualización a partes de horas
class AccountAnalyticLineUpdated(models.Model):
    _inherit = ['account.analytic.line']

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', string='User', required=True, default=_default_user, domain=lambda self: [('id', '=', self.env.uid)])

# actualización a partes de horas
class AccountAnalyticLineNew(models.Model):
    _inherit = ['account.analytic.line']

    @api.model
    def _user_tz(self):
        return pytz.timezone(self.env.user.partner_id.tz)

    @api.model
    def _default_datefrom(self):
        user_time_zone = self._user_tz()
        now_utcz = utc_cero.fromutc(datetime.now())
        #return datetime.combine(now_utcz.date(), dtime(hour=now_utcz.hour))
        return datetime.combine(now_utcz.date(), dtime(hour=now_utcz.hour, minute=now_utcz.minute))

    @api.model
    def _default_dateto(self):
        today = datetime.utcnow() # utc cero without tz
        return datetime.combine(today.date(), dtime(hour=today.hour, minute=today.minute))

    # unit_amount :: campo duración de tipo Float
    # date        :: campo base para fecha de partes de horas

    def _get_number_of_hours(self, date_from, date_to, user_id):
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        resource = self.env['resource.resource'].search([('user_id', '=', user_id)])

        if resource and resource.calendar_id:
            hours = resource.calendar_id.get_working_hours(from_dt, to_dt, resource_id=resource.id, compute_leaves=True)
            return hours
        else:
            time_delta = to_dt - from_dt
            return (time_delta.total_seconds() / 3600)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        date_from = self.date_from
        date_to = self.date_to

        # No date_to set so far: automatically compute one 1 hours later
        if date_from and not date_to:
            date_to_with_delta = fields.Datetime.from_string(date_from) + timedelta(hours=1)
            self.date_to = str(date_to_with_delta)

        # Compute and update the number of hours
        if (date_to and date_from) and (date_from <= date_to):
            self.unit_amount = self._get_number_of_hours(date_from, date_to, self.user_id.id)
        else:
            self.unit_amount = 0

        # check dates
        self.verify_dates()

    @api.onchange('date_to')
    def _onchange_date_to(self):
        date_from = self.date_from
        date_to = self.date_to

        # Compute and update the number of hours
        if (date_to and date_from) and (date_from <= date_to):
            self.unit_amount = self._get_number_of_hours(date_from, date_to, self.user_id.id)
        else:
            self.unit_amount = 0

        # check dates
        self.verify_dates()

    def verify_dates(self):
        resource = self.env['resource.resource'].search([('user_id', '=', self.user_id.id)])

        if resource and resource.calendar_id:
            # tiene contrato (se supone que no ingresa parte de horas si ya no pertenece a la empresa)
            employee = self.env['hr.employee'].search([('resource_id', '=', resource.id)])

            # se verifica contra fecha de inicio de contrato
            if fields.Datetime.from_string(self.date_from) < fields.Datetime.from_string(employee.joining_date):
                raise UserError("El registro ingresado no es válido, verifique su fecha de vinculación")

            # se verifica cruces de fechas con otros registros
            cruce_1 = self.env['account.analytic.line'].search(
                ['&','&', ('date_from', '<', self.date_from), ('date_to', '>=', self.date_from),
                          ('user_id', '=', self.user_id.id)])
            cruce_2 = self.env['account.analytic.line'].search(
                ['&','&', ('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                          ('user_id', '=', self.user_id.id)])
            cruce_3 = self.env['account.analytic.line'].search(
                ['&','&', ('date_from', '<', self.date_from), ('date_to', '>', self.date_to),
                          ('user_id', '=', self.user_id.id)])
            cruce_4 = self.env['account.analytic.line'].search(
                ['&','&', ('date_from', '<=', self.date_to), ('date_to', '>=', self.date_to),
                          ('user_id', '=', self.user_id.id)])

            cruces = cruce_1 | cruce_2 | cruce_3 | cruce_4

            if len(cruces) > 0:
                raise UserError("El registro ingresado no es válido, se cruza con al menos otro")
        else:
            # no tiene contrato
            self.date_from = None
            raise UserError("El registro ingresado no es válido, no se encuentra contrato")

    def get_in_datelist(self):
        employee_tz = pytz.timezone(self.user_id.partner_id.tz)
        date_from = fields.Datetime.from_string(self.date_from)
        date_to = fields.Datetime.from_string(self.date_to)

        return [date_from, date_to]

    def cut_by_months(self, parte_conservar):
        employee_tz = pytz.timezone(self.user_id.partner_id.tz)
        date_from = fields.Datetime.from_string(self.date_from)
        date_to = fields.Datetime.from_string(self.date_to)

        register = []

        # agregando zona horaria utc cero explícita
        auxiliar_utcz_datefrom = utc_cero.localize(date_from)
        auxiliar_utcz_dateto   = utc_cero.localize(date_to)

        # cambiando la zona horaria a la del usuario
        auxiliar_utcu_datefrom = auxiliar_utcz_datefrom.astimezone(employee_tz)
        auxiliar_utcu_dateto   = auxiliar_utcz_dateto.astimezone(employee_tz)

        # comparaciones en utc usuario
        if parte_conservar == 'mes_inicio':            
            auxiliar_date_i = auxiliar_utcu_datefrom
            auxiliar_date_f = timedelta(year=auxiliar_utcu_datefrom.year, month=auxiliar_utcu_datefrom.month, 
                                day=calendar.monthrange(auxiliar_utcu_datefrom.year, auxiliar_utcu_datefrom.month)[1],
                                hour=23, minute=59, second=59)
            auxiliar_date_f = employee_tz.localize(auxiliar_date_f)
        elif parte_conservar == 'mes_fin':
            auxiliar_date_i = timedelta(year=auxiliar_utcu_dateto.year, month=auxiliar_utcu_dateto.month, day=1,
                                hour=0, minute=0, second=0)
            auxiliar_date_i = employee_tz.localize(auxiliar_date_i)
            auxiliar_date_f = auxiliar_utcu_dateto
        else:
            auxiliar_date_i = auxiliar_utcu_datefrom
            auxiliar_date_f = auxiliar_utcu_dateto

        register = [datetime.combine(auxiliar_date_i.date(), auxiliar_date_i.time()),
                    datetime.combine(auxiliar_date_f.date(), auxiliar_date_f.time())]
        return register

    date_from = fields.Datetime('Fecha inicial', required=True, index=True, default=_default_datefrom)
    date_to = fields.Datetime('Fecha final', required=True, index=True)
    state = fields.Selection([
        ('enviado', 'Esperando revisión nómina'),
        ('aprobado', 'Aprobado nómina')], 
        string='Estado', default='enviado')