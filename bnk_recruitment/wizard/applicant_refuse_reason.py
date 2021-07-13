from odoo import api, fields, models


class ApplicantGetRefuseReason(models.TransientModel):
    _name = 'applicant.get.refuse.reason'
    _description = 'Get Refuse Reason'

    refuse_reason_id = fields.Many2one('hr.applicant.refuse.reason', 'Refuse Reason')
    applicant_ids = fields.Many2many('hr.applicant')

    @api.multi
    def action_refuse_reason_apply(self):
        return self.applicant_ids.write({'refuse_reason_id': self.refuse_reason_id.id, 'stage_id': self.env.ref('hr_recruitment.stage_job4').id})
