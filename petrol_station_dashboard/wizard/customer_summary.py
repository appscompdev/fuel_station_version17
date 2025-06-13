from odoo import models, fields, api, _
import datetime
import xlwt
from io import BytesIO
import base64
from xlwt import easyxf
from datetime import timedelta, date


class CustomerSummaryReport(models.TransientModel):
    _name = 'customer.summary.report'
    _description = 'Customer / Vendor Summary Report'

    report_date = fields.Date(string='Date', default=lambda self: fields.Datetime.now())
    start_date = fields.Datetime(string='Start Date', required=True, )
    end_date = fields.Datetime(string='End Date', required=True, default=lambda self: date.today())
    partner_ids = fields.Many2many('res.partner', string='Customer / Vendor')
    summary_file = fields.Binary('Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Excel Report')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_pdf_report(self):
        if self.partner_ids:
            partner = [{'id': j.id, 'name': j.name} for j in self.partner_ids]
        else:
            par = self.env['res.partner'].search([])
            partner = [{'id': j.id, 'name': j.name} for j in par]

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
            },
            'partner': partner,
        }
        return self.env.ref('petrol_station_dashboard.report_action_customer_summary').report_action(self, data=data)

    def get_excel_report(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('Customer / Vendor Summary Report')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_71 = easyxf('align: horiz right;font: bold 1;')
        design_72 = easyxf('align: horiz left;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_10 = easyxf('align: horiz center;')
        design_11 = easyxf('align: horiz right;')
        design_9 = easyxf('align: horiz right;font: bold 1;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;font: bold 1;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_14 = easyxf('align: horiz left;font: bold 1;pattern: pattern solid, fore_colour gray25;')

        for i in range(0, 10):
            worksheet1.col(i).width = 6000
        rows = 0

        date_list = [self.start_date + timedelta(days=x) for x in range((self.end_date - self.start_date).days + 2)]

        stock_move = self.env['stock.move'].search(
            [('state', '=', 'done'), ('create_date', '>=', self.start_date.date()),
             ('create_date', '<=', self.end_date.date())], order="create_date asc")
        product = self.env['product.product'].search(
            [('sale_ok', '=', True), ('purchase_ok', '=', True), ('detailed_type', '=', 'product')])
        all_all = []

        if self.partner_ids:
            partner = [{'id': j.id, 'name': j.name} for j in self.partner_ids]
        else:
            par = self.env['res.partner'].search([])
            partner = [{'id': j.id, 'name': j.name} for j in par]

        for k in partner:
            all_pro_list = []
            for pro in product:
                p_list = []
                s_list = []
                for dl in date_list:
                    purchase_qty = 0
                    for pr in stock_move:
                        if pr.product_id.categ_id.name == 'fuel' or pr.product_id.categ_id.name == 'All':
                            if k[
                                'id'] == pr.picking_id.partner_id.id and pro.id == pr.product_id.id and pr.picking_id.picking_type_id.code == 'incoming':
                                if dl.date() == pr.date.date():
                                    purchase_qty += pr.quantity
                    if purchase_qty:
                        sale_order_wizard = self.env['sale.order.wizard'].search([])
                        dd_price = 0.0
                        for jj in sale_order_wizard:
                            if jj.date.date() == dl.date():
                                dd_price = jj.today_price
                        pur_dic = {
                            'date': dl,
                            'purchase_qty': purchase_qty,
                            'dd_price': dd_price,
                            'total_price': dd_price * purchase_qty,
                        }
                        p_list.append(pur_dic)

                    sale_qty = 0
                    for pr in stock_move:
                        if pr.product_id.categ_id.name == 'fuel' or pr.product_id.categ_id.name == 'All':
                            if k['id'] == pr.picking_id.partner_id.id:
                                if pro.id == pr.product_id.id:
                                    if pr.picking_id.picking_type_id.code == 'outgoing':
                                        if dl.date() == pr.date.date():
                                            sale_qty += pr.quantity
                    if sale_qty:
                        sale_order_wizard = self.env['sale.order.wizard'].search([])
                        dd_price = 0.0
                        for jj in sale_order_wizard:
                            if jj.date.date() == dl.date():
                                dd_price = jj.today_price
                        sale_dic = {
                            'date': dl,
                            'sale_qty': sale_qty,
                            'dd_price': dd_price,
                            'total_price': dd_price * sale_qty,
                        }
                        s_list.append(sale_dic)
                if s_list or p_list:
                    all_dic = {
                        'name': pro.name,
                        's_list': s_list,
                        'p_list': p_list,
                    }
                    all_pro_list.append(all_dic)
            if all_pro_list:
                cus_dic = {
                    'customer': k['name'],
                    'all_dic': all_pro_list,
                }
                all_all.append(cus_dic)

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.write_merge(rows, rows, 0, 5, 'Customer / Vendor Summary Report', design_13)
        rows += 1
        worksheet1.write(rows, 2, 'START DATE', design_14)
        worksheet1.write(rows, 3, self.start_date.strftime('%d-%m-%Y'), design_13)
        rows += 1
        worksheet1.write(rows, 2, 'END DATE', design_14)
        worksheet1.write(rows, 3, self.end_date.strftime('%d-%m-%Y'), design_13)
        rows += 1
        worksheet1.write(rows, 2, 'GENERATED BY', design_14)
        worksheet1.write(rows, 3, self.user_id.name, design_13)
        rows += 2
        worksheet1.write_merge(rows, rows, 2, 3, "PURCHASE", design_13)
        rows += 2
        cols_heads = ['S.NO', 'DATE', 'QTY', 'PRICE', 'TOTAL AMOUNT']
        cols = 0
        for col_head in cols_heads:
            worksheet1.write(rows, cols, _(col_head), design_13)
            cols += 1
        rows += 1
        serial_no = 1
        p_total = 0

        for i in all_all:
            worksheet1.write_merge(rows, rows, 0, 5, i['customer'], design_10)
            rows += 1
            for j in i['all_dic']:
                worksheet1.write(rows, 0, "Product :", design_13)
                worksheet1.write(rows, 1, j['name'], design_13)
                rows += 1
                for k in j['p_list']:
                    if k['purchase_qty']:
                        worksheet1.write(rows, 0, serial_no, design_71)
                        worksheet1.write(rows, 1, k['date'].strftime("%d-%m-%Y"), design_7)
                        worksheet1.write(rows, 2, k['purchase_qty'], design_71)
                        worksheet1.write(rows, 3, f"{k['dd_price']:.2f}", design_71)
                        worksheet1.write(rows, 4, f"{k['total_price']:.2f}", design_71)
                        rows += 1
                        serial_no += 1
                        p_total += k['total_price']

        worksheet1.write(rows, 3, 'Grand Total', design_13)
        worksheet1.write(rows, 4, self.company_id.currency_id.symbol + '' + str(f"{p_total:.2f}"), design_9)
        rows += 2
        worksheet1.write_merge(rows, rows, 2, 3, "SALE", design_13)
        rows += 2
        cols_heads = ['S.NO', 'DATE', 'QTY', 'PRICE', 'TOTAL AMOUNT']
        cols = 0
        for col_head in cols_heads:
            worksheet1.write(rows, cols, _(col_head), design_13)
            cols += 1
        rows += 1
        serial_no = 1
        s_total = 0

        for i in all_all:
            worksheet1.write_merge(rows, rows, 0, 5, i['customer'], design_10)
            rows += 1
            for j in i['all_dic']:
                worksheet1.write(rows, 0, "Product :", design_13)
                worksheet1.write(rows, 1, j['name'], design_13)
                rows += 1
                for k in j['s_list']:
                    if k['sale_qty']:
                        worksheet1.write(rows, 0, serial_no, design_71)
                        worksheet1.write(rows, 1, k['date'].strftime("%d-%m-%Y"), design_7)
                        worksheet1.write(rows, 2, k['sale_qty'], design_71)
                        worksheet1.write(rows, 3, f"{k['dd_price']:.2f}", design_71)
                        worksheet1.write(rows, 4, f"{k['total_price']:.2f}", design_71)
                        rows += 1
                        serial_no += 1
                        s_total += k['total_price']

        worksheet1.write(rows, 3, 'Grand Total', design_13)
        worksheet1.write(rows, 4, self.company_id.currency_id.symbol + '' + str(f"{p_total:.2f}"), design_9)
        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': f'Customer / Vendor Summary Report.xls',
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'customer.summary.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }


class CustomerOutStand(models.AbstractModel):
    _name = 'report.petrol_station_dashboard.customer_summary_template'
    _description = 'Customer / Vendor Summary Report'

    def _get_report_values(self, docids, data=None):
        start_date = datetime.datetime.strptime(data['form']['start_date'], '%Y-%m-%d %H:%M:%S')
        end_date = datetime.datetime.strptime(data['form']['end_date'], '%Y-%m-%d %H:%M:%S')
        date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 2)]

        stock_move = self.env['stock.move'].search([('state', '=', 'done'), ('create_date', '>=', start_date.date()),
                                                    ('create_date', '<=', end_date.date())], order="create_date asc")
        product = self.env['product.product'].search(
            [('sale_ok', '=', True), ('purchase_ok', '=', True), ('detailed_type', '=', 'product')])
        all_all = []
        for k in data['partner']:
            all_pro_list = []
            for pro in product:
                p_list = []
                s_list = []
                for dl in date_list:
                    purchase_qty = 0
                    for pr in stock_move:
                        if pr.product_id.categ_id.name == 'fuel' or pr.product_id.categ_id.name == 'All':
                            if k[
                                'id'] == pr.picking_id.partner_id.id and pro.id == pr.product_id.id and pr.picking_id.picking_type_id.code == 'incoming':
                                if dl.date() == pr.date.date():
                                    purchase_qty += pr.quantity

                    if purchase_qty:
                        sale_order_wizard = self.env['sale.order.wizard'].search([])
                        dd_price = 0.0
                        for jj in sale_order_wizard:
                            if jj.date.date() == dl.date():
                                dd_price = jj.today_price
                        pur_dic = {
                            'date': dl,
                            'purchase_qty': purchase_qty,
                            'dd_price': dd_price,
                            'total_price': dd_price * purchase_qty,
                        }
                        p_list.append(pur_dic)

                    sale_qty = 0
                    for pr in stock_move:
                        if pr.product_id.categ_id.name == 'fuel' or pr.product_id.categ_id.name == 'All':
                            if k['id'] == pr.picking_id.partner_id.id:
                                if pro.id == pr.product_id.id:
                                    if pr.picking_id.picking_type_id.code == 'outgoing':
                                        if dl.date() == pr.date.date():
                                            sale_qty += pr.quantity
                    if sale_qty:
                        sale_order_wizard = self.env['sale.order.wizard'].search([])
                        dd_price = 0.0
                        for jj in sale_order_wizard:
                            if jj.date.date() == dl.date():
                                dd_price = jj.today_price
                        sale_dic = {
                            'date': dl,
                            'sale_qty': sale_qty,
                            'dd_price': dd_price,
                            'total_price': dd_price * sale_qty,
                        }
                        s_list.append(sale_dic)
                if s_list or p_list:
                    all_dic = {
                        'name': pro.name,
                        's_list': s_list,
                        'p_list': p_list,
                    }
                    all_pro_list.append(all_dic)
            if all_pro_list:
                cus_dic = {
                    'customer': k['name'],
                    'all_dic': all_pro_list,
                }
                all_all.append(cus_dic)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'all_all': all_all,
            'today': fields.Date.today().strftime("%d/%m/%Y"),
        }
