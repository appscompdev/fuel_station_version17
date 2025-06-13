from odoo import api, fields, models, _


class EmployeeShift(models.Model):
    _name = 'employee.shift'
    _description = 'Employee Shift'

    name = fields.Char(string='Name')
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    shift_duration = fields.Float(string='Shift Duration')


class IndentVehicleList(models.Model):
    _name = 'indent.vehicle'
    _description = 'Indent Vehicle List'

    name = fields.Char(string='Vehicle No')
    customer_id = fields.Many2one(
        'res.partner', string='Customer', domain=[('customer_rank', '>', 0)]
    )


class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    shift_id = fields.Many2one('employee.shift', string='Shift')


class Contract(models.Model):
    _inherit = 'hr.contract'

    onhand_amount = fields.Float(string='On-Hand Amount')
    available_onhand_amount = fields.Float(string='Available On-Hand Amount')
    petty_cash_received = fields.Boolean(string='Petty Cash Received')
    petty_cash_last = fields.Float(string='Petty Cash Last')


class Company(models.Model):
    _inherit = "res.company"

    title = fields.Char(string="Title")
