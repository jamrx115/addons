# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError

import re
import logging

_logger = logging.getLogger(__name__)

class ciberc_performance (models.Model):
    _name = "ciberc.performance"
    _description = "Evaluaci&oacute;n de desempe&ntilde;o"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Many2one('res.users', string='Nombre del empleado', track_visibility="onchange")
    evaluator_id = fields.Many2one('res.users', string="Evaluador", track_visibility="onchange")
    date = fields.Date(string = "Fecha", help="Ingrese la fecha de creación de la evaluación")
    performance_goal_id = fields.One2many('ciberc.performance.line','ciberc_performance_id',string="Objetivos de rendimiento")
    evolution_personal_goal_id = fields.One2many('ciberc.personal.goals','ciberc_performance_id', string="Objetivos de desarrollo personal")
    general_rating = fields.Selection([('excepcional', 'Excepcional'),('sobresaliente', 'Sobresaliente'),('bueno', 'Bueno'),('mejor', 'Necesita mejorar'),],string="Calificación general", track_visibility="onchange")
    comments_extra = fields.Text(string="Comentarios adicionales")
    department_id = fields.Many2one('hr.department', string="Departamento")
    type_evaluation = fields.Selection([('evaluacion', 'Evaluación de desempeño'),('prueba', 'Periodo de prueba')],string="Tipo")
    state = fields.Selection([('borrador','Borrador'),('primer','Primera fase'),('segundo','Segunda fase'),('finalizada','Finalizada')], string="Estado", track_visibility="onchange",default="borrador")


    @api.one
    def action_segundo_semestre(self):
        self.write({
            'state': 'segundo',
        })

    @api.one
    def action_end_performance(self):
        if self.general_rating == False:
            raise UserError('Antes de terminar la evaluación debe ingresar la calificación general del colaborador')
        else:
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
        res = super(ciberc_performance,self.with_context(mail_create_nosubscribe=True)).create(values)
        return res
    
    @api.multi
    def get_goal(self):
        """
        goal_list = []
        goal_exist_list = []
        goal_set_list = []
        self.env['ciberc.performance.line'].search([('ciberc_performance_id.id', '=', self.id)]).unlink()
        #goals_of_this_employee = self.env['ciberc.goals'].search([('departments_ids', '=', self.department_id.id),('id', 'not in', self.performance_goal_id.goal_id.id)])
        goals_of_this_employee = self.env['ciberc.goals'].search([('departments_ids', '=', self.department_id.id)])
        goals_set_in_this_employee = self.env['ciberc.performance.line']

        for goal_exist in goals_of_this_employee:
            goal_exist_list.append(goal_exist.id)

        for goal_set in goals_set_in_this_employee:
            goal_set_list.append(goal_set.goal_id.id)

        for goal in goal_exist_list:
            if not self.performance_goal_id:
                for goal2 in self.performance_goal_id.ids:
                    if goal != goal2:
                        goal_created  = self.env['ciberc.performance.line'].create({'goal_id': goal})
                        goal_list.append(goal_created.id)
            else:
                goal_created  = self.env['ciberc.performance.line'].create({'goal_id': goal})
                goal_list.append(goal_created.id)
        self.performance_goal_id = goal_list
    """

    
    #FUNCIONA BIEN PERO QUIERO AGREGARLE UN IF PARA QUE NO CARGUE VARIAS VECES LOS MISMOS
    @api.multi
    def get_goal(self):
        goal_list = []
        self.env['ciberc.performance.line'].search([('ciberc_performance_id.id', '=', self.id)]).unlink()
        goals_of_this_employee = self.env['ciberc.goals'].search([('departments_ids', '=', self.department_id.id)])
        for goal in goals_of_this_employee:
            goal_created  = self.env['ciberc.performance.line'].create({
                            'goal_id': goal.id})
            goal_list.append(goal_created.id)
        self.performance_goal_id = goal_list
        return goal_list
    

class ciberc_performance_line (models.Model):
    _name="ciberc.performance.line"
    _description = "Objetivos de rendimiento"

    name = fields.Char(string="Nombre")
    #goal_id = fields.Many2one('ciberc.goals',string="Nombre", domain="[('departments_ids.member_ids.user_id', '=', ciberc_performance_id.department_id)]")
    goal_id = fields.Many2one('ciberc.goals',string="Nombre")
    #goal_id = fields.Many2one('ciberc.goals',string="Nombre", domain="[('departments_ids.member_ids.user_id', '=', uid)]")        
    #goal_id = fields.Many2one('ciberc.goals',string="Nombre", domain="[('departments_ids.member_ids.user_id', '=', 'ciberc_performance.name')]")        
    #goal_id = fields.Many2one('ciberc.goals',string="Nombre", domain="[('departments_ids.member_ids.user_id', '=', 'name_employee.name')]")        
    main_goal_id = fields.Many2one('ciberc.main.goals',related="goal_id.main_goal_related_id", string="objetivo general")
    personal_goal = fields.Char(string="Meta personal")
    first_semester = fields.Char(string="Primera fase")
    second_semester = fields.Char(string="Segunda fase")
    score = fields.Char(string="Calificación")
    comments_employee = fields.Text(string="Comentarios empleado")
    comments_evaluator = fields.Text(string="Comentarios evaluador")
    sequence = fields.Integer(string="secuencia")
    ciberc_performance_id = fields.Many2one('ciberc.performance',string="conexión")

       
    @api.onchange('goal_id')
    def _onchange_goals(self):
        self.main_goal_id = self.goal_id.main_goal_related_id
    


class ciberc_goals (models.Model):
    _name="ciberc.goals"
    _description = "Objetivo especifico"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Nombre')
    main_goal_related_id = fields.Many2one('ciberc.main.goals', string="Objetivo de estrategia general")
    description = fields.Text(string='Descripción')
    departments_ids = fields.Many2many('hr.department',string="Departamento")
    goal = fields.Char(string='Meta')
    goal_min = fields.Char(string='Mínimo')
    goal_max = fields.Char(string='Máximo')

    @api.model
    def create(self, values):
        res=super(ciberc_goals,self.with_context(mail_create_nosubscribe=True)).create(values)
        return res
    

class ciberc_main_goals (models.Model):
    _name="ciberc.main.goals"
    _description = "Objetivo estrategia general"
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    name = fields.Char(string='Nombre')
    description = fields.Text(string='Descripción')
    goal = fields.Char(string='Meta')
    comments = fields.Text(string='Comentarios')
    
    @api.model
    def create(self, values):
        res = super(ciberc_main_goals,self.with_context(mail_create_nosubscribe=True)).create(values)
        return res
   

class ciberc_personal_goals (models.Model):
    _name="ciberc.personal.goals"
    _description = "Objetivo personal"

    inverse = fields.Char(string="Inverso")
    name = fields.Char(string='Nombre')
    main_personal_goal_id = fields.Many2one('ciberc.personal.main.goals',string="Objetivo personal general")
    scope = fields.Char(string='% Alcanzado')
    date = fields.Date(string="Fecha de compromiso")
    comments = fields.Text(string="Comentarios")
    sequence = fields.Integer(string="Secuencia")
    ciberc_performance_id = fields.Many2one('ciberc.performance',string="conexión")


class ciberc_personal_main_goals (models.Model):
    _name="ciberc.personal.main.goals"
    _description = "Objetivo personal general"

    name = fields.Char(string='Nombre')
