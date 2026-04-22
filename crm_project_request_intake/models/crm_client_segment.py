from odoo import fields, models, _
from odoo.exceptions import ValidationError


class CrmClientSegment(models.Model):
    _name = 'crm.client.segment'
    _description = 'CRM Client Segment'
    _order = 'name'

    name = fields.Char(string='Segment Name', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_segment_name', 'unique(name)', 'Client segment name must be unique.'),
    ]