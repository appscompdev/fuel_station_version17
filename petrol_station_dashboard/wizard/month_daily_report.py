from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
from xlwt import easyxf


class MonthDailyReport(models.TransientModel):
    _name = 'month.daily.report'
    _description = 'Day Wise Report'

    report_date = fields.Date(string='Date', default=lambda self: fields.Datetime.now())

    summary_file = fields.Binary('Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Excel Report')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_excel_report_new(self):
        workbook_two = xlwt.Workbook()
        worksheet2 = workbook_two.add_sheet('Day Wise Report')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_8_left = easyxf('align: horiz left;')
        design_8_right = easyxf('align: horiz right;')
        design_8_center = easyxf('align: horiz center;')
        design_9 = easyxf('align: horiz right;font: bold 1;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;font: bold 1;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_14 = easyxf('align: horiz center;font: bold 1;')
        design_14_right = easyxf('align: horiz right;font: bold 1;')
        design_14_left = easyxf('align: horiz left;font: bold 1;')

        for i in range(0, 10):
            worksheet2.col(i).width = 6000
        rows = 0
        worksheet2.set_panes_frozen(True)
        worksheet2.set_horz_split_pos(rows + 1)
        worksheet2.write(rows, 0, self.company_id.name, design_13)
        worksheet2.write_merge(rows, rows, 1, 2, 'Sales', design_13)
        worksheet2.write(rows, 3, self.report_date.strftime('%d-%m-%Y'), design_13)
        rows += 2
        header = ['Income', 'No  / Litres', 'Cost', 'Total']
        count_row = 0
        for i in header:
            worksheet2.write(rows, count_row, i, design_14)
            count_row += 1
        rows += 1
        domain = [
            ('state', '=', 'done')
        ]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        stock_move = self.env['stock.move'].search(domain)

        # FOR DIESEL SALE ###########################################################################
        diesel_count = 0
        diesel_amount_list = []
        for j in stock_move:
            if j.product_id.name == 'Diesel':
                if j.date.date() == self.report_date:  # Diesel
                    if j.sale_line_id:
                        if j.sale_line_id.order_id.date_order.date() == self.report_date:
                            if j.sale_line_id.price_unit not in diesel_amount_list:
                                diesel_amount_list.append(j.sale_line_id.price_unit)
        ccc = 1
        total_diesel_income = 0
        for h in diesel_amount_list:
            for j in stock_move:
                if j.product_id.name == "Diesel" and h == j.sale_line_id.price_unit:  # Diesel
                    if j.date.date() == self.report_date:
                        if j.picking_id.picking_type_id.code == 'outgoing':
                            diesel_count += j.product_uom_qty
                        if j.picking_id.picking_type_id.code == 'incoming':
                            diesel_count -= j.product_uom_qty
            worksheet2.write(rows, 0, 'Diesel' + str(ccc), design_8_center)
            worksheet2.write(rows, 1, diesel_count, design_8_right)
            worksheet2.write(rows, 2, h, design_8_right)
            worksheet2.write(rows, 3, diesel_count * h, design_8_right)
            total_diesel_income += (diesel_count * h)
            ccc += 1
            rows += 1
        worksheet2.write_merge(rows, rows, 0, 2, 'Total Diesel Income', design_14_right)
        worksheet2.write(rows, 3, total_diesel_income, design_14_right)
        rows += 2

        # FOR PETROL SALE  #############################################################
        petrol_count = 0
        petrol_amount_list = []
        for j in stock_move:
            if j.product_id.name == "Petrol" and j.date.date() == self.report_date:  # Petrol
                if j.date.date() == self.report_date:
                    if j.sale_line_id.price_unit not in petrol_amount_list:
                        petrol_amount_list.append(j.sale_line_id.price_unit)
        ccc = 1
        total_petrol_income = 0
        for h in petrol_amount_list:
            for j in stock_move:
                if j.product_id.name == "Petrol" and h == j.sale_line_id.price_unit:  # Petrol
                    if j.date.date() == self.report_date:
                        if j.picking_id.picking_type_id.code == 'outgoing':
                            petrol_count += j.product_uom_qty
                        if j.picking_id.picking_type_id.code == 'incoming':
                            petrol_count -= j.product_uom_qty

            worksheet2.write(rows, 0, 'Petrol' + str(ccc), design_8_center)
            worksheet2.write(rows, 1, petrol_count, design_8_right)
            worksheet2.write(rows, 2, h, design_8_right)
            worksheet2.write(rows, 3, petrol_count * h, design_8_right)
            total_petrol_income += (petrol_count * h)
            ccc += 1
            rows += 1
        worksheet2.write_merge(rows, rows, 0, 2, 'Total Petrol Income', design_14_right)
        worksheet2.write(rows, 3, total_petrol_income, design_14_right)
        rows += 2

        # FOR OTHER PRODUCT SALE #######################################################
        other_product_doamin = [('name', '!=', ["Petrol", "Diesel"]), ('sale_ok', '=', True)]

        if self.company_id:
            other_product_doamin.append(('company_id', '=', self.company_id.id))
        product_product = self.env['product.product'].search(other_product_doamin)
        product_total = 0
        for pp in product_product:
            product_quantity = 0
            for sm in stock_move:
                if pp.id == sm.product_id.id and sm.date.date() == self.report_date:
                    if sm.picking_id.picking_type_id.code == 'outgoing':
                        product_quantity += sm.product_uom_qty
                    if sm.picking_id.picking_type_id.code == 'incoming':
                        product_quantity -= sm.product_uom_qty
            worksheet2.write(rows, 0, pp.display_name, design_8_left)
            worksheet2.write(rows, 1, product_quantity, design_8_right)
            if product_quantity:
                worksheet2.write(rows, 2, pp.list_price, design_8_right)
            else:
                worksheet2.write(rows, 2, 0, design_8_right)
            worksheet2.write(rows, 3, product_quantity * pp.list_price, design_8_right)
            product_total += (product_quantity * pp.list_price)
            rows += 1
        worksheet2.write_merge(rows, rows, 0, 2, 'Total Oil Sale Income', design_14_right)
        worksheet2.write(rows, 3, product_total, design_14_right)
        rows += 1

        # FOR DIESEL NOZZLE WISE SALE ########################################################

        sale_order_wizard = self.env['sale.order.wizard'].search([])
        psp_doamin = [('parent_id', '!=', False)]
        if self.company_id:
            psp_doamin.append(('company_id', '=', self.company_id.id))
        petrol_station_pump = self.env['petrol.station.pump'].search(psp_doamin)
        all_list = []
        for ll in petrol_station_pump:
            reading = []
            total_per_day = []
            for j in sale_order_wizard:
                if j.product_id.name == "Diesel":  # Diesel
                    if j.date.date() == self.report_date and j.pump_id.id == ll.id:
                        if j.start_reading not in reading:
                            reading.append(j.start_reading)
                        if j.end_reading not in reading:
                            reading.append(j.end_reading)
                        total_per_day.append(j.total_reading)
            reading = sorted(reading)
            dic_val = {
                'name': ll.name,
                'reading': reading,
                'total_per_day': total_per_day,
            }
            all_list.append(dic_val)
        header = ['Diesel', 'Opening', 'Reading 1', 'Reading 2', 'Reading 3']
        count_row = 0
        for i in header:
            worksheet2.write(rows, count_row, i, design_14)
            count_row += 1
        rows += 1
        for kk in all_list:
            worksheet2.write(rows, 0, kk['name'], design_8_right)
            if kk['reading']:
                worksheet2.write(rows, 1, kk['reading'][0], design_8_right)
                kk['reading'].pop(0)
                cou = 2
                for g in kk['reading']:
                    worksheet2.write(rows, cou, g, design_8_right)
                    cou += 1
            rows += 1

        rows += 2
        header = ['Diesel', 'Sale 1', 'Sale 2', 'Sale 3']
        count_row = 0
        for i in header:
            worksheet2.write(rows, count_row, i, design_14)
            count_row += 1
        rows += 1
        diesel_sale_sale = 0
        for kk in all_list:
            worksheet2.write(rows, 0, kk['name'], design_8_right)
            if kk['total_per_day']:
                cou = 1
                for j in kk['total_per_day']:
                    worksheet2.write(rows, cou, j, design_8_right)
                    diesel_sale_sale += j
                    cou += 1
            rows += 1
        rows += 1

        # FOR PETROL NOZZLE WISE SALE ###############################################################

        psp_doamin = [('parent_id', '!=', False)]
        if self.company_id:
            psp_doamin.append(('company_id', '=', self.company_id.id))
        petrol_station_pump = self.env['petrol.station.pump'].search(psp_doamin)
        all_list = []
        for ll in petrol_station_pump:
            reading = []
            total_per_day = []
            for j in sale_order_wizard:
                if j.product_id.name == "Petrol":  # Petrol
                    if j.date.date() == self.report_date and j.pump_id.id == ll.id:
                        if j.start_reading not in reading:
                            reading.append(j.start_reading)
                        if j.end_reading not in reading:
                            reading.append(j.end_reading)
                        total_per_day.append(j.total_reading)
            reading = sorted(reading)
            dic_val = {
                'name': ll.name,
                'reading': reading,
                'total_per_day': total_per_day,
            }
            all_list.append(dic_val)
        header = ['Petrol', 'Opening', 'Reading 1', 'Reading 2', 'Reading 3']
        count_row = 0
        for i in header:
            worksheet2.write(rows, count_row, i, design_14)
            count_row += 1
        rows += 1
        petrol_sale_sale = 0
        for kk in all_list:
            worksheet2.write(rows, 0, kk['name'], design_8_right)
            if kk['reading']:
                worksheet2.write(rows, 1, kk['reading'][0], design_8_right)
                kk['reading'].pop(0)
                cou = 2
                for g in kk['reading']:
                    worksheet2.write(rows, cou, g, design_8_right)
                    petrol_sale_sale += g
                    cou += 1
            rows += 1

        rows += 2
        header = ['Petrol', 'Sale 1', 'Sale 2', 'Sale 3']
        count_row = 0
        for i in header:
            worksheet2.write(rows, count_row, i, design_14)
            count_row += 1
        rows += 1

        petrol_sale_sale = 0
        for kk in all_list:
            worksheet2.write(rows, 0, kk['name'], design_8_right)
            if kk['total_per_day']:
                cou = 1
                for j in kk['total_per_day']:
                    worksheet2.write(rows, cou, j, design_8_right)
                    petrol_sale_sale += j
                    cou += 1
            rows += 1
        rows += 2

        product_template = self.env['product.product'].search([('name', '=', ["Diesel", "Petrol"])])
        d_dic = {
            'Opening': 0,
            'Purchase': 0,
            'Sales': 0,
            'Closing': 0,
            'Sample': 0,
            'Dip': 0,
            'Difference': 0,
        }
        for xx in self.env['product.product'].search([('name', '=', "Diesel")]):
            from datetime import timedelta
            yesterday = self.report_date - timedelta(1)
            if yesterday == xx.create_date.date():
                open = xx.qty_available
                d_dic['Opening'] = open
        purchase_product = self.env['stock.move'].search([('picking_type_id', '=', 1)])
        diesel_purchase_val = 0
        for pp in purchase_product:
            if pp.create_date.date() == self.report_date and pp.product_id.name == "Diesel":
                diesel_purchase_val += pp.product_uom_qty
        d_dic['Purchase'] = diesel_purchase_val
        d_dic['Sales'] = diesel_sale_sale
        dip = (diesel_purchase_val - diesel_sale_sale) + d_dic['Opening']
        difference = 0
        for rr in sale_order_wizard:
            if not rr.date == self.report_date and rr.product_id.name == "Diesel":
                pass
                difference += rr.day_difference
        d_dic['Dip'] = dip
        d_dic['Closing'] = difference - dip
        d_dic['Difference'] = difference

        p_dic = {
            'Opening': 0,
            'Purchase': 0,
            'Sales': 0,
            'Closing': 0,
            'Sample': 0,
            'Dip': 0,
            'Difference': 0,
        }
        for xx in self.env['product.product'].search([('name', '=', "Petrol")]):
            from datetime import timedelta
            yesterday = self.report_date - timedelta(1)
            if yesterday == xx.create_date.date():
                open = xx.qty_available
                p_dic['Opening'] = open
        purchase_product = self.env['stock.move'].search([('picking_type_id', '=', 1)])
        petrol_purchase_val = 0
        for pp in purchase_product:
            if pp.create_date.date() == self.report_date and pp.product_id.name == "Petrol":
                petrol_purchase_val += pp.product_uom_qty
        p_dic['Purchase'] = petrol_purchase_val
        p_dic['Sales'] = petrol_sale_sale
        dip = (diesel_purchase_val - petrol_sale_sale) + p_dic['Opening']
        difference = 0
        for rr in sale_order_wizard:
            if not rr.date.date() == self.report_date and rr.product_id.name == "Petrol":
                difference += rr.day_difference
                pass
        p_dic['Dip'] = dip
        p_dic['Closing'] = difference - dip
        p_dic['Difference'] = difference

        worksheet2.write(rows, 0, 'Product', design_14)
        worksheet2.write(rows, 1, 'Diesel', design_14)
        worksheet2.write(rows, 2, 'Petrol', design_14)
        rows += 1
        nrow = rows
        list_word = ['Opening', 'Purchase', 'Sales', 'Sample', 'Closing', 'Dip', 'Difference']
        for lw in list_word:
            worksheet2.write(rows, 0, lw, design_8_left)
            worksheet2.write(rows, 1, d_dic[lw], design_8_right)
            worksheet2.write(rows, 2, p_dic[lw], design_8_right)
            rows += 1

        rows += 1
        ap_domain = [('state', '=', 'posted')]
        aj_domain = [('type', 'in', ['bank', 'cash'])]
        if self.company_id:
            ap_domain.append(('company_id', '=', self.company_id.id))
            aj_domain.append(('company_id', '=', self.company_id.id))
        account_payment = self.env['account.payment'].search(ap_domain)
        account_journal = self.env['account.journal'].search(aj_domain)
        for aj in account_journal:
            aj_count = 0
            for ap in account_payment:
                if ap.date == self.report_date and ap.journal_id.id == aj.id:
                    aj_count += ap.amount_company_currency_signed
            worksheet2.write(rows, 0, aj.name, design_14_left)
            worksheet2.write(rows, 1, aj_count, design_14_right)
            rows += 1
        rows += 2
        new_row = rows
        rows += 1

        he_domain = [('state', '=', 'done')]
        pp_domain = [('can_be_expensed', '=', True)]
        if self.company_id:
            he_domain.append(('company_id', '=', self.company_id.id))
            pp_domain.append(('company_id', '=', self.company_id.id))
        hr_expense = self.env['hr.expense'].search(he_domain)
        product_product = self.env['product.product'].search(pp_domain)
        total_count = 0
        for pp in product_product:
            pp_count = 0
            for he in hr_expense:
                if he.date == self.report_date and pp.id == he.product_id.id:
                    pp_count += he.total_amount_company
                    total_count += he.total_amount_company
            worksheet2.write(rows, 0, pp.name, design_8_left)
            worksheet2.write(rows, 1, pp_count, design_8_right)
            rows += 1
        worksheet2.write(new_row, 0, 'Office Daily Expense', design_14)
        worksheet2.write(new_row, 1, total_count, design_14_right)

        fp = BytesIO()
        o = workbook_two.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': f'Fuels Day Wise Report.xls',
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'month.daily.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }
