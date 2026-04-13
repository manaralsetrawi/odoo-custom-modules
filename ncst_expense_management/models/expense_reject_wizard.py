from odoo import fields, models
from odoo.exceptions import ValidationError


class ExpenseRejectWizard(models.TransientModel):
    _name = 'expense.reject.wizard'
    _description = 'Expense Reject Wizard'

    expense_request_id = fields.Many2one(
        'expense.request',
        string='Expense Request',
        required=True,
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_reject(self):
        self.ensure_one()

        expense = self.expense_request_id

        if expense.state != 'submitted':
            raise ValidationError('Only submitted expense requests can be rejected.')

        if not expense.manager_user_id or expense.manager_user_id != self.env.user:
            raise ValidationError('Only the employee manager can reject this expense request.')

        expense.write({
            'state': 'rejected',
            'rejected_by': self.env.user.id,
            'rejected_date': fields.Datetime.now(),
            'rejection_reason': self.rejection_reason,
        })