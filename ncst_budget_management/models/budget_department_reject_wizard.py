from odoo import fields, models
from odoo.exceptions import ValidationError


class BudgetDepartmentRejectWizard(models.TransientModel):
    _name = 'budget.department.reject.wizard'
    _description = 'Reject Department Budget Request'

    department_budget_id = fields.Many2one(
        'budget.department',
        string='Department Budget Request',
        required=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_reject(self):
        self.ensure_one()

        if not self.department_budget_id:
            raise ValidationError('No department budget request was found.')

        if self.department_budget_id.state != 'submitted':
            raise ValidationError('Only submitted budget requests can be rejected.')

        self.department_budget_id.write({
            'state': 'rejected',
            'rejected_by': self.env.user.id,
            'rejection_date': fields.Datetime.now(),
            'rejection_reason': self.rejection_reason,
        })

        return {'type': 'ir.actions.act_window_close'}