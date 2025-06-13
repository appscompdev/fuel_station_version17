from distutils.command.install import value

from odoo import models, fields, api, tools, _
from datetime import date, timedelta
import random


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_dashboard_all_data(self, data=None):
        print("------------3344444444444444")
        today = date.today()
        value = {
            'filters': {},
            'data': {'petrol': {}, 'diesel': {}, 'oil': {}, 'distilled_water': {}, 'total': {}},
        }
        date_list = today - timedelta(days=100)
        domain = [('date_order', '>=', date_list), ('date_order', '<=', today)]
        if data:
            if data['periods'] == 'month':
                date_list = today - timedelta(days=100)
                domain = [('date_order', '>=', date_list), ('date_order', '<=', today)]
            if data['periods'] == 'yesterday':
                date_list = today - timedelta(days=1)
                domain = [('date_order', '>=', date_list), ('date_order', '<=', today)]
            if data['periods'] == 'week':
                date_list = today - timedelta(days=7)
                domain = [('date_order', '>=', date_list), ('date_order', '<=', today)]
            if data['periods'] == 'today':
                date_list = today
                domain = [('date_order', '=', date_list)]

        sale_order = self.env['sale.order'].search(domain)
        purchase_order = self.env['purchase.order'].search(domain)
        hr_employee = self.env['hr.employee']
        shift_base = self.env['employee.shift'].search([])
        products = self.env['product.product'].search(
            [('sale_ok', '=', True), ('purchase_ok', '=', True), ('detailed_type', '=', 'product')])

        all_products = [
            {'name': i.name, 'd_n': i.display_name, 'id': i, 'product_templ_id': i.product_tmpl_id,
             'sale_quan': 0, 'sale_price': 0, 'val_id': i.product_tmpl_id.id,
             'purchase_price': 0, 'purchase_quan': 0, 'on_hand': "{:,.2f}".format(i.qty_available),
             'uom': i.uom_id.name}
            for i in products]

        for product in all_products:
            for sale in sale_order:
                for line in sale.order_line:
                    if product['product_templ_id'].id == line.product_template_id.id:
                        product['sale_quan'] += line.product_uom_qty
                        product['sale_price'] += line.price_subtotal
                    if line.product_id.product_tmpl_id.categ_id.name == "Oil":
                        product['sale_quan'] += line.product_uom_qty
                        product['sale_price'] += line.price_subtotal

            for purchase in purchase_order:
                for line in purchase.order_line:
                    if product['id'].id == line.product_id.id:
                        product['purchase_quan'] += line.product_qty
                        product['purchase_price'] += line.price_subtotal
                    if line.product_id.product_tmpl_id.categ_id.name == "Oil":
                        product['purchase_quan'] += line.product_uom_qty
                        product['purchase_price'] += line.price_subtotal

        sale_total = 0
        purchase_total = 0
        for i in all_products:
            if i['name'] == 'Petrol':
                value['data']['petrol']['sale'] = "{:,.2f}".format(i['sale_price'])
                value['data']['petrol']['purchase'] = "{:,.2f}".format(i['purchase_price'])
                sale_total += i['sale_price']
                purchase_total += i['purchase_price']
            if i['name'] == 'Diesel':
                value['data']['diesel']['sale'] = "{:,.2f}".format(i['sale_price'])
                value['data']['diesel']['purchase'] = "{:,.2f}".format(i['purchase_price'])
                sale_total += i['sale_price']
                purchase_total += i['purchase_price']
            if i['name'] == 'Distilled Water':
                value['data']['distilled_water']['sale'] = "{:,.2f}".format(i['sale_price'])
                value['data']['distilled_water']['purchase'] = "{:,.2f}".format(i['purchase_price'])
                sale_total += i['sale_price']
                purchase_total += i['purchase_price']
            if i['product_templ_id'].categ_id.name == 'Oil':
                value['data']['oil']['sale'] = "{:,.2f}".format(i['sale_price'])
                value['data']['oil']['purchase'] = "{:,.2f}".format(i['purchase_price'])
                print("-----------------------------------------44444444444444444444444444",
                      value['data']['oil']['purchase'])

                sale_total += i['sale_price']
                purchase_total += i['purchase_price']
        value['data']['total']['sale'] = "{:,.2f}".format(sale_total)
        value['data']['total']['purchase'] = "{:,.2f}".format(purchase_total)
        value['data']['products'] = all_products
        value['data']['symbol'] = self.env.company.currency_id.symbol
        print("999", value['data']['oil'])

        # shift Wise Income

        shift_data = [
            {'shift_name': i.name, 'id': i.id, 'emp': 0, 'value': 0, 'class': i,
             'symbol': self.env.company.currency_id.symbol}
            for i in shift_base]
        shift = [i['id'] for i in shift_data]
        patrol_pump = self.env['petrol.station.pump'].search([])

        for i in shift_data:
            employee = self.env['hr.employee'].search_count([('shift_id', '=', i['id'])])
            i['emp'] = employee
            for j in patrol_pump:
                for k in j.pump_entry_ids:
                    if k.employee_id.shift_id.id == i['id']:
                        i['value'] += k.advance_amount

        value['data']['shift_data'] = shift_data

        # Hr Employees

        employees = [{'id': i.id, 'name': i.name,
                      'shift': i.shift_id.name if i.shift_id.name else '-',
                      'mobile': i.mobile_phone if i.mobile_phone else '-',
                      'dept': i.department_id.name if i.department_id else '-'}
                     for i in hr_employee.search([])]

        value['data']['employees'] = employees
        value['filters']['company_name'] = self.env.company.name
        print("222222222222",value)
        return value

    def get_dashboard_chart(self, data=None):
        today = date.today()
        values = {}
        date_list = [today - timedelta(days=i) for i in range(30, 1, -3)]
        domain = [('date_order', '>=', date_list[0]), ('date_order', '<', today)]
        if data:
            if data['periods'] == 'month':
                date_list = [today - timedelta(days=i) for i in range(30, 0, -3)]
                domain = [('date_order', '>=', date_list[0]), ('date_order', '<=', today)]
            if data['periods'] == 'yesterday':
                date_list = [today - timedelta(days=i) for i in range(1, 0, -1)]
                domain = [('date_order', '>=', date_list[0]), ('date_order', '<=', today)]
            if data['periods'] == 'week':
                date_list = [today - timedelta(days=i) for i in range(7, 0, -1)]
                domain = [('date_order', '>=', date_list[0]), ('date_order', '<=', today)]
            if data['periods'] == 'today':
                date_list = today
                domain = [('date_order', '=', date_list)]

        products = self.env['product.product'].search(
            [('sale_ok', '=', True), ('purchase_ok', '=', True), ('detailed_type', '=', 'product')])
        sales = self.env['sale.order'].search(domain)
        colors = ['#cb0c9f', '#ff8000', '#3333ff', '#000099', '#ffcc00', '#000000', '#ac3939', '#00cc99',
                  '#808080', '#6600ff', '#cc0000', '#993333', '#999966', '#ffff66', '#00ff99', '#ff5050',
                  '#66ff99', '#cc00cc', '#ffcc00', '#003300', '#3333cc', '#cc33ff', '#660033', '#990099']
        all_products = [
            {'name': i.name, 'd_n': i.display_name, 'id': i.id, 'product_templ_id': i.product_tmpl_id.id,
             'value': [], 'color': self.choose_color(colors)}
            for i in products]

        for i in all_products:
            for dd in date_list:
                val = 0
                for sale in sales:
                    if sale.date_order.date() >= dd < sale.date_order.date():
                        for line in sale.order_line:
                            if line.product_template_id.id == i['product_templ_id']:
                                val += line.price_subtotal
                i['value'].append(val)

        values['products'] = all_products
        values['labels'] = date_list

        return values

    def choose_color(self, param):
        try:
            color = random.choices(param)
            if color[0]:
                param.remove(color[0])
                return color
        except:
            colors = ['#cb0c9f', '#ff8000', '#3333ff', '#000099', '#ffcc00', '#000000', '#ac3939', '#00cc99',
                      '#66ff99', '#cc00cc', '#ffcc00', '#003300', '#3333cc', '#cc33ff', '#660033', '#990099']
            color = random.choices(colors)
            return color
