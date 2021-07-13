from odoo import api, fields, models, tools, _
from datetime import datetime


class HrEmployeeReport(models.Model):
    _name = 'hr.employee.report'
    _auto = False

    id = fields.Integer(_('ID'))
    year = fields.Integer(_('Year'), readonly=True)
    month = fields.Many2one('hr.period', string=_('Month'), readonly=True)
    department_id = fields.Many2one('hr.department', string=_('Department'), readonly=True)
    emp_type = fields.Selection(selection=[
        ('new_emp', _('New Employee')), ('balance_emp', _('Balance Employee')),
        ('resigned_emp', _('Resigned Employee')), ('join_resigned_in_month_emp', _('Join Resigned In Month Employee'))
    ], string=_('Employee Type'), readonly=True)
    measure = fields.Integer(string=_('Measure Employee'), readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'hr_employee_report')
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW hr_employee_report AS
            (
            SELECT 
                row_number() OVER() AS id,
                'new_emp' as emp_type,
                new_emp.year as year,
                new_emp.month as hp_month,
                new_emp.hp_id as month,
                new_emp.department as department_id,
                new_emp.emp_count as measure
                FROM
                (SELECT
                    COUNT(he.id) as emp_count, hp.id as hp_id, hp.month as month, hp.year as year, he.department_id as department
                    FROM hr_employee as he, hr_period as hp
                    WHERE 
                        he.active = True
                        AND EXTRACT(YEAR FROM he.join_date) = hp.year
                        AND CAST(EXTRACT(MONTH FROM he.join_date) AS INT) = CAST(hp.month AS INT)
                    GROUP BY hp.year, hp.month, hp.id, he.department_id) 
                AS new_emp
            UNION ALL
            SELECT 
                row_number() OVER() + 10000 AS id,
                'join_resigned_in_month_emp' as emp_type,
                join_resigned_in_month_emp.year as year,
                join_resigned_in_month_emp.month as hp_month,
                join_resigned_in_month_emp.hp_id as month,
                join_resigned_in_month_emp.department as department_id,
                join_resigned_in_month_emp.emp_count as measure
                FROM
                (SELECT
                    COUNT(he.id) as emp_count, hp.id as hp_id, hp.month as month, hp.year as year, he.department_id as department
                    FROM hr_employee as he, hr_period as hp
                    WHERE 
                        he.active = True
                        AND EXTRACT(YEAR FROM he.join_date) = hp.year
                        AND CAST(EXTRACT(MONTH FROM he.join_date) AS INT) = CAST(hp.month AS INT)
                        AND CAST(EXTRACT(MONTH FROM he.resigned_date) AS INT) = CAST(hp.month AS INT)
                    GROUP BY hp.year, hp.month, hp.id, he.department_id) 
                AS join_resigned_in_month_emp
            UNION ALL 
            SELECT 
                row_number() OVER() + 100000 AS id,
                'resigned_emp' as emp_type,
                resigned_emp.year as year,
                resigned_emp.month as hp_month,
                resigned_emp.hp_id as month,
                resigned_emp.department as department_id,
                resigned_emp.emp_count as measure
                FROM
                (SELECT 
                    COUNT(he.id) as emp_count, hp.id as hp_id, hp.month as month, hp.year as year, he.department_id as department
                    FROM hr_employee as he, hr_period as hp
                    WHERE 
                        he.active = True
                        AND EXTRACT(YEAR FROM he.resigned_date) = hp.year
                        AND CAST(EXTRACT(MONTH FROM he.resigned_date) AS INT) = CAST(hp.month AS INT)
                    GROUP BY hp.year, hp.month, hp.id, he.department_id) 
                AS resigned_emp
            UNION ALL 
            SELECT 
                row_number() OVER() + 1000000 AS id, 
                'balance_emp' as emp_type,
                balance_emp.year as year,
                balance_emp.month as hp_month,
                balance_emp.hp_id as month,
                balance_emp.department as department_id,
                balance_emp.emp_count as measure
                FROM
                (SELECT 
                    COUNT(he.id) as emp_count, hp.id as hp_id, hp.month as month, hp.year as year, he.department_id as department
                    FROM hr_employee as he, hr_period as hp
                    WHERE 
                        he.active = True
                        AND (
                            (EXTRACT(YEAR FROM he.join_date) < hp.year AND he.resigned_date IS NULL)
                        OR  (
                            EXTRACT(YEAR FROM he.join_date) = hp.year AND he.resigned_date IS NULL
                            AND CAST(EXTRACT(MONTH FROM he.join_date) AS INT) < CAST(hp.month AS INT)
                            )
                        OR  (
                            EXTRACT(YEAR FROM he.join_date) < hp.year 
                            AND CAST(EXTRACT(YEAR FROM he.resigned_date) AS INT) > hp.year
                            )
                        OR  (
                            EXTRACT(YEAR FROM he.join_date) < hp.year
                            AND CAST(EXTRACT(YEAR FROM he.resigned_date) AS INT) = hp.year 
                            AND CAST(EXTRACT(MONTH FROM he.resigned_date) AS INT) >= CAST(hp.month AS INT)
                            )
                        OR  (
                            EXTRACT(YEAR FROM he.join_date) = hp.year
                            AND CAST(EXTRACT(YEAR FROM he.resigned_date) AS INT) = hp.year
                            AND CAST(EXTRACT(MONTH FROM he.join_date) AS INT) < CAST(hp.month AS INT)
                            AND CAST(EXTRACT(MONTH FROM he.resigned_date) AS INT) >= CAST(hp.month AS INT)
                            )
                        OR  (
                            EXTRACT(YEAR FROM he.join_date) = hp.year
                            AND CAST(EXTRACT(YEAR FROM he.resigned_date) AS INT) > hp.year
                            AND CAST(EXTRACT(MONTH FROM he.join_date) AS INT) < CAST(hp.month AS INT)
                            )
                            )
                    GROUP BY hp.year, hp.month, hp.id, he.department_id) 
                AS balance_emp
            ORDER BY year, hp_month
            );
        ''')
