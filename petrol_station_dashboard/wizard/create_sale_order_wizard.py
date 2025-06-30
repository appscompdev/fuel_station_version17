from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tests.common import Form, tagged
from datetime import datetime


class SaleOrderCreateWizard(models.Model):
    _name = 'sale.order.wizard'
    _description = 'Sale Order Create Wizard'
    _rec_name = 'name'
    _order = 'create_date desc'

    @api.model
    def default_get(self, fields):
        global i
        line_val = []
        test_line_val = []
        petty_line_val = []
        test_content = ['quantity', 'quality']
        res = super().default_get(fields)
        context = dict(self._context or {})
        pump_entry_line = self.env['petrol.station.pump.line'].sudo().search([('id', 'in', context.get('active_ids'))])
        payment = self.env['account.journal'].sudo().search(
            [('type', '=', 'cash'), ('name', '=', 'Cash'), ('company_id', '=', self.env.company.id)])
        coa_id = self.env['account.account'].search(
            [('name', '=', 'Petty Cash'), ('company_id', '=', self.env.company.id)])
        for i in pump_entry_line:
            line = (0, 0, {
                'description': i.petrol_pump.name + ' (Advance Amount)',
                'date': i.create_date,
                'amount': i.advance_amount,
                'employee_id': i.employee_id.id,
                'sub_employee_id': i.sub_employee_id.id,
                'payment_mode': payment.id,
                'record_type': 'advance',
                'payment_create': True,
                'default': True,
            })
            line_val.append(line)
        for a in test_content:
            test_line = (0, 0, {
                'test_record_type': a,
            })
            test_line_val.append(test_line)
        for jk in range(2):
            test_line = {
                'employee_id': i.employee_id.id,
                'description': 'Petty Cash Return /' + i.employee_id.name + '/' + str(datetime.today().date()),
            }
            if jk == 0:
                test_line.update({
                    'coa_id': coa_id.id
                })
            else:
                test_line.update({
                    'coa_id': i.employee_id.coa_id.id
                })
            petty_line_val.append((0, 0, test_line))
        res["journal_ids"] = petty_line_val
        res["line_ids"] = line_val
        res["test_sale_ids"] = test_line_val
        res["pump_id"] = i.petrol_pump.id
        res["start_reading"] = i.petrol_pump.end_reading
        res["end_reading"] = i.petrol_pump.last_reading
        return res

    def _get_default_bouche_id(self):
        return self.env['petrol.station.pump'].search(
            [('pump_sale_type', '=', 'tank'), ('parent_id', '!=', False)]).id

    pump_entry_ids = fields.One2many('petrol.station.pump.line', 'petrol_pump')
    name = fields.Char(string='Name')
    line_ids = fields.One2many('sale.order.wizard.line', 'sale_create_id')
    expense_ids = fields.One2many('sale.order.wizard.line', 'expense_sale_id')
    credit_sale_ids = fields.One2many('sale.order.wizard.line', 'credit_sale_id')
    test_sale_ids = fields.One2many('sale.order.wizard.line', 'test_sale_id')
    pump_id = fields.Many2one('petrol.station.pump', string='Pump Name')
    product_id = fields.Many2one('product.template', string='Fuel', domain=[('sale_ok', '=', True)],
                                 related='pump_id.product_id')
    start_reading = fields.Float(string='Start Reading', digits=(12, 3))
    end_reading = fields.Float(string='End Reading', digits=(12, 3))
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    total_reading = fields.Float(string='Total Reading', compute='_onchange_end_reading', digits=(12, 3))
    today_price = fields.Monetary(string='Today Price', required=True)
    total_price = fields.Monetary(string='Total Price', compute='_compute_total_price')
    working_hours = fields.Float(string='Working Hours', related='pump_id.employee_id.shift_id.shift_duration')
    actual_working_hours = fields.Float(string='Actual Working Hours')
    final_total_price = fields.Monetary(string='Total Price', compute='_compute_total_price')
    total_price_sub = fields.Monetary(string='SubTotal Price', compute='_compute_sub_total_price')
    balance_price = fields.Monetary(string='Balance Price', compute='_compute_balance_total_price')
    state = fields.Selection([
        ("draft", "Draft"),
        ("done", "Done"),
    ], string="State", default='draft')
    payment_count = fields.Integer(string='Payment Count', compute='_compute_payment_count')
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
    sale_count = fields.Integer(string='Sales Count', compute='_compute_sale_count')
    indent_count = fields.Integer(string='Indent Count', compute='_compute_indent_count')
    test_sale_count = fields.Integer(string='Test Sales Count', compute='_compute_test_sale_count')
    test_sale_value = fields.Float(string='Test Sale Value', compute='get_test_sale_value')
    test_sale_amount = fields.Monetary(string='Test Sale Amount', compute='get_final_sale_count')
    final_sale_count = fields.Float(string='Final Sale', compute='get_final_sale_count')

    final_sale_amount = fields.Monetary(string='Final Amount', compute='get_final_sale_count')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    picking_id = fields.Many2one('stock.picking', string='Delivery')
    return_id = fields.Many2one('stock.picking', string='Return')
    test_need = fields.Boolean(string='QC/QT Check')
    credit_sale_amount = fields.Monetary(string='Credit Sale Amount', compute='_compute_sub_total_price')
    total_expense_amount = fields.Monetary(string='Expense Amount', compute='_compute_sub_total_price')
    total_advance_amount = fields.Monetary(string='Advance Amount', compute='_compute_sub_total_price')
    journal_ids = fields.One2many('sale.order.wizard.line', 'journal_entry_id')
    return_petty_cash = fields.Monetary(string='Petty Cash Return')
    emp_petty_cash_onhand = fields.Monetary(string='On-hand Petty Cash', compute='compute_onhand_petty_cash')
    emp_petty_cash_balance = fields.Monetary(string='Balance Petty Cash')

    bouches_sale_ids = fields.One2many('sale.order.wizard.line', 'bouches_sale_id')
    bouches_need = fields.Boolean(string='Bouches')

    oil_sale_ids = fields.One2many('sale.order.wizard.line', 'oil_sale_id')
    oil_sale_amount = fields.Monetary(string='Oil Sale Amount', compute='_compute_sub_total_price')
    date = fields.Datetime(string='Date', default=lambda self: fields.datetime.now())
    credit_payment_ids = fields.One2many('sale.order.wizard.line', 'credit_payment_id')
    credit_payment_amount = fields.Monetary(string='Credit Payment Amount', compute='_compute_sub_total_price')

    day_difference = fields.Float(string='Day Difference')

    def get_bouche_sale_details(self):
        self.sudo().ensure_one()
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_out_invoice_tree')
        return {
            'name': _('Bouche Sale Details'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('pay_ref', '=', self.id), ('pump_sale_type', '=', 'tank'),
                       ('move_type', '=', 'out_invoice')],
        }

    @api.onchange('added_qty')
    def compute_added_qty(self):
        for a in self:
            if a.added_qty > 0.00:
                if a.bouche_id.bouche_capacity < (a.added_qty + a.bouches_available):
                    raise UserError('Alert')
                else:
                    a.bou_total_qty = a.added_qty + a.bouches_available
            else:
                a.bou_total_qty = a.bouches_available

    @api.onchange('bouche_id')
    def compute_bounche_available(self):
        for a in self:
            if a.bouche_id:
                a.bouches_available = a.bouche_id.onhand_qty
            else:
                a.bouches_available = False

    def bouch_sale_quantity_update(self):
        bou_saled_qty = 0.00
        for i in self.bouches_sale_ids:
            bou_saled_qty += i.bouche_sale_qty
        self.bouche_id.onhand_qty = self.bou_total_qty - bou_saled_qty

    @api.depends('pump_id', 'return_petty_cash')
    def compute_onhand_petty_cash(self):
        for a in self:
            if a.pump_id:
                a.emp_petty_cash_onhand = a.pump_id.employee_id.contract_id.available_onhand_amount
            else:
                a.emp_petty_cash_onhand = 0.00
            if a.return_petty_cash > 0.00:
                a.emp_petty_cash_balance = a.pump_id.employee_id.contract_id.available_onhand_amount - a.return_petty_cash
            else:
                a.emp_petty_cash_balance = a.pump_id.employee_id.contract_id.available_onhand_amount

    @api.onchange('return_petty_cash')
    def compute_petty_cash_return(self):
        for a in self:
            if a.return_petty_cash > 0.00:
                for b in a.journal_ids:
                    if b.coa_id == a.pump_id.employee_id.coa_id:
                        b.credit = a.return_petty_cash
                    else:
                        b.debit = a.return_petty_cash
            else:
                for b in a.journal_ids:
                    b.credit = 0.00
                    b.debit = 0.00

    @api.depends('test_sale_ids')
    def get_test_sale_value(self):
        test_sale_value = 0.00
        for i in self:
            for j in i.test_sale_ids:
                test_sale_value += j.test_qty
            i.test_sale_value = test_sale_value

    @api.depends('line_ids', 'expense_ids', 'credit_sale_ids', 'test_sale_ids', 'today_price', 'return_petty_cash',
                 'oil_sale_amount')
    def get_final_sale_count(self):
        for i in self:
            i.final_sale_count = i.total_reading - i.test_sale_value
            i.final_sale_amount = i.final_sale_count * i.today_price
            i.test_sale_amount = i.test_sale_value * i.today_price
            if i.return_petty_cash > 0.00:
                i.final_sale_amount += i.return_petty_cash
            if i.oil_sale_amount > 0.00:
                i.final_sale_amount += i.oil_sale_amount

    def _compute_payment_count(self):
        self.payment_count = self.sudo().env['account.payment'].sudo(). \
            search_count([('pay_ref', '=', self.id)])

    def get_payment_details(self):
        self.sudo().ensure_one()
        form_view = self.env.ref('account.view_account_payment_form')
        tree_view = self.env.ref('account.view_account_payment_tree')
        return {
            'name': _('Payment Details'),
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('pay_ref', '=', self.id)],
        }

    def _compute_expense_count(self):
        self.expense_count = self.sudo().env['hr.expense'].sudo(). \
            search_count([('pay_ref', '=', self.id)])

    def get_expense_details(self):
        self.sudo().ensure_one()
        form_view = self.env.ref('hr_expense.hr_expense_view_form')
        tree_view = self.env.ref('hr_expense.view_my_expenses_tree')
        return {
            'name': _('Expense Details'),
            'res_model': 'hr.expense',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('pay_ref', '=', self.id)],
        }

    def _compute_sale_count(self):
        self.sale_count = self.sudo().env['sale.order'].sudo(). \
            search_count([('pay_ref', '=', self.id)])

    def get_sale_details(self):
        self.sudo().ensure_one()
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_quotation_tree_with_onboarding')
        return {
            'name': _('Sales Details'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('pay_ref', '=', self.id)],
        }

    def _compute_test_sale_count(self):
        self.test_sale_count = self.sudo().env['sale.order'].sudo(). \
            search_count([('pay_ref', '=', self.id), ('sale_type', '=', 'test_sale')])

    def get_test_sale_details(self):
        self.sudo().ensure_one()
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_quotation_tree_with_onboarding')
        return {
            'name': _('Test Sales Details'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('pay_ref', '=', self.id), ('sale_type', '=', 'test_sale')],
        }

    def _compute_indent_count(self):
        self.indent_count = self.sudo().env['account.move'].sudo(). \
            search_count([('pay_ref', '=', self.id), ('move_type', '=', 'out_invoice')])

    def get_indent_details(self):
        self.sudo().ensure_one()
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_out_invoice_tree')
        return {
            'name': _('Indent Details'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('pay_ref', '=', self.id), ('move_type', '=', 'out_invoice')],
        }

    @api.depends('end_reading')
    def _onchange_end_reading(self):
        for i in self:
            if i.end_reading != 0.00:
                if i.end_reading <= i.start_reading:
                    i.total_reading = 0.00
                else:
                    i.total_reading = i.end_reading - i.start_reading
            else:
                i.total_reading = 0.00

    @api.depends('total_price', 'total_price_sub')
    def _compute_balance_total_price(self):
        for i in self:
            cp_amount = 0.00
            i.balance_price = i.final_total_price - i.total_price_sub - cp_amount

    @api.depends('line_ids', 'expense_ids', 'credit_sale_ids', 'test_sale_ids', 'bouches_sale_ids', 'oil_sale_ids',
                 'credit_payment_ids')
    def _compute_sub_total_price(self):
        total_price = 0.00
        total_expense = 0.00
        total_credit = 0.00
        oil_sale_amount = 0.00
        credit_payment_amount = 0.00
        for a in self:
            for b in a.line_ids:
                total_price += b.amount
            a.total_advance_amount = total_price
            for c in a.expense_ids:
                total_price += c.amount
                total_expense += c.amount
            for d in a.credit_sale_ids:
                total_price += d.amount
                total_credit += d.amount
            a.total_price_sub = total_price
            a.total_expense_amount = total_expense
            a.credit_sale_amount = total_credit
            for o in a.oil_sale_ids:
                oil_sale_amount += o.oil_amount
            a.oil_sale_amount = oil_sale_amount
            for cp in a.credit_payment_ids:
                credit_payment_amount += cp.amount
            a.credit_payment_amount = credit_payment_amount
            for ts in a.test_sale_ids:
                a.total_price_sub += ts.total_amount

    @api.depends('today_price', 'end_reading', 'return_petty_cash', 'oil_sale_amount', 'credit_payment_amount',
                 'total_price')
    def _compute_total_price(self):
        for i in self:
            if i.total_reading != 0.00 and i.today_price != 0.00:
                i.total_price = i.total_reading * i.today_price
                i.final_total_price = i.total_reading * i.today_price
            else:
                i.total_price = 0.00
                i.final_total_price = 0.00

            if i.return_petty_cash > 0.00:
                i.final_total_price += i.return_petty_cash

            if i.oil_sale_amount > 0.00:
                i.final_total_price += i.oil_sale_amount

            if i.credit_payment_amount > 0.00:
                i.final_total_price += i.credit_payment_amount

    def action_create_return_order(self):
        stock_return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_ids=self.picking_id.ids, active_id=self.picking_id.id, active_model='stock.picking'))
        stock_return_picking = stock_return_picking_form.save()
        for y in stock_return_picking.product_return_moves:
            if self.product_id.product_variant_id == y.product_id:
                y.quantity = self.test_sale_value
            else:
                y.quantity = 0.00

        stock_return_picking_action = stock_return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(stock_return_picking_action['res_id'])

        self.return_id = return_pick.id

        if return_pick.state == 'assigned':
            for mi in return_pick.move_ids_without_package:
                mi.quantity = mi.product_uom_qty
            return_pick.button_validate()

    def _create_credit_payment(self):
        for cp in self.credit_payment_ids:
            vals = {
                'payment_type': 'inbound',
                'amount': cp.amount,
                'journal_id': cp.payment_mode.id,
                'ref': 'Credit Sale Payment (' + cp.customer_id.name + ')',
                'partner_id': cp.customer_id.id,
                'pay_ref': self.id,
                'date': self.date.date(),
                'entry_type': 'credit',
            }
            payment = self.env['account.payment'].sudo().create(vals)
            payment.action_post()

    def _create_expenses(self):
        for e in self.expense_ids:
            expense = self.env['hr.expense'].create({
                'name': e.description,
                'product_id': e.product_id.id,
                'total_amount': e.amount,
                'pay_ref': self.id,
                'date': self.date.date(),
                'payment_mode': 'company_account',
                'employee_id': e.employee_id.id,
            })
            report_data = expense._get_default_expense_sheet_values()
            expense_sheet = self.env['hr.expense.sheet'].sudo().create(report_data)
            expense_sheet.action_submit_sheet()
            expense_sheet.action_approve_expense_sheets()
            expense_sheet.action_sheet_move_create()

    def action_create_sale_order(self):
        if self.balance_price == 0.00:
            sale_line_ids = []
            petty_line_vals = []
            test_qty = 0.00
            ad_amount = 0.00
            ad_payment_mode = 0.00
            ad_description = ''
            context = dict(self._context or {})
            pump_entry_line = self.env['petrol.station.pump.line'].sudo().search(
                [('id', 'in', context.get('active_ids'))])
            for pl in pump_entry_line:
                pl.quotation_create = True
            partner = self.env['res.partner'].search([('default_customer', '=', True)])
            for l in self.line_ids:
                ad_amount += l.amount
                ad_payment_mode = l.payment_mode.id
                ad_description = l.description
            if ad_amount > 0.00:
                ad_amount -= self.credit_payment_amount
                vals = {
                    'payment_type': 'inbound',
                    'amount': ad_amount,
                    'journal_id': ad_payment_mode,
                    'ref': ad_description,
                    'entry_type': 'advance',
                    'partner_id': partner.id,
                    'pay_ref': self.id,
                    'date': self.date.date(),
                }
                payment = self.env['account.payment'].sudo().create(vals)
                payment.action_post()
            for c in self.credit_sale_ids:
                line_ids = []
                service_vals = (0, 0, {
                    'name': c.credit_sale_id.pump_id.product_id.product_variant_id.name,
                    'product_id': c.credit_sale_id.pump_id.product_id.product_variant_id.id,
                    'price_unit': c.amount,
                    'account_id': c.credit_sale_id.pump_id.product_id.property_account_income_id.id if c.credit_sale_id.pump_id.product_id.property_account_income_id
                    else c.credit_sale_id.pump_id.product_id.categ_id.property_account_income_categ_id.id,
                    'quantity': 1,
                })
                line_ids.append(service_vals)
                invoice = self.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'invoice_origin': self.pump_id.name,
                    'narration': self.pump_id.name,
                    'partner_id': c.customer_id.id,
                    'partner_shipping_id': c.customer_id.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'pay_ref': self.id,
                    'invoice_date': self.date,
                    'indent_no': c.indent_no,
                    'invoice_line_ids': line_ids
                })
                invoice.action_post()
            if self.return_petty_cash > 0.00:
                for journal in self.journal_ids:
                    debit_line_vals = {
                        'name': 'Petty Cash /' + '/' + self.pump_id.name + '/' + str(
                            journal.employee_id.name) + '/' + str(
                            datetime.today().date()),
                        'account_id': journal.coa_id.id,
                        'debit': journal.debit,
                        'credit': journal.credit,
                    }
                    petty_line_vals.append((0, 0, debit_line_vals))
                journal_entry = self.env['account.move'].create({
                    'move_type': 'entry',
                    'ref': 'Petty Cash /' + self.pump_id.name + '/' + str(self.pump_id.employee_id.name) + '/' + str(
                        datetime.today().date()),
                    'invoice_line_ids': petty_line_vals,
                })
                journal_entry.action_post()
                contract = self.pump_id.employee_id.contract_id
                contract.write({
                    'petty_cash_received': False,
                    'available_onhand_amount': contract.available_onhand_amount - self.return_petty_cash,
                })

            for bo in self.bouches_sale_ids:
                bo.bouche_id.onhand_qty += bo.bouche_sale_qty

            for f in self.test_sale_ids:
                test_qty += f.test_qty

            sale_line_id = {
                'product_template_id': self.pump_id.product_id.id,
                'product_id': self.pump_id.product_id.product_variant_id.id,
                'name': self.pump_id.product_id.name,
                'product_uom_qty': self.total_reading,
                'product_uom': self.pump_id.product_id.uom_id.id,
                'price_unit': self.today_price,
            }
            sale_line_ids.append((0, 0, sale_line_id))
            for oil in self.oil_sale_ids:
                sale_line_id = {
                    'product_id': oil.oil_id.id,
                    'name': oil.oil_id.display_name,
                    'product_uom_qty': oil.oil_qty,
                    'product_uom': oil.oil_id.uom_id.id,
                    'price_unit': oil.list_price,
                }
                sale_line_ids.append((0, 0, sale_line_id))
            sale = self.env['sale.order'].sudo().create({
                'partner_id': partner.id,
                'employee_id': self.pump_id.employee_id.id,
                'petrol_pump': self.pump_id.id,
                'pay_ref': self.id,
                'date_order': self.date,
                'effective_date': self.date,
                'create_date': self.date,
                'order_line': sale_line_ids,
            })
            sale.action_confirm()
            self.sale_id = sale.id
            for x in sale.picking_ids:
                x.date = self.date
                if x.state == 'assigned':
                    for mi in x.move_ids_without_package:
                        mi.quantity = mi.product_uom_qty
                        mi.date = self.date.date()
                    x.button_validate()
                    self.picking_id = x.id
                    if self.test_need:
                        self.action_create_return_order()
            sale._create_invoices()
            for invoice in sale.invoice_ids:
                invoice.action_post()
                advance_pay = self.env['account.payment'].search(
                    [('pay_ref', '=', self.id), ('entry_type', '=', 'advance')])
                if advance_pay:
                    for aa in advance_pay:
                        if aa.state == 'posted' and aa.amount != 0.00:
                            lines = aa.move_id.line_ids.filtered(lambda line: line.credit > 0)
                            lines += invoice.line_ids.filtered(
                                lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                            lines.reconcile()

            self.pump_id.start_reading = self.pump_id.end_reading
            self.pump_id.end_reading = self.end_reading
            self.pump_id.close_statement_check = False
            self.pump_id.old_reading_update_time = self.pump_id.new_reading_update_time
            self.state = 'done'
            self._create_credit_payment()
            self._create_expenses()
        else:
            raise UserError(_('Balance Price should be zero.'))

    @api.model
    def create(self, values):
        values['name'] = self.sudo().env['ir.sequence'].get('sale.order.wizard') or 'New'
        res = super(SaleOrderCreateWizard, self).create(values)
        return res


class SaleOrderCreateWizardLine(models.Model):
    _name = 'sale.order.wizard.line'
    _description = 'Sale Order Create Wizard Line'

    def _get_default_bouche_id(self):
        return self.env['petrol.station.pump'].search(
            [('pump_sale_type', '=', 'tank'), ('parent_id', '!=', False)]).id

    sale_create_id = fields.Many2one('sale.order.wizard', string='Sale Create')
    expense_sale_id = fields.Many2one('sale.order.wizard', string='Sale Create')
    credit_sale_id = fields.Many2one('sale.order.wizard', string='Sale Create')
    test_sale_id = fields.Many2one('sale.order.wizard', string='Sale Create')
    credit_payment_id = fields.Many2one('sale.order.wizard', string='Sale Create')
    description = fields.Char(string='Description', compute='compute_description', readonly=False)
    date = fields.Datetime(string='Date', default=lambda self: fields.datetime.now())
    amount = fields.Float(string='Amount')
    default = fields.Boolean(string='Default')
    payment_create = fields.Boolean(string='Payment', compute='compute_payment_mode')
    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    sub_employee_id = fields.Many2one('hr.employee', string='Supportive Employee')
    customer_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)])
    product_id = fields.Many2one('product.product', string='Expense Type', domain=[('can_be_expensed', '=', True)])
    payment_mode = fields.Many2one('account.journal', string='Payment Mode',
                                   domain=lambda self: [('company_id', '=', self.env.user.company_id.id),
                                                        ('type', 'in', ['cash', 'bank'])])

    indent_no = fields.Char(string='Indent No')
    record_type = fields.Selection([
        ("advance", "Advance"),
        ("online", "Online"),
        ("credit", "Credit Sale"),
        ("beta", "Beta amount"),
        ("food", "Food amount"),
        ("travel", "Travel amount"),
        ("others", "Others"),
    ], default="advance")

    ad_record_type = fields.Selection([
        ("advance", "Advance"),
        ("online", "Online"),
        ("final", "Final Payment"),
    ], default="advance", string='Record Type')
    ex_record_type = fields.Selection([
        ("expense", "Expense"),
    ], default="expense", string='Record Type')
    cr_record_type = fields.Selection([
        ("credit", "Credit Sale"),
    ], default="credit", string='Record Type')

    test_record_type = fields.Selection([
        ("quantity", "Quantity"),
        ("quality", "Quality"),
    ], default="quantity", string='Record Type')

    fuel_id = fields.Many2one('product.template', string='Fuel', domain=[('sale_ok', '=', True)],
                              related='test_sale_id.pump_id.product_id')
    test_qty = fields.Float(string='Liters')
    total_amount = fields.Monetary(string='Total', compute='compute_total_amount')
    per_liter_amount = fields.Monetary(string='Amount', related='test_sale_id.today_price')

    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id.id)

    journal_entry_id = fields.Many2one('sale.order.wizard', string='Sale Create')
    coa_id = fields.Many2one('account.account', string='Account')
    debit = fields.Monetary(string='Debit')
    credit = fields.Monetary(string='Credit')

    bouches_sale_id = fields.Many2one('sale.order.wizard', string='Bouches Sale')
    bouche_id = fields.Many2one('petrol.station.pump', string='Bouche Name', domain=[
        ('pump_sale_type', '=', 'tank'),
        ('parent_id', '!=', False)
    ])
    nozzle_id = fields.Many2one('petrol.station.pump', string='Nozzle Name', domain=[
        ('pump_sale_type', '=', 'nozzle'),
        ('parent_id', '!=', False)
    ], related='bouches_sale_id.pump_id')
    bouche_capacity = fields.Float(string='Capacity')
    onhand_qty = fields.Float(string='On-hand')
    vehicle_no = fields.Char(string='Vehicle No', compute='compute_vechicle_no')
    vehicle_number = fields.Char(string='Vehicle No', compute='compute_vechicle_no')
    driver_id = fields.Many2one('hr.employee', string='Driver')
    bouche_sale_qty = fields.Float(string='Qty')
    bouche_amount = fields.Float(string='Amount', compute='compute_bouche_amount')
    payment_type = fields.Selection([
        ('received', 'Received'),
        ('later', 'Credit')
    ], string="Payment Type", default="received")

    oil_sale_id = fields.Many2one('sale.order.wizard', string='Oil Sale')

    oil_id = fields.Many2one('product.product', string='Product', domain=[('detailed_type', '=', 'product'),
                                                                          ('categ_id.name', '=', 'Oil')])
    list_price = fields.Float(string='Price', compute='get_product_price')
    oil_qty = fields.Float(string='Qty')
    oil_amount = fields.Float(string='Amount', compute='get_product_price', readonly=False)
    indent_vehicle = fields.Many2one('indent.vehicle', string='Vehicle No',
                                     domain="[('customer_id', '=', customer_id)]")

    @api.depends('oil_id', 'oil_qty')
    def get_product_price(self):
        for o in self:
            if o.oil_id:
                o.list_price = o.oil_id.list_price
                o.oil_amount = o.oil_qty * o.oil_id.list_price
            else:
                o.list_price = 0.00
                o.oil_amount = 0.00

    @api.onchange('bouche_id')
    def get_bouches_details(self):
        for a in self:
            if a.bouche_id:
                a.bouche_capacity = a.bouche_id.bouche_capacity
                a.onhand_qty = a.bouche_id.onhand_qty
                a.vehicle_no = a.bouche_id.vehicle_no
                a.driver_id = a.bouche_id.driver_id.id
            else:
                a.bouche_capacity = False
                a.onhand_qty = False
                a.vehicle_no = False
                a.driver_id = False

    @api.depends('bouche_sale_qty')
    def compute_bouche_amount(self):
        for i in self:
            if i.bouche_sale_qty:
                i.bouche_amount = i.bouche_sale_qty * i.bouches_sale_id.today_price
                i.onhand_qty += i.bouche_sale_qty
            else:
                i.bouche_amount = 0.00
                i.onhand_qty = i.bouche_id.onhand_qty

    @api.depends('customer_id', 'payment_mode', 'cr_record_type', 'product_id')
    def compute_description(self):
        for i in self:
            if i.expense_sale_id and i.payment_mode:
                i.description = (dict(i._fields['ex_record_type'].selection).get(
                    i.ex_record_type)) + '(' + i.payment_mode.name + ')'
            if i.credit_sale_id and i.customer_id:
                i.description = (dict(i._fields['cr_record_type'].selection).get(
                    i.cr_record_type)) + '(' + i.customer_id.name + ')'
            if i.sale_create_id and i.payment_mode:
                i.description = "Advance Amount (" + i.payment_mode.name + ")"

    @api.depends('payment_mode')
    def compute_payment_mode(self):
        for i in self:
            if i.payment_mode:
                i.payment_create = True
            else:
                i.payment_create = False

    @api.depends('test_qty', 'per_liter_amount')
    def compute_total_amount(self):
        for i in self:
            if i.test_qty > 0.00:
                i.total_amount = i.per_liter_amount * i.test_qty
            else:
                i.total_amount = 0.00

    @api.depends('customer_id')
    def compute_vechicle_no(self):
        for i in self:
            if i.credit_sale_id:
                vehicle = self.env['indent.vehicle'].search([('customer_id', '=', i.customer_id.id)])
                if vehicle:
                    i.write({
                        'vehicle_number': vehicle.name,
                        'vehicle_no': vehicle.name,
                    })
                else:
                    i.write({
                        'vehicle_number': False,
                        'vehicle_no': False,
                    })
            else:
                i.write({
                    'vehicle_number': False,
                    'vehicle_no': False,
                })
