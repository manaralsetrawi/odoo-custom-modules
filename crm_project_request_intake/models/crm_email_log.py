from odoo import fields, models


class CrmEmailLog(models.Model):
    _name = 'crm.email.log'
    _description = 'CRM Email Log'
    _order = 'email_date desc, id desc'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead / Opportunity',
        required=True,
        ondelete='cascade',
    )

    subject = fields.Char(string='Subject', required=True)
    sender_email = fields.Char(string='Sender Email')
    recipient_email = fields.Char(string='Recipient Email')

    email_date = fields.Datetime(
        string='Email Date',
        default=fields.Datetime.now,
        required=True,
    )

    email_type = fields.Selection([
        ('inquiry', 'Client Inquiry'),
        ('followup', 'Follow-up'),
        ('meeting', 'Meeting Coordination'),
        ('proposal', 'Proposal / Quotation'),
        ('approval', 'Approval Discussion'),
        ('general', 'General Communication'),
    ], string='Email Type', default='general', required=True)

    direction = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ], string='Direction', default='outgoing', required=True)

    body_preview = fields.Text(string='Message Preview')
    notes = fields.Text(string='Internal Notes')