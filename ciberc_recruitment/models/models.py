# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ciberc_applicant(models.Model):
    _inherit = 'hr.applicant'

    firstname = fields.Char("Nombres")
    lastname  = fields.Char("Apellidos")

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
                                                           'work_email': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.email or False,
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