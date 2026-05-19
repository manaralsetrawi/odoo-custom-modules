from odoo import api, fields, models, Command
from odoo.exceptions import AccessError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # -------------------------------------------------------------------------
    # PHASE 1 - LINK PURCHASE REQUEST TO RFQ / PO
    # -------------------------------------------------------------------------

    purchase_request_id = fields.Many2one(
        "purchase.request",
        string="Purchase Request",
        tracking=True,
        help="Related purchase request for this quotation or purchase order.",
    )

    quotation_count_for_request = fields.Integer(
        string="Quotation Count",
        compute="_compute_quotation_count_for_request",
        help="Number of quotations linked to the same purchase request.",
    )

    has_purchase_request = fields.Boolean(
        string="Has Purchase Request",
        compute="_compute_has_purchase_request",
        help="Technical helper showing whether this RFQ is linked to a purchase request.",
    )

    is_above_quotation_threshold = fields.Boolean(
        string="Above BD 1000",
        compute="_compute_is_above_quotation_threshold",
        help="True when the RFQ total amount is greater than BD 1000.",
    )

    is_multi_quotation_case = fields.Boolean(
        string="Multi Quotation Case",
        compute="_compute_is_multi_quotation_case",
        help="True when more than one quotation exists for the same purchase request.",
    )

    available_vendor_ids = fields.Many2many(
        "res.partner",
        string="Available Vendors",
        compute="_compute_available_vendor_ids",
        help="Vendors who can supply all products in the selected Purchase Request.",
    )

    missing_vendor_price = fields.Boolean(
        string="Missing Vendor Price",
        compute="_compute_missing_vendor_price",
        help="Technical helper showing whether one or more RFQ lines still have no vendor price.",
    )

    # -------------------------------------------------------------------------
    # PHASE 2 - QUOTATION EVALUATION AND VENDOR RECOMMENDATION
    # -------------------------------------------------------------------------

    technical_evaluation = fields.Selection(
        [
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        string="Technical Evaluation",
        default="pending",
        tracking=True,
        help="Technical evaluation result for this supplier quotation.",
    )

    commercial_evaluation = fields.Selection(
        [
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        string="Commercial Evaluation",
        default="pending",
        tracking=True,
        help="Commercial evaluation result for this supplier quotation.",
    )

    evaluation_notes = fields.Text(
        string="Evaluation Notes",
        help="Notes related to technical and commercial evaluation of this quotation.",
    )

    is_recommended_vendor = fields.Boolean(
        string="Recommended Vendor",
        tracking=True,
        help="Checked when this quotation is selected as the recommended vendor.",
    )

    recommendation_reason = fields.Text(
        string="Recommendation Reason",
        help="Reason for selecting this supplier quotation.",
    )

    meets_minimum_quotation_rule = fields.Boolean(
        string="Meets Minimum Quotation Rule",
        compute="_compute_meets_minimum_quotation_rule",
        help="True when the required number of quotations is available for this Purchase Request.",
    )

    quotation_exception_reason = fields.Text(
        string="Quotation Exception Justification",
        help="Required justification when fewer than 3 quotations are available for purchases above BD 1000.",
    )

    # -------------------------------------------------------------------------
    # PHASE 3 - FINANCIAL APPROVAL ROUTING
    # -------------------------------------------------------------------------

    financial_approval_state = fields.Selection(
        [
            ("not_required", "Not Required"),
            ("to_approve", "Waiting for Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Financial Approval Status",
        default="not_required",
        tracking=True,
        help="Financial approval status based on the total quotation amount.",
    )

    required_financial_approval_level = fields.Selection(
        [
            ("finance_director", "Director of Finance"),
            ("deputy_ceo", "Deputy CEO"),
            ("ceo", "CEO"),
        ],
        string="Required Financial Approval",
        compute="_compute_required_financial_approval_level",
        store=True,
        tracking=True,
        help="Required financial approver level based on the total amount.",
    )

    financial_approved_by = fields.Many2one(
        "res.users",
        string="Financially Approved By",
        readonly=True,
        tracking=True,
        help="User who approved this quotation in the financial approval step.",
    )

    financial_approved_date = fields.Datetime(
        string="Financial Approval Date",
        readonly=True,
        tracking=True,
        help="Date and time when financial approval was completed.",
    )

    financial_rejection_reason = fields.Text(
        string="Financial Rejection Reason",
        tracking=True,
        help="Reason entered when the quotation is rejected in the financial approval step.",
    )

    budget_reservation_id = fields.Many2one(
        "budget.reservation",
        string="Budget Reservation",
        readonly=True,
        copy=False,
        help="Budget reservation created for this RFQ before financial approval.",
    )

    budget_reservation_status = fields.Selection(
        related="budget_reservation_id.state",
        string="Budget Reservation Status",
        readonly=True,
        store=False,
    )

    # -------------------------------------------------------------------------
    # PHASE 4 - PURCHASE ORDER ISSUANCE AND VENDOR ACKNOWLEDGMENT
    # -------------------------------------------------------------------------

    vendor_ack_required = fields.Boolean(
        string="Vendor Acknowledgment Required",
        default=True,
        tracking=True,
        help="Indicates whether vendor acknowledgment is required for this purchase order.",
    )

    vendor_ack_received = fields.Boolean(
        string="Vendor Acknowledged",
        tracking=True,
        help="Checked when the vendor acknowledges the purchase order.",
    )

    vendor_ack_recorded_by = fields.Many2one(
        "res.users",
        string="Acknowledgment Recorded By",
        readonly=True,
        tracking=True,
        help="User who recorded the vendor acknowledgment.",
    )

    vendor_ack_date = fields.Datetime(
        string="Acknowledgment Date",
        readonly=True,
        tracking=True,
        help="Date and time when vendor acknowledgment was recorded.",
    )

    vendor_ack_notes = fields.Text(
        string="Vendor Acknowledgment Notes",
        help="Notes related to vendor acknowledgment of the purchase order.",
    )

    is_confirmed_purchase_order = fields.Boolean(
        string="Is Confirmed Purchase Order",
        compute="_compute_is_confirmed_purchase_order",
        help="Technical helper showing whether this record is already a confirmed Purchase Order.",
    )

    # -------------------------------------------------------------------------
    # PHASE 5 + 6 - BILLING / PAYMENT TRACKING / PROCUREMENT CLOSURE
    # -------------------------------------------------------------------------

    vendor_bill_ids = fields.One2many(
        "account.move",
        "purchase_order_id",
        string="Vendor Bills",
        help="Vendor bills linked to this Purchase Order.",
    )

    vendor_bill_count = fields.Integer(
        string="Vendor Bill Count",
        compute="_compute_vendor_bill_metrics",
        help="Number of vendor bills linked to this Purchase Order.",
    )

    verified_vendor_bill_count = fields.Integer(
        string="Verified Vendor Bill Count",
        compute="_compute_vendor_bill_metrics",
        help="Number of verified vendor bills linked to this Purchase Order.",
    )

    all_vendor_bills_verified = fields.Boolean(
        string="All Vendor Bills Verified",
        compute="_compute_vendor_bill_metrics",
        help="True when all linked vendor bills are verified.",
    )

    payment_status_summary = fields.Selection(
        [
            ("no_bill", "No Vendor Bill"),
            ("unpaid", "Unpaid"),
            ("partial", "Partially Paid"),
            ("in_payment", "In Payment"),
            ("paid", "Paid"),
        ],
        string="Payment Status Summary",
        compute="_compute_payment_status_summary",
        help="Summary of payment progress across linked vendor bills.",
    )

    ready_for_procurement_closure = fields.Boolean(
        string="Ready for Procurement Closure",
        compute="_compute_ready_for_procurement_closure",
        help="True when vendor acknowledgment, receipt confirmation, bill verification, and payment are all completed.",
    )

    procurement_closure_state = fields.Selection(
        [
            ("open", "Open"),
            ("closed", "Closed"),
        ],
        string="Procurement Closure Status",
        default="open",
        tracking=True,
        help="Final closure state of the procurement cycle.",
    )

    procurement_closed_by = fields.Many2one(
        "res.users",
        string="Procurement Closed By",
        readonly=True,
        tracking=True,
        help="User who marked the procurement cycle as closed.",
    )

    procurement_closed_date = fields.Datetime(
        string="Procurement Closed Date",
        readonly=True,
        tracking=True,
        help="Date and time when the procurement cycle was closed.",
    )

    # -------------------------------------------------------------------------
    # UI IMPROVEMENT - WORKFLOW PROGRESS STATUS
    # -------------------------------------------------------------------------

    workflow_progress_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("under_evaluation", "Under Evaluation"),
            ("recommended", "Recommended Vendor Selected"),
            ("waiting_finance", "Waiting for Financial Approval"),
            ("finance_approved", "Financially Approved"),
            ("po_issued", "Purchase Order Issued"),
            ("vendor_acknowledged", "Vendor Acknowledged"),
            ("receipt_confirmed", "Receipt Confirmed"),
            ("invoice_verified", "Invoice Verified"),
            ("paid", "Paid"),
            ("closed", "Closed"),
        ],
        string="Workflow Progress",
        compute="_compute_workflow_progress_status",
        store=True,
        help="Shows the current procurement workflow progress for this RFQ/PO.",
    )

    # -------------------------------------------------------------------------
    # SAFE UI EDITABILITY HELPERS
    # -------------------------------------------------------------------------

    can_edit_procurement_fields = fields.Boolean(
        compute="_compute_role_edit_permissions",
        help="Technical helper to allow Procurement Officer to edit selected procurement fields only.",
    )

    can_edit_financial_rejection = fields.Boolean(
        compute="_compute_role_edit_permissions",
        help="Technical helper to allow financial approvers to edit financial rejection reason only.",
    )

    # -------------------------------------------------------------------------
    # VENDOR / PRODUCT HELPERS
    # -------------------------------------------------------------------------

    def _get_supplier_partner_from_seller(self, seller):
        if "partner_id" in seller._fields:
            return seller.partner_id
        return seller.name

    def _get_common_vendors_for_pr_products(self, purchase_request):
        if not purchase_request or not purchase_request.line_ids:
            return self.env["res.partner"]

        common_vendor_ids = None

        for pr_line in purchase_request.line_ids:
            product = pr_line.product_id
            if not product:
                continue

            seller_partners = self.env["res.partner"]
            for seller in product.product_tmpl_id.seller_ids:
                partner = self._get_supplier_partner_from_seller(seller)
                if partner and partner.is_company and partner.supplier_rank > 0:
                    seller_partners |= partner

            product_vendor_ids = set(seller_partners.ids)

            if common_vendor_ids is None:
                common_vendor_ids = product_vendor_ids
            else:
                common_vendor_ids &= product_vendor_ids

        if not common_vendor_ids:
            return self.env["res.partner"]

        return self.env["res.partner"].browse(list(common_vendor_ids))

    def _get_vendor_sellerinfo_for_product(self, product, vendor, quantity=0.0):
        if not product or not vendor:
            return False

        matched_sellers = product.product_tmpl_id.seller_ids.filtered(
            lambda s: (
                self._get_supplier_partner_from_seller(s) == vendor
                and (not s.product_id or s.product_id == product)
            )
        )

        if not matched_sellers:
            return False

        eligible = matched_sellers.filtered(lambda s: not s.min_qty or quantity >= s.min_qty)
        if eligible:
            matched_sellers = eligible

        matched_sellers = matched_sellers.sorted(
            key=lambda s: (
                -(s.min_qty or 0.0),
                s.sequence if "sequence" in s._fields else 0,
                s.id,
            )
        )

        return matched_sellers[:1] if matched_sellers else False

    def _apply_vendor_prices_to_order_lines(self):
        self.ensure_one()

        if not self.partner_id:
            return {
                "warning": {
                    "title": "Vendor Required",
                    "message": "Please select a vendor first.",
                }
            }

        missing_products = []

        for line in self.order_line.filtered(lambda l: l.product_id):
            seller = self._get_vendor_sellerinfo_for_product(
                line.product_id,
                self.partner_id,
                quantity=line.product_qty,
            )

            if seller:
                # force-update the RFQ line price from supplier info
                line.update({
                    "price_unit": seller.price,
                })
            else:
                line.update({
                    "price_unit": 0.0,
                })
                missing_products.append(line.product_id.display_name)

        if missing_products:
            return {
                "warning": {
                    "title": "Missing Vendor Prices",
                    "message": (
                        "No vendor price was found for these products: %s. "
                        "Their price was left as 0.0, so please review them."
                    ) % ", ".join(missing_products)
                }
            }

        return {}

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends("purchase_request_id")
    def _compute_has_purchase_request(self):
        for order in self:
            order.has_purchase_request = bool(order.purchase_request_id)

    @api.depends("purchase_request_id")
    def _compute_quotation_count_for_request(self):
        for order in self:
            if order.purchase_request_id:
                order.quotation_count_for_request = self.search_count(
                    [("purchase_request_id", "=", order.purchase_request_id.id)]
                )
            else:
                order.quotation_count_for_request = 0

    @api.depends("purchase_request_id", "purchase_request_id.line_ids.product_id")
    def _compute_available_vendor_ids(self):
        for order in self:
            if not order.purchase_request_id:
                order.available_vendor_ids = False
                continue

            order.available_vendor_ids = order._get_common_vendors_for_pr_products(order.purchase_request_id)

    @api.depends("order_line.price_unit", "order_line.product_id")
    def _compute_missing_vendor_price(self):
        for order in self:
            order.missing_vendor_price = any(
                line.product_id and not line.price_unit
                for line in order.order_line
            )

    @api.onchange("purchase_request_id")
    def _onchange_purchase_request_id_fill_order_lines(self):
        self.ensure_one()

        self.partner_id = False

        if not self.purchase_request_id:
            self.order_line = [Command.clear()]
            return {
                "domain": {
                    "partner_id": [("supplier_rank", ">", 0), ("is_company", "=", True)]
                }
            }

        new_lines = [Command.clear()]

        for pr_line in self.purchase_request_id.line_ids:
            if not pr_line.product_id:
                continue

            line_name = pr_line.product_id.display_name
            if pr_line.specifications:
                line_name = f"{line_name}\nSpecifications: {pr_line.specifications}"

            new_lines.append(
                Command.create(
                    {
                        "product_id": pr_line.product_id.id,
                        "name": line_name,
                        "product_qty": pr_line.quantity,
                        "product_uom": pr_line.product_id.uom_po_id.id
                        or pr_line.product_id.uom_id.id,
                        "price_unit": 0.0,
                        "date_planned": fields.Datetime.now(),
                    }
                )
            )

        self.order_line = new_lines

        valid_vendors = self._get_common_vendors_for_pr_products(self.purchase_request_id)

        result = {
            "domain": {
                "partner_id": [
                    ("id", "in", valid_vendors.ids),
                    ("supplier_rank", ">", 0),
                    ("is_company", "=", True),
                ]
            }
        }

        if not valid_vendors:
            result["warning"] = {
                "title": "No Matching Vendors",
                "message": "No company vendor in Odoo is configured to supply all products in this Purchase Request.",
            }

        return result

    @api.onchange("partner_id")
    def _onchange_partner_id_apply_vendor_prices(self):
        self.ensure_one()

        if not self.partner_id or not self.purchase_request_id:
            return {}

        valid_vendors = self._get_common_vendors_for_pr_products(self.purchase_request_id)
        if self.partner_id not in valid_vendors:
            self.partner_id = False
            return {
                "warning": {
                    "title": "Invalid Vendor",
                    "message": "This vendor does not supply all products in the selected Purchase Request.",
                }
            }

        result = self._apply_vendor_prices_to_order_lines()

        # force refresh of totals in the form after prices are updated
        self._amount_all()

        return result

    @api.depends("amount_total")
    def _compute_is_above_quotation_threshold(self):
        for order in self:
            order.is_above_quotation_threshold = order.amount_total > 1000

    @api.depends("quotation_count_for_request")
    def _compute_is_multi_quotation_case(self):
        for order in self:
            order.is_multi_quotation_case = order.quotation_count_for_request > 1

    @api.depends(
        "purchase_request_id",
        "quotation_count_for_request",
        "is_above_quotation_threshold",
        "quotation_exception_reason",
    )
    def _compute_meets_minimum_quotation_rule(self):
        for order in self:
            if not order.purchase_request_id:
                order.meets_minimum_quotation_rule = False
            elif not order.is_above_quotation_threshold:
                order.meets_minimum_quotation_rule = True
            elif order.quotation_count_for_request >= 3:
                order.meets_minimum_quotation_rule = True
            else:
                order.meets_minimum_quotation_rule = bool(order.quotation_exception_reason)

    @api.depends("amount_total")
    def _compute_required_financial_approval_level(self):
        for order in self:
            if order.amount_total <= 5000:
                order.required_financial_approval_level = "finance_director"
            elif order.amount_total <= 9999:
                order.required_financial_approval_level = "deputy_ceo"
            else:
                order.required_financial_approval_level = "ceo"

    @api.depends("state")
    def _compute_is_confirmed_purchase_order(self):
        for order in self:
            order.is_confirmed_purchase_order = order.state == "purchase"

    @api.depends("vendor_bill_ids.invoice_verification_status")
    def _compute_vendor_bill_metrics(self):
        for order in self:
            bills = order.vendor_bill_ids.filtered(
                lambda m: m.move_type == "in_invoice"
            )
            order.vendor_bill_count = len(bills)
            order.verified_vendor_bill_count = len(
                bills.filtered(lambda m: m.invoice_verification_status == "verified")
            )
            order.all_vendor_bills_verified = bool(bills) and all(
                bill.invoice_verification_status == "verified" for bill in bills
            )

    @api.depends("vendor_bill_ids.payment_state")
    def _compute_payment_status_summary(self):
        for order in self:
            bills = order.vendor_bill_ids.filtered(
                lambda m: m.move_type == "in_invoice"
            )

            if not bills:
                order.payment_status_summary = "no_bill"
                continue

            payment_states = set(bills.mapped("payment_state"))

            if payment_states == {"paid"}:
                order.payment_status_summary = "paid"
            elif "in_payment" in payment_states:
                order.payment_status_summary = "in_payment"
            elif "partial" in payment_states:
                order.payment_status_summary = "partial"
            else:
                order.payment_status_summary = "unpaid"

    @api.depends_context("uid")
    def _compute_role_edit_permissions(self):
        user = self.env.user

        is_procurement_officer = user.has_group(
            "purchase_execution_workflow.group_procurement_officer"
        )
        is_financial_approver = (
            user.has_group("purchase_execution_workflow.group_finance_director")
            or user.has_group("purchase_execution_workflow.group_deputy_ceo")
            or user.has_group("purchase_execution_workflow.group_ceo")
        )

        for order in self:
            order.can_edit_procurement_fields = is_procurement_officer
            order.can_edit_financial_rejection = is_financial_approver

    @api.depends(
        "state",
        "purchase_request_id",
        "is_recommended_vendor",
        "financial_approval_state",
        "vendor_ack_received",
        "picking_ids.end_user_confirmed",
        "vendor_bill_ids.invoice_verification_status",
        "vendor_bill_ids.payment_state",
        "procurement_closure_state",
    )
    def _compute_workflow_progress_status(self):
        for order in self:
            incoming_pickings = order.picking_ids.filtered(
                lambda p: p.picking_type_id.code == "incoming"
            )
            bills = order.vendor_bill_ids.filtered(
                lambda m: m.move_type == "in_invoice"
            )

            if order.procurement_closure_state == "closed":
                order.workflow_progress_status = "closed"
            elif bills and all(bill.payment_state == "paid" for bill in bills):
                order.workflow_progress_status = "paid"
            elif bills and all(
                bill.invoice_verification_status == "verified" for bill in bills
            ):
                order.workflow_progress_status = "invoice_verified"
            elif incoming_pickings and all(
                p.end_user_confirmed for p in incoming_pickings if p.state == "done"
            ):
                order.workflow_progress_status = "receipt_confirmed"
            elif order.vendor_ack_received:
                order.workflow_progress_status = "vendor_acknowledged"
            elif order.state == "purchase":
                order.workflow_progress_status = "po_issued"
            elif order.financial_approval_state == "approved":
                order.workflow_progress_status = "finance_approved"
            elif order.financial_approval_state == "to_approve":
                order.workflow_progress_status = "waiting_finance"
            elif order.is_recommended_vendor:
                order.workflow_progress_status = "recommended"
            elif order.purchase_request_id:
                order.workflow_progress_status = "under_evaluation"
            else:
                order.workflow_progress_status = "draft"

    @api.depends(
        "state",
        "vendor_ack_required",
        "vendor_ack_received",
        "picking_ids.state",
        "picking_ids.end_user_confirmed",
        "vendor_bill_ids.invoice_verification_status",
        "vendor_bill_ids.payment_state",
    )
    def _compute_ready_for_procurement_closure(self):
        for order in self:
            ready = True

            if order.state != "purchase":
                ready = False

            if order.vendor_ack_required and not order.vendor_ack_received:
                ready = False

            incoming_pickings = order.picking_ids.filtered(
                lambda p: p.picking_type_id.code == "incoming"
            )
            if not incoming_pickings:
                ready = False
            else:
                for picking in incoming_pickings:
                    if picking.state != "done":
                        ready = False
                        break
                    if picking.is_grn_required and not picking.end_user_confirmed:
                        ready = False
                        break

            bills = order.vendor_bill_ids.filtered(
                lambda m: m.move_type == "in_invoice"
            )
            if not bills:
                ready = False
            else:
                if not all(
                    bill.invoice_verification_status == "verified" for bill in bills
                ):
                    ready = False
                if not all(bill.payment_state == "paid" for bill in bills):
                    ready = False

            order.ready_for_procurement_closure = ready

    # -------------------------------------------------------------------------
    # ACCESS RIGHTS HELPERS
    # -------------------------------------------------------------------------

    def _check_procurement_officer_access(self):
        if not self.env.user.has_group(
            "purchase_execution_workflow.group_procurement_officer"
        ):
            raise AccessError("Only a Procurement Officer can perform this action.")

    def _check_financial_approver_access(self):
        for order in self:
            if order.required_financial_approval_level == "finance_director":
                if not self.env.user.has_group(
                    "purchase_execution_workflow.group_finance_director"
                ):
                    raise AccessError(
                        "Only the Director of Finance can approve or reject this quotation."
                    )
            elif order.required_financial_approval_level == "deputy_ceo":
                if not self.env.user.has_group(
                    "purchase_execution_workflow.group_deputy_ceo"
                ):
                    raise AccessError(
                        "Only the Deputy CEO can approve or reject this quotation."
                    )
            elif order.required_financial_approval_level == "ceo":
                if not self.env.user.has_group("purchase_execution_workflow.group_ceo"):
                    raise AccessError(
                        "Only the CEO can approve or reject this quotation."
                    )

    # -------------------------------------------------------------------------
    # VALIDATION HELPERS
    # -------------------------------------------------------------------------

    def _check_procurement_validations(self):
        for order in self:
            if (
                order.amount_total > 1000
                and
                order.purchase_request_id
                and order.purchase_request_id.state != "approved"
            ):
                raise ValidationError(
                    "The Purchase Request must be approved before confirming the Purchase Order."
                )

            if (
                order.amount_total > 1000
                and order.quotation_count_for_request < 3
                and not order.quotation_exception_reason
            ):
                raise ValidationError(
                    "At least 3 quotations are required for purchases above 1000 BD, or a justification must be entered."
                )

            if not order.is_recommended_vendor:
                raise ValidationError(
                    "You must mark this quotation as recommended before confirming the Purchase Order."
                )

    def _check_minimum_quotation_requirement(self):
        for order in self:
            if not order.purchase_request_id:
                raise ValidationError(
                    "Please link this quotation to a Purchase Request before confirming it."
                )

            if (
                order.is_above_quotation_threshold
                and order.quotation_count_for_request < 3
                and not order.quotation_exception_reason
            ):
                raise ValidationError(
                    "At least 3 quotations are required for purchase requests above BD 1000, or a justification must be entered."
                )

    def _check_evaluation_completion(self):
        for order in self:
            if order.technical_evaluation == "pending":
                raise ValidationError(
                    "Please complete the technical evaluation before confirming this quotation."
                )

            if order.commercial_evaluation == "pending":
                raise ValidationError(
                    "Please complete the commercial evaluation before confirming this quotation."
                )

    def _check_recommended_vendor_selected(self):
        for order in self:
            if not order.is_recommended_vendor:
                raise ValidationError(
                    "Only the recommended quotation can be confirmed as a Purchase Order."
                )

    def _check_financial_approval_completed(self):
        for order in self:
            if order.financial_approval_state != "approved":
                raise ValidationError(
                    "Financial approval must be completed before confirming this Purchase Order."
                )

    def _check_vendor_acknowledgment_if_required(self):
        for order in self:
            if order.vendor_ack_required and not order.vendor_ack_received:
                raise ValidationError(
                    "Vendor acknowledgment is required before continuing this purchase process."
                )

    def _check_ready_for_procurement_closure(self):
        for order in self:
            if not order.ready_for_procurement_closure:
                raise ValidationError(
                    "This procurement cycle cannot be closed yet. Please complete vendor acknowledgment, receipt confirmation, invoice verification, and payment first."
                )

    def _check_vendor_matches_purchase_request_products(self):
        for order in self:
            if not order.purchase_request_id or not order.partner_id:
                continue

            valid_vendors = order._get_common_vendors_for_pr_products(order.purchase_request_id)
            if order.partner_id not in valid_vendors:
                raise ValidationError(
                    "The selected vendor does not supply all products in the linked Purchase Request."
                )

    # -------------------------------------------------------------------------
    # BUDGET RESERVATION HELPERS
    # -------------------------------------------------------------------------

    def _check_and_create_budget_reservation(self):
        for order in self:
            if not order.purchase_request_id:
                raise ValidationError(
                    "Please link this quotation to a Purchase Request before budget checking."
                )

            if not order.purchase_request_id.department_id:
                raise ValidationError(
                    "The linked Purchase Request does not have a department."
                )

            if order.budget_reservation_id and order.budget_reservation_id.state in ["reserved", "used"]:
                continue

            department = order.purchase_request_id.department_id

            department_budgets = self.env["budget.department"].sudo().search([
                ("department_id", "=", department.id),
                ("state", "=", "approved"),
                ("general_budget_id.state", "=", "active"),
                ("remaining_balance", ">", 0),
            ], order="approval_date asc, id asc")

            total_available = sum(department_budgets.mapped("remaining_balance"))

            if order.amount_total > total_available:
                raise ValidationError(
                    "Insufficient department budget. The RFQ total amount is greater than the available approved budget balance for this department."
                )

            reservation = self.env["budget.reservation"].sudo().create({
                "department_id": department.id,
                "amount": order.amount_total,
                "description": f"Automatic reservation for RFQ/PO {order.name}",
                "request_ref": order.purchase_request_id.name or order.name,
            })

            reservation.sudo().write({
                "state": "reserved",
                "submitted_by": self.env.user.id,
                "submitted_date": fields.Datetime.now(),
                "reserved_by": self.env.user.id,
                "reserved_date": fields.Datetime.now(),
            })

            reservation.sudo()._allocate_reservation_lines()

            order.budget_reservation_id = reservation.id

    def _mark_budget_reservation_used(self):
        for order in self:
            if order.budget_reservation_id and order.budget_reservation_id.state == "reserved":
                order.budget_reservation_id.sudo().action_mark_used()

    def _cancel_budget_reservation(self):
        for order in self:
            if order.budget_reservation_id and order.budget_reservation_id.state == "reserved":
                order.budget_reservation_id.sudo().write({
                    "state": "cancelled",
                    "cancelled_by": self.env.user.id,
                    "cancelled_date": fields.Datetime.now(),
                    "cancel_reason": "Cancelled automatically because the RFQ was financially rejected.",
                })

    # -------------------------------------------------------------------------
    # SAFE FIELD WRITE PROTECTION
    # -------------------------------------------------------------------------

    def write(self, vals):
        procurement_editable_fields = {
            "technical_evaluation",
            "commercial_evaluation",
            "recommendation_reason",
            "evaluation_notes",
            "vendor_ack_required",
            "vendor_ack_notes",
            "quotation_exception_reason",
        }
        finance_editable_fields = {
            "financial_rejection_reason",
        }

        protected_fields = procurement_editable_fields | finance_editable_fields
        touched_protected_fields = set(vals.keys()) & protected_fields

        if touched_protected_fields and not self.env.is_superuser():
            allowed_fields = set()

            if self.env.user.has_group(
                "purchase_execution_workflow.group_procurement_officer"
            ):
                allowed_fields |= procurement_editable_fields

                if vals.get("financial_rejection_reason") is False:
                    allowed_fields.add("financial_rejection_reason")

            if (
                self.env.user.has_group("purchase_execution_workflow.group_finance_director")
                or self.env.user.has_group("purchase_execution_workflow.group_deputy_ceo")
                or self.env.user.has_group("purchase_execution_workflow.group_ceo")
            ):
                allowed_fields |= finance_editable_fields

            forbidden_fields = touched_protected_fields - allowed_fields
            if forbidden_fields:
                raise AccessError(
                    "You are not allowed to edit these fields: %s"
                    % ", ".join(sorted(forbidden_fields))
                )

        return super().write(vals)

    # -------------------------------------------------------------------------
    # NOTIFICATION HELPERS
    # -------------------------------------------------------------------------

    def _create_financial_approval_activity(self):
        activity_type = self.env.ref("mail.mail_activity_data_todo")

        for order in self:
            if order.required_financial_approval_level == "finance_director":
                group_xmlid = "purchase_execution_workflow.group_finance_director"
                approval_label = "Director of Finance"
            elif order.required_financial_approval_level == "deputy_ceo":
                group_xmlid = "purchase_execution_workflow.group_deputy_ceo"
                approval_label = "Deputy CEO"
            elif order.required_financial_approval_level == "ceo":
                group_xmlid = "purchase_execution_workflow.group_ceo"
                approval_label = "CEO"
            else:
                continue

            group = self.env.ref(group_xmlid, raise_if_not_found=False)
            if not group:
                continue

            users = self.env["res.users"].search([("groups_id", "in", [group.id])])

            for user in users:
                existing_activity = self.env["mail.activity"].search(
                    [
                        ("res_model", "=", "purchase.order"),
                        ("res_id", "=", order.id),
                        ("user_id", "=", user.id),
                        ("activity_type_id", "=", activity_type.id),
                        ("summary", "=", "Financial Approval Required"),
                    ],
                    limit=1,
                )

                if existing_activity:
                    continue

                self.env["mail.activity"].create(
                    {
                        "activity_type_id": activity_type.id,
                        "res_model_id": self.env["ir.model"]._get_id("purchase.order"),
                        "res_id": order.id,
                        "user_id": user.id,
                        "summary": "Financial Approval Required",
                        "note": (
                            f"Financial approval is required for RFQ/PO {order.name}. "
                            f"Please open Purchase > Orders, review this record, and approve or reject it "
                            f"as the {approval_label}."
                        ),
                        "date_deadline": fields.Date.today(),
                    }
                )

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def action_mark_as_recommended(self):
        self._check_procurement_officer_access()

        for order in self:
            if not order.purchase_request_id:
                raise ValidationError(
                    "Please link this quotation to a Purchase Request before marking it as recommended."
                )

            if order.technical_evaluation != "accepted":
                raise ValidationError(
                    "Technical evaluation must be accepted before recommending this quotation."
                )

            if order.commercial_evaluation != "accepted":
                raise ValidationError(
                    "Commercial evaluation must be accepted before recommending this quotation."
                )

            other_orders = self.search(
                [
                    ("purchase_request_id", "=", order.purchase_request_id.id),
                    ("id", "!=", order.id),
                ]
            )
            other_orders.write({"is_recommended_vendor": False})

            order.is_recommended_vendor = True

    def action_submit_financial_approval(self):
        self._check_procurement_officer_access()

        for order in self:
            order._check_minimum_quotation_requirement()
            order._check_evaluation_completion()
            order._check_recommended_vendor_selected()
            order._check_vendor_matches_purchase_request_products()
            order._check_and_create_budget_reservation()

            order.financial_approval_state = "to_approve"
            order.financial_rejection_reason = False
            order._create_financial_approval_activity()

    def action_financial_approve(self):
        self._check_financial_approver_access()

        for order in self:
            if order.financial_approval_state != "to_approve":
                raise ValidationError(
                    "Only quotations waiting for financial approval can be approved."
                )

            order.financial_approval_state = "approved"
            order.financial_approved_by = self.env.user
            order.financial_approved_date = fields.Datetime.now()
            order.financial_rejection_reason = False
            order._mark_budget_reservation_used()

    def action_open_financial_reject_wizard(self):
        self._check_financial_approver_access()
        self.ensure_one()

        if self.financial_approval_state != "to_approve":
            raise ValidationError(
                "Only quotations waiting for financial approval can be rejected."
            )

        return {
            "name": "Reject Financial Approval",
            "type": "ir.actions.act_window",
            "res_model": "financial.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_purchase_order_id": self.id,
            },
        }

    def action_financial_reject(self):
        self._check_financial_approver_access()

        for order in self:
            if order.financial_approval_state != "to_approve":
                raise ValidationError(
                    "Only quotations waiting for financial approval can be rejected."
                )

            if not order.financial_rejection_reason:
                raise ValidationError(
                    "Please enter the financial rejection reason before rejecting this quotation."
                )

            order.financial_approval_state = "rejected"
            order.financial_approved_by = False
            order.financial_approved_date = False
            order._cancel_budget_reservation()

    def action_mark_vendor_acknowledged(self):
        self._check_procurement_officer_access()

        for order in self:
            if order.state != "purchase":
                raise ValidationError(
                    "Vendor acknowledgment can only be recorded after the quotation is confirmed as a Purchase Order."
                )

            if order.vendor_ack_received:
                raise ValidationError(
                    "Vendor acknowledgment has already been recorded for this Purchase Order."
                )

            order.vendor_ack_received = True
            order.vendor_ack_recorded_by = self.env.user
            order.vendor_ack_date = fields.Datetime.now()

    def action_mark_procurement_closed(self):
        self._check_procurement_officer_access()

        for order in self:
            order._check_ready_for_procurement_closure()
            order.procurement_closure_state = "closed"
            order.procurement_closed_by = self.env.user
            order.procurement_closed_date = fields.Datetime.now()

    def button_confirm(self):
        self._check_procurement_validations()
        self._check_minimum_quotation_requirement()
        self._check_evaluation_completion()
        self._check_recommended_vendor_selected()
        self._check_vendor_matches_purchase_request_products()
        self._check_financial_approval_completed()
        return super().button_confirm()