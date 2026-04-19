from odoo import api, fields, models


class CrmSupportTicket(models.Model):
    _name = 'crm.support.ticket'
    _description = 'CRM Support Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Ticket Reference", required=True, copy=False, default="New")
    lead_id = fields.Many2one('crm.lead', string="Related Lead/Opportunity", tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", tracking=True)
    subject = fields.Char(string="Subject", required=True, tracking=True)
    description = fields.Text(string="Description")
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
    ], string="Priority", default='1', tracking=True)

    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('waiting_customer', 'Waiting Customer'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], string="Status", default='new', tracking=True)

    assigned_user_id = fields.Many2one('res.users', string="Assigned To", tracking=True)
    resolution_notes = fields.Text(string="Resolution Notes")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('crm.support.ticket') or 'New'
        return super().create(vals)

    def action_mark_in_progress(self):
        self.status = 'in_progress'

    def action_mark_resolved(self):
        self.status = 'resolved'

    def action_mark_closed(self):
        self.status = 'closed'