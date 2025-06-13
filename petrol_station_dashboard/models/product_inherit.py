from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pump_color = fields.Selection([('green', 'Green'), ('blue', 'Blue')], string="Pump Color", default="green")


class ProductProduct(models.Model):
    _inherit = "product.product"

    pump_color = fields.Selection([('green', 'Green'), ('blue', 'Blue')], string="Pump Color", default="green")
