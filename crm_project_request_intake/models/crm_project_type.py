from odoo import fields, models


class CrmProjectType(models.Model):
    _name = 'crm.project.type'
    _description = 'CRM Project Type'
    _order = 'name'

    name = fields.Char(string='Project Type', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_project_type_name', 'unique(name)', 'Project type must be unique.')
    ]