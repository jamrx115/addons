# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, http
from openerp.http import request

_logger = logging.getLogger(__name__)


class EmployeeCode(models.Model):
    _inherit = 'hr.employee'

    _sql_constraints = [
        ('employee_code_unique', 'UNIQUE(x_code)', 'El código ingresado ya fue asignado')
    ]

    _logger.debug('------------------------------- Employee Code')

    @api.model
    def create(self, vals):
        if not vals.get('x_code'):
            vals['x_code'] = self.env['ir.sequence'].next_by_code('hr.employee.code')
        return super(EmployeeCode, self).create(vals)


class ApplicantCode(models.Model):
    _inherit = 'hr.applicant'

    _sql_constraints = [
        ('applicant_code_unique', 'UNIQUE(x_code_applicant)', 'El código ingresado ya fue asignado')
    ]

    _logger.debug('------------------------------- Applicant Code')

    @api.model
    def create(self, vals):
        if not vals.get('x_code_applicant') and not (vals.get('x_bolsa_de_empleo') or vals.get('x_candidatura_esp')):
            vals['x_code_applicant'] = self.env['ir.sequence'].next_by_code('hr.applicant.code')
        if vals.get('x_tipo_de_cliente'):
            if vals.get('x_tipo_de_cliente') == 'cliente_interno':
                vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Requerimientos (CI)')], limit=1).ids[0]
            if vals.get('x_tipo_de_cliente') == 'cliente_externo':
                vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Requerimientos (CE)')], limit=1).ids[0]
        if vals.get('x_esta_aprobacion'):
            if vals.get('x_esta_aprobacion') == 'aprobado':
                vals['stage_id'] = 6
	if vals.get('x_bolsa_de_empleo'):
            vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Bolsa de empleo')], limit=1).ids[
                0]
        if vals.get('x_candidatura_esp'):
            vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Vacantes activas')], limit=1).ids[0]
        return super(ApplicantCode, self).create(vals)



