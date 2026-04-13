from odoo import fields, models


class BudgetReservationLine(models.Model):
    _name = 'budget.reservation.line'
    _description = 'Budget Reservation Line'
    _order = 'id asc'

    reservation_id = fields.Many2one(
        'budget.reservation',
        string='Reservation',
        required=True,
        ondelete='cascade',
    )

    department_budget_id = fields.Many2one(
        'budget.department',
        string='Department Budget',
        required=True,
        ondelete='cascade',
    )

    department_id = fields.Many2one(
        related='department_budget_id.department_id',
        string='Department',
        store=True,
        readonly=True,
    )

    general_budget_id = fields.Many2one(
        related='department_budget_id.general_budget_id',
        string='General Budget',
        store=True,
        readonly=True,
    )

    currency_id = fields.Many2one(
        related='department_budget_id.currency_id',
        string='Currency',
        store=True,
        readonly=True,
    )

    amount = fields.Monetary(
        string='Reserved Amount',
        required=True,
        currency_field='currency_id',
    )

    reservation_state = fields.Selection(
        related='reservation_id.state',
        string='Reservation State',
        store=True,
        readonly=True,
    )