# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat, Tobias Zehntner
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from odoo import api, fields, models, tools
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

HOURS_PER_DAY = 8

class HRHolidays(models.Model):
    _inherit = 'hr.holidays'

    is_batch = fields.Boolean(default=False)

    # TODO Holiday allocation 'by company'

    @api.onchange('date_from')
    def _onchange_date_from(self):
        """
        Overwrite method using user timezone
        """
        if not self.date_from:
            return
        # No date_to set so far: automatically compute one 8 hours later
        if not self.date_to:
            date_to_with_delta = fields.Datetime.from_string(
                self.date_from) + timedelta(hours=self.get_hours_per_day())
            self.date_to = str(date_to_with_delta)

        date_from_user_tz = self.change_to_user_tz(self.date_from)
        date_to_user_tz = self.change_to_user_tz(self.date_to)

        # Compute and update the number of days
        if (date_from_user_tz and date_to_user_tz) \
                and (date_from_user_tz <= date_to_user_tz):
            num_days_raw = self._get_number_of_days(date_from_user_tz,
                                                    date_to_user_tz,
                                                    self.employee_id.id)
            self.compute_days(num_days_raw, date_from_user_tz, date_to_user_tz)
        else:
            self.number_of_days_temp = 0

    def get_hours_per_day(self):
        """
        Inherit method to change hours per day used for leaves
        """
        return HOURS_PER_DAY

    @api.onchange('date_to')
    def _onchange_date_to(self):
        """
        Overwrite method using user timezone
        """
        if not (self.date_from or self.date_to):
            return

        date_from_user_tz = self.change_to_user_tz(self.date_from)
        date_to_user_tz = self.change_to_user_tz(self.date_to)

        # Compute and update the number of days
        if (date_from_user_tz and date_to_user_tz) \
                and (date_from_user_tz <= date_to_user_tz):
            num_days_raw = self._get_number_of_days(date_from_user_tz,
                                                    date_to_user_tz,
                                                    self.employee_id.id)
            self.compute_days(num_days_raw, date_from_user_tz,
                              date_to_user_tz)
        else:
            self.number_of_days_temp = 0

    def change_to_user_tz(self, date):
        """
        Take date and return it in the user timezone
        :param date:
        :return:
        """
        if not date:
            return False
        date_object = datetime.strptime(date,
                                        tools.DEFAULT_SERVER_DATETIME_FORMAT)
        date_user_tz = fields.Datetime.context_timestamp(self.sudo(self._uid),
                                                         date_object)
        date_user_tz_string = date_user_tz.strftime(DTF)
        return date_user_tz_string

    def daterange(self, date_from, date_to):
        """
        Take range of two dates and return all affected dates
        """
        date_from = datetime.strptime(date_from, DTF)
        date_to = datetime.strptime(date_to, DTF)
        for n in range(int((date_to - date_from).days) + 1):
            yield date_from + timedelta(n)

    def compute_days(self, number_of_days, date_from, date_to):
        """
        From a range of dates, compute the number of days that should be
        deducted from the leave (not counting weekends and public holidays)
        """
        if self.employee_id:
            self.number_of_days_temp = self.deduct_special_days(number_of_days)
        else:
            self.number_of_days_temp = number_of_days

    def deduct_special_days(self, number_of_days=0):
        """
        Remove the number of special days from the days count
        """
        days_to_deduct = 0
        special_days = self.get_special_days(self.date_from, self.date_to,
                                             self.employee_id)

        for date in special_days:
            days_to_deduct += 1

        days_without_special_days = number_of_days - days_to_deduct
        return days_without_special_days

    def get_special_days(self, date_from, date_to, employee):
        """
        Return dict of special days (Date: Name)

        Partly Deprecated: Since we now generate actual leave entries for
        public holidays they do no longer need to be deducted from the number
        of days (overlapping leaves cannot be created anyway). We should
        keep removing Sat/Sun and probably make it possible to remove other
        weekdays as well for countries with other work schedules
        """
        public_leave_ids = self.env['hr.public_holiday'].search([
            ('company_ids', 'in', employee.company_id.id)]
        )
        deduct_saturday = employee.company_id.deduct_saturday_in_leave
        deduct_sunday = employee.company_id.deduct_sunday_in_leave

        special_days = {}

        for date in self.daterange(date_from, date_to):
            date_str = str(date.date())
            public_leave = public_leave_ids.filtered(
                lambda r: r.date == date_str)
            if public_leave:
                special_days[date.date()] = 'Public Holiday: %s' \
                                            % public_leave.name
            elif date.weekday() == 5 and deduct_saturday:
                special_days[date.date()] = 'Saturday'
            elif date.weekday() == 6 and deduct_sunday:
                special_days[date.date()] = 'Sunday'

        return special_days
