# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
import logging

_logger = logging.getLogger(__name__)

class ciberc_knowledge (models.Model):
    _name="ciberc.knowledge"
    _description= " Solicitud de capacitacion"

    name = fields.Many2one('res.users', string='Nombre completo',track_visibility="always")
    date = fields.Date(string="Fecha de solicitud")
    approver_id = fields.Many2one('ciberc.approver.knowledge',string="Aprobador")
    department_id = fields.Many2one('hr.department', string="Departamento")
    country_id = fields.Many2one('res.country',string="País ubicación de trabajo")
    email = fields.Char(string="Correo electrónico interno")
    knowledge = fields.Selection([('interno','Interno'),('externo','Externo')], string="Modalidad de capacitación/entrenamiento")
    kind_knowledge = fields.Selection([('habilidadestecnicas','Habilidades técnicas o actualización de conocimientos'),('habilidadesgerenciales','Habilidades gerenciales'),('nuevosmetodos','Nuevos metodos y procedimientos'),('habilidadesdeventas','Habilidades de ventas y/o servicio al cliente'),('otros','Otros')], string="Tipos de capacitaciones/entrenamientos")
    knowledge_application = fields.Selection([('diplomado','Diplomado'),('curso','Curso'),('seminario','Seminario'),('taller','Taller'),('examen','Examen'),('otro','Otro')], string="Solicitud de capacitación/entrenamiento")
    knowledge_application_details = fields.Text(string="Detalles de la solicitud de entrenamiento")
    knowledge_topic = fields.Text(string="Tema de capacitación/entrenamiento")
    knowledge_start = fields.Date(string="Fecha inicio")
    knowledge_end = fields.Date(string="Fecha fin")
    knowledge_time = fields.Integer(string="Duración de capacitacion/entrenamiento (hrs)")
    knowledge_cost = fields.Char(string="Costo de capacitacion/entrenamiento")
    currency_id = fields.Many2one('res.currency',string="Moneda")
    excuse = fields.Selection([('asociado','Asociado al proyecto'),('cumplimiento','Cumplimiento del rol'),('seguimiento','Seguimiento evaluación de desempeño'),('otro','Otro')],string="Justificación de capacitación/entrenamiento")
    excuse_details = fields.Text(string="Especificación de la justificación")

    exam_name_id = fields.Many2one('x_certificacion.conocimientos', string="Nombre del examen")
    partner = fields.Char(string="Tecnologia/partner")
    code_exam = fields.Char(string="Código del examen", size=10)
    cost_exam = fields.Char(string="Costo del examen")
    currency_two_id = fields.Many2one('res.currency',string="Moneda")
    date_exam = fields.Date(string="Fecha a presentar el examen")
    schedule_start = fields.Float(string="Hora de inicio")
    schedule_end = fields.Float(string="Hora de fin")
    place = fields.Char(string="Centro de evaluación")
    user = fields.Char(string="User")
    password = fields.Char(string="Password")
    pin = fields.Char(string="Test track pin")
    cost_centre_id = fields.Many2one('account.analytic.account', string="Centro de costo")
    #Campos para talento humano
    reason = fields.Selection([('duplicado','Duplicado'),('impertinente','No es pertinente')], string="Motivo de rechazo o de aplazamiento")
    reason_detail = fields.Text(string="Detalles del motivo")
    supplier_id = fields.Many2one('res.partner', domain=[('supplier','=',True)],string="Proveedor")
    final_cost = fields.Integer(string="Costo final")
    currency_three_id = fields.Many2one('res.currency',string="Moneda")
    deferment = fields.Boolean(string="¿Desea configurar fecha de aplazamiento?")
    deferment_date = fields.Date(string="Fecha de aplazamiento")
    #Campos para la validación
    tecnical_details = fields.Text(string="Observaciones de la validación técnica")
    #estados
    state = fields.Selection([('solicitud','Solicitud'),('validacion','Validación técnica'),('jefe','Jefe'),('talento','Talento Humano'),('pendiente','Pendiente de aprobación'),('aprobada','Aprobada'),('proceso','En proceso'),('rechazada','Rechazada'),('aplazada','Aplazada'),('terminada','Terminada')], string="Estado", track_visibility="always",default="solicitud")
    """
    def on_change_standard(self, cr, uid, ids, exam_name_id, context=None):
            student_obj = self.pool.get('x_certificacion.conocimientos')
            student_data = student_obj.browse(cr, uid, exam_name_id, context=context)
            return student_data
    """
    #Acciones para los botones
    @api.model
    def create(self, values):
        """
        employee = self.env['x_certificacion.conocimientos'].browse(self.exam_name_id)
        if 'employee.x_name' in 'CCIE':
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self).create(values)
            return line
        """
        
        if values ['exam_name_id'] == 38:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self).create(values)
            return line
        if values ['exam_name_id'] == 39:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self).create(values)
            return line
        if values ['exam_name_id'] == 40:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self).create(values)
            return line
        if values ['exam_name_id'] == 41:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self).create(values)
            return line
        if values ['exam_name_id'] == 42:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self).create(values)
            return line
        else:
            values['state'] = 'jefe'
            line = super(ciberc_knowledge, self).create(values)
            return line
        
    @api.one
    def action_valid_exam(self):
        self.write({
            'state': 'jefe',
        })

    @api.one
    def action_no_valid_exam(self):
        self.write({
            'state': 'rechazada',
        })

    @api.one
    def action_vobo(self):
        self.write({
            'state': 'talento',
        })

    @api.one
    def action_pendiente_aprobacion(self):
        self.write({
            'state': 'pendiente',
        })

    @api.one
    def action_aprobar(self):
        self.write({
            'state': 'aprobada',
        })

    @api.one
    def action_en_proceso(self):
        self.write({
            'state': 'proceso',
        })

    @api.one
    def action_terminada(self):
        self.write({
            'state': 'terminada',
        })

    @api.one
    def action_devolver(self):
        self.write({
            'state': 'solicitud',
        })

    @api.one
    def action_rechazar(self):
        self.write({
            'state': 'rechazada',
        })

    @api.one
    def action_aplazar(self):
        self.write({
            'state': 'aplazada',
        })



class ciberc_approver_knowledge (models.Model):
    _name="ciberc.approver.knowledge"
    _description= " Aprobador de la capacitacion"

    name = fields.Many2one('res.users', string='Nombre')
    email = fields.Char(string='Correo')
    user_odoo = fields.Char(string='Usuario Odoo')

class ciberc_evaluation_knowledge (models.Model):
    _name="ciberc.evaluation.knowledge"
    _description= "Evaluacion de la capacitacion"

    date = fields.Date(string='Fecha')
    name = fields.Many2one('res.users', string='Nombre')
    department_id = fields.Many2one('hr.department',string='Departamento')
    knowledge_topic_evaluation = fields.Char(string="Tema capacitación")
    applied = fields.Text(string="Aplicacion")
    evaluator_id = fields.Many2one('res.users',string="Evaluador")
