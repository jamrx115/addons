# -*- coding: utf-8 -*-

from odoo import models, api


class MultiPaySlipWiz(models.TransientModel):
    _name = 'multi.payslip.wizard'

    @api.multi
    def multi_payslip(self):
        payslip_ids = self.env['hr.payslip']. \
            browse(self._context.get('active_ids'))
        for payslip in payslip_ids:
            if payslip.state == 'draft':
                payslip.action_payslip_done()
