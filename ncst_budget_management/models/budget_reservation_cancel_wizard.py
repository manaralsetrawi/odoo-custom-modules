from odoo import fields, models # type: ignore
from odoo.exceptions import ValidationError # type: ignore


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

        is_manager = self.env.user.has_group('ncst_budget_management.group_budget_finance_manager')
        is_creator = self.budget_reservation_id.created_by == self.env.user

        if not (is_manager or is_creator):
            raise ValidationError('Only the reservation creator or the Finance Manager can cancel this reservation.')

        if self.budget_reservation_id.state != 'reserved':
            raise ValidationError('Only reserved reservations can be cancelled.')

        self.budget_reservation_id.write({
            'state': 'cancelled',
            'cancelled_by': self.env.user.id,
            'cancelled_date': fields.Datetime.now(),
            'cancel_reason': self.cancel_reason,
        })

        return {'type': 'ir.actions.act_window_close'}