# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
import calendar
from datetime import datetime
from odoo.exceptions import Warning

MONTHS = [('01', 'January'),
          ('02', 'February'),
          ('03', 'March'),
          ('04', 'April'),
          ('05', 'May'),
          ('06', 'June'),
          ('07', 'July'),
          ('08', 'August'),
          ('09', 'September'),
          ('10', 'October'),
          ('11', 'November'),
          ('12', 'December')]


class MultiEmployeeWiz(models.TransientModel):
    _name = 'multi.employee.wiz'

    emplyee_id_obj = fields.Many2one('multi.payslip', "Id")
    employee_id = fields.Many2one('hr.employee', "Employee")
    month_from = fields.Selection(MONTHS, 'Month From', required=True)
    month_to = fields.Selection(MONTHS, 'Month To', required=True)
    active = fields.Boolean("Active Employee")


class MultiPayslipWiz(models.TransientModel):
    _name = 'multi.payslip'

    employee_ids = fields.One2many(
        'multi.employee.wiz', 'emplyee_id_obj', 'Employee(s)')

#     set selected employee in wizard
    @api.model
    def default_get(self, fields):
        res = super(MultiPayslipWiz, self).default_get(fields)
        employees = self.env['hr.employee'].browse(
            self._context.get('active_ids', False))
        emp_list = []
        for employee in employees:
            emp_list.append(
                (0, 0, {'employee_id': employee.id, 'active': True}))
        res['employee_ids'] = emp_list
        return res

#     create selected employee's contract
    @api.multi
    def multi_payslip(self):
        action = []
        for emp_id in self.employee_ids:
            emp_contract = \
                self.env['hr.contract'].get_employee_active_contract(emp_id)
            if not emp_contract['contract_id']:
                raise Warning(
                    _('Please Create Contract for employee = %s.') %
                    emp_id.employee_id.name)
            now = datetime.now()
            mon_from = int(emp_id.month_from)
            mon_to = int(emp_id.month_to)

            for cur_month in range(mon_from, mon_to):
                if cur_month == now.month or mon_to >= now.month:
                    raise Warning(
                        _('Please select correct month less then '
                            'current month.'))
                else:
                    last_day_of_month = calendar.monthrange(
                        now.year, cur_month)[1]
                    date_str = str(now.year) + '-' + \
                        str(cur_month) + '-' + str(last_day_of_month)
                    first_date = datetime.strptime(
                        str(now.year) + '-' + str(cur_month) + '-' + '01',
                        '%Y-%m-%d')
                    last_date = datetime.strptime(date_str, '%Y-%m-%d')

                    val = {'employee_id': emp_id.employee_id.id,
                           'name': emp_id.employee_id.name + ' \'s Payslip',
                           'contract_id': emp_contract['contract_id'],
                           'struct_id': emp_contract['struct_id'],
                           'date_from': first_date,
                           'date_to': last_date,
                           }
                    vals = self.env['hr.payslip'].create(val)
                    action = self.env.ref(
                        'hr_payroll.action_view_hr_payslip_form').read()[0]
                    action['views'] = [
                        (self.env.ref('hr_payroll.view_hr_payslip_form').id,
                            'form')]
                    action['res_id'] = vals.id
        return action


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _order = 'date_start desc'

#     find contract of employee.
    @api.multi
    def get_employee_active_contract(self, rec):
        contract_id = False
        employee_id = rec.employee_id
        if employee_id:
            contract_id_obj = self.env['hr.contract'].search(
                [('employee_id', '=', employee_id.id),
                 ('state', '!=', 'close')], order="date_start desc", limit=1)
            contract_id = contract_id_obj and contract_id_obj.id or False
            struct_id = contract_id_obj.struct_id and \
                contract_id_obj.struct_id.id or False
        val = {'contract_id': contract_id,
               'struct_id': struct_id}
        return val
