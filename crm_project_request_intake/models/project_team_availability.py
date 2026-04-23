from odoo import fields, models


class ProjectTeamAvailability(models.Model):
    _name = 'project.team.availability'
    _description = 'Project Team Availability'
    _order = 'year desc, month desc'

    team_id = fields.Many2one(
        'project.assignment.team',
        string='Team',
        required=True,
        ondelete='cascade',
    )

    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month', required=True)

    year = fields.Integer(string='Year', required=True)

    availability_status = fields.Selection([
        ('available', 'Available'),
        ('partial', 'Partially Available'),
        ('unavailable', 'Unavailable'),
    ], string='Availability Status', required=True, default='available')

    notes = fields.Text(string='Notes')