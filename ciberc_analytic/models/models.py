# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta, time as dtime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, AccessError

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
        today_user = datetime.now(tz=self._user_tz())
        today_utcz = utc_cero.fromutc(datetime.now())
        return datetime.combine(today_utcz.date(), dtime(hour=today_utcz.hour))

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

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            self.unit_amount = self._get_number_of_hours(date_from, date_to, self.user_id.id)
        else:
            self.unit_amount = 0

    @api.onchange('date_to')
    def _onchange_date_to(self):
        date_from = self.date_from
        date_to = self.date_to

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            self.unit_amount = self._get_number_of_hours(date_from, date_to, self.user_id.id)
        else:
            self.unit_amount = 0

    date_from = fields.Datetime('Fecha inicial', required=True, default=_default_datefrom)
    date_to = fields.Datetime('Fecha final', required=True, default=_default_dateto)
    state = fields.Selection([
        ('enviado', 'Esperando revisión nómina'),
        ('aprobado', 'Aprobado nómina')], 
        string='Estado', default='enviado')
