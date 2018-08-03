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


class etq_results(models.Model):
    _name = "at.evaluation.result"
    _description = "Evaluation Result"

    evaluation_id = fields.Many2one('at.evaluation', string="Evaluación", readonly=True)
    user_id = fields.Many2one('res.users', string="Usuario")
    score = fields.Char(string="Puntaje", compute="_compute_score", store=True)
    results = fields.One2many('at.evaluation.result.question', 'result_id', string="Resultados", readonly=True)
    token = fields.Char(string="Token")
    state = fields.Selection([('incomplete', 'Incompleto'), ('complete', 'Completo')], string="Estado")
    approved = fields.Char(string="Aprobado?")

    @api.one
    @api.depends('results')
    def _compute_score(self):
        num_questions = self.env['at.evaluation.result.question'].search_count([('result_id', '=', self.id)])
	correct_questions = self.env['at.evaluation.result.question'].search_count(
            [('result_id', '=', self.id), ('correct', '=', True)])
	if(num_questions):
	        self.score = str(correct_questions) + "/" + str(num_questions) + " " + str(
        	    float(float(correct_questions) / float(num_questions)) * 100) + "%"


class etq_result_question(models.Model):
    _name = "at.evaluation.result.question"
    _description = "Evaluation Result Question"

    result_id = fields.Many2one('at.evaluation.result', string="Result", readonly=True)
    question = fields.Many2one('at.evaluation.question', string="Question", readonly=True)
    question_options = fields.One2many('at.evaluation.result.question.option', 'question_id', string="Options", readonly=True)
    correct = fields.Boolean(string="Correct", readonly=True)
    question_name = fields.Html(related="question.question", string="Question")


class etq_result_question_options(models.Model):
    _name = "at.evaluation.result.question.option"
    _desciption = "Evaluation Result Question Option"

    question_id = fields.Many2one('at.evaluation.result.question', string="Question ID", readonly=True)
    option_id = fields.Many2one('at.evaluation.question.option', string="Option", readonly=True)
    option_name = fields.Char(related="option_id.option", string="Option")
    question_options_value = fields.Char(string="Option Value", readonly=True)
