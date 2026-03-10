from odoo import models, fields

class MyModel(models.Model):
    _name = 'my.model'
    _description = 'My First Model'

    name = fields.Char(string="Title", required=True)

    description = fields.Text(string="Description")

    date = fields.Date(string="Date", default=fields.Date.today)

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
        ],
        string="Status",
        default='draft'
    )

    active = fields.Boolean(string="Active", default=True)

    partner_id = fields.Many2one(
        'res.partner',
        string="Customer"
    )