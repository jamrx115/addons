# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re
import logging

_logger = logging.getLogger(__name__)

class ciberc_tipo_novedad_contrato (models.Model):
    _name="ciberc.tipo.novedad.contrato"
    _description= "Tipo novedad contrato"

    name = fields.Char(string='Descripción', copy=False)

# clase creada por alltic que une los campos horario desde contrato
class ciberc_contract(models.Model):
    _inherit = 'hr.contract'

    # -campo personalizado para vacaciones o días libres
    annual_holiday = fields.Integer('Días libres anuales',
                                    help='Vacaciones para contrato laboral y días libres para prestación de servicios')
    # -campos personalizado para cuenta bancaria
    # bank_account_contract_id = fields.Many2one('res.partner.bank', string='Cuenta bancaria', help='Cuenta bancaria para pagos nómina', groups='hr.group_hr_user,base.group_user')
    x_bank_id = fields.Many2one('res.bank', string='Banco')
    x_cuenta_bancaria = fields.Char(string='Número cuenta bancaria')
    x_tipo_cuenta = fields.Char(string='Tipo cuenta')
    x_cod_swift = fields.Char(string='Código Swift')
    x_currency_id = fields.Many2one('res.currency', string='Moneda')
    # -otros campos personalizados
    x_bonificacion = fields.Float(string='Bonificación')
    x_comision = fields.Float(string='Comisión')
    x_dias_aguinaldo = fields.Float(string='Dias aguinaldo', readonly=True)
    x_dias_bono_14 = fields.Float(string='Días calculo Bono 14')
    x_isr = fields.Float(string='Impuesto')
    x_meses_isr = fields.Float(string='Meses ISR')
    x_numero_contrato = fields.Char(string='Identificador Contrato Físico')
    x_renta_ex_patrono = fields.Float(string='Renta Ex-Patrono')
    x_tipo_novedad_contrato_id = fields.Many2one('ciberc.tipo.novedad.contrato', string='Tipo novedad creacion del contrato')
    x_tipo_novedad_cierre_contrato_id = fields.Many2one('ciberc.tipo.novedad.contrato', string='Tipo novedad cierre del contrato')

    # -override
    @api.model
    def create(self, vals):
        res = super(ciberc_contract, self).create(vals)

        if vals['working_hours']:
            self.employee_id.resource_id.write({'calendar_id': self.working_hours.id})

        if vals['date_start']:
            self.employee_id.write({'joining_date': self.date_start})

        return res

    # -override
    @api.multi
    def write(self, vals):
        for contract_obj in self:
            res = super(ciberc_contract, contract_obj).write(vals)
            # escribir el horario en datos de empleado
            if contract_obj.working_hours:
                contract_obj.employee_id.resource_id.write({'calendar_id': contract_obj.working_hours.id})
            # escribir la fecha de inicio de labores en datos de empleado
            if contract_obj.date_start:
                contract_obj.employee_id.write({'joining_date': contract_obj.date_start})
            return res

# clase creada por alltic que vuelve solo lectura el campo horario en empleado
class ciberc_resource(models.Model):
    _inherit = 'resource.resource'

    calendar_id = fields.Many2one("resource.calendar", string='Working Time', readonly=True, help="Define the schedule of resource")