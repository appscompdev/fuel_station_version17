from datetime import datetime, timedelta
from odoo import api, fields, models, _


class PetrolStation(models.Model):
    _name = 'petrol.station.pump'
    _description = 'Petrol Station Pump'

    name = fields.Char(string='Name')
    s_no = fields.Char(string='S NO')
    start_reading = fields.Float(string='Start Reading', digits=(12, 3))
    end_reading = fields.Float(string='End Reading', store=True, digits=(12, 3))
    last_reading = fields.Float(string='Last Reading', digits=(12, 3))
    employee_id = fields.Many2one('hr.employee', string='Employee')
    product_id = fields.Many2one('product.template', string='Fuel',
                                 domain=[('sale_ok', '=', True), ('detailed_type', '=', 'product')])
    product_ids = fields.Many2many('product.template', string='Fuel')
    pump_color = fields.Selection(string="Pump Color", related="product_id.pump_color")
    parent_id = fields.Many2one('petrol.station.pump', string='Category', )
    new_reading_update_time = fields.Datetime(string='Update Time')
    old_reading_update_time = fields.Datetime(string='Update Time')
    close_statement_check = fields.Boolean(string='Close Check')
    pump_entry_ids = fields.One2many('petrol.station.pump.line', 'petrol_pump')
    pump_sale_type = fields.Selection([
        ('nozzle', 'Nozzle'),
        ('tank', 'Bouches'),
        ('truck', 'Rental Truck'),
    ], string="Pump Sale Type", default="nozzle")
    bouche_capacity = fields.Float(string='Capacity')
    onhand_qty = fields.Float(string='On-hand')
    vehicle_no = fields.Char(string='Vehicle No')
    driver_id = fields.Many2one('hr.employee', string='Driver')

    model_id = fields.Many2one('fleet.vehicle.model', string='Model')
    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle Name')
    truck_rental = fields.Many2one('product.product', string='Rental Product')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    end_km = fields.Float(string="Ending Km", related='fleet_id.odometer')

    shift_id = fields.Many2one('employee.shift', string='Shift', related='employee_id.shift_id')

    @api.onchange('name')
    def compute_parent_id(self):
        if self.pump_sale_type == 'bouches':
            self.sudo().write({
                'parent_id': self.env.ref('petrol_station_dashboard.petrol_pump_bouches').id,
            })
        elif self.pump_sale_type == 'truck':
            self.write({
                'parent_id': self.env.ref('petrol_station_dashboard.petrol_pump_truck').id,
            })
        else:
            self.write({
                'parent_id': False
            })

    bouch_ids = fields.One2many('bouches.entry.line', 'bouche_id')
    bouches_sale_ids = fields.One2many('sale.order.wizard.line', 'bouche_id')

    # Send the data for dashboard
    def fetch_data(self):
        ott = fields.Datetime.now()
        val = {}
        data = []
        machines = self.env['petrol.station.pump'].search(
            [('parent_id', '!=', False)])
        employee_id = self.env['hr.employee'].search([('company_id', '=', self.env.company.id)], order='id')
        emp_data = [{'id': e.id, 'name': e.name} for e in employee_id]
        petty_cash = self.env['res.users'].has_group('petrol_station_dashboard.group_petty_cash')
        support_person = self.env['res.users'].has_group('petrol_station_dashboard.group_supportive_person')
        for machine in machines:
            if machine.old_reading_update_time:
                ott = machine.old_reading_update_time + timedelta(hours=5, minutes=30)
            product_data = [p.name for p in machine.product_ids]
            data.append({
                'petty_cash_received': machine.employee_id.contract_id.petty_cash_received,
                'onhand_amount': machine.employee_id.contract_id.onhand_amount,
                'available_onhand_amount': machine.employee_id.contract_id.available_onhand_amount,
                'petty_cash_last': machine.employee_id.contract_id.petty_cash_last,
                'machine_id': machine.id,
                'id': machine.id,
                'name': machine.name,
                's_no': machine.s_no,
                'pump_color': machine.pump_color,
                'parent_id': machine.parent_id.name,
                'start_reading': machine.start_reading,
                'end_reading': machine.end_reading,
                'last_reading': machine.last_reading,
                'employee_id': machine.employee_id.id,
                'fuel_id': machine.product_id.name,
                'old_update_time': ott,
                'new_update_time': machine.new_reading_update_time,
                'employee_name': machine.employee_id.name,
                'check': machine.close_statement_check,
                'petty_cash': petty_cash,
                'support_person': support_person,
                'fleet_id': machine.fleet_id.name,
                'last_odometer': machine.fleet_id.odometer,
                'pump_sale_type': machine.pump_sale_type,
                'bouche_capacity': machine.bouche_capacity,
                'bouche_onhand': machine.onhand_qty,
            })
            val['data'] = data
            val['emp_data'] = emp_data
            val['title'] = self.env.company.title
        emp_data[0] = {'id': 0, 'name': ''}
        print("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq", val['data'])
        return val

    def rental_truck_invoice(self, id, expense_dict, amount, start_km, end_km):
        partner = self.env['res.partner'].search([('default_customer', '=', True)])
        machines = self.env['petrol.station.pump'].search([('id', '=', id)])
        for k in expense_dict:
            if float(next(iter(k.values()))) > 0.00:
                expense = self.env['hr.expense'].sudo().create({
                    'name': 'Expense (' + next(iter(k.keys())) + ')',
                    'total_amount': float(next(iter(k.values()))),
                    'fleet_id': machines.fleet_id.id,
                })

        line_ids = []
        service_vals = (0, 0, {
            'product_id': machines.truck_rental.id,
            'price_unit': amount,
            'account_id': machines.truck_rental.property_account_income_id.id
            if machines.truck_rental.property_account_income_id.id
            else machines.truck_rental.categ_id.property_account_income_categ_id.id,
            'quantity': 1,
        })
        line_ids.append(service_vals)
        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'invoice_origin': machines.name,
            'narration': machines.name,
            'partner_id': partner.id,
            'partner_shipping_id': partner.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'fleet_id': machines.fleet_id.id,
            'invoice_line_ids': line_ids
        })
        invoice.action_post()
        machines.fleet_id.odometer = end_km

    def update_petty_cash(self, id, petty_amount):
        machines = self.env['petrol.station.pump'].search([('id', '=', id)])
        for i in machines:
            i.employee_id.contract_id.write({
                'petty_cash_received': True,
                'petty_cash_last': petty_amount,
                'onhand_amount': i.employee_id.contract_id.onhand_amount + float(petty_amount),
                'available_onhand_amount': i.employee_id.contract_id.available_onhand_amount + float(petty_amount),
            })

    def get_fuel_list(self, id):
        fuel_pro = []
        product_data = []
        machines = self.env['petrol.station.pump'].search([('id', '=', id)])
        for i in machines:
            product_data = [p.name for p in i.product_ids]
        fuel_pro.append({
            'fuel_pro': product_data,
        })
        return fuel_pro

    def update_end_time(self, end_time, end_reading, id):
        dt = False
        machines = self.env['petrol.station.pump'].search([('id', '=', id)])
        for i in machines:
            if end_time:
                dt = datetime.fromisoformat(end_time)
                dt -= timedelta(hours=5, minutes=30)
            i.update({
                'new_reading_update_time': dt,
                'last_reading': end_reading,
            })

    def update_close_statement(self, id):
        machines = self.env['petrol.station.pump'].search([('id', '=', id)])
        for i in machines:
            i.update({
                'close_statement_check': True,
            })

    def create_journal_entry(self, id, petty_cash_amt, employee):
        line_vals = []
        coa_id = self.env['account.account'].search([('code', '=', '100102'), ('name', '=', 'Petty Cash')])
        employee_id = self.env['hr.employee'].search([('id', '=', employee)])
        debit_line_vals = {
            'name': 'Petty Cash /' + str(employee_id.name) + '/' + str(datetime.today().date()),
            'account_id': coa_id.id,
            'debit': 0.00,
            'credit': float(petty_cash_amt),
        }
        line_vals.append((0, 0, debit_line_vals))
        credit_line_vals = {
            'name': 'Petty Cash /' + str(employee_id.name) + '/' + str(datetime.today().date()),
            'account_id': employee_id.coa_id.id,
            'debit': float(petty_cash_amt),
            'credit': 0.00,
        }
        line_vals.append((0, 0, credit_line_vals))
        journal_entry = self.env['account.move'].create({
            'move_type': 'entry',
            'ref': 'Petty Cash /' + str(employee_id.name) + '/' + str(datetime.today().date()),
            'invoice_line_ids': line_vals,
        })
        journal_entry.action_post()


class PetrolStationLine(models.Model):
    _name = 'petrol.station.pump.line'
    _description = 'Petrol Station Line'
    _rec_name = 'petrol_pump'

    petrol_pump = fields.Many2one('petrol.station.pump', string='Pump Name')
    pump_name = fields.Char(string='Pump Name')
    start_reading = fields.Float(string='Start Reading', digits=(12, 3))
    end_reading = fields.Float(string='End Reading', digits=(12, 3))
    amount = fields.Float(string='Amount')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    sub_employee_id = fields.Many2one('hr.employee', string='Supportive Employee')
    record_date = fields.Datetime(string='Date')
    fp_id = fields.Float(string='FP. ID')
    pump_sno = fields.Float(string='Pump Sno')
    pump_sno_new = fields.Char(string='Pump Sno')
    date_time = fields.Datetime(string='Date')
    nozzle_no = fields.Float(string='Nozzle No')
    shift_sale = fields.Float(string='Shift Sale')
    shift_vol = fields.Float(string='Shift Vol')
    cum_volume = fields.Float(string='Cum Volume')
    cum_sale = fields.Float(string='Cum Sale')
    advance_amount = fields.Float(string='Advance Amount')
    quotation_create = fields.Boolean(string='Quotation')
    advance_create = fields.Boolean(string='Advance')
    product_id = fields.Many2one('product.template', string='Fuel', related='petrol_pump.product_id')
    parent_id = fields.Many2one('petrol.station.pump', string='Parent', related='petrol_pump.parent_id', readonly=True)

    petrol_pump_daily = fields.Many2one('petrol.pump.daily.entry', string='Pump Daily Entry')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def create_record(self, dict):
        vals_update = {}
        print('+++++++++++++++++++++', dict)
        if dict:
            sub_emp = False
            if 'sub_emp_id' in dict:
                if dict['sub_emp_id']:
                    sub_emp = dict['sub_id']
            pump_line_id = self.create({
                'pump_sno_new': dict['pump_sno'],
                'cum_sale': dict['cum_sale'],
                'petrol_pump': dict['id'],
                'employee_id': dict['emp_id'],
                'sub_employee_id': sub_emp,
                'start_reading': dict['start_reading'],
                'end_reading': dict['end_reading'],
                'advance_amount': dict['advance_amount'],
                'advance_create': True,
            })
            pump_line_id = self.env['petrol.station.pump'].search([('id', '=', dict['id'])])
            if dict['end_reading'] != 0.00:
                vals_update.update({
                    'end_reading': dict['end_reading'],
                })
