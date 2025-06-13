from datetime import datetime, timedelta
from odoo import models, fields, api, _


class FuelStationDayEndReport(models.TransientModel):
    _name = 'fuel.day.end.report'
    _description = 'Fuel Station Day End Report'

    report_date = fields.Date(string='Date', default=lambda self: fields.Datetime.now())
    start_date = fields.Datetime(string='Start Date', required=True, compute='_onchange_report_date')
    end_date = fields.Datetime(string='End Date', required=True, compute='_onchange_report_date')

    @api.depends('report_date')
    def _onchange_report_date(self):
        now = self.report_date
        start_of_day = datetime(now.year, now.month, now.day)
        end_of_day = start_of_day + timedelta(days=1)
        self.start_date = start_of_day
        self.end_date = end_of_day

    def get_pdf_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
            },
        }
        return self.env.ref('petrol_station_dashboard.report_day_end_action').report_action(self, data=data)


class FuelDayEndPDFReport(models.AbstractModel):
    _name = 'report.petrol_station_dashboard.report_fuel_day_close_template'
    _description = 'Fuel Day End PDF Report'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        start_date_2 = start_date.strftime("%d-%m-%Y")
        end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
        end_date -= timedelta(seconds=1)
        end_date_2 = end_date.strftime("%d-%m-%Y")

        product = self.env['product.product'].search([('detailed_type', '=', 'product')])
        product_list = [j.id for j in product]
        product_dict = {product_name: False for product_name in product}
        stock_details = self.env['stock.move'].search([
            ('product_id', 'in', product_list),
            ('state', '=', 'done'),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ])
        for pd in product_list:
            in_qty = 0.00
            out_qty = 0.00
            today_price = 0.00
            for k in stock_details:
                if pd == k.product_id.id:
                    if k.picking_code == 'incoming':
                        today_price = k.sale_line_id.price_unit or k.price_unit
                        in_qty += k.product_uom_qty
                    if k.picking_code == 'outgoing':
                        today_price = k.sale_line_id.price_unit or k.price_unit
                        out_qty += k.product_uom_qty
            for j in product_dict:
                if j.id == pd:
                    vals = {
                        'in': in_qty,
                        'out': out_qty,
                        'sale': round(out_qty - in_qty, 2),
                        'today_price': today_price,
                        'total_price': round(((out_qty - in_qty) * today_price), 2),
                    }
                    if (round(out_qty - in_qty, 2) != 0 or
                            today_price != 0 or
                            round(((out_qty - in_qty) * today_price), 2) != 0):
                        product_dict[j] = vals

        close_entry = self.env['sale.order.wizard'].search([
            ('state', '=', 'done'),
            ('date', '>=', start_date - timedelta(hours=5, minutes=30)),
            ('date', '<=', end_date - timedelta(hours=5, minutes=30))
        ])

        journal_list = self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])])
        close_id = [ce.id for ce in close_entry]
        j_name = []
        for j in journal_list:
            j_name.append(j.name)
        journal_dictionary = {journal_name: 0 for journal_name in j_name}
        payment = self.env['account.payment'].search([('pay_ref', 'in', close_id)])
        expenses = self.env['hr.expense'].search([('pay_ref', 'in', close_id)])
        invoices = self.env['account.move'].search([('pay_ref', 'in', close_id), ('move_type', '=', 'out_invoice')])
        invoice_data = {invoice.partner_id: 0 for invoice in invoices}
        for pay in payment:
            val = {
                pay.journal_id.name: round(pay.amount, 2)
            }
            for k in val:
                if k in journal_dictionary:
                    journal_dictionary[k] = journal_dictionary[k] + val[k]
        credits_ids = []
        for inv in invoices:
            vals = {
                inv.partner_id: round(inv.amount_total, 2)
            }
            for t in vals:
                if t in invoice_data:
                    invoice_data[t] = invoice_data[t] + vals[t]
            credit_list = {
                'partner': inv.partner_id.name,
                'indent_no': inv.indent_no,
                'amount': round(inv.amount_total, 2),
            }
            credits_ids.append(credit_list)
        expenses_ids = []
        for ex in expenses:
            expense = {
                'nozzle': str(ex.pay_ref.pump_id.parent_id.name) + " - " + str(ex.pay_ref.pump_id.name),
                'employee': ex.employee_id.name,
                'type': ex.product_id.name,
                'amount': round(ex.total_amount, 2)
            }
            expenses_ids.append(expense)

        all_val = []
        for k in product_dict:
            if not product_dict[k]:
                all_val.append(k)
        for jj in all_val:
            product_dict.pop(jj)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'start_date': start_date_2,
            'end_date': end_date_2,
            'sale_dic': product_dict,
            'payment': journal_dictionary,
            'credit': invoice_data,
            'credit_ids': credits_ids,
            'expense_ids': expenses_ids,
            'today': fields.Date.today().strftime("%d/%m/%Y"),
        }
