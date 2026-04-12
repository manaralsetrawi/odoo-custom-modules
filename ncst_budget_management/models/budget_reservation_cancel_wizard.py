from odoo import fields, models
from odoo.exceptions import ValidationError


class BudgetReservationCancelWizard(models.TransientModel):
    _name = 'budget.reservation.cancel.wizard'
    _description = 'Cancel Budget Reservation'

    budget_reservation_id = fields.Many2one(
        'budget.reservation',
        string='Budget Reservation',
        required=True,
    )
    cancel_reason = fields.Text(
        string='Cancellation Reason',
        required=True,
    )

    def action_confirm_cancel(self):
        self.ensure_one()

        if not self.budget_reservation_id:
            raise ValidationError('No reservation record was found.')

        if self.budget_reservation_id.state not in ['draft', 'submitted', 'reserved']:
            raise ValidationError('Only draft, submitted, or reserved reservations can be cancelled.')

        self.budget_reservation_id.write({
            'state': 'cancelled',
            'cancelled_by': self.env.user.id,
            'cancelled_date': fields.Datetime.now(),
            'cancel_reason': self.cancel_reason,
        })

        return {'type': 'ir.actions.act_window_close'}