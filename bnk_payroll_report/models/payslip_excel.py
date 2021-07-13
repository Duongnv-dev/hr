# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class PayslipExcelWizard(models.TransientModel):
    _name = 'payslip.excel.wizard'
    _description = 'Wizard to export excel'

    name = fields.Char('Payslip Export')
    payslip_batch_id = fields.Many2one('hr.payslip.run', 'Payslip Batch')
    department_id = fields.Many2one('hr.department')
    line_ids = fields.Many2many('hr.payslip', 'payslip_excel_wizard_rel', 'wizard_id', 'payslip_id')
    month = fields.Many2one('hr.payroll.month')

    @api.onchange('month')
    def onchange_payslip_line(self):
        domain = []
        if self.month:
            domain.append(('month', '=', self.month.id))
            pays = self.env['hr.payslip'].search(domain)
            self.line_ids = [(6, 0, pays.ids)]
        else:
            self.line_ids = [(5, )]

    def export_payroll(self):
        return self.env.ref('bnk_payroll_report.payslip_export_excel').report_action(self)


class ReportInvoiceXlsx(models.AbstractModel):
    _name = "report.bnk_payroll_report.export_payroll"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, form):
        ws1 = workbook.add_worksheet('TONG LUONG THUC TE CHI')
        ws2 = workbook.add_worksheet('LUONG THUE')
        ws3 = workbook.add_worksheet('LUONG VANG LAI')
        ws4 = workbook.add_worksheet('FORMULA LUONG GOI BANK')
        ws5 = workbook.add_worksheet('ROUND NUMBER FOR BANK')
        title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 13,
            'text_wrap': True,
            'bold': True,
        })
        small_title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bold': True,
        })
        title_top = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 16,
            'text_wrap': False,
            'bold': True,
        })
        detail_number = workbook.add_format({
            'valign': 'vcenter',
            'align': 'right',
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
        cat_title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 14,
            'text_wrap': True,
            'bold': True,
            'bg_color': '03A9E3',
        })
        cat_color_title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 14,
            'text_wrap': True,
            'bold': True,
            'bg_color': 'FFFF00',
        })
        top = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 18,
            'text_wrap': True,
            'bold': True,
        })
        top_no_border = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 18,
            'text_wrap': True,
            'bold': True,
        })
        top_date = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 16,
            'text_wrap': True,
            'bold': True,
        })
        detail_no_border = workbook.add_format({
            'align': 'center',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 13,
            'text_wrap': False,
            'bold': True,
        })

        company = form.env.user.company_id
        self.set_sheet_one(ws1, title, company, form.month, top, top_date, title_top)
        self.set_sheet_two(ws2, title, company, form.month, top, top_date, title_top)
        self.set_sheet_three(ws3, title, top_no_border)
        self.set_sheet_four(ws4, title, top_no_border)

        # detail
        stt_total1 = 1
        stt_total2 = 1
        row1 = 7
        row2 = 7

        roman_number = 1
        payslip_dict = {'Unassign': [], 'Contributor': []}
        for line in form.line_ids:
            if line.contract_id.type_id.code == 'contributor':
                payslip_dict['Contributor'].append(line)
            elif not line.department_id:
                payslip_dict['Unassign'].append(line)
            elif line.department_id.name in payslip_dict.keys():
                payslip_dict[line.department_id.name].append(line)
            else:
                payslip_dict[line.department_id.name] = [line,]

        for key in payslip_dict.keys():
            if key == 'Contributor':
                continue
            roman_txt = self.get_roman_number(roman_number)
            roman_number += 1
            self.write_category(ws1, key, roman_txt, row1, cat_title, col=43)
            row1 += 1

            stt_total1, row1 = self.write_detail(ws1, payslip_dict[key], stt_total1, row1, title, detail_txt,
                                                 detail_number)

            self.write_category(ws2, key, roman_txt, row2, cat_color_title, col=32)
            row2 += 1
            stt_total2, row2 = self.write_detail_sheet_two(ws2, payslip_dict[key], stt_total2, row2, title, detail_txt,
                                                 detail_number)
        self.write_detail_contributor(ws3, payslip_dict['Contributor'], detail_txt, detail_number)
        self.write_detail_sheet_four(ws4, form.line_ids, small_title, detail_number, detail_no_border, detail_txt)

    def get_day(self, payslip):
        worked_day = 0
        for line in payslip.worked_days_line_ids:
            if line.code.startswith('WORK100') or line.code.startswith('PUBLIC') or line.code.startswith('LEGAL'):
                worked_day += line.number_of_days
        return {'worked_day': worked_day}

    def get_insurance(self, payslip):
        bhxh = bhyt = bhtn = 0
        bhxhdn = bhytdn = bhtndn = 0
        for line in payslip.line_ids:
            if line.code == 'BHXH':
                bhxh = line.total
            elif line.code == 'BHYT':
                bhyt = line.total
            elif line.code == 'BHTN':
                bhtn = line.total
            elif line.code == 'DNBHXH':
                bhxhdn = line.total
            elif line.code == 'DNBHYT':
                bhytdn = line.total
            elif line.code == 'DNBHTN':
                bhtndn = line.total
        return {'xh': bhxh, 'yt': bhyt, 'tn': bhtn, 'xhdn': bhxhdn, 'ytdn': bhytdn, 'tndn': bhtndn}

    def get_salary(self, payslip):
        wage = ot = 0
        pcn = pct = 0
        ttnt = gt = tntt = ttncn = 0
        sbl = sep = oip = 0
        cash = bank = 0
        wage_by_mon = 0
        for line in payslip.line_ids:
            if line.code == 'WAGB':
                wage = line.total
            elif line.code in ['OTT', 'OTNT']:
                ot += line.total
            elif line.code == 'PCN':
                pcn = line.total
            elif line.code == 'PCT':
                pct = line.total
            elif line.code == 'TTNT':
                ttnt = line.total
            elif line.code == 'GTTCN':
                gt = line.total
            elif line.code == 'TNTT':
                tntt = line.total
            elif line.code == 'TTNCN':
                ttncn = line.total
            elif line.code == 'SBL':
                sbl = line.total
            elif line.code == 'SEP':
                sep = line.total
            elif line.code == 'OIP':
                oip = line.total
            elif line.code == 'SCA':
                cash = line.total
            elif line.code == 'TLB':
                bank = line.total
            elif line.code == 'WAGE':
                wage_by_mon = line.total

        result = {
            'wage': wage, 'ot': ot, 'pcn': pcn, 'pct': pct, 'ttnt': ttnt, 'gt': gt, 'tntt': tntt,
            'ttncn': ttncn, 'sbl': sbl, 'sep': sep, 'oip': oip, 'cash': cash, 'bank': bank, 'wage_by_mon': wage_by_mon
        }
        return result

    def get_roman_number(self, number):
        if number == 1:
            roman_text = 'I'
        elif number == 2:
            roman_text = 'II'
        elif number == 3:
            roman_text = 'III'
        elif number == 4:
            roman_text = 'IV'
        elif number == 5:
            roman_text = 'V'
        elif number == 6:
            roman_text = 'VI'
        elif number == 7:
            roman_text = 'VII'
        elif number == 8:
            roman_text = 'VII'
        elif number == 9:
            roman_text = 'IX'
        elif number == 10:
            roman_text = 'X'

        return roman_text

    def get_project(self, line):
        date_from = datetime.strftime(line.date_from, '%Y-%m-%d')
        date_to = datetime.strftime(line.date_to, '%Y-%m-%d')
        allocates = self.env['allocate.resource'].search([
            ('employee_id', '=', line.employee_id.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])
        if not allocates:
            return []
        list_projects = []
        for al in allocates:
            if al.project_id.name not in list_projects:
                list_projects.append(al.project_id.name)
        return list_projects

    def write_category(self, ws, key, roman_txt, row, title_format, col):
        ws.set_row(row, 40)
        ws.write(row, 0, roman_txt, title_format)
        ws.write(row, 1, 'SL', title_format)
        ws.write(row, 2, key, title_format)
        ws.write(row, 3, key, title_format)
        for c in range(4, col):
            ws.write(row, c, '', title_format)

    def write_detail(self, ws1, value, total_stt, row, title, detail_txt, detail_number):
        stt = 1
        for line in value:
            workday = self.get_day(line)
            insurance = self.get_insurance(line)
            salary = self.get_salary(line)
            salary_day = 0

            projects = self.get_project(line)
            projects = ', '.join(projects)

            if workday['worked_day']:
                salary_day = salary['wage'] / workday['worked_day']
            ws1.set_row(row, 30)
            ws1.write(row, 0, total_stt, detail_txt)
            ws1.write(row, 1, stt, detail_txt)
            ws1.write(row, 2, line.employee_id.name, detail_txt)
            ws1.write(row, 3, line.employee_id.name, detail_txt)
            ws1.write(row, 4, line.contract_id.type_id.name, detail_txt)
            ws1.write(row, 5, projects, detail_txt)
            ws1.write(row, 6, '', detail_number)  # Tong luong
            ws1.write(row, 7, line.contract_id.insurance_salary, detail_number)  # Luong co ban
            ws1.write(row, 8, salary['wage'] - line.contract_id.insurance_salary, detail_number)  # Luong nang suat
            ws1.write(row, 9, salary['wage'], detail_number)
            ws1.write(row, 10, salary_day, detail_number)
            ws1.write(row, 11, workday['worked_day'], title)
            ws1.write(row, 12, salary['pcn'], detail_number)
            ws1.write(row, 13, salary['ot'], detail_number)
            ws1.write(row, 14, salary['pct'], detail_number)
            ws1.write(row, 15, salary['wage'] + salary['pcn'] + salary['ot'] + salary['pct'], detail_number)
            ws1.write(row, 16, insurance['xhdn'], detail_number)
            ws1.write(row, 17, insurance['ytdn'], detail_number)
            ws1.write(row, 18, insurance['tndn'], detail_number)
            ws1.write(row, 19, 0, detail_number)
            ws1.write(row, 20, insurance['xhdn'] + insurance['ytdn'] + insurance['tndn'], detail_number)
            ws1.write(row, 21, insurance['xh'], detail_number)
            ws1.write(row, 22, insurance['yt'], detail_number)
            ws1.write(row, 23, insurance['tn'], detail_number)
            ws1.write(row, 24, 0, detail_number)
            ws1.write(row, 25, insurance['xh'] + insurance['yt'] + insurance['tn'], detail_number)
            ws1.write(row, 26, salary['ttnt'], detail_number)  # Thu nhap chiu thue
            ws1.write(row, 27, salary['gt'], detail_number)
            ws1.write(row, 28, salary['pcn'], detail_number)
            ws1.write(row, 29, '', detail_number)
            ws1.write(row, 30, salary['tntt'], detail_number)
            ws1.write(row, 31, salary['ttncn'], detail_number)
            ws1.write(row, 32, salary['sbl'], detail_number)
            ws1.write(row, 33, salary['oip'], detail_number)
            ws1.write(row, 34, salary['cash'] + salary['bank'], detail_number)
            ws1.write(row, 35, salary['cash'], detail_number)
            ws1.write(row, 36, salary['bank'], detail_number)
            ws1.write(row, 37, '', detail_number)
            ws1.write(row, 38, salary['sep'], detail_number)
            ws1.write(row, 39, '', detail_number)
            ws1.write(row, 40, '', detail_txt)
            ws1.write(row, 41, '', detail_txt)
            ws1.write(row, 42, line.employee_id.site_id.name or '', detail_txt)
            stt += 1
            row += 1
            total_stt += 1
        return total_stt, row

    def write_detail_sheet_two(self, ws, value, total_stt, row, title, detail_txt, detail_number):
        stt = 1
        for line in value:
            workday = self.get_day(line)
            insurance = self.get_insurance(line)
            salary = self.get_salary(line)
            projects = self.get_project(line)
            projects = ', '.join(projects)

            ws.set_row(row, 30)
            ws.write(row, 0, total_stt, detail_txt)
            ws.write(row, 1, stt, detail_txt)
            ws.write(row, 2, line.employee_id.name, detail_txt)
            ws.write(row, 3, line.employee_id.name, detail_txt)
            ws.write(row, 4, projects, detail_txt)
            ws.write(row, 5, line.contract_id.insurance_salary, detail_number)  # Luong co ban
            ws.write(row, 6, salary['wage'] - line.contract_id.insurance_salary, detail_number)
            ws.write(row, 7, salary['wage'], detail_number)
            ws.write(row, 8, workday['worked_day'], title)
            ws.write(row, 9, salary['pcn'], detail_number)
            ws.write(row, 10, salary['ot'], detail_number)
            ws.write(row, 11, salary['pct'], detail_number)
            ws.write(row, 12, salary['wage'] + salary['pcn'] + salary['ot'] + salary['pct'], detail_number)
            ws.write(row, 13, insurance['xhdn'], detail_number)
            ws.write(row, 14, insurance['ytdn'], detail_number)
            ws.write(row, 15, insurance['tndn'], detail_number)
            ws.write(row, 16, 0, detail_number)
            ws.write(row, 17, insurance['xhdn'] + insurance['ytdn'] + insurance['tndn'], detail_number)
            ws.write(row, 18, insurance['xh'], detail_number)
            ws.write(row, 19, insurance['yt'], detail_number)
            ws.write(row, 20, insurance['tn'], detail_number)
            ws.write(row, 21, 0, detail_number)
            ws.write(row, 22, insurance['xh'] + insurance['yt'] + insurance['tn'], detail_number)
            ws.write(row, 23, salary['gt'], detail_number)
            ws.write(row, 24, salary['pcn'], detail_number)
            ws.write(row, 25, salary['tntt'], detail_number)
            ws.write(row, 26, salary['ttncn'], detail_number)
            ws.write(row, 27, line.personal_tax_number or '', detail_txt)
            ws.write(row, 28, salary['sbl'], detail_number)
            ws.write(row, 29, salary['cash'] + salary['bank'], detail_number)
            ws.write(row, 30, salary['cash'], detail_number)
            ws.write(row, 31, salary['bank'], detail_number)
            stt += 1
            row += 1
            total_stt += 1
        return total_stt, row

    def write_detail_contributor(self, ws, line_ids, detail_txt, detail_number):
        stt = 1
        row = 4
        for line in line_ids:
            salary = self.get_salary(line)
            ttn = salary['wage'] + salary['pcn'] + salary['ot'] + salary['pct'] + salary['wage_by_mon']
            ws.write(row, 0, stt, detail_txt)
            ws.write(row, 1, line.employee_id.name, detail_txt)
            ws.write(row, 2, line.employee_id.identification_id or '', detail_txt)
            ws.write(row, 3, ttn, detail_number)
            ws.write(row, 4, salary['ttncn'], detail_number)
            ws.write(row, 5, salary['bank'], detail_number)
            row += 1

    def write_detail_sheet_four(self, ws, line_ids, small_title, detail_number, detail_no_border, detail_txt):
        stt = 1
        row = 4
        for line in line_ids:
            salary = self.get_salary(line)
            bank_account = line.bank_account_id
            ws.write(row, 0, stt, detail_txt)
            ws.write(row, 1, line.employee_id.name, detail_txt)
            ws.write(row, 2, bank_account.acc_number or '', detail_txt)
            ws.write(row, 3, salary['bank'], detail_number)
            ws.write(row, 4, bank_account.bank_name or '', detail_txt)
            stt += 1
            row += 1
        ws.write(row, 2, 'Kiểm tra', small_title)
        ws.merge_range(row, 3, row, 4, '', detail_no_border)
        row += 1
        ws.write(row, 2, 'Tổng CK', small_title)
        ws.merge_range(row, 3, row, 4, '', detail_no_border)
        row += 1
        ws.write(row, 2, 'CK TPMH', small_title)
        ws.merge_range(row, 3, row, 4, '', detail_no_border)
        row += 1
        ws.write(row, 2, 'CK CNQ7', small_title)
        ws.merge_range(row, 3, row, 4, '', detail_no_border)
        row += 1

        ws.merge_range(row, 0, row, 1, 'NGƯỜI LẬP', detail_no_border)
        ws.write(row, 2, 'KIỂM TRA', detail_no_border)
        ws.write(row, 3, '', detail_no_border)
        ws.write(row, 4, 'DUYỆT', detail_no_border)

    def set_sheet_one(self, ws1, title, company, month, top, top_date, title_top):
        ws1.set_column(0, 0, 7)  # A
        ws1.set_column(1, 1, 7)
        ws1.set_column(2, 2, 35)
        ws1.set_column(3, 3, 25)
        ws1.set_column(4, 4, 15)  # E
        ws1.set_column(5, 5, 15)
        ws1.set_column(6, 6, 20)
        ws1.set_column(7, 7, 20)
        ws1.set_column(8, 8, 20)  # I
        ws1.set_column(9, 9, 25)
        ws1.set_column(10, 10, 15)
        ws1.set_column(11, 11, 15)
        ws1.set_column(12, 12, 15)  # N
        ws1.set_column(13, 13, 15)  # O
        ws1.set_column(14, 14, 23)
        ws1.set_column(15, 15, 20)
        ws1.set_column(16, 16, 20)
        ws1.set_column(17, 17, 20)
        ws1.set_column(18, 18, 20)
        ws1.set_column(19, 19, 20)  # U
        ws1.set_column(20, 20, 20)
        ws1.set_column(21, 21, 20)
        ws1.set_column(22, 22, 20)
        ws1.set_column(23, 23, 20)
        ws1.set_column(24, 24, 20)  # z

        ws1.set_column(25, 25, 25)  # AA
        ws1.set_column(26, 26, 25)
        ws1.set_column(27, 27, 25)
        ws1.set_column(28, 28, 25)
        ws1.set_column(29, 29, 25)
        ws1.set_column(30, 30, 25)
        ws1.set_column(31, 31, 25)
        ws1.set_column(32, 32, 25)
        ws1.set_column(33, 33, 25)

        ws1.set_column(34, 34, 25)  # AJ
        ws1.set_column(35, 35, 30)
        ws1.set_column(36, 36, 25)
        ws1.set_column(37, 37, 25)
        ws1.set_column(38, 38, 25)
        ws1.set_column(39, 39, 25)
        ws1.set_column(40, 40, 35)  # AO
        ws1.set_column(41, 41, 25)
        ws1.set_column(41, 41, 25)
        ws1.set_column(42, 42, 25)

        ws1.set_row(0, 30.0)
        ws1.set_row(1, 30.0)
        ws1.set_row(5, 60.0)
        ws1.set_row(6, 60.0)

        addr = ', '.join([x for x in [company.street, company.street2, company.city, company.state_id.name,
                                      company.country_id.name] if x is not False])
        ws1.merge_range(0, 0, 0, 3, company.name, title_top)
        ws1.merge_range(1, 0, 1, 3, addr, title_top)
        ws1.merge_range(0, 13, 0, 18, 'BẢNG TỔNG LƯƠNG NỘI BỘ', top)
        ws1.merge_range(1, 13, 1, 18, month.name, top_date)

        ws1.merge_range(5, 0, 6, 1, 'STT', title)
        ws1.merge_range(5, 2, 6, 2, 'MS', title)
        ws1.merge_range(5, 3, 6, 3, 'HỌ TÊN', title)
        ws1.merge_range(5, 4, 6, 4, 'HƠP ĐỒNG', title)
        ws1.merge_range(5, 5, 6, 5, 'DỰ ÁN', title)
        ws1.merge_range(5, 6, 6, 6, 'TỔNG LƯƠNG THỰC TẾ', title)
        ws1.merge_range(5, 7, 6, 7, 'LƯƠNG CB (1)', title)
        ws1.merge_range(5, 8, 6, 8, 'LƯƠNG NĂNG SUẤT (2)', title)
        ws1.merge_range(5, 9, 6, 9, 'LƯƠNG THEO HỢP ĐỒNG (1+2)', title)
        ws1.merge_range(5, 10, 6, 10, 'LƯƠNG/NGÀY', title)
        ws1.merge_range(5, 11, 6, 11, 'NGÀY CÔNG', title)

        ws1.merge_range(5, 12, 5, 14, 'PHỤ CẤP', title)
        ws1.write(6, 12, 'ĂN TRƯA', title)
        ws1.write(6, 13, 'TĂNG CA', title)
        ws1.write(6, 14, 'PC KHÁC', title)
        ws1.merge_range(5, 15, 6, 15, 'TỔNG THU NHẬP', title)

        ws1.merge_range(5, 16, 5, 19, 'CTY TRÍCH BHXH, BHYT, BTTN (21.5%) - CĐ (2%)', title)
        ws1.write(6, 16, 'BHXH (17.5%)', title)
        ws1.write(6, 17, 'BHYT (3%)', title)
        ws1.write(6, 18, 'BHTN (1%)', title)
        ws1.write(6, 19, 'KP CĐ (2%)', title)
        ws1.merge_range(5, 20, 6, 20, 'CTY TRÍCH BHXH, BHYT, BTTN, CĐ (23.5%)', title)

        ws1.merge_range(5, 21, 5, 24, 'NLĐ TRÍCH BHXH, BHYT, BTTN (10.5%) - CĐ (1%)', title)
        ws1.write(6, 21, 'BHXH (8%)', title)
        ws1.write(6, 22, 'BHYT (1.5%)', title)
        ws1.write(6, 23, 'BHTN (1%)', title)
        ws1.write(6, 24, 'KP CĐ (1%)', title)
        ws1.merge_range(5, 25, 6, 25, 'TRỪ TRÍCH BHXH, BHYT, BTTN, CĐ (11.5%)', title)

        ws1.merge_range(5, 26, 6, 26, 'THU NHẬP CHỊU THUẾ', title)
        ws1.merge_range(5, 27, 6, 27, 'GIẢM TRỪ GIA CẢNH', title)
        ws1.merge_range(5, 28, 6, 28, 'KHOẢN TRỪ TRƯỚC KHI TÍNH THUẾ (TIỀN ĂN, ĐIỆN THOẠI MỨC KHOÁN, TĂNG CA)', title)
        ws1.merge_range(5, 29, 6, 29, 'THU NHẬP CHUNG TÍNH THUẾ', title)
        ws1.merge_range(5, 30, 6, 30, 'THU NHẬP TÍNH THUẾ', title)
        ws1.merge_range(5, 31, 6, 31, 'THUẾ TNCN', title)
        ws1.merge_range(5, 32, 6, 32, 'TRỪ KHÁC', title)
        ws1.merge_range(5, 33, 6, 33, 'CÁC KHOẢN CỘNG LƯƠNG', title)
        ws1.merge_range(5, 34, 6, 34, 'TỔNG LƯƠNG THỰC NHẬN', title)

        ws1.merge_range(5, 35, 5, 37, 'THỰC NHẬN', title)
        ws1.write(6, 35, 'TIỀN MẶT', title)
        ws1.write(6, 36, 'CHUYỂN KHOẢN CTY', title)
        ws1.write(6, 37, 'CHUYỂN KHOẢN NỘI BỘ', title)
        ws1.merge_range(5, 38, 6, 38, 'TẠM ỨNG', title)
        ws1.merge_range(5, 39, 6, 39, 'NGUYỄN CHUYỂN TIỀN', title)
        ws1.merge_range(5, 40, 6, 40, 'NOTE', title)
        ws1.merge_range(5, 41, 6, 41, 'STATUS', title)
        ws1.merge_range(5, 42, 6, 42, 'SITE', title)

    def set_sheet_two(self, ws, title, company, month, top, top_date, title_top):
        ws.set_column(0, 0, 7)  # A
        ws.set_column(1, 1, 7)
        ws.set_column(2, 2, 35)
        ws.set_column(3, 3, 25)
        ws.set_column(4, 4, 15)
        ws.set_column(5, 5, 20)
        ws.set_column(6, 6, 20)
        ws.set_column(7, 7, 20)  # I
        ws.set_column(8, 8, 10)
        ws.set_column(9, 9, 15)
        ws.set_column(10, 10, 15)
        ws.set_column(11, 11, 15)  # N
        ws.set_column(12, 12, 15)  # O
        ws.set_column(13, 13, 23)
        ws.set_column(14, 14, 20)
        ws.set_column(15, 15, 20)
        ws.set_column(16, 16, 20)
        ws.set_column(17, 17, 20)
        ws.set_column(18, 18, 20)  # U
        ws.set_column(19, 19, 20)
        ws.set_column(20, 20, 20)
        ws.set_column(21, 21, 20)
        ws.set_column(22, 22, 20)

        ws.set_column(23, 23, 25)  # AA
        ws.set_column(24, 24, 25)
        ws.set_column(25, 25, 25)
        ws.set_column(26, 26, 25)
        ws.set_column(27, 27, 25)
        ws.set_column(28, 28, 25)
        ws.set_column(29, 29, 25)
        ws.set_column(30, 30, 25)
        ws.set_column(32, 31, 25)

        ws.set_row(5, 60.0)
        ws.set_row(6, 60.0)

        addr = ', '.join([x for x in [company.street, company.street2, company.city, company.state_id.name,
                                      company.country_id.name] if x is not False])
        ws.merge_range(0, 0, 0, 3, company.name, title_top)
        ws.merge_range(1, 0, 1, 3, addr, title_top)
        ws.merge_range(0, 12, 1, 16, 'BẢNG THANH TOÁN LƯƠNG', top)
        ws.merge_range(2, 12, 3, 16, '{}'.format(month.name), top_date)

        ws.merge_range(5, 0, 6, 1, 'STT', title)
        ws.merge_range(5, 2, 6, 2, 'MS', title)
        ws.merge_range(5, 3, 6, 3, 'HỌ TÊN', title)
        ws.merge_range(5, 4, 6, 4, 'DỰ ÁN', title)
        ws.merge_range(5, 5, 6, 5, 'LƯƠNG CB (1)', title)
        ws.merge_range(5, 6, 6, 6, 'LƯƠNG NĂNG SUẤT (2)', title)
        ws.merge_range(5, 7, 6, 7, 'LƯƠNG THEO HỢP ĐỒNG (1+2)', title)
        ws.merge_range(5, 8, 6, 8, 'NGÀY CÔNG', title)

        ws.merge_range(5, 9, 5, 11, 'PHỤ CẤP', title)
        ws.write(6, 9, 'ĂN TRƯA', title)
        ws.write(6, 10, 'TĂNG CA', title)
        ws.write(6, 11, 'PC KHÁC', title)
        ws.merge_range(5, 12, 6, 12, 'TỔNG THU NHẬP', title)

        ws.merge_range(5, 13, 5, 16, 'CTY TRÍCH BHXH, BHYT, BTTN (21.5%) - CĐ (2%)', title)
        ws.write(6, 13, 'BHXH (17.5%)', title)
        ws.write(6, 14, 'BHYT (3%)', title)
        ws.write(6, 15, 'BHTN (1%)', title)
        ws.write(6, 16, 'KP CĐ (2%)', title)
        ws.merge_range(5, 17, 6, 17, 'CTY TRÍCH BHXH, BHYT, BTTN, CĐ (23.5%)', title)

        ws.merge_range(5, 18, 5, 21, 'NLĐ TRÍCH BHXH, BHYT, BTTN (10.5%) - CĐ (1%)', title)
        ws.write(6, 18, 'BHXH (8%)', title)
        ws.write(6, 19, 'BHYT (1.5%)', title)
        ws.write(6, 20, 'BHTN (1%)', title)
        ws.write(6, 21, 'KP CĐ (1%)', title)
        ws.merge_range(5, 22, 6, 22, 'TRỪ TRÍCH BHXH, BHYT, BTTN, CĐ (11.5%)', title)

        ws.merge_range(5, 23, 6, 23, 'GIẢM TRỪ GIA CẢNH', title)
        ws.merge_range(5, 24, 6, 24, 'KHOẢN TRỪ TRƯỚC KHI TÍNH THUẾ (TIỀN ĂN, ĐIỆN THOẠI MỨC KHOÁN, TĂNG CA)', title)
        ws.merge_range(5, 25, 6, 25, 'THU NHẬP TÍNH THUẾ', title)
        ws.merge_range(5, 26, 6, 26, 'THUẾ TNCN', title)
        ws.merge_range(5, 27, 6, 27, 'MS TTNCN', title)
        ws.merge_range(5, 28, 6, 28, 'TRỪ KHÁC', title)
        ws.merge_range(5, 29, 6, 29, 'TỔNG LƯƠNG', title)

        ws.merge_range(5, 30, 5, 31, 'THỰC NHẬN', title)
        ws.write(6, 30, 'TIỀN MẶT', title)
        ws.write(6, 31, 'CHUYỂN KHOẢN CTY', title)

    def set_sheet_three(self, ws, title, top_no_border):
        ws.set_column(0, 0, 7)  # A
        ws.set_column(1, 1, 20)
        ws.set_column(2, 2, 25)
        ws.set_column(3, 3, 25)
        ws.set_column(4, 4, 20)
        ws.set_column(5, 5, 20)  # F

        ws.merge_range(1, 1, 1, 4, 'LƯƠNG CỘNG TÁC VIÊN ', top_no_border)
        ws.merge_range(2, 0, 3, 0, 'STT', title)
        ws.merge_range(2, 1, 3, 1, 'HỌ TÊN', title)
        ws.merge_range(2, 2, 3, 2, 'CMND', title)
        ws.merge_range(2, 3, 3, 3, 'TỔNG LƯƠNG', title)
        ws.merge_range(2, 4, 3, 4, 'THUẾ TNCN', title)
        ws.merge_range(2, 5, 3, 5, 'CHUYỂN KHOẢN CTY', title)

    def set_sheet_four(self, ws, title, top_no_border):
        ws.set_column(0, 0, 7)  # A
        ws.set_column(1, 1, 25)
        ws.set_column(2, 2, 20)
        ws.set_column(3, 3, 20)
        ws.set_column(4, 4, 50)

        ws.merge_range(0, 0, 2, 4, 'DANH SACH CHUYEN KHOAN NGAN HANG', top_no_border)
        ws.write(3, 0, 'STT', title)
        ws.write(3, 1, 'TÊN NHÂN VIÊN', title)
        ws.write(3, 2, 'SỐ TÀI KHOẢN', title)
        ws.write(3, 3, 'SỐ TIỀN', title)
        ws.write(3, 4, 'TÊN NGÂN HÀNG', title)
