from odoo import fields, models


class ExpenseType(models.Model):
    _name = 'expense.type'
    _description = 'Expense Type'
    _order = 'name'

    name = fields.Char(string='Expense Type', required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')