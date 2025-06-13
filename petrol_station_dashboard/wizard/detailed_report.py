from odoo import models, fields, api, _
import datetime
import xlwt
from io import BytesIO
import base64
from xlwt import easyxf
from datetime import timedelta


class DetailedReport(models.TransientModel):
    _name = 'detailed.report'
    _description = 'Detailed Report'

    report_date = fields.Date(string='Date', default=lambda self: fields.Datetime.now())
    start_date = fields.Datetime(string='Start Date', required=True, )
    end_date = fields.Datetime(string='End Date', required=True, default=lambda self: fields.Datetime.now())
    partner_ids = fields.Many2many('res.partner', string='Customer')
    summary_file = fields.Binary('Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Excel Report')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_pdf_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
            },
            'partner': [{'id': j.id, 'name': j.name} for j in self.partner_ids],
        }
        return self.env.ref('petrol_station_dashboard.report_action_detailed').report_action(self, data=data)

    def get_excel_report(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('Detailed Report')
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
        sale_order_line = self.env['sale.order.line'].search(
            [('create_date', '>=', self.start_date.date()),
             ('create_date', '<=', self.end_date.date())], order="create_date asc")
        res_partner = self.env['res.users'].search([])
        petrol_station_pump = self.env['petrol.station.pump'].search([])
        product = self.env['product.template'].search(
            [('sale_ok', '=', True), ('purchase_ok', '=', True), ('detailed_type', '=', 'product')])
        date_list = [self.start_date + timedelta(days=x) for x in range((self.end_date - self.start_date).days + 2)]
        stock_tt_total = []
        for j in product:
            if j.categ_id.name == "fuel" or j.categ_id.name == "All":
                all_val = []
                for k in date_list:
                    s_qty = 0
                    for i in sale_order_line:
                        if i.order_id.state == 'sale' and j.id == i.product_template_id.id and k.date() == i.order_id.date_order.date():
                            s_qty += i.qty_delivered
                    if s_qty:
                        sale_order_wizard = self.env['sale.order.wizard'].search([])
                        dd_price = 0.0
                        for jj in sale_order_wizard:
                            if jj.date.date() == k.date() and j.id == jj.product_id.id:
                                dd_price = jj.today_price
                        val = {
                            'date': k.date(),
                            's_qty': s_qty,
                            'dd_price': dd_price,
                            'total': dd_price * s_qty,
                        }
                        all_val.append(val)
                if all_val:
                    vv_val = {
                        'name': j.name,
                        'all_val': all_val,
                    }
                    stock_tt_total.append(vv_val)

        product_tt_total = []
        for qq in res_partner:
            all_val_all = []
            for pp in product:
                pro_all_val = []
                if pp.categ_id.name == "Fuel":
                    for k in date_list:
                        s_qty = 0
                        for i in sale_order_line:
                            if pp.id == i.product_template_id.id and i.order_id.state == 'sale' and qq.id == i.order_id.user_id.id and k.date() == i.order_id.date_order.date():
                                s_qty += i.qty_delivered
                        if s_qty:
                            sale_order_wizard = self.env['sale.order.wizard'].search([])
                            dd_price = 0.0
                            for jj in sale_order_wizard:
                                if jj.date.date() == k.date() and pp.id == jj.product_id.id:
                                    dd_price = jj.today_price
                            val = {
                                'date': k.date(),
                                's_qty': s_qty,
                                'dd_price': dd_price,
                                'total': dd_price * s_qty,
                            }
                            pro_all_val.append(val)
                if pro_all_val:
                    vv_val = {
                        'name': pp.name,
                        'all_val': pro_all_val,
                    }
                    all_val_all.append(vv_val)
            if all_val_all:
                valss = {
                    'name': qq.name,
                    'val': all_val_all,
                }
                product_tt_total.append(valss)

        nozzle_tt_total = []
        for qq in petrol_station_pump:
            pro_all_val = []
            for k in date_list:
                s_qty = 0
                for i in sale_order_line:
                    if i.order_id.state == 'sale' and qq.id == i.order_id.pay_ref.pump_id.id and k.date() == i.order_id.date_order.date():
                        s_qty += i.qty_delivered
                if s_qty:
                    sale_order_wizard = self.env['sale.order.wizard'].search([])
                    dd_price = 0.0
                    for jj in sale_order_wizard:
                        if jj.date.date() == k.date() and qq.product_id.id == jj.product_id.id:
                            dd_price = jj.today_price
                    val = {
                        'date': k.date(),
                        's_qty': s_qty,
                        'dd_price': dd_price,
                        'total': dd_price * s_qty,
                    }
                    pro_all_val.append(val)
            if pro_all_val:
                vv_val = {
                    'name': str(qq.name) + "-" + str(qq.parent_id.name),
                    'all_val': pro_all_val,
                }
                nozzle_tt_total.append(vv_val)
        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.write_merge(rows, rows, 0, 5, 'Detailed Report', design_13)
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
        if stock_tt_total:
            worksheet1.write_merge(rows, rows, 2, 3, "STOCK SUMMARY", design_13)
            rows += 2
            cols_heads = ['S.NO', 'DATE', 'QTY', 'PRICE', 'TOTAL AMOUNT']
            cols = 0
            for col_head in cols_heads:
                worksheet1.write(rows, cols, _(col_head), design_13)
                cols += 1
            rows += 1
            serial_no = 1
            p_total = 0

            for i in stock_tt_total:
                worksheet1.write_merge(rows, rows, 0, 5, "Stock :" + i['name'], design_10)
                rows += 1
                for k in i['all_val']:
                    if k['s_qty']:
                        worksheet1.write(rows, 0, serial_no, design_71)
                        worksheet1.write(rows, 1, k['date'].strftime("%d-%m-%Y"), design_7)
                        worksheet1.write(rows, 2, k['s_qty'], design_71)
                        worksheet1.write(rows, 3, f"{k['dd_price']:.2f}", design_71)
                        worksheet1.write(rows, 4, f"{k['total']:.2f}", design_71)
                        rows += 1
                        serial_no += 1
                        p_total += k['total']

            worksheet1.write(rows, 3, 'Grand Total', design_13)
            worksheet1.write(rows, 4, self.company_id.currency_id.symbol + '' + str(f"{p_total:.2f}"), design_9)
            rows += 2
        if product_tt_total:
            worksheet1.write_merge(rows, rows, 2, 3, "USER SUMMARY", design_13)
            rows += 2
            cols_heads = ['S.NO', 'DATE', 'QTY', 'PRICE', 'TOTAL AMOUNT']
            cols = 0
            for col_head in cols_heads:
                worksheet1.write(rows, cols, _(col_head), design_13)
                cols += 1
            rows += 1
            serial_no = 1
            p_total = 0

            for i in product_tt_total:
                worksheet1.write_merge(rows, rows, 0, 5, "User :" + i['name'], design_10)
                rows += 1
                for kk in i['val']:
                    worksheet1.write_merge(rows, rows, 0, 5, kk['name'], design_10)
                    rows += 1
                    for k in kk['all_val']:
                        if k['s_qty']:
                            worksheet1.write(rows, 0, serial_no, design_71)
                            worksheet1.write(rows, 1, k['date'].strftime("%d-%m-%Y"), design_7)
                            worksheet1.write(rows, 2, k['s_qty'], design_71)
                            worksheet1.write(rows, 3, f"{k['dd_price']:.2f}", design_71)
                            worksheet1.write(rows, 4, f"{k['total']:.2f}", design_71)
                            rows += 1
                            serial_no += 1
                            p_total += k['total']

            worksheet1.write(rows, 3, 'Grand Total', design_13)
            worksheet1.write(rows, 4, self.company_id.currency_id.symbol + '' + str(f"{p_total:.2f}"), design_9)
            rows += 2
        if nozzle_tt_total:
            worksheet1.write_merge(rows, rows, 2, 3, "NOZZLE SUMMARY", design_13)
            rows += 2
            cols_heads = ['S.NO', 'DATE', 'QTY', 'PRICE', 'TOTAL AMOUNT']
            cols = 0
            for col_head in cols_heads:
                worksheet1.write(rows, cols, _(col_head), design_13)
                cols += 1
            rows += 1
            serial_no = 1
            p_total = 0

            for i in nozzle_tt_total:
                worksheet1.write_merge(rows, rows, 0, 5, i['name'], design_10)
                rows += 1
                for k in i['all_val']:
                    if k['s_qty']:
                        worksheet1.write(rows, 0, serial_no, design_71)
                        worksheet1.write(rows, 1, k['date'].strftime("%d-%m-%Y"), design_7)
                        worksheet1.write(rows, 2, k['s_qty'], design_71)
                        worksheet1.write(rows, 3, f"{k['dd_price']:.2f}", design_71)
                        worksheet1.write(rows, 4, f"{k['total']:.2f}", design_71)
                        rows += 1
                        serial_no += 1
                        p_total += k['total']

            worksheet1.write(rows, 3, 'Grand Total', design_13)
            worksheet1.write(rows, 4, self.company_id.currency_id.symbol + '' + str(f"{p_total:.2f}"), design_9)
        rows += 2
        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': f'Detailed Report.xls',
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'detailed.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }


class CustomerOutStand(models.AbstractModel):
    _name = 'report.petrol_station_dashboard.detailed_template'
    _description = 'Detailed Report'

    def _get_report_values(self, docids, data=None):
        start_date = datetime.datetime.strptime(data['form']['start_date'], '%Y-%m-%d %H:%M:%S')
        end_date = datetime.datetime.strptime(data['form']['end_date'], '%Y-%m-%d %H:%M:%S')
        sale_order_line = self.env['sale.order.line'].search(
            [('create_date', '>=', start_date.date()),
             ('create_date', '<=', end_date.date())], order="create_date asc")
        res_partner = self.env['res.users'].search([])
        petrol_station_pump = self.env['petrol.station.pump'].search([])
        product = self.env['product.template'].search(
            [('sale_ok', '=', True), ('purchase_ok', '=', True), ('detailed_type', '=', 'product')])
        date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 2)]
        stock_tt_total = []
        for j in product:
            if j.categ_id.name == "fuel" or j.categ_id.name == "All":
                all_val = []
                for k in date_list:
                    s_qty = 0
                    for i in sale_order_line:
                        if i.order_id.state == 'sale' and j.id == i.product_template_id.id and k.date() == i.order_id.date_order.date():
                            s_qty += i.qty_delivered
                    if s_qty:
                        sale_order_wizard = self.env['sale.order.wizard'].search([])
                        dd_price = 0.0
                        for jj in sale_order_wizard:
                            if jj.date.date() == k.date() and j.id == jj.product_id.id:
                                dd_price = jj.today_price
                        val = {
                            'date': k.date(),
                            's_qty': s_qty,
                            'dd_price': dd_price,
                            'total': dd_price * s_qty,
                        }
                        all_val.append(val)
                if all_val:
                    vv_val = {
                        'name': j.name,
                        'all_val': all_val,
                    }
                    stock_tt_total.append(vv_val)

        product_tt_total = []
        for qq in res_partner:
            all_val_all = []
            for pp in product:
                pro_all_val = []
                if pp.categ_id.name == "Fuel":
                    for k in date_list:
                        s_qty = 0
                        for i in sale_order_line:
                            if pp.id == i.product_template_id.id and i.order_id.state == 'sale' and qq.id == i.order_id.user_id.id and k.date() == i.order_id.date_order.date():
                                s_qty += i.qty_delivered
                        if s_qty:
                            sale_order_wizard = self.env['sale.order.wizard'].search([])
                            dd_price = 0.0
                            for jj in sale_order_wizard:
                                if jj.date.date() == k.date() and pp.id == jj.product_id.id:
                                    dd_price = jj.today_price
                            val = {
                                'date': k.date(),
                                's_qty': s_qty,
                                'dd_price': dd_price,
                                'total': dd_price * s_qty,
                            }
                            pro_all_val.append(val)
                if pro_all_val:
                    vv_val = {
                        'name': pp.name,
                        'all_val': pro_all_val,
                    }
                    all_val_all.append(vv_val)
            if all_val_all:
                valss = {
                    'name': qq.name,
                    'val': all_val_all,
                }
                product_tt_total.append(valss)

        nozzle_tt_total = []
        for qq in petrol_station_pump:
            pro_all_val = []
            for k in date_list:
                s_qty = 0
                for i in sale_order_line:
                    if i.order_id.state == 'sale' and qq.id == i.order_id.pay_ref.pump_id.id and k.date() == i.order_id.date_order.date():
                        s_qty += i.qty_delivered
                if s_qty:
                    sale_order_wizard = self.env['sale.order.wizard'].search([])
                    dd_price = 0.0
                    for jj in sale_order_wizard:
                        if jj.date.date() == k.date() and qq.product_id.id == jj.product_id.id:
                            dd_price = jj.today_price
                    val = {
                        'date': k.date(),
                        's_qty': s_qty,
                        'dd_price': dd_price,
                        'total': dd_price * s_qty,
                    }
                    pro_all_val.append(val)
            if pro_all_val:
                vv_val = {
                    'name': str(qq.name) + "-" + str(qq.parent_id.name),
                    'all_val': pro_all_val,
                }
                nozzle_tt_total.append(vv_val)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'stock_tt_total': stock_tt_total,
            'product_tt_total': product_tt_total,
            'nozzle_tt_total': nozzle_tt_total,
            'today': fields.Date.today().strftime("%d/%m/%Y"),
        }
