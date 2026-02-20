from odoo import models, fields

class EmployeeDocument(models.Model):
    _name = "hr.employee.document"
    _description = "Employee Document"

    name = fields.Char(string="Document Name", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    document_file = fields.Binary(string="File")
    document_type = fields.Selection([
        ('contract', 'Contract'),
        ('certificate', 'Certificate'),
        ('other', 'Other')
    ], string="Document Type")
    notes = fields.Text(string="Notes")