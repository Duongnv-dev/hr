# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, SUPERUSER_ID, _
import datetime
from datetime import datetime, timedelta
from num2words import num2words


class InvoiceExcel(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_print_invoice_xlsx(self):
        return self.env.ref('bnk_account.export_invoice_xlsx').with_context(
            language=self.partner_id.lang).report_action(self)


class ReportInvoiceXlsx(models.AbstractModel):
    _name = "report.bnk_invoice.export_invoice"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, form):
        self = self.with_context(lang=form.partner_id.lang)
        # add a worldsheet
        ws = workbook.add_worksheet(_(form.number))
        ws.set_column(0, 0, 1)
        ws.set_column(1, 1, 1)
        ws.set_column(2, 2, 17)
        ws.set_column(3, 3, 15)
        # set width colume E
        ws.set_column(4, 4, 9)
        ws.set_column(5, 5, 10)
        ws.set_column(6, 6, 13)
        ws.set_column(7, 7, 4)
        ws.set_column(8, 8, 7)
        ws.set_column(9, 9, 13)
        ws.set_column(10, 10, 13)

        ws.set_row(2, 30.0)
        ws.set_row(6, 25.0)

        title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 24,
            'text_wrap': True,
            'bold': True,
        })

        content_left = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bold': True,
        })

        content_left_top = workbook.add_format({
            'valign': 'top',
            'align': 'left',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bold': True,
        })
        content_center_bold = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 11,
            'text_wrap': True,
            'bold': True,
        })
        content_center_bold_number = workbook.add_format({
            'valign': 'vcenter',
            'align': 'right',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 11,
            'text_wrap': True,
            'bold': True,
            'num_format': '#,##0.0',
        })
        content_center = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 11,
            'text_wrap': True,
        })
        content_center_number = workbook.add_format({
            'valign': 'vcenter',
            'align': 'right',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 11,
            'text_wrap': True,
            'num_format': '#,##0.0',
        })

        header_size_street = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
        })

        header_size_name = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 20,
            'text_wrap': True,
        })

        row_pos = 1
        user = self.env.user

        # get company logo
        if form.company_id.logo:
            path = '/company_logo_' + user.login + '_' + str(datetime.now()) + '.png'
            path = path.replace(' ', '_')
            read_file_obj = self.env['create.tempfile']
            image = form.company_id.logo
            small_image = tools.image_resize_image_medium(image)
            logo_data = read_file_obj.create_tempfile(small_image, path)
            ws.insert_image('C{row_pos}'.format(row_pos=row_pos), logo_data, {'x_scale': 0.61, 'y_scale': 0.60})

        address_partner = ''
        address_company = ''
        if form.partner_id.street:
            address_partner = form.partner_id.street
        if form.partner_id.street2:
            address_partner += ', ' + form.partner_id.street2
        if form.partner_id.city:
            address_partner += ', ' + form.partner_id.city
        if form.partner_id.state_id:
            address_partner += ', ' + form.partner_id.state_id.name
        if form.partner_id.country_id:
            address_partner += ', ' + form.partner_id.country_id.name

        if form.company_id.street:
            address_company = form.company_id.street
        if form.company_id.street2:
            address_company += ', ' + form.company_id.street2
        if form.company_id.city:
            address_company += ', ' + form.company_id.city
        if form.company_id.state_id:
            address_company += ', ' + form.company_id.state_id.name
        if form.company_id.country_id:
            address_company += ', ' + form.company_id.country_id.name

        ws.merge_range(
            'D{row_pos}:H{row_pos}'.format(
                row_pos=row_pos + 2),
            form.company_id.name or '', header_size_name)
        if address_company:
            ws.merge_range(
                'C{row_pos}:H{row_pos}'.format(
                    row_pos=row_pos + 4), _('Address:') + address_company, header_size_street)
        else:
            ws.merge_range(
                'C{row_pos}:H{row_pos}'.format(
                    row_pos=row_pos + 4), _('Address:'), header_size_street)

        if form.company_id.phone:
            ws.merge_range(
                'C{row_pos}:H{row_pos}'.format(
                    row_pos=row_pos + 5), _('Telephone: ') + form.company_id.phone, header_size_street)
        else:
            ws.merge_range(
                'C{row_pos}:H{row_pos}'.format(
                    row_pos=row_pos + 5), _('Telephone: '), header_size_street)
        ws.merge_range(
            'C{row_pos}:H{row_pos}'.format(
                row_pos=row_pos + 6), _('INVOICE'), title)
        ws.merge_range(
            'C{row_pos}:H{row_pos}'.format(
                row_pos=row_pos + 7), '', title)
        if form.date_invoice:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 8),
                           _('Date: ') + form.date_invoice.strftime("%d/%m/%Y"), content_left)
        else:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 8),
                           _('Date: '), content_left)
        if form.partner_id.name:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 9), _('Customer: ') + form.partner_id.name,
                           content_left)
        else:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 9), _('Customer: '), content_left)

        if address_partner:
            ws.merge_range('C{row_pos}:F{row_pos}'.format(row_pos=row_pos + 10), _('To: ') + address_partner,
                           content_left)
        else:
            ws.merge_range('C{row_pos}:F{row_pos}'.format(row_pos=row_pos + 10), _('To: '), content_left)

        if address_partner:
            ws.merge_range('C{row_pos}:F{row_pos}'.format(row_pos=row_pos + 11),
                           _('Address: ') + address_partner, content_left)
        else:
            ws.merge_range('C{row_pos}:F{row_pos}'.format(row_pos=row_pos + 11),
                           _('Address: '), content_left)
        if form.partner_id.mobile:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 12),
                           _("Telephone: ") + form.partner_id.mobile, content_left)
        else:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 12),
                           _("Telephone: "), content_left)
        if form.number:
            ws.merge_range('F{row_pos}:H{row_pos}'.format(row_pos=row_pos + 8), _('No: ') + form.number, content_left)
        else:
            ws.merge_range('F{row_pos}:H{row_pos}'.format(row_pos=row_pos + 8), _('No: '),
                           content_left)
        if form.contract_no:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 13), _('Contract: ') + form.contract_no,
                           content_left)
        else:
            ws.merge_range('C{row_pos}:E{row_pos}'.format(row_pos=row_pos + 13), _('Contract: '), content_left)

        if form.contract_date:
            ws.merge_range('F{row_pos}:H{row_pos}'.format(row_pos=row_pos + 13),
                           _('Contract Date: ') + form.contract_date.strftime("%d/%m/%Y"), content_left)
        else:
            ws.merge_range('F{row_pos}:H{row_pos}'.format(row_pos=row_pos + 13),
                           _('Contract Date: '), content_left)
        ws.merge_range(
            'C{row_pos}:F{row_pos}'.format(
                row_pos=row_pos + 14), _('Description of Goods and/or Services:'), content_left)
        ws.merge_range(
            'C{row_pos}:C{col}'.format(
                row_pos=row_pos + 17, col=row_pos + 18), _('Part No'), content_center_bold)
        ws.merge_range(
            'D{row_pos}:D{col}'.format(
                row_pos=row_pos + 17, col=row_pos + 18), _('Description'), content_center_bold)
        ws.merge_range(
            'E{row_pos}:E{col}'.format(
                row_pos=row_pos + 17, col=row_pos + 18), _('Quantity'), content_center_bold)
        ws.merge_range(
            'F{row_pos}:F{col}'.format(
                row_pos=row_pos + 17, col=row_pos + 18), _('Amount'), content_center_bold)
        ws.merge_range(
            'G{row_pos}:H{col}'.format(
                row_pos=row_pos + 17, col=row_pos + 18), _('Total({})').format(form.currency_id.symbol),
            content_center_bold)
        # get invoice lines
        invoices_lines = form.invoice_line_ids
        if invoices_lines:
            increment = 0
            row_pos = 19
            for inv in invoices_lines:
                row_pos += 1
                increment += 1
                ws.write('C{row_pos}'.format(row_pos=row_pos), increment, content_center)
                ws.write('C{row_pos}'.format(row_pos=row_pos + 1), '', content_center)
                ws.write('D{row_pos}'.format(row_pos=row_pos), inv.product_id.name, content_center)
                ws.write('D{row_pos}'.format(row_pos=row_pos + 1), _('Total'), content_center_bold)
                ws.write('E{row_pos}'.format(row_pos=row_pos), inv.quantity, content_center)
                ws.write('E{row_pos}'.format(row_pos=row_pos + 1), '', content_center)
                ws.write('F{row_pos}'.format(row_pos=row_pos), inv.price_unit, content_center_number)
                ws.write('F{row_pos}'.format(row_pos=row_pos + 1), '', content_center_number)
                ws.merge_range(
                    'G{row_pos}:H{row_pos}'.format(
                        row_pos=row_pos), inv.price_subtotal, content_center_number)
                ws.merge_range(
                    'G{row_pos}:H{row_pos}'.format(
                        row_pos=row_pos + 1), form.amount_total, content_center_bold_number)

        row_pos += 3
        if form.partner_id.lang != "ja_JP":
            ws.write('C{row_pos}'.format(row_pos=row_pos), _('In Words:'), content_left)
        else:
            pass
        if form.partner_id.lang:
            if form.partner_id.lang == "en_US":
                if form.currency_id:
                    if form.currency_id.name == 'USD':
                        ws.merge_range(
                            'D{row_pos}:H{col}'.format(
                                row_pos=row_pos, col=row_pos + 1),
                            num2words(form.amount_total, lang='en', to='currency', separator=' and',
                                      currency='USD').capitalize(),
                            content_left_top)
                    elif form.currency_id.name == 'VND':
                        ws.merge_range(
                            'D{row_pos}:H{col}'.format(
                                row_pos=row_pos, col=row_pos + 1),
                            num2words(form.amount_total, lang='en').capitalize() + ' dong.',
                            content_left_top)
                else:
                    ws.merge_range(
                        'D{row_pos}:H{col}'.format(
                            row_pos=row_pos, col=row_pos + 1), '', content_left_top)
            elif form.partner_id.lang == "vi_VN":
                if form.currency_id:
                    in_words = num2words(form.amount_total, lang='vi').capitalize()
                    if form.currency_id.name == 'USD':
                        ws.merge_range(
                            'D{row_pos}:H{col}'.format(
                                row_pos=row_pos, col=row_pos + 1), in_words + 'USD.', content_left_top)
                    elif form.currency_id.name == 'VND':
                        ws.merge_range(
                            'D{row_pos}:H{col}'.format(
                                row_pos=row_pos, col=row_pos + 1), in_words + ' đồng.', content_left_top)
                else:
                    ws.merge_range(
                        'D{row_pos}:H{col}'.format(
                            row_pos=row_pos, col=row_pos + 1), '', content_left_top)

        row_pos += 2
        ws.write('C{row_pos}'.format(row_pos=row_pos), _('Payment Term:'), content_left)
        ws.write('C{row_pos}'.format(row_pos=row_pos + 1), _('Our Bank  Name:'), content_left)
        ws.write('C{row_pos}'.format(row_pos=row_pos + 2), _('Address:'), content_left)
        ws.write('C{row_pos}'.format(row_pos=row_pos + 3), _('Our Account No.:'), content_left)
        ws.write('C{row_pos}'.format(row_pos=row_pos + 4), _('SWIFT code: '), content_left)
        ws.write('C{row_pos}'.format(row_pos=row_pos + 5), _('Beneficiary:'), content_left)

        ws.merge_range('D{row_pos}:G{row_pos}'.format(row_pos=row_pos), form.payment_term_id.name or '', content_left)
        ws.merge_range('D{row_pos}:G{row_pos}'.format(row_pos=row_pos + 1), form.partner_bank_id.bank_id.name or '',
                       content_left)
        ws.merge_range('D{row_pos}:G{row_pos}'.format(row_pos=row_pos + 2), form.partner_bank_id.bank_id.street or '',
                       content_left)
        ws.merge_range('D{row_pos}:G{row_pos}'.format(row_pos=row_pos + 3), form.partner_bank_id.acc_number or '',
                       content_left)
        ws.merge_range('D{row_pos}:G{row_pos}'.format(row_pos=row_pos + 4), 'BFTVVNVX037', content_left)
        ws.merge_range('D{row_pos}:G{row_pos}'.format(row_pos=row_pos + 5), form.partner_bank_id.partner_id.name or '',
                       content_left)
        ws.set_row(row_pos, 28.0)
        ws.set_row(row_pos + 1, 28.0)
