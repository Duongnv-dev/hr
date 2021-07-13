from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time
from calendar import monthrange


class PayslipBatch(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')

    def compute_sheet(self):
        t_start = time.time()
        self = self.with_context(from_batch=True)
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        exists_payslip_emp = []
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            result = self.env['hr.payslip'].check_overlap_payslip(False, from_date, to_date, employee)
            # override
            contracts = self.env['hr.payslip'].get_all_contract(employee, from_date, to_date)
            if not contracts:
                continue
            # contract_type = list(set([c.type_id.code for c in contracts]))
            if result:
                exists_payslip_emp.append(employee.name)
                continue
            if employee.is_trial_15:
                continue
            if len(contracts) > 1:
                payslips = self.split_payslip(contracts, from_date, to_date, employee, payslips, active_id, run_data)
            else:
                slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id,
                                                                        contract_id=False)
                res = {
                    'employee_id': employee.id,
                    'name': slip_data['value'].get('name'),
                    'struct_id': slip_data['value'].get('struct_id'),
                    'contract_id': slip_data['value'].get('contract_id'),
                    'payslip_run_id': active_id,
                    'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                    'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                    'date_from': from_date,
                    'date_to': to_date,
                    'credit_note': run_data.get('credit_note'),
                    'company_id': employee.company_id.id,
                }
                payslips += self.env['hr.payslip'].create(res)
        if exists_payslip_emp:
            payslip_run = self.env['hr.payslip.run'].browse(active_id)
            payslip_run.create_log_overlap(exists_payslip_emp)
        payslips.onchange_has_insurance_multi()
        payslips.compute_sheet()
        print('total time {}'.format(time.time() - t_start))
        return {'type': 'ir.actions.act_window_close'}

    def split_payslip(self, contracts, from_date, to_date, employee, payslips, active_id, run_data):
        contracts_in_period = []
        for cont in contracts:
            end_date = to_date
            if cont.date_end:
                end_date = cont.date_end
            if from_date <= cont.date_start and cont.date_start <= to_date:
                contracts_in_period.append([cont.date_start, cont])
            elif from_date <= end_date and end_date <= to_date:
                contracts_in_period.append([cont.date_start, cont])
            elif cont.date_start > from_date and end_date < to_date:
                contracts_in_period.append([cont.date_start, cont])
            elif cont.date_start < from_date and (cont.date_end > to_date or not cont.date_end):
                contracts_in_period.append([cont.date_start, cont])
        contracts_in_period.sort(key=lambda x: x[0])
        for cip in contracts_in_period:
            if cip[1].date_start == from_date:
                from_date_ = from_date
            else:
                from_date_ = max(cip[1].date_start, from_date)

            if cip[1].date_end == to_date:
                to_date_ = to_date
            elif cip[1].date_end:
                to_date_ = min(cip[1].date_end, to_date)
            else:
                to_date_ = to_date
            slip_data = self.env['hr.payslip'].onchange_employee_id(date_from=from_date_, date_to=to_date_,
                                                                    employee_id=employee.id,
                                                                    contract_id=cip[1].id)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': cip[1].id,
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date_,
                'date_to': to_date_,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        return payslips


class HrPayslipRunInherit(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']

    def create_log_overlap(self, exists_payslip_emp):
        for rec in self:
            rec.message_post(body='Exists Payslips of Employees: {}'.format(exists_payslip_emp))

    def send_email_batch(self):
        if not self.slip_ids:
            raise UserError(_('No payslip to send email'))
        sent = []
        for slip in self.slip_ids:
            slip.sudo().action_send_email_payslip()
            sent.append(slip.employee_id.name)
        self.message_post(body='Sent email salary for employee {}'.format(sent))
        return True

    @api.onchange('date_start')
    def onchange_period_end(self):
        if not self.date_start:
            return
        crr_year = self.date_start.year
        crr_mon = self.date_start.month
        end_date = '{}-{}-{}'.format(crr_year, crr_mon, monthrange(crr_year, crr_mon)[1])
        self.date_end = end_date
