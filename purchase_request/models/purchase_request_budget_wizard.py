from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseRequestBudgetWizard(models.TransientModel):
    _name = 'purchase.request.budget.wizard'
    _description = 'Purchase Request Budget Verification Wizard'

    purchase_request_id = fields.Many2one(
        'purchase.request',
        string='Purchase Request',
        required=True,
    )

    available_budget = fields.Float(
        string='Available Budget',
        required=True,
    )

    budget_note = fields.Text(
        string='Budget Verification Note',
    )

    def action_confirm_budget_verification(self):
        self.ensure_one()

        purchase_request = self.purchase_request_id

        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )

        if purchase_request.state != 'waiting_budget':
            raise UserError("This purchase request is not waiting for budget verification.")

        if not current_employee or not current_employee.department_id:
            raise UserError("The current user is not linked to an employee with a department.")

        if current_employee.department_id.id != 2:
            raise UserError("Only employees in the Finance & Accounting department can verify budget.")

        if self.available_budget < purchase_request.amount_total:
            raise UserError("Budget is insufficient for this purchase request.")

        purchase_request.write({
            'budget_available_amount': self.available_budget,
            'budget_note': self.budget_note,
            'budget_verified': True,
            'budget_verified_by': self.env.user.id,
            'budget_verified_date': fields.Datetime.now(),
            'state': 'approved',
        })

        purchase_request.message_post(
            body="Budget verified by Finance. Purchase Request approved."
        )

        return {'type': 'ir.actions.act_window_close'}