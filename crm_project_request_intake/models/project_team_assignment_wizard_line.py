from odoo import api, fields, models


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
        domain="[('department_id.name', '=', 'AI Research and Development')]",
    )

    employee_team_id = fields.Many2one(
        'project.assignment.team',
        string='Employee Team',
        compute='_compute_employee_team_id',
        store=False,
    )

    workload_percentage = fields.Float(
        string='Total Allocation (%)',
        required=True,
        default=0.0,
    )

    notes = fields.Char(string='Notes')

    @api.depends('employee_id')
    def _compute_employee_team_id(self):
        Team = self.env['project.assignment.team']
        for line in self:
            team = Team.search([
                ('member_ids', 'in', line.employee_id.id)
            ], limit=1)
            line.employee_team_id = team.id if team else False