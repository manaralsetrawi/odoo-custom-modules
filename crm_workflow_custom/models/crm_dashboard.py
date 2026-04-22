from odoo import api, fields, models


class CrmDashboard(models.Model):
    _name = 'crm.dashboard'
    _description = 'CRM Dashboard'
    _auto = False

    name = fields.Char(string='Name')
    total_requests = fields.Integer(string='Total Requests')
    new_inquiries = fields.Integer(string='New Inquiries')
    waiting_approval = fields.Integer(string='Waiting Approval')
    approved_requests = fields.Integer(string='Approved Requests')
    rejected_requests = fields.Integer(string='Rejected Requests')
    overdue_followups = fields.Integer(string='Overdue Follow-ups')

    @api.model
    def get_dashboard_data(self):
        lead_model = self.env['crm.lead']

        total_requests = lead_model.search_count([])
        new_inquiries = lead_model.search_count([('stage_id.name', '=', 'New Inquiry')])
        waiting_approval = lead_model.search_count([('stage_id.name', '=', 'Waiting Approval')])
        approved_requests = lead_model.search_count([('stage_id.name', '=', 'Approved')])
        rejected_requests = lead_model.search_count([('stage_id.name', '=', 'Rejected')])
        overdue_followups = lead_model.search_count([('followup_status', '=', 'overdue')])

        recent_requests = lead_model.search([], order='create_date desc', limit=5)
        waiting_approval_requests = lead_model.search(
            [('stage_id.name', '=', 'Waiting Approval')],
            order='write_date desc',
            limit=5
        )
        overdue_requests = lead_model.search(
            [('followup_status', '=', 'overdue')],
            order='next_followup_date asc',
            limit=5
        )

        return {
            'total_requests': total_requests,
            'new_inquiries': new_inquiries,
            'waiting_approval': waiting_approval,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests,
            'overdue_followups': overdue_followups,
            'recent_requests': recent_requests,
            'waiting_approval_requests': waiting_approval_requests,
            'overdue_requests': overdue_requests,
        }