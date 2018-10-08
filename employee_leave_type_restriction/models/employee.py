# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api, fields, models, _

class HrHolidaysStatus(models.Model):
    _inherit = "hr.holidays.status"


    employee_tag_ids = fields.Many2many('hr.employee.category', string='Employee Tag')

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args = args + ['|',self.get_domain(),('employee_tag_ids','=',False)]
        return super(HrHolidaysStatus, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(HrHolidaysStatus, self).name_search(name, args, operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('number', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = domain + ['|',self.get_domain(),('employee_tag_ids','=',False)]
        return super(HrHolidaysStatus, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    def get_domain(self):
        tags = []
        leave_type_ids = []
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        tag_ids = emp.category_ids
        for tag in tag_ids:
            tags.append(tag.id)
        domain_tuple = ('employee_tag_ids', 'in', tags)
        return domain_tuple
       









