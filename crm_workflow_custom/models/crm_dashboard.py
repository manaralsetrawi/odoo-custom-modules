from odoo import api, fields, models


class CrmDashboard(models.Model):
    """Read-only helper model for the CRM dashboard UI.

    Note: _auto = False means there is no SQL table for this model.
    We return aggregated data via :meth:`get_dashboard_data`.
    """

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
        """Domain used for all 'Project Request' CRM leads."""
        return [
            ('type', '=', 'opportunity'),
            # Custom field on crm.lead that tags the opportunity as a project request.
            ('request_type', '=', 'project_request'),
        ]

    @api.model
    def get_dashboard_data(self):
        """Build the dashboard payload (counts + top 5 lists).

        Used by the frontend to render KPIs and small tables.
        """
        lead_model = self.env['crm.lead']
        # All queries start from the same base domain to keep numbers consistent.
        base_domain = self._get_project_request_domain()

        # KPI counters (search_count is cheaper than search + len()).
        total_requests = lead_model.search_count(base_domain)
        # Stages are filtered by their display name; keep these in sync with your CRM pipeline.
        new_inquiries = lead_model.search_count(base_domain + [('stage_id.name', '=', 'New Inquiry')])
        waiting_approval = lead_model.search_count(base_domain + [('stage_id.name', '=', 'Waiting Approval')])
        approved_requests = lead_model.search_count(base_domain + [('stage_id.name', '=', 'Approved')])
        rejected_requests = lead_model.search_count(base_domain + [('stage_id.name', '=', 'Rejected')])

        # Custom fields on crm.lead used for follow-ups:
        # - followup_status: selection, includes 'overdue'
        # - next_followup_date: date/datetime used for ordering
        overdue_followups = lead_model.search_count(base_domain + [('followup_status', '=', 'overdue')])

        # Latest created project requests.
        recent_requests_records = lead_model.search(
            base_domain,
            order='create_date desc',
            limit=5
        )

        # Requests currently waiting for approval (most recently updated).
        waiting_approval_records = lead_model.search(
            base_domain + [('stage_id.name', '=', 'Waiting Approval')],
            order='write_date desc',
            limit=5
        )

        # Overdue follow-ups ordered by the next follow-up date (soonest first).
        overdue_records = lead_model.search(
            base_domain + [('followup_status', '=', 'overdue')],
            order='next_followup_date asc',
            limit=5
        )

        recent_requests = [
            {
                'id': rec.id,
                'name': rec.name or '-',
                # Prefer the linked partner; fall back to lead contact fields.
                'customer': rec.partner_id.name or rec.partner_name or rec.contact_name or '-',
                'stage': rec.stage_id.name or '-',
                # Used by the dashboard CSS to color the stage badge.
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
                # Convert to string to keep RPC/JSON payload simple.
                'next_followup_date': str(rec.next_followup_date) if rec.next_followup_date else '-',
                # Human-readable label from the selection definition.
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
        """Map a stage name to a CSS class (badge style)."""
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
        # Default class keeps the UI stable for unexpected/new stage names.
        return mapping.get(stage_name, 'crmdsh_badge_default')