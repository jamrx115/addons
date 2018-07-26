# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re

class ciberc_cities(models.Model):
    _name = "ciberc.city"

    name = fields.Char(string='Nombre',required=True)
    code = fields.Char(string='Código',)
    state_id = fields.Many2one("res.country.state", string='Estado/Departamento', ondelete='restrict',required=True)

class ciberc_employee(models.Model):
    _inherit = 'hr.employee'

    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced'),
        ('unmarried', 'Unmarried')
    ], string='Marital Status', groups='hr.group_hr_user')

    x_state_id = fields.Many2one("res.country.state", string='Estado/Departamento', ondelete='restrict')
    x_city_id = fields.Many2one("ciberc.city", string='Ciudad', ondelete='restrict')
    x_hide_state = fields.Boolean(string='Hide', compute="_compute_hide_country_id")
    x_hide_city = fields.Boolean(string='Hide', compute="_compute_hide_state_id")

    x_pais_reside = fields.Many2one("res.country", string="País residencia", ondelete='restrict')
    x_pais_nace = fields.Many2one("res.country", string="País nacimiento", ondelete='restrict')
    x_birth_state_id = fields.Many2one("res.country.state", string='Estado/Departamento', ondelete='restrict')
    x_birth_city_id = fields.Many2one("ciberc.city", string='Ciudad', ondelete='restrict')
    x_hide_birth_state = fields.Boolean(string='Hide', compute="_compute_hide_birth_country_id")
    x_hide_birth_city = fields.Boolean(string='Hide', compute="_compute_hide_birth_state_id")

    # Pais Estado Ciudad Reside
    @api.multi
    @api.onchange('x_pais_reside')
    def _onchange_country_id(self):
        self.x_state_id = False
        self.x_city_id = False
        if self.x_pais_reside:
            return {'domain': {'x_state_id': [('country_id', '=', self.x_pais_reside.id)]}}
        else:
            return {'domain': {'x_state_id': []}}

    @api.depends('x_pais_reside')
    def _compute_hide_country_id(self):
        for record in self:
            if record.x_pais_reside:
                record.x_hide_state = False
            else:
                record.x_hide_state = True

    @api.multi
    @api.onchange('x_state_id')
    def _onchange_state_id(self):
        if self.x_state_id:
            return {'domain': {'x_city_id': [('state_id', '=', self.x_state_id.id)]}}
        else:
            return {'domain': {'x_city_id': []}}

    @api.depends('x_state_id')
    def _compute_hide_state_id(self):
        for record in self:
            if record.x_state_id:
                record.x_hide_city = False
            else:
                record.x_hide_city = True

    # Pais Estado Ciudad Nacimiento
    @api.multi
    @api.onchange('x_pais_nace')
    def _onchange_birth_country_id(self):
        self.x_birth_state_id = False
        self.x_birth_city_id = False
        if self.x_pais_nace:
            return {'domain': {'x_birth_state_id': [('country_id', '=', self.x_pais_nace.id)]}}
        else:
            return {'domain': {'x_birth_state_id': []}}

    @api.depends('x_pais_nace')
    def _compute_hide_birth_country_id(self):
        for record in self:
            if record.x_pais_nace:
                record.x_hide_birth_state = False
            else:
                record.x_hide_birth_state = True

    @api.multi
    @api.onchange('x_birth_state_id')
    def _onchange_birth_state_id(self):
        if self.x_birth_state_id:
            return {'domain': {'x_birth_city_id': [('state_id', '=', self.x_birth_state_id.id)]}}
        else:
            return {'domain': {'x_birth_city_id': []}}

    @api.depends('x_birth_state_id')
    def _compute_hide_birth_state_id(self):
        for record in self:
            if record.x_birth_state_id:
                record.x_hide_birth_city = False
            else:
                record.x_hide_birth_city = True

    # Regular expressions
    @api.multi
    @api.onchange('x_identificacion')
    def _check_value_identification(self):
        if self.x_identificacion:
            pattern = "^\w[a-zA-Z0-9_\-]{7,19}$"
            if re.match(pattern, self.x_identificacion) == None:
                self.x_identificacion = ""
                return {
                    'warning': {'title': _('Error'),
                                'message': 'Formato de número de identificación no valido, debe incluir términos alfanúmeros y guion (si aplica), longitud máxima de caracteres 20', }
                }

    @api.multi
    @api.onchange('x_nit')
    def _check_value_nit(self):
        if self.x_nit:
            pattern = "^\w[a-zA-Z0-9_\-]{7,19}$"
            if re.match(pattern, self.x_nit) == None:
                self.x_nit = ""
                return {
                    'warning': {'title': _('Error'),
                                'message': 'Formato de número de identificación no valido, debe incluir términos alfanúmeros y guion (si aplica), longitud máxima de caracteres 20', }
                }

    @api.multi
    @api.onchange('x_cedula_extranjeria')
    def _check_value_idn(self):
        if self.x_cedula_extranjeria:
            pattern = "^\w[a-zA-Z0-9_\-]{7,19}$"
            if re.match(pattern, self.x_cedula_extranjeria) == None:
                self.x_cedula_extranjeria = ""
                return {
                    'warning': {'title': _('Error'),
                                'message': 'Formato de número de identificación no valido, debe incluir términos alfanúmeros y guion (si aplica), longitud máxima de caracteres 20', }
                }
