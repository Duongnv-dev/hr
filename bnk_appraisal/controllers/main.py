
import json

from odoo import http, fields
from odoo.http import request
from odoo.tools import ustr
from math import ceil

from odoo.addons.survey.controllers.main import Survey


class BnKAppraisal(http.Controller):

    def page_range(self, total_record, limit):
        '''Returns number of pages required for pagination'''
        total = ceil(total_record / float(limit))
        return range(1, int(total + 1))

    @http.route(['/appraisal/results/<model("survey.user_input"):appraisal_answer>'],
                type='http', auth='user', website=True)
    def appraisal_reporting(self, appraisal_answer, token=None, **post):
        '''Display survey Results & Statistics for given survey.'''
        result_template = 'survey.result'
        current_filters = []
        filter_display_data = []
        filter_finish = False
        survey = appraisal_answer.survey_id
        appraisal_id = appraisal_answer.appraisal_id
        if not survey.user_input_ids or not [input_id.id for input_id in survey.user_input_ids if
                                             input_id.state != 'new']:
            result_template = 'survey.no_result'
        if 'finished' in post:
            post.pop('finished')
            filter_finish = True
        # if post or filter_finish:
        #     filter_data = self.get_filter_data(post)
        #     current_filters = survey.filter_input_ids(filter_data, filter_finish)
        #     filter_display_data = survey.get_filter_display_data(filter_data)
        survey_dict = self.prepare_result_appraisal_dict(survey, current_filters, appraisal_id)
        return request.render(result_template,
                              {'survey': survey,
                               'survey_dict': self.prepare_result_appraisal_dict(survey, current_filters, appraisal_id),
                               'page_range': self.page_range,
                               'current_filters': current_filters,
                               'filter_display_data': filter_display_data,
                               'filter_finish': filter_finish
                               })

    def prepare_result_appraisal_dict(self, survey, current_filters=None, appraisal_id=None):
        """Returns dictionary having values for rendering template"""
        current_filters = current_filters if current_filters else []
        Survey = request.env['survey.survey']
        result = {'page_ids': []}
        for page in survey.page_ids:
            page_dict = {'page': page, 'question_ids': []}
            for question in page.question_ids:
                question_dict = {
                    'question': question,
                    'input_summary': Survey.get_input_appraisal_summary(question, current_filters, appraisal_id),
                    'prepare_result': Survey.prepare_appraisal_result(question, current_filters, appraisal_id),
                    'graph_data': self.get_graph_data_appraisal(question, current_filters, appraisal_id),
                }

                page_dict['question_ids'].append(question_dict)
            result['page_ids'].append(page_dict)
        return result

    def get_graph_data_appraisal(self, question, current_filters=None, appraisal_id=None):
        '''Returns formatted data required by graph library on basis of filter'''
        # TODO refactor this terrible method and merge it with prepare_result_dict
        current_filters = current_filters if current_filters else []
        Survey = request.env['survey.survey']
        result = []
        if question.type == 'multiple_choice':
            result.append({'key': ustr(question.question),
                           'values': Survey.prepare_appraisal_result(question, current_filters, appraisal_id)['answers']
                           })
        if question.type == 'simple_choice':
            result = Survey.prepare_appraisal_result(question, current_filters, appraisal_id)['answers']
        if question.type == 'matrix':
            data = Survey.prepare_appraisal_result(question, current_filters, appraisal_id)
            for answer in data['answers']:
                values = []
                for row in data['rows']:
                    values.append({'text': data['rows'].get(row), 'count': data['result'].get((row, answer))})
                result.append({'key': data['answers'].get(answer), 'values': values})
        return json.dumps(result)


class CustomSurvey(Survey):

    def _check_state(self, user_input):
        '''Prevent opening of the survey if the state is cancel
        !This will NOT disallow access to users who have already partially filled the survey !'''
        state_cancel_id = request.env.ref('oh_appraisal.hr_appraisal_cancel').id
        if user_input.appraisal_id.state.id == state_cancel_id:
            return request.render("survey.notopen")
        return None

    @http.route(['/survey/start/<model("survey.survey"):survey>',
                 '/survey/start/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True)
    def start_survey(self, survey, token=None, **post):
        UserInput = request.env['survey.user_input']

        # Test mode
        if token and token == "phantom":
            _logger.info("[survey] Phantom mode")
            user_input = UserInput.create({'survey_id': survey.id, 'test_entry': True})
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.render('survey.survey_init', data)
        # END Test mode

        # Controls if the survey can be displayed
        errpage = self._check_bad_cases(survey, token=token)
        if errpage:
            return errpage

        # Manual surveying
        if not token:
            vals = {'survey_id': survey.id}
            if not request.env.user._is_public():
                vals['partner_id'] = request.env.user.partner_id.id
            user_input = UserInput.create(vals)
        else:
            user_input = UserInput.sudo().search([('token', '=', token)], limit=1)
            if not user_input:
                return request.render("survey.403", {'survey': survey})

        # Do not open expired survey

        errpage = self._check_deadline(user_input)
        if errpage:
            return errpage

        # Do not open if appraisal is Cancel
        errpage = self._check_state(user_input)
        if errpage:
            return errpage

        # Select the right page
        if user_input.state == 'new':  # Intro page
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.render('survey.survey_init', data)
        else:
            return request.redirect('/survey/fill/%s/%s' % (survey.id, user_input.token))

