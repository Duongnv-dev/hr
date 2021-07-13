# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import datetime, pytz


class ChangeDateTime(models.Model):
    _name = 'change.datetime'
    _description = 'Change Datetime'

    def change_utc_to_local_datetime(self, souce_date, option):
        user_tz = self.env.user.tz or False
        if user_tz:
            tz_now = datetime.datetime.now(pytz.timezone(user_tz))
            difference = tz_now.utcoffset().total_seconds() / 60 / 60
            difference = int(difference)
        else:
            difference = 9
        utc_date = datetime.datetime.strptime(souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = utc_date + datetime.timedelta(hours=difference)
        return local_date.strftime(option)

    def change_local_datetime_to_utc(self, souce_date, option):
        user_tz = self.env.user.tz or False
        if user_tz:
            tz_now = datetime.datetime.now(pytz.timezone(user_tz))
            difference = tz_now.utcoffset().total_seconds() / 60 / 60
            difference = int(difference)
        else:
            difference = 9
        local_date = datetime.datetime.strptime(souce_date,
                                                '%Y-%m-%d %H:%M:%S')
        utc_date = local_date + datetime.timedelta(hours=-difference)
        return utc_date.strftime(option)

    def get_month_future(self, month, year, delta_months):
        if month + delta_months <= 12:
            return month + delta_months, year
        delta_years = (delta_months - (12 - month)) / 12
        month_in_future = (delta_months - (12 - month)) % 12
        return month_in_future, year + delta_years

    # souce_date type date
    def get_date_report(self, souce_date, option):
        day = datetime.datetime.strftime(souce_date, option)
        return day

    # option = '%H:%M %d/%m/%Y'
    def get_datetime_report(self, source_date, option):
        datetime_local = self.change_utc_to_local_datetime(source_date, option)
        return datetime_local


