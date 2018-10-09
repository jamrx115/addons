# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
import logging

_logger = logging.getLogger(__name__)

class ciberc_performance (models.Model):
    _name = "ciberc.performance"
    _description = "Evaluaci&oacute;n de desempe&ntilde;o"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Many2one('res.users', string='Nombre del empleado', track_visibility="onchange")
    evaluator_id = fields.Many2one('res.users', string="Evaluador", track_visibility="onchange")
    date = fields.Date(string="Fecha", help="Ingrese la fecha de creación de la evaluación")
    performance_goal_id =fields.One2many('ciberc.performance.line','name', string="Objetivos de rendimiento")
    evolution_personal_goal_id = fields.Many2many('ciberc.personal.goals', string="Objetivos de desarrollo personal")
    general_rating = fields.Selection([('excepcional', 'Excepcional'),('sobresaliente', 'Sobresaliente'),('bueno', 'Bueno'),('mejor', 'Necesita mejorar'),],string="Calificación general", track_visibility="onchange")
    comments_extra = fields.Text(string="Comentarios adicionales")
    department_id = fields.Many2one('hr.department', string="Departamento")
    state = fields.Selection([('borrador','Borrador'),('primer','Primer semestre'),('segundo','Segundo semestre'),('finalizada','Finalizada')], string="Estado", track_visibility="onchange",default="borrador")

    @api.one
    def action_segundo_semestre(self):
        self.write({
            'state': 'segundo',
        })

    @api.one
    def action_end_performance(self):
        self.write({
            'state': 'finalizada',
        })

    @api.one
    def action_back_performance(self):
        self.write({
            'state': 'primer',
        })

    @api.model
    def create(self, values):
        values['state'] = 'primer'
        line = super(ciberc_performance, self).create(values)
        return line
    """
    @api.multi
    def _get_goals(self):
        for line in used_car_ids:
            result.append((0, 0, {'first_semester': line.first_semester, 'second_semester': line.second_semester}))
        self.performance_goal_id = result
    """

class ciberc_performance_line (models.Model):
    _name="ciberc.performance.line"
    _description = "Objetivos de rendimiento"


    name = fields.Char(string="Nombre")
    goal_id = fields.Many2one('ciberc.goals',string="Nombre")
    #goal_id = fields.Many2one('ciberc.goals',string="Nombre", domain="[('departments_ids.member_ids.user_id', '=', uid)]")        
    #goal_id = fields.Many2one('ciberc.goals',string="Nombre", domain="[('departments_ids.member_ids.user_id', '=', 'ciberc_performance.name')]")        
    #goal_id = fields.Many2one('ciberc.goals',string="Nombre", domain="[('departments_ids.member_ids.user_id', '=', 'name_employee.name')]")        
    first_semester = fields.Char(string="Primer semestre")
    second_semester = fields.Char(string="Segundo semestre")
    score = fields.Char(string="Calificación")
    comments_employee = fields.Text(string="Comentarios empleado")
    comments_evaluator = fields.Text(string="Comentarios evaluador")
    personal_goal_id = fields.Char(string="Meta personal")
    sequence = fields.Integer(String="secuencia")


class ciberc_main_goals (models.Model):
    _name="ciberc.main.goals"
    _description = "Objetivo estrategia general"
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    name = fields.Char(string='Nombre')
    description = fields.Text(string='Descripción')
    goal = fields.Char(string='Meta')
    comments = fields.Text(string='Comentarios')

class ciberc_goals (models.Model):
    _name="ciberc.goals"
    _description = "Objetivo"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Nombre')
    main_goal_related_id = fields.Many2one('ciberc.main.goals', string="Objetivo estrategia general")
    description = fields.Text(string='Descripción')
    departments_ids = fields.Many2many('hr.department',string="Departamento")
    goal = fields.Char(string='Meta')
    goal_min = fields.Char(string='Mínimo')
    goal_max = fields.Char(string='Máximo')
    #pruebas 
    user_id = fields.Many2one('res.users',string="Usuario")
    performance_id = fields.Many2one('ciberc.performance', string="Performance")
    name_employee = fields.Many2one('ciberc.performance',string="nombre del empleado asociado")


class ciberc_personal_goals (models.Model):
    _name="ciberc.personal.goals"
    _description = "Objetivo personal"

    name = fields.Char(string='Nombre')
    scope = fields.Char(string='% Alcanzado')
    date = fields.Date(string="Fecha de compromiso")
    comments = fields.Text(string="Comentarios")
    sequence = fields.Integer(string="Secuencia")

