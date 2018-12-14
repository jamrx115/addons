# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import re
import pytz
import logging

_logger = logging.getLogger(__name__)

class BveView(models.Model):
    _inherit = 'bve.view'

    @api.multi
    def _create_bve_view(self):
        self.ensure_one()

        # create views
        View = self.env['ir.ui.view']
        old_views = View.sudo().search([('model', '=', self.model_name)])
        old_views.sudo().unlink()

        view_vals = [{
            'name': 'Pivot Analysis',
            'type': 'pivot',
            'model': self.model_name,
            'priority': 16,
            'arch': """<?xml version="1.0"?>
                           <pivot string="Pivot Analysis">
                           {}
                           </pivot>
                        """.format("".join(self._create_view_arch()))
        }, {
            'name': 'Graph Analysis',
            'type': 'graph',
            'model': self.model_name,
            'priority': 16,
            'arch': """<?xml version="1.0"?>
                           <graph string="Graph Analysis"
                            type="bar" stacked="True">
                            {}
                           </graph>
                        """.format("".join(self._create_view_arch()))
        }, {
            'name': 'Search BI View',
            'type': 'search',
            'model': self.model_name,
            'priority': 16,
            'arch': """<?xml version="1.0"?>
                           <search string="Search BI View">
                           {}
                           </search>
                        """.format("".join(self._create_view_arch()))
        }]

        for vals in view_vals:
            View.sudo().create(vals)

        # create Tree view
        tree_view = View.sudo().create(
            {'name': 'Tree Analysis',
             'type': 'tree',
             'model': self.model_name,
             'priority': 16,
             'arch': """<?xml version="1.0"?>
                            <tree string="List Analysis" create="false">
                            {}
                            </tree>
                         """.format("".join(self._create_tree_view_arch()))
             })

        # set the Tree view as the default one
        action_vals = {
            'name': self.name,
            'res_model': self.model_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,graph,pivot',
            'view_id': tree_view.id,
            'limit' : 1000, # ONLY THIS LINE IS NEW
            'context': "{'service_name': '%s'}" % self.name,
        }

        ActWindow = self.env['ir.actions.act_window']
        action_id = ActWindow.sudo().create(action_vals)
        self.write({
            'action_id': action_id.id,
            'view_id': tree_view.id,
            'state': 'created'
        })

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def get_empty_list_help(self, help):
        """ Override of BaseModel.get_empty_list_help() to generate an help message
        that adds alias information. """
        model = self._context.get('empty_list_help_model')
        res_id = self._context.get('empty_list_help_id')
        catchall_domain = self.env['ir.config_parameter'].sudo().get_param("mail.catchall.domain")
        document_name = self._context.get('empty_list_help_document_name', _('document'))
        add_arrow = not help or help.find("oe_view_nocontent_create") == -1
        alias = None

        if catchall_domain and model and res_id:  # specific res_id -> find its alias (i.e. section_id specified)
            record = self.env[model].sudo().browse(res_id)
            # check that the alias effectively creates new records
            if record.alias_id and record.alias_id.alias_name and \
                    record.alias_id.alias_model_id and \
                    record.alias_id.alias_model_id.model == self._name and \
                    record.alias_id.alias_force_thread_id == 0:
                alias = record.alias_id
        if not alias and catchall_domain and model:  # no res_id or res_id not linked to an alias -> generic help message, take a generic alias of the model
            Alias = self.env['mail.alias']
            aliases = Alias.search([
                ("alias_parent_model_id.model", "=", model),
                ("alias_name", "!=", False),
                ('alias_force_thread_id', '=', False),
                ('alias_parent_thread_id', '=', False)], order='id ASC')
            if aliases and len(aliases) == 1:
                alias = aliases[0]

        if add_arrow:
            return "<p class='oe_view_nocontent_create'>%(dyn_help)s</p>%(static_help)s" % {
                'static_help': help or '',
                'dyn_help': _("Click here to add new %s") % document_name,
            }

        return help

# clase creada por alltic que modifica x_code
class JobCode(models.Model):
    _inherit = 'hr.job'

    _sql_constraints = [
        ('job_code_unique', 'UNIQUE(x_code)', 'El código ingresado ya fue asignado')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('x_code'):
            vals['x_code'] = self.env['ir.sequence'].next_by_code('hr.job.code')
        return super(JobCode, self).create(vals)

#
class LoginUserEmail(models.Model):
    _inherit = ['res.users']
    
    @api.onchange('login')
    def on_change_login(self):
        if self.login and tools.single_email_re.match(self.login):
            #self.email = self.login
            pass

# actualización a partes de horas
class AccountAnalyticLine(models.Model):
    _inherit = ['account.analytic.line']

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', string='User', default=_default_user, domain=lambda self: [('id', '=', self.env.uid)])

# actualización de préstamos
class HrLoanUpdated(models.Model):
    _inherit = 'hr.loan'

    def get_installment_day(self, date):
        if date.day <= 15:
            day = 15
        else:
            if date.month == 2:
                day = 28
            else:
                day = 30
        return day

    # override
    @api.multi
    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            self.env['hr.loan.line'].search([('loan_id.id', '=', self.id)]).unlink() # new
            date_base = datetime.strptime(loan.payment_date, '%Y-%m-%d')
            date_start = datetime(year=date_base.year, month=date_base.month, day=self.get_installment_day(date_base))
            amount = loan.loan_amount / loan.installment
            limit = loan.installment + 1
            for i in range(1, limit):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_base = date_start + relativedelta(days=13)
                date_start = datetime(year=date_base.year, month=date_base.month,
                                      day=self.get_installment_day(date_base))
        return True

# actualización de países
class ResCountryUpdated(models.Model):
    _inherit = 'res.country'

    code_ext = fields.Char('Código Ext.')

# actualización de vencimiento de pasaportes
class EmployeeUpdated(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        user_tz = pytz.timezone(self.env.user.partner_id.tz)
        now = datetime.now(tz=user_tz)
        #now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=1)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date)
                exp_is_coming = exp_date1  - timedelta(days=140)
                diferencia = (exp_date1-date_now).days
                if date_now >= exp_is_coming:
                    if diferencia > 0:
                        mail_content = "Por medio del presente correo se le informa,  " + i.name + ", su pasaporte No. " + i.passport_id + " vence el " + \
                                   str(i.passport_expiry_date) + " (aproximadamente en " +str(diferencia)+" dias). Se sugiere renovarlo antes de esta fecha"
                        subject = _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date)
                    else:
                        mail_content = "Por medio del presente correo se le informa,  " + i.name + ", su pasaporte No. " + i.passport_id + " ha expirado el " + \
                                   str(i.passport_expiry_date) + " (hace " +str(-1*diferencia)+" dias). Se sugiere renovarlo lo antes posible"
                        subject = ('Pasaporte %s vencido el %s') % (i.passport_id, i.passport_expiry_date)
                    main_content = {
                        'subject': subject,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()
