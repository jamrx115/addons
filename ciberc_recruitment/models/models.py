# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# clase creada por alltic que modifica el modelo Candidato
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
                vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Requerimientos Vo. Bo.')], limit=1).ids[0]
        if vals.get('x_bolsa_de_empleo'):
            vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Únete a nuestro equipo')], limit=1).ids[0]
        if vals.get('x_candidatura_esp'):
            vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Oportunidad de trabajo')], limit=1).ids[0]
        return super(ApplicantCode, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('x_tipo_de_cliente'):
            if vals.get('x_tipo_de_cliente') == 'cliente_interno':
                vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Requerimientos (CI)')], limit=1).ids[0]

            if vals.get('x_tipo_de_cliente') == 'cliente_externo':
                vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Requerimientos (CE)')], limit=1).ids[0]

        if vals.get('x_esta_aprobacion'):
            if vals.get('x_esta_aprobacion') == 'aprobado':
                vals['stage_id'] = self.env['hr.recruitment.stage'].search([('name', '=', 'Requerimientos Vo. Bo.')], limit=1).ids[0]

        return super(ApplicantCode, self).write(vals)

# clase creada por alltic que modifica el modelo Candidato
class ciberc_applicant(models.Model):
    _inherit = 'hr.applicant'

    firstname = fields.Char("Nombres")
    lastname  = fields.Char("Apellidos")

    x_interest_country = fields.Many2one("x_pais_interes", string='País de Interés', ondelete='restrict')
    x_residence_country = fields.Many2one("res.country", string='País de Residencia', ondelete='restrict')

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            address_id = contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            if applicant.job_id and applicant.firstname or applicant.lastname:
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})

                employee = self.env['hr.employee'].create({'name': applicant.partner_name or False,
                                                           'firstname': applicant.firstname or ' ',
                                                           'lastname': applicant.lastname or ' ',
                                                           'job_id': applicant.job_id.id,
                                                           'address_home_id': address_id,
                                                           'department_id': applicant.department_id.id or False,
                                                           'address_id': applicant.company_id and applicant.company_id.partner_id and applicant.company_id.partner_id.id or False,
                                                           'work_email': False,
                                                           'work_phone': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.phone or False})
                applicant.write({'emp_id': employee.id})
                applicant.job_id.message_post(
                    body=(
                        'New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
                employee._broadcast_welcome()
            else:
                raise UserError('You must define an Applied Job and a Contact Name for this applicant.')

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        if employee:
            dict_act_window['res_id'] = employee.id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window
