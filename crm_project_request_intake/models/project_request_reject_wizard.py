from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ProjectRequestRejectWizard(models.TransientModel):
    _name = 'project.request.reject.wizard'
    _description = 'Reject Project Request Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    rejection_category = fields.Selection([
        ('budget', 'Budget Issue'),
        ('timeline', 'Timeline Issue'),
        ('scope', 'Scope Not Suitable'),
        ('technical', 'Technical Limitation'),
        ('other', 'Other'),
    ], string='Rejection Category', required=True)

    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_rejection(self):
        self.ensure_one()

        lead = self.lead_id
        if not lead:
            raise ValidationError(_("No lead was found for rejection."))

        if lead.request_type != 'project_request' or lead.type != 'lead':
            raise ValidationError(
                _("Only project request leads can be rejected."))

        if lead.intake_state != 'under_review':
            raise ValidationError(
                _("Only requests under review can be rejected."))

        rejected_stage = lead._get_stage_by_xmlid(
            'crm_project_request_intake.crm_stage_project_request_rejected'
        )

        full_reason = "%s\n\n%s" % (
            dict(self._fields['rejection_category'].selection).get(
                self.rejection_category, ''),
            self.rejection_reason,
        )

        lead.write({
            'intake_state': 'rejected',
            'intake_rejection_reason': full_reason,
            'stage_id': rejected_stage.id,
        })
        lead._send_project_request_rejection_email()
        
        self.env['crm.email.log'].create({
            'lead_id': lead.id,
            'subject': 'Project Request Rejection - %s' % (lead.name or ''),
            'sender_email': self.env.user.email or '',
            'recipient_email': lead.email_from or lead.intake_client_email or '',
            'email_type': 'rejection',
            'direction': 'outgoing',
            'body_preview': full_reason,
            'notes': 'Automatic rejection email sent after the project request was rejected.',
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
