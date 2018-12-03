# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime
from odoo.exceptions import UserError
from openerp.exceptions import except_orm, Warning, RedirectWarning

import re
import logging

_logger = logging.getLogger(__name__)

class ciberc_knowledge (models.Model):
    _name="ciberc.knowledge"
    _description= "Solicitud de capacitacion"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Many2one('res.users', string='Nombre completo',track_visibility="onchange")
    date = fields.Date(string="Fecha de solicitud", track_visibility="onchange")
    approver_id = fields.Many2one('ciberc.approver.knowledge',string="Aprobador", track_visibility="onchange")
    department_id = fields.Many2one('hr.department', string="Departamento", track_visibility="onchange")
    country_id = fields.Many2one('res.country',string="País ubicación de trabajo")
    email = fields.Char(string="Correo electrónico interno",related="name.employee_ids.work_email",store=True, copy=True)
    knowledge = fields.Selection([('interno','Interno'),('externo','Externo')], string="Modalidad de capacitación/entrenamiento", track_visibility="onchange")
    kind_knowledge = fields.Selection([('habilidadestecnicas','Habilidades técnicas o actualización de conocimientos'),('habilidadesgerenciales','Habilidades gerenciales'),('nuevosmetodos','Nuevos metodos y procedimientos'),('habilidadesdeventas','Habilidades de ventas y/o servicio al cliente'),('otros','Otros')], string="Tipos de capacitaciones/entrenamientos")
    knowledge_application = fields.Selection([('diplomado','Diplomado'),('curso','Curso'),('seminario','Seminario'),('taller','Taller'),('examen','Examen'),('otro','Otro')], string="Solicitud de capacitación/entrenamiento", track_visibility="onchange")
    knowledge_application_details = fields.Text(string="Detalles de la solicitud de entrenamiento")
    knowledge_topic = fields.Char(string="Tema de capacitación/entrenamiento", track_visibility="onchange")
    knowledge_start = fields.Date(string="Fecha inicio")
    knowledge_end = fields.Date(string="Fecha fin")
    knowledge_time = fields.Integer(string="Duración de capacitacion/entrenamiento (hrs)")
    knowledge_cost = fields.Float(string="Costo de capacitacion/entrenamiento", digits=(15,2))
    currency_id = fields.Many2one('res.currency',string="Moneda")
    excuse = fields.Selection([('asociado','Asociado al proyecto'),('cumplimiento','Cumplimiento del rol'),('seguimiento','Seguimiento evaluación de desempeño'),('otro','Otro')],string="Justificación de capacitación/entrenamiento")
    excuse_details = fields.Text(string="Especificación de la justificación")
    #Campos para cuando se seleccione la opción de "examen"
    exam_name_id = fields.Many2one('x_certificacion.conocimientos', string="Nombre del examen")
    partner = fields.Char(string="Tecnologia/partner")
    code_exam = fields.Char(string="Código del examen", size=10)
    cost_exam = fields.Float(string="Costo del examen",digits=(15,2))
    currency_two_id = fields.Many2one('res.currency',string="Moneda")
    date_exam = fields.Date(string="Fecha a presentar el examen")
    schedule_start = fields.Float(string="Hora de inicio")
    schedule_end = fields.Float(string="Hora de fin")
    place = fields.Char(string="Centro de evaluación")
    user = fields.Char(string="User")
    password = fields.Char(string="Password")
    pin = fields.Char(string="Test track pin")
    cost_centre_id = fields.Char(string="Centro de costo")
    #Campos para los otros actores del proceso
    reason = fields.Many2one('ciberc.reasons', string="Motivo de rechazo o de aplazamiento")
    reason_detail = fields.Text(string="Detalles del motivo")
    supplier_id = fields.Many2one('res.partner', domain=[('supplier','=',True)],string="Proveedor")
    final_cost = fields.Float(string="Costo final", digits=(15,2))
    currency_three_id = fields.Many2one('res.currency',string="Moneda")
    deferment = fields.Boolean(string="¿Desea configurar fecha de aplazamiento?")
    deferment_date = fields.Date(string="Fecha de aplazamiento")
    #Campos para la validación
    tecnical_details = fields.Text(string="Observaciones de la validación técnica")
    #estados
    state = fields.Selection([('solicitud','Solicitud'),('validacion','Validación técnica'),('jefe','Jefe'),('talento','Talento Humano'),('pendiente','Pendiente de aprobación'),('aprobada','Aprobada'),('proceso','En proceso'),('rechazada','Rechazada'),('aplazada','Aplazada'),('terminada','Terminada')], string="Estado", track_visibility="onchange",default="solicitud")
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
            line = super(ciberc_knowledge, self.with_context(mail_create_nosubscribe=True)).create(values)
            if line:
                template_id = self.env.ref('ciberc_knowledge.knowledge_email_template_tecnical')
            if template_id:
                self.env['mail.template'].browse(template_id.id).send_mail(line.id)
            return line
        if values ['exam_name_id'] == 39:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self.with_context(mail_create_nosubscribe=True)).create(values)
            if line:
                template_id = self.env.ref('ciberc_knowledge.knowledge_email_template_tecnical')
            if template_id:
                self.env['mail.template'].browse(template_id.id).send_mail(line.id)
            return line
        if values ['exam_name_id'] == 40:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self.with_context(mail_create_nosubscribe=True)).create(values)
            if line:
                template_id = self.env.ref('ciberc_knowledge.knowledge_email_template_tecnical')
            if template_id:
                self.env['mail.template'].browse(template_id.id).send_mail(line.id)
            return line
        if values ['exam_name_id'] == 41:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self.with_context(mail_create_nosubscribe=True)).create(values)
            if line:
                template_id = self.env.ref('ciberc_knowledge.knowledge_email_template_tecnical')
            if template_id:
                self.env['mail.template'].browse(template_id.id).send_mail(line.id)
            return line
        if values ['exam_name_id'] == 42:
            values['state'] = 'validacion'
            line = super(ciberc_knowledge, self.with_context(mail_create_nosubscribe=True)).create(values)
            if line:
                template_id = self.env.ref('ciberc_knowledge.knowledge_email_template_tecnical')
            if template_id:
                self.env['mail.template'].browse(template_id.id).send_mail(line.id)
            return line
        else:
            values['state'] = 'jefe'
            line = super(ciberc_knowledge, self.with_context(mail_create_nosubscribe=True)).create(values)
            if line:
                template_id = self.env.ref('ciberc_knowledge.knowledge_email_template_boss')
            if template_id:
                self.env['mail.template'].browse(template_id.id).send_mail(line.id)
            return line
        
    @api.multi
    def action_valid_exam(self):
        
        if self.tecnical_details == False:
            raise UserError('Primero debe ingresar las observaciones técnicas')
        else:
            # Find the e-mail template
            template = self.env.ref('ciberc_knowledge.knowledge_email_template_boss')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id)
            self.write({
                'state': 'jefe',
            })

    @api.one
    def action_no_valid_exam(self):
        if self.tecnical_details == False:
            raise UserError('Primero debe ingresar las observaciones técnicas')
        else:
            # Find the e-mail template
            template = self.env.ref('ciberc_knowledge.knowledge_email_template_rejected')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id)
            self.write({
                'state': 'rechazada',
            })

    @api.one
    def action_vobo(self):
        # Find the e-mail template
        template = self.env.ref('ciberc_knowledge.knowledge_email_template_human_services')
        # Send out the e-mail template to the user
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.write({
            'state': 'talento',
        })

    @api.one
    def action_pendiente_aprobacion(self):
        # Find the e-mail template
        template = self.env.ref('ciberc_knowledge.knowledge_email_template_management')
        # Send out the e-mail template to the user
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.write({
            'state': 'pendiente',
        })

    @api.one
    def action_aprobar(self):
        # Find the e-mail template
        template = self.env.ref('ciberc_knowledge.knowledge_email_template_approved')
        # Send out the e-mail template to the user
        self.env['mail.template'].browse(template.id).send_mail(self.id)
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
            'state': 'jefe',
        })

    @api.one
    def action_rechazar(self):
        if self.reason == False:
            raise UserError('Primero debe ingresar un motivo')
        else:
            # Find the e-mail template
            template = self.env.ref('ciberc_knowledge.knowledge_email_template_rejected')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id)
            self.write({
                'state': 'rechazada',
            })

    @api.one
    def action_aplazar(self):
        if self.reason == False:
            raise UserError('Primero debe ingresar un motivo')
        else:
            # Find the e-mail template
            template = self.env.ref('ciberc_knowledge.knowledge_email_template_deferment')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id)
            self.write({
                'state': 'aplazada',
            })

    @api.multi
    def action_request_documents(self):
        # Find the e-mail template
        template = self.env.ref('ciberc_knowledge.knowledge_email_template_documents')
        # Send out the e-mail template to the user
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.onchange('name')
    def _onchange_employee_work_email(self):
        self.email = self.name.employee_ids.work_email
        

class ciberc_approver_knowledge (models.Model):
    _name="ciberc.approver.knowledge"
    _description= " Aprobador de la capacitacion"

    name = fields.Many2one('res.users', string='Nombre')
    email = fields.Char(string='Correo')
    user_odoo = fields.Char(string='Usuario Odoo')

class ciberc_evaluation_knowledge (models.Model):
    _name="ciberc.evaluation.knowledge"
    _description= "Evaluacion de la capacitacion"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    date = fields.Date(string='Fecha', track_visibility="onchange")
    knowledge_topic_evaluation = fields.Char(string="Capacitación/entrenamiento", track_visibility="onchange")
    name = fields.Many2one('res.users', string='Nombre', track_visibility="onchange")
    job_id = fields.Many2one('hr.job',string="Puesto", track_visibility="onchange")
    department_id = fields.Many2one('hr.department',string='Departamento', track_visibility="onchange")

    question1 = fields.Selection([('malo','Malo'),('regular','Regular'),('bueno','Bueno'),('excelente','Excelente')],string="1. Antes de esta capacitación, mi nivel de conocimientos o competencias para el objetivo de este curso era:")
    question1_details = fields.Text(string="1. Detalles")
    question2 = fields.Selection([('malo','Malo'),('regular','Regular'),('bueno','Bueno'),('excelente','Excelente')],string="2. Después de esta capacitación mi nivel de conocimientos o competencias para el objetivo de este curso será:")
    question2_details = fields.Text(string="2. Detalles")
    question3 = fields.Selection([('25','25%'),('50','50%'),('75','75%'),('100','100%')],string="3. Estime que porcentaje de lo aprendido en esta capacitación podrá aplicar en su trabajo:")
    question3_details = fields.Text(string="3. Detalles")
    question4 = fields.Selection([('bajo','Bajo'),('medio','Medio'),('medioalto','Medio Alto'),('alto','Alto')],string="4. Seleccione el nivel de importancia del contenido de la capacitación en relación con su trabajo actual:")
    question4_details = fields.Text(string="4. Detalles")
    question5 = fields.Selection([('insatisfecho','Insatisfecho'),('poco','Poco satisfecho'),('satisfecho','Satisfecho'),('muy','Muy satisfecho')],string="5. Que tan satisfecho se encuentra con las herramientas brindadas por la capacitación para el desarrollo de su trabajo:")
    question5_details = fields.Text(string="5. Detalles")
    question6 = fields.Selection([('adicionar','Adicionar'),('darmas','Dar más énfasis'),('darmenos','Dar menos énfasis'),('suprimir','Suprimir')],string="6. Para mejorar futuras capacitaciones indique los temas a los cuales se les podría: ")
    question6_details = fields.Text(string="6. Detalles")

    applied = fields.Text(string="Aplicación")
    observations = fields.Text(string="Observaciones")
    
    @api.model
    def create(self, values):
        #Funcion que cancela la suscripción automatica de seguidores en el documento en el momento de la creación.
        res = super(ciberc_evaluation_knowledge,self.with_context(mail_create_nosubscribe=True)).create(values)
        return res

    @api.one
    @api.constrains('question1','question2','question3','question4','question5','question6')
    def _check_value(self):
        if self.question1 == False:
            raise exceptions.ValidationError("Debe ingresar una respuesta a la pregunta 1")
        elif self.question2 == False:
            raise exceptions.ValidationError("Debe ingresar una respuesta a la pregunta 2")
        elif self.question3 == False:
            raise exceptions.ValidationError("Debe ingresar una respuesta a la pregunta 3")
        elif self.question4 == False:
            raise exceptions.ValidationError("Debe ingresar una respuesta a la pregunta 4")
        elif self.question5 == False:
            raise exceptions.ValidationError("Debe ingresar una respuesta a la pregunta 5")
        elif self.question6 == False:
            raise exceptions.ValidationError("Debe ingresar una respuesta a la pregunta 6")

class reasons (models.Model):
    _name="ciberc.reasons"
    _description= "Razones de rechazo"

    name = fields.Char(string='Nombre')

    @api.multi
    def unlink(self):
        range_obj = self.env['ciberc.knowledge']
        rule_ranges = range_obj.search([('reason', 'in', self.ids)])
        if len(rule_ranges) > 1:
            raise Warning(_("¡Está tratando de eliminar un motivo de rechazo que aun está siendo usado!"))
        return super(reasons, self).unlink()