from odoo import fields, models


class FinanceExceptionResultWizard(models.TransientModel):
    _name = 'finance.exception.result.wizard'
    _description = 'Finance Exception Result Wizard'

    move_id = fields.Many2one(
        'account.move',
        string='Document',
        readonly=True,
    )

    finance_exception_status = fields.Selection([
        ('valid', 'Valid'),
        ('has_issue', 'Has Issue'),
        ('blocked', 'Blocked'),
    ], string='Exception Status', readonly=True)

    finance_exception_summary = fields.Text(
        string='Check Result',
        readonly=True,
    )

    finance_missing_invoice_date = fields.Boolean(
        string='Missing Invoice / Bill Date',
        readonly=True,
    )

    finance_missing_payment_term = fields.Boolean(
        string='Missing Payment Terms / Due Date',
        readonly=True,
    )

    finance_missing_due_date = fields.Boolean(
        string='Missing Due Date',
        readonly=True,
    )

    finance_missing_tax = fields.Boolean(
        string='Missing Tax',
        readonly=True,
    )

    finance_invalid_date_sequence = fields.Boolean(
        string='Date Later Than Due Date',
        readonly=True,
    )

    finance_missing_vendor_ref = fields.Boolean(
        string='Missing Vendor Reference',
        readonly=True,
    )

    finance_duplicate_vendor_ref = fields.Boolean(
        string='Duplicate Vendor Bill Reference',
        readonly=True,
    )