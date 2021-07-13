
from odoo import api, fields, models

from odoo.addons.http_routing.models.ir_http import slug
from collections import Counter, OrderedDict
from itertools import product


class Survey(models.Model):
    _inherit = "survey.survey"

    @api.model
    def get_input_appraisal_summary(self, question, current_filters=None, appraisal_id=None):
        """ Returns overall summary of question e.g. answered, skipped, total_inputs on basis of filter """
        current_filters = current_filters if current_filters else []
        result = {}
        if question.survey_id.user_input_ids:
            appraisal_input_ids = [appraisal_input for appraisal_input in question.survey_id.user_input_ids
                                   if appraisal_input.appraisal_id == appraisal_id]

            result['total_inputs'] = len(appraisal_input_ids)

            question_input_ids = []
            for user_input in question.user_input_line_ids:
                if not user_input.skipped:
                    question_input_ids.append(user_input.user_input_id)

            result['answered'] = len(set(question_input_ids) & set(appraisal_input_ids))
            result['skipped'] = result['total_inputs'] - result['answered']
        return result

    def prepare_appraisal_result(self, question, current_filters=None, appraisal_id=None):
        """ Compute statistical data for questions by counting number of vote per choice on basis of filter """
        current_filters = current_filters if current_filters else []
        result_summary = {}

        # Calculate and return statistics for choice
        if question.type in ['simple_choice', 'multiple_choice']:
            comments = []
            answers = OrderedDict(
                (label.id, {'text': label.value, 'count': 0, 'answer_id': label.id}) for label in question.labels_ids)
            for input_line in question.user_input_line_ids:
                if input_line.answer_type == 'suggestion' and answers.get(input_line.value_suggested.id) and (
                        not (current_filters) or input_line.user_input_id.id in current_filters) and input_line.user_input_id.appraisal_id == appraisal_id:
                    answers[input_line.value_suggested.id]['count'] += 1
                if input_line.answer_type == 'text' and (
                        not (current_filters) or input_line.user_input_id.id in current_filters) and input_line.user_input_id.appraisal_id == appraisal_id:
                    comments.append(input_line)
            result_summary = {'answers': list(answers.values()), 'comments': comments}

        # Calculate and return statistics for matrix
        if question.type == 'matrix':
            rows = OrderedDict()
            answers = OrderedDict()
            res = dict()
            comments = []
            [rows.update({label.id: label.value}) for label in question.labels_ids_2]
            [answers.update({label.id: label.value}) for label in question.labels_ids]
            for cell in product(rows, answers):
                res[cell] = 0
            for input_line in question.user_input_line_ids:
                if input_line.answer_type == 'suggestion' and (not (
                current_filters) or input_line.user_input_id.id in current_filters) and input_line.value_suggested_row and input_line.user_input_id.appraisal_id == appraisal_id:
                    res[(input_line.value_suggested_row.id, input_line.value_suggested.id)] += 1
                if input_line.answer_type == 'text' and (
                        not current_filters or input_line.user_input_id.id in current_filters) and input_line.user_input_id.appraisal_id == appraisal_id:
                    comments.append(input_line)
            result_summary = {'answers': answers, 'rows': rows, 'result': res, 'comments': comments}

        # Calculate and return statistics for free_text, textbox, date
        if question.type in ['free_text', 'textbox', 'date']:
            result_summary = []
            for input_line in question.user_input_line_ids:
                if not (current_filters or input_line.user_input_id.id in current_filters) and input_line.user_input_id.appraisal_id == appraisal_id:
                    result_summary.append(input_line)

        # Calculate and return statistics for numerical_box
        if question.type == 'numerical_box':
            result_summary = {'input_lines': []}
            all_inputs = []
            for input_line in question.user_input_line_ids:
                if not (current_filters or input_line.user_input_id.id in current_filters) and input_line.user_input_id.appraisal_id == appraisal_id:
                    all_inputs.append(input_line.value_number)
                    result_summary['input_lines'].append(input_line)
            if all_inputs and input_line.user_input_id.appraisal_id == appraisal_id:
                result_summary.update({'average': round(sum(all_inputs) / len(all_inputs), 2),
                                       'max': round(max(all_inputs), 2),
                                       'min': round(min(all_inputs), 2),
                                       'sum': sum(all_inputs),
                                       'most_common': Counter(all_inputs).most_common(5)})
        return result_summary


class AnswerAppraisal(models.Model):
    _inherit = 'survey.user_input'

    user_input_url = fields.Char()
    answerer_id = fields.Many2one('hr.employee', string='Answerer', readonly=True)

    @api.multi
    def action_appraisal_results(self):
        """ Open the website page with the appraisal results """
        self.ensure_one()
        self.user_input_url = '/appraisal/results/' + slug(self)
        return {
            'type': 'ir.actions.act_url',
            'name': "Appraisal Results",
            'target': 'new',
            'url': self.user_input_url
        }


