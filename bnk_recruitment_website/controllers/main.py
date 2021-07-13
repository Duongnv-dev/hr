from odoo import http, SUPERUSER_ID, _
import datetime
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment

class WebsiteFormInherit(WebsiteForm):
    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        return super(WebsiteFormInherit, self).website_form(model_name, **kwargs)

    def insert_attachment(self, model, id_record, files):
        res = super(WebsiteFormInherit, self).insert_attachment(model, id_record, files)
        model_name = model.sudo().model
        record = model.env[model_name].browse(id_record)
        today = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if model_name == 'hr.applicant':
            for file in files:
                for attachment in record.attachment_ids:
                    data = attachment.datas.decode()
                    record.write({
                        'cv_file_name': '{}_{}'.format(today, file.filename),
                        'cv_data': data
                    })
        else:
            return res

class WebsiteHrRecruitmentInherit(WebsiteHrRecruitment):
    @http.route('''/jobs/apply/<model("hr.job"):job>''', type='http', auth="public", website=True, sitemap=True)
    def jobs_apply(self, job, **kwargs):
        res = super(WebsiteHrRecruitmentInherit, self).jobs_apply(job, **kwargs)
        categories = request.env['hr.applicant.category'].search([])
        site_ids = request.env['hr.site'].search([])
        error = {}
        default = {}
        if categories and site_ids:
            return request.render("website_hr_recruitment.apply", {
                'job': job,
                'error': error,
                'default': default,
                'categories': categories,
                'site_ids': site_ids,
            })
        return res
