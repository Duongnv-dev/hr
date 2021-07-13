from odoo import models, fields, api, _
from datetime import datetime


class EmployeeDataExcelWizard(models.TransientModel):
    _name = 'employee.excel.wizard'
    _description = 'Wizard to export excel'

    name = fields.Char('Employees Data')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_ids = fields.Many2many('hr.department', string='Department')
    site_ids = fields.Many2many('hr.site', string='Location(Site)')

    @api.onchange('department_ids', 'site_ids')
    def onchange_employees(self):
        domain = []
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        if self.site_ids:
            domain.append(('site_id', 'in', self.site_ids.ids))
        employees = self.env['hr.employee'].search(domain)
        self.employee_ids = [(6, 0, employees.ids)]

    def export_employees_data_xlsx(self):
        return self.env.ref('bnk_employee.employees_data_export_excel').report_action(self)


class EmployeesDataXLSX(models.AbstractModel):
    _name = 'report.bnk_employee.export_employees_data_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, form):
        es = workbook.add_worksheet(_('Employees Data'))
        company = form.env.user.company_id
        title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 13,
            'text_wrap': True,
            'bold': True,
        })
        detail_wage = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 13,
            'text_wrap': True,
            'bold': False,
            'num_format': '#,##0.00',
        })
        detail_txt = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 13,
            'text_wrap': True,
            'bold': False,
        })
        detail_number = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 13,
            'text_wrap': True,
            'bold': False,
        })
        detail_no = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 13,
            'text_wrap': True,
            'bold': False,
            'num_format': '#',
        })
        self.set_sheet(es, company, title)
        self.write_data(es, form, detail_txt, detail_wage, detail_number, detail_no)

    def write_data(self, es, form, detail_txt, detail_wage, detail_number, detail_no):
        stt = 1
        row = 7
        employees = form.employee_ids
        for employee in employees:
            birthday = ''
            join_date = ''
            if employee.birthday:
                birthday = datetime.strftime(employee.birthday, '%Y-%m-%d')
            if employee.join_date:
                join_date = datetime.strftime(employee.join_date, '%Y-%m-%d')
            other_income = ''
            es.set_row(row, 25)
            es.write(row, 0, stt, detail_no)
            es.write(row, 1, employee.name, detail_txt)
            es.write(row, 2, birthday, detail_number)
            es.write(row, 3, employee.id_attendance, detail_number)
            es.write(row, 4, employee.work_email, detail_txt)
            es.write(row, 5, employee.contract_id.wage, detail_wage)
            es.write(row, 6, other_income, detail_txt)
            es.write(row, 7, join_date, detail_number)
            es.write(row, 8, employee.department_id.name or '', detail_txt)
            es.write(row, 9, employee.site_id.name, detail_txt)
            stt += 1
            row += 1
        return row

    def set_sheet(self, es, company, title):
        es.set_column(0, 0, 5)
        es.set_column(1, 1, 35)
        es.set_column(2, 2, 15)
        es.set_column(3, 3, 18)
        es.set_column(4, 4, 40)
        es.set_column(5, 5, 15)
        es.set_column(6, 6, 20)
        es.set_column(7, 7, 20)
        es.set_column(8, 8, 30)
        es.set_column(9, 9, 15)

        addr = ', '.join([x for x in [company.street, company.street2, company.city, company.state_id.name,
                                      company.country_id.name] if x is not False])
        es.merge_range(0, 0, 0, 3, company.name)
        es.merge_range(1, 0, 1, 3, addr)

        es.merge_range(5, 0, 6, 0, _('No.'), title)
        es.merge_range(5, 1, 6, 1, _('Employee Name'), title)
        es.merge_range(5, 2, 6, 2, _('Date Of Birth'), title)
        es.merge_range(5, 3, 6, 3, _('Attendance ID'), title)
        es.merge_range(5, 4, 6, 4, _('Work Email'), title)
        es.merge_range(5, 5, 6, 5, _('Gross Salary'), title)
        es.merge_range(5, 6, 6, 6, _('Other Income'), title)
        es.merge_range(5, 7, 6, 7, _('Join Date'), title)
        es.merge_range(5, 8, 6, 8, _('Department'), title)
        es.merge_range(5, 9, 6, 9, _('Location(Site)'), title)
