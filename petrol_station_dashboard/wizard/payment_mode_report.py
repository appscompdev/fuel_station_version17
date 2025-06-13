from datetime import datetime
from odoo import models, fields, api, _


class PaymentModeReport(models.TransientModel):
    _name = 'payment.mode.report'
    _description = 'Payment Mode Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True, default=lambda self: fields.Datetime.now())
    journal_id = fields.Many2many('account.journal', domain=[('type', 'in', ['cash', 'bank'])],
                                  string='Payment Mode')

    def get_pdf_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
            },
            'journal': [j for j in self.journal_id.ids],
        }
        return self.env.ref('petrol_station_dashboard.report_payment_mode_action').report_action(self, data=data)


class PaymentModePDFReport(models.AbstractModel):
    _name = 'report.petrol_station_dashboard.report_payment_mode_template'
    _description = 'Payment Mode Report'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        start_date_2 = start_date.strftime("%d-%m-%Y")
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date_2 = start_date.strftime("%d-%m-%Y")
        journal = data['journal']

        value = []
        j_name = []
        if journal:
            for k in journal:
                journal_list = self.env['account.journal'].search([('id', '=', k)])
                j_name.append(journal_list.name)
        if journal:
            journal_dictionary = {journal_name: 0 for journal_name in j_name}
            total_amount = 0.00
            for k in journal:
                payment = self.env['account.payment'].search([
                    ('date', '>=', start_date),
                    ('date', '<=', end_date),
                    ('journal_id', '=', k),
                    ('state', '=', 'posted'),
                ])
                for pay in payment:
                    total_amount += round(pay.amount, 2)
                    val = {
                        pay.journal_id.name: round(pay.amount, 2),
                    }
                    for l in val:
                        if l in journal_dictionary:
                            journal_dictionary[l] += val[l]
                    value.append({
                        'date': pay.date,
                        'journal': pay.journal_id.name,
                        'sales_person': pay.pay_ref.pump_id.employee_id.name,
                        'nozzle': pay.pay_ref.pump_id.name,
                        'pump': pay.pay_ref.pump_id.parent_id.name,
                        'amount': pay.company_id.currency_id.symbol + ' ' + str(round(pay.amount, 2)),
                    })
        else:
            payment = self.env['account.payment'].search([
                ('date', '>=', start_date),
                ('date', '<=', end_date)
            ])
            journal_list = self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])])

            j_name = []
            for j in journal_list:
                j_name.append(j.name)
            journal_dictionary = {journal_name: 0 for journal_name in j_name}
            total_amount = 0.00
            for pay in payment:
                total_amount += round(pay.amount, 2)
                val = {
                    pay.journal_id.name: round(pay.amount, 2),
                }
                for k in val:
                    if k in journal_dictionary:
                        journal_dictionary[k] = journal_dictionary[k] + val[k]
                value.append({
                    'date': pay.date.strftime("%d-%m-%Y"),
                    'journal': pay.journal_id.name,
                    'sales_person': pay.pay_ref.pump_id.employee_id.name,
                    'nozzle': pay.pay_ref.pump_id.name,
                    'pump': pay.pay_ref.pump_id.parent_id.name,
                    'amount': pay.company_id.currency_id.symbol + ' ' + str(round(pay.amount, 2)),
                })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'start_date': start_date_2,
            'end_date': end_date_2,
            'data': value,
            'journal_dict': journal_dictionary,
            'today': fields.Date.today().strftime("%d/%m/%Y"),
            'symbol': self.env.user.company_id.currency_id.symbol,
            'total': self.env.user.company_id.currency_id.symbol + ' ' + str(total_amount),

        }
