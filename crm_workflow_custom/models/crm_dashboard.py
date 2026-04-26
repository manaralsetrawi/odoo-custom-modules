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

    def _get_project_request_domain(self):
        return [
            ('type', '=', 'opportunity'),
            ('request_type', '=', 'project_request'),
        ]

    @api.model
    def get_dashboard_data(self):
        lead_model = self.env['crm.lead']
        base_domain = self._get_project_request_domain()

        total_requests = lead_model.search_count(base_domain)
        new_inquiries = lead_model.search_count(base_domain + [('stage_id.name', '=', 'New Inquiry')])
        waiting_approval = lead_model.search_count(base_domain + [('stage_id.name', '=', 'Waiting Approval')])
        approved_requests = lead_model.search_count(base_domain + [('stage_id.name', '=', 'Approved')])
        rejected_requests = lead_model.search_count(base_domain + [('stage_id.name', '=', 'Rejected')])
        overdue_followups = lead_model.search_count(base_domain + [('followup_status', '=', 'overdue')])

        recent_requests_records = lead_model.search(
            base_domain,
            order='create_date desc',
            limit=5
        )

        waiting_approval_records = lead_model.search(
            base_domain + [('stage_id.name', '=', 'Waiting Approval')],
            order='write_date desc',
            limit=5
        )

        overdue_records = lead_model.search(
            base_domain + [('followup_status', '=', 'overdue')],
            order='next_followup_date asc',
            limit=5
        )

        recent_requests = [
            {
                'id': rec.id,
                'name': rec.name or '-',
                'customer': rec.partner_id.name or rec.partner_name or rec.contact_name or '-',
                'stage': rec.stage_id.name or '-',
                'stage_class': self._get_stage_badge_class(rec.stage_id.name or ''),
            }
            for rec in recent_requests_records
        ]

        waiting_approval_requests = [
            {
                'id': rec.id,
                'name': rec.name or '-',
                'customer': rec.partner_id.name or rec.partner_name or rec.contact_name or '-',
                'owner': rec.user_id.name or '-',
            }
            for rec in waiting_approval_records
        ]

        overdue_requests = [
            {
                'id': rec.id,
                'name': rec.name or '-',
                'next_followup_date': str(rec.next_followup_date) if rec.next_followup_date else '-',
                'status': dict(rec._fields['followup_status'].selection).get(rec.followup_status, '-') if rec.followup_status else '-',
            }
            for rec in overdue_records
        ]

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

    def _get_stage_badge_class(self, stage_name):
        mapping = {
            'New Inquiry': 'crmdsh_badge_new',
            'Initial Discussion': 'crmdsh_badge_discussion',
            'Requirement Analysis': 'crmdsh_badge_analysis',
            'Solution Design': 'crmdsh_badge_solution',
            'Proposal Submitted': 'crmdsh_badge_proposal',
            'Waiting Approval': 'crmdsh_badge_waiting',
            'Approved': 'crmdsh_badge_approved',
            'Rejected': 'crmdsh_badge_rejected',
        }
        return mapping.get(stage_name, 'crmdsh_badge_default')