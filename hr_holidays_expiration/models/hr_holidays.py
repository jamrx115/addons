# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class HRHolidays(models.Model):
    _inherit = "hr.holidays"

    @api.model
    def default_get(self, fields):
        res = super(HRHolidays, self).default_get(fields)
        company = self.env.user.company_id
        res['expire_template_id'] = (company.expire_template_id.id)
        res['notify_template_id'] = (company.notify_template_id.id)
        return res

    @api.model
    def check_expiring(self):
        _logger.debug("ONESTEiN hr_holidays check_expiring")
        allocation_req_list = self.search([
            ('expiration_date', '!=', False),
            ('approval_date', '!=', False),
            ('expired', '=', False),
            ('type', '!=', 'remove')])

        # notification
        allocation_req_list._set_notification()
        # expiring
        allocation_req_list._set_expiration()

    @api.multi
    def _set_notification(self):

        def notification_not_sent(holiday):
            return holiday.email_notify and not holiday.notification_sent

        for holiday in self:
            if notification_not_sent(holiday):
                exp_date = datetime.strptime(
                    holiday.expiration_date,
                    DEFAULT_SERVER_DATE_FORMAT)
                note_date = datetime.today() + timedelta(holiday.notify_period)

                if exp_date <= note_date and holiday.notify_template_id:
                    holiday.notify_template_id.send_mail(holiday.id)
                    holiday.notification_sent = True

    @api.multi
    def _set_expiration(self):
        for holiday in self:
            if datetime.strptime(
                    holiday.expiration_date,
                    DEFAULT_SERVER_DATE_FORMAT) <= datetime.today():
                holiday.expired = True
                if holiday.expire_template_id:
                    holiday.expire_template_id.send_mail(holiday.id)

    # notification
    email_notify = fields.Boolean('Notificar vencimiento via email')
    notify_period = fields.Integer("Periodo de notificación (días)",
        help="Cantidad de días antes de que expiren los festivos para enviar el correo electrónico de notificación.")
    notify_template_id = fields.Many2one('mail.template', string='Plantilla de correo para notificaciones')
    notification_sent = fields.Boolean(string='Enviar notificación de vencimiento')
    notify_to = fields.Many2one('hr.employee', string='Notificar vencimiento a')

    # expiring
    expiration_date = fields.Date()
    expired = fields.Boolean(default=False)
    expire_template_id = fields.Many2one('mail.template', string='Plantilla de correo para vencimientos')
    approval_date = fields.Date(string="Fecha aprobado")

    @api.multi
    def action_approve(self):
        res = super(HRHolidays, self).action_approve()
        self.write({'approval_date': fields.Datetime.now()})
        return res

    @api.multi
    def action_draft(self):
        res = super(HRHolidays, self).action_draft()
        self.write({'approval_date': None})
        return res
