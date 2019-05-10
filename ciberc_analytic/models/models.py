# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, AccessError

import logging
import time
import pytz
import math
import re

_logger = logging.getLogger(__name__)
utc_time_zone = pytz.utc

# actualización a partes de horas
class AccountAnalyticLine(models.Model):
    _inherit = ['account.analytic.line']

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', string='User', default=_default_user, domain=lambda self: [('id', '=', self.env.uid)])