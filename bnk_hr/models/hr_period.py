from odoo import api, fields, models, _
from datetime import datetime


class HrPeriod(models.Model):
    _name = 'hr.period'

    name = fields.Char(compute='cp_period_name', store=True)
    period = fields.Char(compute='cp_period_name', store=True)
    year = fields.Integer(require=True)
    month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                              ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                              ('10', 'October'), ('11', 'November'), ('12', 'December')], require=True)

    _sql_constraints = [
        ('unique_name', 'unique (name)', 'Period name already exists!')
    ]

    @api.depends('month', 'year')
    def cp_period_name(self):
        for p in self:
            if not p.month or not p.year:
                if not p.name:
                    p.name = 'New'
                continue

            p.name = '{}/{}'.format(p.month, p.year)
            p.period = '{}-{}'.format(p.year, p.month)

    def check_or_create_period(self, mon, year):
        mon_ = self.convert_month(mon)
        period = self.env['hr.period'].search([('year', '=', year), ('month', '=', mon_)], limit=1)
        if not period:
            period = self.env['hr.period'].create({'year': year, 'month': mon_})
            period.cp_period_name()

        return period.id

    def convert_month(self, mon):
        mon = int(mon)
        if mon < 10:
            month = '0{}'.format(mon)
        else:
            month = str(mon)
        return month


class AutoCreatePeriod(models.Model):
    _name = 'auto.create.period'
    _description = 'Auto Create Period'

    def _auto_create_period(self):
        current_year = datetime.now().year
        current_month = datetime.now().month
        join_date_list = self.env['hr.employee'].search([]).mapped('join_date')
        years_join = []
        for date in join_date_list:
            if date and date.year not in years_join:
                years_join.append(date.year)
        for year in range(min(years_join), current_year + 1):
            if year < current_year:
                year_period = self.env['hr.period'].search([('year', '=', year)])
                if not year_period:
                    for month in range(1, 13):
                        if month < 10:
                            period = self.env['hr.period'].search([('period', '=', '{}-0{}'.format(str(year), str(month)))])
                            if not period:
                                self.env['hr.period'].create({
                                    'year': year,
                                    'month': '0{}'.format(str(month))
                                })
                        if month >= 10:
                            period = self.env['hr.period'].search([('period', '=', '{}-{}'.format(str(year), str(month)))])
                            if not period:
                                self.env['hr.period'].create({
                                    'year': year,
                                    'month': '{}'.format(str(month))
                                })
            if year == current_year:
                year_period = self.env['hr.period'].search([('year', '=', year)])
                if not year_period:
                    for month in range(1, 13):
                        if month < 10 and month <= current_month:
                            period = self.env['hr.period'].search(
                                [('period', '=', '{}-0{}'.format(str(year), str(month)))])
                            if not period:
                                self.env['hr.period'].create({
                                    'year': year,
                                    'month': '0{}'.format(str(month))
                                })
                        if current_month >= month >= 10:
                            period = self.env['hr.period'].search([('period', '=', '{}-{}'.format(str(year), str(month)))])
                            if not period:
                                self.env['hr.period'].create({
                                    'year': year,
                                    'month': '{}'.format(str(month))
                                })
