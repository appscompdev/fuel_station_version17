from odoo import models, fields, api, _


class BouchesEntryDetails(models.Model):
    _name = 'bouches.entry.details'
    _description = 'Bouches Entry Details'

    name = fields.Char(string='Name', default='New')
    date = fields.Datetime(string='Date', default=lambda self: fields.Datetime.now())
    user = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    bouch_ids = fields.One2many('bouches.entry.line', 'bouch_entry')
    today_price = fields.Float(string='Today Price')
    state = fields.Selection([
        ("draft", "Draft"),
        ("done", "Done"),
    ], string="State", default='draft')
    bouche_id = fields.Many2one('petrol.station.pump', string='Bouche Name', domain=[
        ('pump_sale_type', '=', 'tank'),
        ('parent_id', '!=', False)
    ])
    bou_total_qty = fields.Float(string='Total', compute='compute_bouche_total_sale')

    @api.depends('bouch_ids')
    def compute_bouche_total_sale(self):
        for i in self:
            bou_saled_qty = 0.00
            for j in i.bouch_ids:
                bou_saled_qty += j.bouche_sale_qty
            i.bou_total_qty = bou_saled_qty

    def action_confirm(self):
        for bo in self.bouch_ids:
            bouche_payment = self.env['account.payment'].sudo().create({
                'payment_type': 'inbound',
                'amount': bo.bouche_amount,
                'journal_id': bo.payment_mode.id,
                'ref': 'Bouches Sale (' + bo.customer_id.name + ')',
                'partner_id': bo.customer_id.id,
            })
            bouche_payment.action_post()
            line_ids = []
            service_vals = (0, 0, {
                'name': bo.bouche_id.product_id.product_variant_id.display_name,
                'product_id': bo.bouche_id.product_id.product_variant_id.id,
                'price_unit': bo.bouch_entry.today_price,
                'account_id': bo.bouche_id.product_id.property_account_income_id.id if bo.bouche_id.product_id.property_account_income_id
                else bo.bouche_id.product_id.categ_id.property_account_income_categ_id.id,
                'quantity': bo.bouche_sale_qty,
            })
            line_ids.append(service_vals)
            invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'invoice_origin': self.bouche_id.name,
                'narration': self.bouche_id.name,
                'partner_id': bo.customer_id.id,
                'partner_shipping_id': bo.customer_id.id,
                'currency_id': self.env.user.company_id.currency_id.id,
                'bouch_ref': self.id,
                'pump_sale_type': 'tank',
                'invoice_line_ids': line_ids
            })
            invoice.action_post()

            if bo.payment_type == 'received' and bouche_payment.state == 'posted':
                lines = bouche_payment.move_id.line_ids.filtered(lambda line: line.credit > 0)
                lines += invoice.line_ids.filtered(
                    lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                lines.reconcile()
        self.bouche_id.onhand_qty -= self.bou_total_qty
        self.state = 'done'

    @api.model
    def create(self, values):
        values['name'] = self.sudo().env['ir.sequence'].get('bouches.entry.details') or 'New'
        res = super(BouchesEntryDetails, self).create(values)
        return res


class BouchesEntryDetailsLine(models.Model):
    _name = 'bouches.entry.line'
    _description = 'Bouches Entry line'

    bouch_entry = fields.Many2one('bouches.entry.details', string='Bouch Entry')
    customer_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)])
    bouche_id = fields.Many2one('petrol.station.pump', string='Bouche Name', domain=[
        ('pump_sale_type', '=', 'tank'),
        ('parent_id', '!=', False)
    ], related='bouch_entry.bouche_id')
    bouche_capacity = fields.Float(string='Capacity', compute='compute_bouche_capacity')
    onhand_qty = fields.Float(string='On-hand', compute='compute_bouche_capacity')
    bouche_sale_qty = fields.Float(string='Qty')
    bouche_amount = fields.Float(string='Amount', compute='compute_bouche_amount')
    payment_type = fields.Selection([
        ('received', 'Received'),
        ('later', 'Credit')
    ], string="Payment Type", default="received")
    vehicle_no = fields.Char(string='Vehicle No')
    payment_mode = fields.Many2one('account.journal', string='Payment Mode', domain=[('type', 'in', ['cash', 'bank'])])

    @api.depends('bouche_id')
    def compute_bouche_capacity(self):
        for i in self:
            i.bouche_capacity = i.bouche_id.bouche_capacity
            i.onhand_qty = i.bouche_id.onhand_qty

    @api.depends('bouche_sale_qty')
    def compute_bouche_amount(self):
        for i in self:
            if i.bouche_sale_qty:
                i.bouche_amount = i.bouche_sale_qty * i.bouch_entry.today_price
            else:
                i.bouche_amount = 0.00
