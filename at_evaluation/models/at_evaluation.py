# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import requests
from openerp.http import request
from datetime import datetime
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
import unicodedata
import re

_logger = logging.getLogger(__name__)


class AtEvaluationExam(models.Model):
    _name = 'at.evaluation'

    name = fields.Char(string='Nombre',required=True)
    departments = fields.Many2many('hr.department',string="Departamentos",required=True)
    content = fields.Text(string='Contenido',required=True)
    time = fields.Integer(string='Tiempo',default="15",required=True)
    approval_percentage = fields.Float(string='Procentaje de aprobación',default="60",required=True)
    slug = fields.Char(string="Slug", compute="slug_me", store="True")
    show_correct_questions = fields.Boolean(string="Mostrar preguntas correctas?")
    questions = fields.One2many('at.evaluation.question', 'evaluation_id', string="Preguntas",required=True)
    fill_mode = fields.Selection([('all', 'Todas las preguntas'), ('random', 'Random')], string="Modo de llenado", default="all")
    fill_mode_random_number = fields.Integer(string="Número de preguntas aleatorias")

    @api.onchange('fill_mode')
    def _onchange_fill_mode(self):
        if self.fill_mode == "random":
            self.fill_mode_random_number = len(self.questions)

    @api.multi
    def results(self):
        return "hola"

    @api.multi
    def view_quiz(self):
        quiz_url = request.httprequest.host_url + "evaluation/content/" + str(self.slug)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': quiz_url
        }

    @api.one
    @api.depends('name')
    def slug_me(self):
        if self.name:
            s = ustr(self.name)
            uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
            slug = re.sub('[\W_]', ' ', uni).strip().lower()
            slug = re.sub('[-\s]+', '-', slug)
            self.slug = slug


class AtQuestion(models.Model):
    _name = "at.evaluation.question"
    _rec_name = "question"

    evaluation_id = fields.Many2one('at.evaluation', string="Evaluación ID")
    image = fields.Binary(string="Imagen")
    question = fields.Html(string="Pregunta")
    question_rendered = fields.Html(string="Visualizaciòn de pregunta", compute="render_question")
    question_type = fields.Selection([('multi_choice', 'Selección múltiple')],default="multi_choice", string="Tipo de pregunta")
    question_options = fields.One2many('at.evaluation.question.option', 'question_id', string="Selección múltiple")
    num_options = fields.Integer(string="Opciones", compute="calc_options")
    num_correct = fields.Integer(string="Correcta opción", compute="calc_correct")

    @api.one
    @api.depends('question')
    def render_question(self):
        if self.question:
            temp_string = self.question
            temp_string = temp_string.replace("{1}", "<i><input name=\"question" + str(
                self.id) + "option1\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{2}", "<i><input name=\"question" + str(
                self.id) + "option2\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{3}", "<i><input name=\"question" + str(
                self.id) + "option3\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{4}", "<i><input name=\"question" + str(
                self.id) + "option4\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{5}", "<i><input name=\"question" + str(
                self.id) + "option5\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{6}", "<i><input name=\"question" + str(
                self.id) + "option6\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{7}", "<i><input name=\"question" + str(
                self.id) + "option7\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{8}", "<i><input name=\"question" + str(
                self.id) + "option8\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{9}", "<i><input name=\"question" + str(
                self.id) + "option9\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            self.question_rendered = temp_string

    @api.one
    @api.depends('question_options')
    def calc_options(self):
        self.num_options = self.question_options.search_count([('question_id', '=', self.id)])

    @api.one
    @api.depends('question_options')
    def calc_correct(self):
        self.num_correct = self.question_options.search_count([('question_id', '=', self.id), ('correct', '=', True)])


class AtQuestionOptions(models.Model):
    _name = "at.evaluation.question.option"
    _rec_name = "option"

    question_id = fields.Many2one('at.evaluation.question', string="Question ID")
    option = fields.Char(string="Opción")
    correct = fields.Boolean(string="Correcta")
