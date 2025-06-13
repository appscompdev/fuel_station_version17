from odoo import api, fields, models, _
from odoo.fields import Command


class Contract(models.Model):
    _inherit = 'hr.contract'

    beta_amount = fields.Float(string='Beta Amount')
    onhand_amount = fields.Float(string='On-Hand Amount')
    available_onhand_amount = fields.Float(string='Available On-Hand Amount')
    petty_cash_received = fields.Boolean(string='Petty Cash Received')
    petty_cash_last = fields.Float(string='Petty Cash Last')


class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    pump_entry_ids = fields.One2many('petrol.station.pump.line', 'employee_id')
    outstanding = fields.Float(string='Outstanding')
    coa_id = fields.Many2one('account.account', string='Chart of Account')
    driver = fields.Boolean(string="Driver")
    license_no = fields.Char(string="License Number")
    license_reg_date = fields.Date(string="License Issued Date")
    license_expiry_date = fields.Date(string="License Expiry Date")
    shift_id = fields.Many2one('employee.shift', string='Shift')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    petrol_pump = fields.Many2one('petrol.station.pump', string='Pump Name', domain=[('parent_id', '!=', False)])
    beta_amount = fields.Float(string='Beta Amount')
    beta_hours = fields.Float(string='Beta Hours')
    beta_create = fields.Boolean(string='Beta Create')
    indent_reference = fields.Char(string='Indent Ref')
    sale_type = fields.Selection([
        ('indent', 'Indent'),
        ('normal', 'Normal'),
        ('test_sale', 'Test'), ], string="Sale Type", default="normal")
    employee_id = fields.Many2one('hr.employee', string='Employee Name')

    pay_ref = fields.Many2one('sale.order.wizard', string='Origin')

    def _prepare_confirmation_values(self):
        return {
            'state': 'sale',
        }

    # INVOICING
    def _prepare_invoice(self):
        self.ensure_one()

        return {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(
                self.partner_invoice_id)).id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_user_id': self.user_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [Command.set(self.transaction_ids.ids)],
            'company_id': self.company_id.id,
            'invoice_line_ids': [],
            'user_id': self.user_id.id,
            'invoice_date': self.pay_ref.date,
            'invoice_date_due': self.pay_ref.date,
        }

    def create_beta_line(self):
        if not self.beta_create:
            product_id = self.env['product.template'].sudo().search([('add_beta_line', '=', True)])
            for p in product_id:
                self.env['sale.order.line'].sudo().create({
                    'product_id': p.product_variant_id.id,
                    'product_template_id': p.id,
                    'product_uom_qty': self.beta_hours,
                    'product_uom': p.uom_id.id,
                    'price_unit': -self.beta_amount,
                    'tax_id': False,
                    'order_id': self.id,
                })
                self.env['hr.expense'].sudo().create({
                    'name': 'Beta Expense',
                    'product_id': self.env.ref('petrol_station_dashboard.expense_product_beta').id,
                    'employee_id': self.user_id.employee_id.id,
                    'sale_id': self.id,
                    'total_amount': self.beta_hours * self.beta_amount,
                })
                self.beta_create = True

    def set_picking_confirm(self):
        picking = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        for i in picking:
            i.button_validate()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    add_beta_line = fields.Boolean(string='Add Beta Line')
    pump_color = fields.Selection([('green', 'Green'), ('blue', 'Blue')], string="Pump Color", default="green")


class ProductProduct(models.Model):
    _inherit = "product.product"

    pump_color = fields.Selection([('green', 'Green'), ('blue', 'Blue')], string="Pump Color", default="green")


class HrExpense(models.Model):
    _inherit = "hr.expense"

    sale_id = fields.Many2one('sale.order', string='Sale')
    pay_ref = fields.Many2one('sale.order.wizard', string='Origin')
    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    density = fields.Float(string='Density')
    today_sale_price = fields.Float(string='MRP')
    difference_amount = fields.Float(string='Margin/L')
    sub_total = fields.Monetary(string='Sub Total')

    @api.onchange('sub_total')
    def depends_sub_total(self):
        if self.product_qty and self.sub_total:
            self.write({
                'price_unit': self.sub_total / self.product_qty,
            })

    @api.onchange('today_sale_price')
    def depends_price_unit(self):
        if self.price_unit and self.today_sale_price:
            self.write({
                'difference_amount': self.today_sale_price - self.price_unit,
            })


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_customer = fields.Boolean(string='Default Customer')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    pay_ref = fields.Many2one('sale.order.wizard', string='Origin')
    entry_type = fields.Selection([
        ('advance', 'Advance'),
        ('credit', 'Credit Payment')
    ], string="Entry Type", default="advance")


class AccountMove(models.Model):
    _inherit = "account.move"

    pay_ref = fields.Many2one('sale.order.wizard', string='Origin')
    bouch_ref = fields.Many2one('bouches.entry.details', string='Origin')
    indent_no = fields.Char(string='Indent No')
    pump_sale_type = fields.Selection([
        ('nozzle', 'Nozzle'),
        ('tank', 'Bouches')
    ], string="Pump Sale Type", default="nozzle")
    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle')

    @api.depends('needed_terms')
    def _compute_invoice_date_due(self):
        for move in self:
            if move.pay_ref:
                today = move.pay_ref.date.date()
            else:
                today = fields.Date.context_today(self)
            move.invoice_date_due = move.needed_terms and max(
                (k['date_maturity'] for k in move.needed_terms.keys() if k),
                default=False,
            ) or move.invoice_date_due or today


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_indent_count')

    def _compute_expense_count(self):
        self.expense_count = self.sudo().env['hr.expense'].sudo(). \
            search_count([('fleet_id', '=', self.id)])

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
            'domain': [('fleet_id', '=', self.id)],
        }

    def _compute_indent_count(self):
        self.invoice_count = self.sudo().env['account.move'].sudo(). \
            search_count([('fleet_id', '=', self.id)])

    def get_indent_details(self):
        self.sudo().ensure_one()
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_out_invoice_tree')
        return {
            'name': _('Invoice Details'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('fleet_id', '=', self.id)],
        }


class Company(models.Model):
    _inherit = "res.company"

    title = fields.Char(string="Title")


class Picking(models.Model):
    _inherit = "stock.picking"

    pay_ref = fields.Many2one('sale.order.wizard', string='Origin', compute='_compute_pay_ref')

    @api.depends('sale_id')
    def _compute_pay_ref(self):
        for i in self:
            if i.sale_id:
                i.pay_ref = i.sale_id.pay_ref.id
            else:
                i.pay_ref = False

    def _action_done(self):
        self._check_company()

        todo_moves = self.move_ids.filtered(
            lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_ids.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        self.write({'date_done': self.pay_ref.date, 'priority': '0'})
        if self.pay_ref:
            for sm in self.move_ids:
                sm.date = self.date
            for sl in self.move_line_ids:
                sl.date = self.date

        # if incoming/internal moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(
            lambda p: p.picking_type_id.code in ('incoming', 'internal')).move_ids.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
        return True
