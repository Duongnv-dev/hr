# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, SUPERUSER_ID, _
import datetime
from datetime import datetime, timedelta
from num2words import num2words


class ReportAllocateResource(models.TransientModel):
    _inherit = 'report.allocate.resource'

    @api.multi
    def action_print_xlsx(self):
        return self.env.ref('bnk_allocate_resource_widget.export_allocate_resource_detail_xlsx').with_context(
            language=self.env.user.partner_id.lang).report_action(self)


class ReportAllocateResourceXlsx(models.AbstractModel):
    _name = "report.bnk_allocate.allocate_resource_detail_xlsx"
    _inherit = 'report.report_xlsx.abstract'

    def next_char(self, current_char):
        if not current_char:
            return ''
        last_char = current_char[-1]
        prefix = current_char[:len(current_char) - 1]

        if last_char.upper() == 'Z':
            if not prefix:
                return 'AA'
            current_char = self.next_char(prefix) + 'A'
            return current_char

        return prefix + chr(ord(last_char) + 1)

    def generate_xlsx_report(self, workbook, data, form):
        def next_char(c, step=1):
            for index in range(0, step):
                c = self.next_char(c)
            return c

        def get_style(line, date_item, datas):
            style_dict = {
                'valign': 'vcenter',
                'align': 'center',
                'border': 1,
                'font_name': 'Arial',
                'font_size': 10,
                'text_wrap': True,
            }

            bg_color = ''
            color = ''
            font_weight = ''
            font_style = ''

            billable = 'o'
            if line['date'][date_item]['total_percent'] > 0:
                billable = 'none_billable'
                bg_color = '#FFE080'

            if line['date'][date_item]['billable']:
                billable = 'billable'
                bg_color = '#FFC000'

            holiday = 'o'
            if date_item in datas['public_holiday_list']:
                holiday = 'public_holiday'
                bg_color = '#dce8e3'

            if date_item in datas['holiday_list']:
                holiday = 'holiday'
                bg_color = '#d9d9d9'

            over = 'o'
            if line['date'][date_item]['total_percent'] > 100:
                over = 'over'
                color = '#0a011a'
                font_weight = 'bold'

            if line['date'][date_item]['un_ot_total'] > 100:
                over = 'over_not_ot'
                color = '#ff0303'
                font_weight = 'bold'

            if line['date'][date_item]['total_percent'] < 100:
                over = 'not_enough'
                color = '#037dff'
                font_style = 'italic'

            if font_weight:
                style_dict['bold'] = True

            if font_style:
                style_dict['italic'] = True

            if color:
                style_dict['font_color'] = color

            if bg_color:
                style_dict['bg_color'] = bg_color

            style = workbook.add_format(style_dict)

            return style

        datas = form.get_allocate_resource_widget_data(form.id)
        groupby_label = datas['groupby_label']

        # add a worldsheet
        ws = workbook.add_worksheet(_(form.date_from or ''))
        ws.set_column(0, 0, 13)
        ws.set_column(1, 1, 13)
        ws.set_column(2, 2, 9)
        ws.set_column(3, 3, 9)
        ws.set_column(4, 4, 9)
        ws.set_column(5, 5, 9)

        if form.group_by_project:
            ws.set_column(6, 6, 10)
        else:
            ws.set_column(6, 6, 4)

        # ws.set_row(2, 30.0)

        top_header = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bold': True,
        })

        table_body = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
        })

        holiday = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
        })
        holiday.set_bg_color('#d9d9d9')

        public_holiday = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
        })

        holiday_bill_over = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
        })

        event = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bg_color': '#cdd4cf',
        })

        total = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bg_color': '#aae4f2',
        })

        total_billable = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bg_color': '#a4cf64',
        })

        unallocate_total = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bg_color': '#F8CAAD',
        })

        total_header = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bg_color': '#aae4f2',
            'bold': True
        })

        total_billable_header = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bg_color': '#a4cf64',
            'bold': True
        })

        unallocate_total_header = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 10,
            'text_wrap': True,
            'bg_color': '#F8CAAD',
            'bold': True
        })

        public_holiday.set_bg_color('#dce8e3')

        row_pos = 1

        prefix_header = groupby_label
        prefix_header.extend(['Skill', 'Place'])

        col = 'A'
        for header in prefix_header:
            ws.merge_range(
                '{col}{row_pos}:{col}{row_pos_1}'.format(
                    col=col, row_pos=row_pos, row_pos_1=row_pos + 1),
                header, top_header)
            col = next_char(col)

        ws.merge_range(
            '{col}{row_pos}:{col}{row_pos_1}'.format(
                col=col, row_pos=row_pos, row_pos_1=row_pos + 1),
            'Total', total_header)
        col = next_char(col)

        ws.merge_range(
            '{col}{row_pos}:{col}{row_pos_1}'.format(
                col=col, row_pos=row_pos, row_pos_1=row_pos + 1),
            'Billable total', total_billable_header)
        col = next_char(col)

        ws.merge_range(
            '{col}{row_pos}:{col}{row_pos_1}'.format(
                col=col, row_pos=row_pos, row_pos_1=row_pos + 1),
            'Unallocate total', unallocate_total_header)
        col = next_char(col)

        month_col = col
        # print date header
        for month_item in datas['month_list']:
            next_col = next_char(month_col, month_item['num_day']-1)

            index = '{col}{row_pos}:{next_col}{row_pos}'.format(
                col=month_col, next_col=next_col,
                row_pos=row_pos)
            ws.merge_range(
                index, month_item['month'], top_header)
            month_col = next_char(next_col)

        col_num = 6
        row_pos += 1
        for date_item in datas['date_list']:
            col_num += 1
            style = top_header
            if date_item in datas['public_holiday_list']:
                style = public_holiday

            if date_item in datas['holiday_list']:
                style = holiday

            ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                     date_item.split('-')[2], style)
            ws.set_column(col_num, col_num, 4)
            col = next_char(col)

        # table body
        event_flag = True
        for line in datas['grid']:
            event_flag = not event_flag
            event_style = event
            if not event_flag:
                event_style = table_body

            col = 'A'
            row_pos += 1
            for label in line['label']:
                ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                         label, event_style)
                col = next_char(col)

            ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                     line['skill'], event_style)
            col = next_char(col)

            ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                     line['place'], event_style)
            col = next_char(col)

            ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                     line['total'], total)
            col = next_char(col)

            ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                     line['billable_total'], total_billable)
            col = next_char(col)

            ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                     line['unallocate_total'], unallocate_total)
            col = next_char(col)

            for date_item in datas['date_list']:
                style = get_style(line, date_item, datas)
                percent = line['date'][date_item]['total_percent'] or ''
                ws.write('{col}{row_pos}'.format(row_pos=row_pos, col=col),
                         percent, style)
                col = next_char(col)




