from odoo import fields, models


class FinanceBillCompletenessWizard(models.TransientModel):
    _name = 'finance.bill.completeness.wizard'
    _description = 'Finance Bill Completeness Wizard'

    move_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        readonly=True,
    )

    finance_readiness_status = fields.Selection([
        ('incomplete', 'Needs Completion'),
        ('ready', 'Ready for Review'),
    ], string='Completeness Status', readonly=True)

    finance_readiness_summary = fields.Text(
        string='Check Result',
        readonly=True,
    )

    finance_missing_bill_reference = fields.Boolean(
        string='Bill Reference Missing',
        readonly=True,
    )

    finance_missing_bill_tax = fields.Boolean(
        string='Tax Missing',
        readonly=True,
    )