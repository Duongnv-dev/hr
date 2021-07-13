from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError
import datetime


class Asset(models.Model):
    _inherit = 'account.asset.asset'

    user_id = fields.Many2one('res.users', 'User')
    employee_id = fields.Many2one('hr.employee', 'Employee', readonly=True, track_visibility='onchange')
    location_id = fields.Many2one('bnk.location', string="Asset Location", track_visibility='onchange')
    asset_request_id = fields.Many2one('asset.request', string="Asset Request")
    value = fields.Float(string='Gross Value', required=False, readonly=True, digits=0,
                         states={'draft': [('readonly', False)]}, oldname='purchase_value')
    date = fields.Date(string='Date', required=False, readonly=True, states={'draft': [('readonly', False)]},
                       default=fields.Date.context_today, oldname="purchase_date")
    date_first_depreciation = fields.Selection([
        ('last_day_period', 'Based on Last Day of Purchase Period'),
        ('manual', 'Manual')],
        string='Depreciation Dates', default='manual',
        readonly=True, states={'draft': [('readonly', False)]}, required=False,
        help='The way to compute the date of the first depreciation.\n'
             '  * Based on last day of purchase period: The depreciation dates will be based on the last day of the purchase month or the purchase year (depending on the periodicity of the depreciations).\n'
             '  * Based on purchase date: The depreciation dates will be based on the purchase date.\n')

    first_depreciation_manual_date = fields.Date(
        string='First Depreciation Date', required=False,
        readonly=True, states={'draft': [('readonly', False)]},
        help='Note that this date does not alter the computation of the first journal entry in case of prorata temporis assets. It simply changes its accounting date'
    )
    maintenance_request_id = fields.One2many('maintenance.request','asset_id')
    start_date = fields.Date(string='Warranty Date')
    end_date = fields.Date(string='Warranty expires')
    owner = fields.Many2one('res.partner', string="Asset Owner")
    borrowed_asset = fields.Boolean(default = False, string="3rd party Asset")
    id_asset = fields.Char('Asset Code', compute='cp_asset_id', store=True)
    id_barcode = fields.Binary('Barcode', compute='compute_barcode', store=True)

    @api.depends('category_id.code')
    def cp_asset_id(self):
        for s in self:
            if not s.category_id:
                continue
            if s.id_asset:
                code = s.category_id.code + '{:08}'.format(s.id)
                if s.id_asset == code:
                    continue
                s.id_asset = code
            elif type(s.id) is int:
                code = s.category_id.code + '{:08}'.format(s.id)
                s.id_asset = code

    @api.depends('id_asset')
    def compute_barcode(self):
        for s in self:
            if not s.id_asset:
                continue
            barcode = s.env['tool.barcodez'].barcode(s.id_asset, False)
            s.id_barcode = barcode


class ReportBarcodeXlsx(models.AbstractModel):
    _name = "report.bnk_asset.export_barcode"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, form):
        data_ = []
        for f in form:
            data_.append([f.name, f.id_asset, f.id_barcode])
        if not data_:
            return
        ws = workbook.add_worksheet('Barcode')
        ws.set_column(0, 0, 25)
        ws.set_column(1, 1, 15)
        ws.set_column(1, 1, 50)

        content_left = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 12,
            'text_wrap': True,
            'bold': True,
        })
        content_center = workbook.add_format({
            'valign': 'vcenter',
            'align': 'content',
            'border': 1,
            'font_name': 'Arial',
            'font_size': 12,
            'text_wrap': True,
            'bold': True,
        })
        content_header = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 0,
            'font_name': 'Arial',
            'font_size': 18,
            'text_wrap': True,
            'bold': True,
        })

        row = 2
        ws.merge_range('B{}:C{}'.format(row, row+1), 'Barcode Asset', content_header)

        row = row + 3
        for d in data_:
            if d[2]:
                ws.merge_range('A{}:A{}'.format(row, row + 8), d[0], content_left)
                ws.merge_range('B{}:B{}'.format(row, row + 8), d[1], content_left)
                image = d[2]
                read_file_obj = self.env['create.tempfile']
                time = '{}'.format(datetime.datetime.now())
                for t in time:
                    if t in ['-', ' ', ':', '.']:
                       time = time.replace(t, '_')
                logo_data = read_file_obj.create_tempfile(image, '/barcode_{}_{}'.format(self._uid, time))
                ws.merge_range('C{}:G{}'.format(row, row+8), '', content_center)
                ws.insert_image('C{}:G{}'.format(row, row+8), logo_data, {'x_scale': 0.70, 'y_scale': 0.60})
                row += 9
            else:
                ws.write('A{}'.format(row), d[0], content_left)
                ws.write('B{}'.format(row), d[1], content_left)
                ws.write('C{}'.format(row), '', content_center)
                row += 1


class Location(models.Model):
    _name = 'bnk.location'
    _description = "BnK Asset Location"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Location", required="True", track_visibility='onchange')
    asset_ids = fields.One2many('account.asset.asset', 'location_id', string="Asset Number",
                                track_visibility='onchange')


class AssetCategory(models.Model):
    _inherit = 'account.asset.category'

    code = fields.Char(required=True, track_visibility='onchange')
    asset_ids = fields.One2many('account.asset.asset','category_id', string='Asset', track_visibility='onchange')