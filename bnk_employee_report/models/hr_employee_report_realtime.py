from odoo import api, fields, models, tools, _
from datetime import datetime


class HrEmployeeReport(models.Model):
    _name = 'hr.employee.report.realtime'
    _auto = False

    id = fields.Integer(_('ID'))
    date = fields.Date(_('Date'), readonly=True)
    department_id = fields.Many2one('hr.department', string=_('Department'), readonly=True)
    emp_type = fields.Selection(selection=[
        ('new_emp', _('New Employee')), ('balance_emp', _('Balance Employee')),
        ('resigned_emp', _('Resigned Employee'))], string=_('Employee Type'), readonly=True)
    measure = fields.Integer(string=_('Measure Employee'), readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'hr_employee_report_realtime')
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW hr_employee_report_realtime AS
            (
            SELECT row_number() OVER() AS id,
                'new_emp' as emp_type,
                new_emp.department as department_id,
                new_emp.date as date,
                new_emp.emp_count as measure
            FROM
            (SELECT
                COUNT(he.id) as emp_count, d.date as date, he.department_id as department
                FROM hr_employee as he, (SELECT generate_series(MIN(he.join_date), CURRENT_DATE, '1 day')::date AS date FROM hr_employee as he) AS d
                WHERE
                    he.active = True
                    AND he.join_date = d.date
                GROUP BY d.date, he.department_id)
            AS new_emp
            UNION ALL
            SELECT row_number() OVER() + 100000 AS id,
                'resigned_emp' as emp_type,
                resigned_emp.department as department_id,
                resigned_emp.date as date,
                resigned_emp.emp_count as measure
            FROM
            (SELECT
                COUNT(he.id) as emp_count, d.date as date, he.department_id as department
                FROM hr_employee as he, (SELECT generate_series(MIN(he.join_date), CURRENT_DATE, '1 day')::date AS date FROM hr_employee as he) AS d
                WHERE
                    he.active = True
                    AND he.resigned_date = d.date
                GROUP BY d.date, he.department_id)
            AS resigned_emp
            UNION ALL 
            SELECT row_number() OVER() + 1000000 AS id,
                'balance_emp' as emp_type,
                balance_emp.department as department_id,
                balance_emp.date as date,
                balance_emp.emp_count as measure
            FROM
            (SELECT
                COUNT(he.id) as emp_count, d.date as date, he.department_id as department
                FROM hr_employee as he, (SELECT generate_series(MIN(he.join_date), CURRENT_DATE, '1 day')::date AS date FROM hr_employee as he) AS d
                WHERE
                    he.active = True
                    AND (
                        (he.join_date < d.date and he.resigned_date is NULL)
                        OR
                        (he.join_date < d.date and he.resigned_date >= d.date)
                        )
                GROUP BY d.date, he.department_id)
            AS balance_emp
        ORDER BY date
            );
        ''')
