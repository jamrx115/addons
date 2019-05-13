# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
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

    # -override
    working_hours = fields.Many2one('resource.calendar', string='Working Schedule', required=True)
    # nuevo campo para vacaciones o días libres
    annual_holiday = fields.Integer('Días libres anuales',
                                    help='Vacaciones para contrato laboral y días libres para prestación de servicios')
    # -nuevos campos para cuenta bancaria
    # bank_account_contract_id = fields.Many2one('res.partner.bank', string='Cuenta bancaria', help='Cuenta bancaria para pagos nómina', groups='hr.group_hr_user,base.group_user')
    x_bank_id = fields.Many2one('res.bank', string='Banco')
    x_cuenta_bancaria = fields.Char(string='Número cuenta bancaria')
    x_tipo_cuenta = fields.Char(string='Tipo cuenta')
    x_cod_swift = fields.Char(string='Código Swift')
    x_currency_id = fields.Many2one('res.currency', string='Moneda')
    
    # -otros nuevos campos
    x_bonificacion = fields.Float(string='Bonificación')
    x_comision = fields.Float(string='Comisión')
    x_dias_aguinaldo = fields.Float(string='Dias aguinaldo', readonly=True)
    x_dias_bono_14 = fields.Float(string='Días calculo Bono 14')
    x_isr = fields.Float(string='Impuesto sobre la renta', help='Valor descontable mensual (GT)')
    x_medic_pre  = fields.Boolean(string='Descuento por servicios médicos', help='Aplica para salario > 2 SMMLV (CO)')
    x_medic_prep = fields.Integer(string='Descuento mensual', help='Aplica para Colombia')
    x_pensi_volu = fields.Boolean(string='Descuento por pensiones voluntarias', help='Aplica para salario >= 1 SMMLV')
    x_pensi_volun = fields.Integer(string='Descuento mensual', help='Aplica para Colombia')
    x_embargoc_b = fields.Boolean(string='Descuento por embargo *', help='Aplica para Colombia')
    x_medios = fields.Integer(string='Medios')
    x_meses_isr = fields.Float(string='Meses ISR')
    x_numero_contrato = fields.Char(string='Identificador Contrato Físico')
    x_renta_ex_patrono = fields.Float(string='Renta Ex-Patrono')
    x_tipo_novedad_contrato_id = fields.Many2one('ciberc.tipo.novedad.contrato', string='Tipo novedad creacion del contrato', required=True)
    x_tipo_novedad_cierre_contrato_id = fields.Many2one('ciberc.tipo.novedad.contrato', string='Tipo novedad cierre del contrato')

    x_aplica_rec  = fields.Boolean(string='Aplica recargos', default=False, help='Aplica para Colombia')

    # RTE FTE COLOMBIA
    x_porcent_ali = fields.Float(string='Porcentaje alimentación dependientes', help='Aplica para Colombia')
    x_viat_ocasi  = fields.Integer(string='Viáticos ocasionales reembolsables', help='Aplica para Colombia')
    x_ahorros_afc = fields.Integer(string='Ahorros cuentas AFC', help='Aplica para Colombia, valor descontable mensual')
    x_rentrab_ex  = fields.Integer(string='Rentas de trabajo exentas', help='Aplica para Colombia')
    x_int_viviend = fields.Integer(string='Intereses en préstamos vivienda', help='Aplica para Colombia')
    x_polizas_seg = fields.Integer(string='Pólizas de seguros', help='Aplica para Colombia')
    x_ss_medprep  = fields.Integer(string='Medicina Prepagada para SS', help='Aplica para Colombia (No es descuento)')
    x_ben_medprep = fields.Integer(string='Beneficio base de retención por Medicina Prepagada', help='Aplica para Colombia')

    # COSTOS PROYECTOS
    x_benef_transp = fields.Float(string='Transporte')
    x_benef_educat = fields.Float(string='Educación')
    x_benef_comuni = fields.Float(string='Móvil')
    x_benef_intern = fields.Float(string='Internet')
    x_benef_vivien = fields.Float(string='Vivienda')
    x_benef_salud  = fields.Float(string='Seguro médico')
    x_benef_otros  = fields.Float(string='Otros')

    # -override
    @api.model
    def create(self, vals):
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])

        res = super(ciberc_contract, self).create(vals)
        employee_obj = self.env['hr.employee'].search([('id', '=', vals['employee_id'])], limit=1)
        if vals['working_hours']:
            self.employee_id.resource_id.write({'calendar_id': self.working_hours.id})

        if vals['date_start']:
            if vals['x_tipo_novedad_contrato_id'] == tipo_novedad_contrato_vinculacion.id:
                employee_obj.write({'joining_date': vals['date_start']})

        return res

    # -override
    @api.multi
    def write(self, vals):
        tipo_novedad_contrato_vinculacion = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])
        _logger.debug('***************')
        _logger.debug('tipo_novedad_contrato_vinculacion %s', tipo_novedad_contrato_vinculacion)
        res = super(ciberc_contract, self).write(vals)

        for contract_obj in self:
            employee_obj = self.env['hr.employee'].search([('id', '=', contract_obj.employee_id.id)], limit=1)
            # escribir el horario en datos de empleado
            if contract_obj.working_hours:
                contract_obj.employee_id.resource_id.write({'calendar_id': contract_obj.working_hours.id})
            # escribir la fecha de inicio de labores en datos de empleado
            if contract_obj.date_start:
                if contract_obj.x_tipo_novedad_contrato_id.id == tipo_novedad_contrato_vinculacion.id:
                    employee_obj.write({'joining_date': contract_obj.date_start})
            return res

    # para la tarea programada
    def contrato_sirve(self, contract):
        sirve = False
        contratos = self.env['hr.contract'].search([('employee_id', '=', contract.employee_id.id)], order='date_start').filtered(
            lambda c: datetime.strptime(c.date_start, '%Y-%m-%d').date() > datetime.strptime(contract.date_end, '%Y-%m-%d').date())
        for c in contratos:
            if not c.date_end:
                return True
        return sirve

    def llenar_bolsas(self):
        today = datetime.now().date()
        year_str = str(today.year)[2:]  # [2:] = 18 y [1:] = 018

        # Selección de tipos de novedad contrato
        tipo_novedad_despido_obj = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Despido')])
        tipo_novedad_renuncia_obj = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Renuncia')])
        tipo_novedad_vinculacion_obj = self.env['ciberc.tipo.novedad.contrato'].search([('name', '=', 'Vinculación laboral')])

        # filtro 1: contratos abiertos que coinciden en mes y día, de tipo novedad contrato vinculación, y sin fecha fin
        birthday_contracts_p1 = self.env['hr.contract'].search([('state', '=', 'open')]).filtered(
            lambda c: datetime.strptime(c.date_start, '%Y-%m-%d').date().month == today.month and
                      datetime.strptime(c.date_start, '%Y-%m-%d').date().day == today.day and
                      c.x_tipo_novedad_contrato_id.id == tipo_novedad_vinculacion_obj.id and
                      not c.date_end)

        # filtro 2: contratos cerrados que coinciden en mes y día, de tipo novedad contrato vinculación, con fecha fin y tipo de novedad de cierre de contrato distinto a despido o renuncia
        birthday_contracts_p2_aux = self.env['hr.contract'].search([('state', '=', 'close')]).filtered(
            lambda c: datetime.strptime(c.date_start, '%Y-%m-%d').date().month == today.month and
                      datetime.strptime(c.date_start, '%Y-%m-%d').date().day == today.day and
                      c.x_tipo_novedad_contrato_id.id == tipo_novedad_vinculacion_obj.id and
                      c.date_end and
                      c.x_tipo_novedad_cierre_contrato_id.id != tipo_novedad_despido_obj.id and
                      c.x_tipo_novedad_cierre_contrato_id.id != tipo_novedad_renuncia_obj.id
        )

        birthday_contracts = []
        for c in birthday_contracts_p1:
            birthday_contracts.append(c)
        for c in birthday_contracts_p2_aux:
            incluir = self.contrato_sirve(c)
            if incluir:
                birthday_contracts.append(c)

        for c in birthday_contracts:
            bag_size = c.annual_holiday
            asignacion_previa = False
            prefijo = ''
            prefijo_ext = ''

            if bag_size > 0:
                # 1. obtener prefijos
                if c.type_id.name.startswith( 'Nómina Local'.decode('utf-8') ):
                    prefijo = 'VAC'
                    prefijo_ext = 'Vacaciones'
                elif c.type_id.name.startswith( 'Servicios Profesionales'.decode('utf-8') ):
                    prefijo = 'DLI'
                    prefijo_ext = 'Días libres'
                # 2. obtener la bolsa de días
                bolsa_dias = self.env['hr.holidays.status'].search([('code', '=', prefijo + year_str)])
                # 3. CASO existe la bolsa de días -> consultar asignación previa
                if bolsa_dias:
                    asignacion_previa = self.env['hr.holidays'].search(['&', ('holiday_status_id', '=', bolsa_dias.id),
                                                                             ('employee_id', '=', c.employee_id.id)])
                # 4. CASO no existe la bolsa de días -> crear la bolsa
                else:
                    bolsa_dias = self.env['hr.holidays.status'].create({
                        'name': prefijo_ext + ' ' + str(today - timedelta(days=365)).year + '-' + str(today.year),
                        'code': prefijo + year_str,
                        'color_name': 'lavender',
                        'double_validation': False,
                        'limit': False,
                        'active': True
                    })
                # 5. asignar días bajo condiciones: bolsa días creada y sin asignación previa
                if bolsa_dias and len(asignacion_previa) == 0:
                    # asignar días a la bolsa
                    new_holiday = self.env['hr.holidays'].create({
                        'name': 'Asignación de bolsa de días por cumplimiento de año laborado',
                        'type': 'add',
                        'holiday_type': 'employee',
                        'holiday_status_id': bolsa_dias.id,
                        'employee_id': c.employee_id.id,
                        'department_id': c.department_id.id,
                        'number_of_days_calendar': bag_size,
                        'number_of_days_temp': bag_size,
                        'number_of_days': bag_size,
                        'state': 'validate'
                    })
        return

# clase creada por alltic que vuelve solo lectura el campo horario en empleado
class ciberc_resource(models.Model):
    _inherit = 'resource.resource'

    calendar_id = fields.Many2one("resource.calendar", string='Working Time', readonly=True, help="Define the schedule of resource")