from odoo import fields, models


class ProjectTeamAssignmentWizardLine(models.TransientModel):
    _name = 'project.team.assignment.wizard.line'
    _description = 'Project Team Assignment Wizard Line'

    wizard_id = fields.Many2one(
        'project.team.assignment.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
    )

    workload_percentage = fields.Float(
        string='Workload (%)',
        required=True,
        default=0.0,
    )

    notes = fields.Char(string='Notes')