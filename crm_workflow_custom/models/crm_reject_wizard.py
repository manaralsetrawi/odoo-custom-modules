from odoo import fields, models, _
from odoo.exceptions import ValidationError


class CrmRejectWizard(models.TransientModel):
    _name = 'crm.reject.wizard'
    _description = 'CRM Reject Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', required=True, readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_reject(self):
        self.ensure_one()

        if not self.rejection_reason:
            raise ValidationError(_("Please enter the rejection reason."))

        self.lead_id.rejection_reason = self.rejection_reason
        self.lead_id.action_reject_project_confirm()

        return {'type': 'ir.actions.act_window_close'}