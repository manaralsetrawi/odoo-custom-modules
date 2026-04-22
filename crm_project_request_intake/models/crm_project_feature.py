# models/crm_project_feature.py
from odoo import fields, models


class CrmProjectFeature(models.Model):
    _name = 'crm.project.feature'
    _description = 'CRM Project Feature'
    _order = 'name'

    name = fields.Char(string='Feature Name', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_project_feature_name', 'unique(name)', 'Project feature must be unique.')
    ]