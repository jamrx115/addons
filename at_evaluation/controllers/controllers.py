import openerp.http as http
from openerp.http import request
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)
import werkzeug
import json
import random
from random import randrange
import uuid


class MyController(http.Controller):

    @http.route('/evaluation/<exam_slug>', type="http", auth="public", website=True)
    def take_exam(self, exam_slug):
        exam = http.request.env['at.evaluation'].sudo().search([('slug', '=', exam_slug)])[0]
        token = uuid.uuid4().__str__()
        exam_result = http.request.env['at.evaluation.result'].sudo().create(
            {'evaluation_id': exam.id, 'token': token, 'state': 'incomplete', 'user_id': request.env.user.id})
        if exam.fill_mode == "random":
            questions = random.sample(exam.questions, exam.fill_mode_random_number)
            for question in questions:
                # Add random question to result
                request.env['at.evaluation.result.question'].sudo().create(
                    {'result_id': exam_result.id, 'question': question.id})
        else:
            questions = exam.questions
            for question in questions:
                request.env['at.evaluation.result.question'].sudo().create({'result_id': exam_result.id, 'question': question.id})
        return werkzeug.utils.redirect("/evaluation/" + exam_slug + "/" + token)

    @http.route('/evaluation/content/<exam_slug>', type="http", auth="public", website=True)
    def exam_content(self, exam_slug):
        exam = http.request.env['at.evaluation'].sudo().search([('slug', '=', exam_slug)])[0]
        return http.request.render('at_evaluation.at_evaluation_content', {'exam': exam})

    @http.route('/evaluation/<exam_slug>/<string:token>', type="http", auth="public", website=True)
    def take_exam_token(self, exam_slug, token):
        exam = http.request.env['at.evaluation'].sudo().search([('slug', '=', exam_slug)])[0]
        exam_result = request.env['at.evaluation.result'].search([('token', '=', token)])
        if exam_result.state == "complete":
            return "This attempt has already been used up"
        else:
            questions = exam_result.results
            return http.request.render('at_evaluation.at_evaluation_question_page',
                                       {'exam': exam, 'questions': questions, 'token': token})

    @http.route('/evaluation/results', type="http", auth="public", website=True)
    def exam_result(self, **kwargs):
        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        exam_results = ""
        question_count = 0
        correct_count = 0
        exam_result = request.env['at.evaluation.result'].search([('token', '=', values['token'])])
        if request.env.user.partner_id.name != 'Public user':
            exam_result.user_id = request.env.user.id
        for result_question in exam_result.results:
            question_count += 1
            exam_question = result_question.question
            if exam_question.question_type == 'multi_choice':
                if result_question.question.num_correct > 1:
                    question_result = True
                    # Go through each option in the question
                    for option in exam_question.question_options:
                        post_name = "question" + str(exam_question.id) + "option" + str(option.id)
                        # They didn't have a checkbox checked for a correct option
                        if option.correct == True and (post_name in values) == False:
                            question_result = False
                        # They checked the wrong option
                        if option.correct == False and (post_name in values) == True:
                            question_result = False
                        if post_name in values:
                            request.env['at.evaluation.result.question.option'].sudo().create(
                                {'question_id': result_question.id, 'option_id': int(values[post_name])})
                    if question_result == True:
                        correct_count += 1
                    result_question.correct = question_result
                elif exam_question.num_correct == 1:
                    # Find the only correct option for the question
                    correct_option = request.env['at.evaluation.question.option'].search(
                        [('question_id', '=', exam_question.id), ('correct', '=', True)])[0].id
                    # They choose the correct option
                    if int(values["question" + str(exam_question.id)]) == int(correct_option):
                        question_result = True
                        correct_count += 1
                    else:
                        question_result = False
                    result_question.correct = question_result
                    request.env['at.evaluation.result.question.option'].sudo().create(
                        {'question_id': result_question.id,'option_id': int(values["question" + str(exam_question.id)])})
        percent = float(correct_count) / float(question_count) * 100
        if float(percent) >= float(exam_result.evaluation_id.approval_percentage):
            exam_result.approved = 'Si'
        else:
            exam_result.approved = 'No'
	exam_result.score = percent	
        exam_result.state = "complete"
        return request.render('at_evaluation.at_evaluation_results',{'exam_result': exam_result, 'question_count': question_count,
                               'correct_count': correct_count, 'percent': percent})
