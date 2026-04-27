import logging
import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class NCSTAIChatbotController(http.Controller):

    @http.route("/ncst_ai_chatbot/message", type="json", auth="user")
    def send_message(self, message=None):
        if not message:
            return {"success": False, "reply": "Please write a message first."}

        message_lower = message.lower().strip()

        try:
            if message_lower in ["help", "commands", "what can you do"]:
                return {"success": True, "reply": self._get_help_message()}

            live_reply = self._handle_live_odoo_question(message_lower)
            if live_reply:
                return {"success": True, "reply": live_reply}

            return self._ask_openai(message)

        except Exception as e:
            _logger.exception("Chatbot error: %s", e)
            return {
                "success": False,
                "reply": "Sorry, I could not complete this request. Please try another question.",
            }

    # ---------------------------------------------------------
    # HELP
    # ---------------------------------------------------------

    def _get_help_message(self):
        return """You can ask me:

- Explain CRM workflow
- Explain CRM stages
- Explain project request approval
- Explain project team assignment
- Explain procurement workflow
- Explain purchase request workflow
- Explain financial approval in procurement
- Explain GRN confirmation
- Explain vendor bill verification
- Explain finance invoice review
- Explain budget reservation
- Explain expense workflow
- Show pending CRM project requests
- Show finance invoices waiting for review
- Show procurement approvals"""

    # ---------------------------------------------------------
    # LIVE ODOO DATA
    # ---------------------------------------------------------

    def _handle_live_odoo_question(self, message_lower):
        if ("crm" in message_lower or "project request" in message_lower) and (
            "pending" in message_lower or "show" in message_lower or "waiting" in message_lower
        ):
            return self._safe_get_pending_crm_requests()

        if (
            ("finance" in message_lower or "invoice" in message_lower or "invoices" in message_lower)
            and ("show" in message_lower or "list" in message_lower or "pending" in message_lower or "waiting" in message_lower)
        ):
            return self._safe_get_finance_invoices_waiting_review()

        if (
            ("procurement" in message_lower or "purchase" in message_lower)
            and ("approval" in message_lower or "pending" in message_lower or "waiting" in message_lower or "show" in message_lower)
        ):
            return self._safe_get_procurement_pending_approvals()

        return False

    def _safe_get_pending_crm_requests(self):
        try:
            Lead = request.env["crm.lead"]

            domain = [
                ("request_type", "=", "project_request"),
                ("type", "=", "lead"),
                ("intake_state", "in", ["submitted", "under_review"]),
            ]

            leads = Lead.search(domain, limit=10, order="create_date desc")

            if not leads:
                return "No pending CRM project requests found."

            lines = ["Pending CRM project requests:"]

            for lead in leads:
                client = lead.contact_name or lead.intake_client_name or lead.partner_id.name or "No client"
                state = dict(lead._fields["intake_state"].selection).get(
                    lead.intake_state, lead.intake_state
                )
                lines.append(f"- {lead.name} | Client: {client} | Status: {state}")

            return "\n".join(lines)

        except Exception as e:
            _logger.exception("CRM live data error: %s", e)
            return "I could not load CRM project requests. Please check the CRM fields."

    def _safe_get_finance_invoices_waiting_review(self):
        try:
            Move = request.env["account.move"]

            domain = [
                ("move_type", "=", "out_invoice"),
                ("finance_review_state", "in", ["draft", "submitted"]),
                ("state", "=", "draft"),
            ]

            invoices = Move.search(domain, limit=10, order="invoice_date desc, create_date desc")

            if not invoices:
                return "No finance invoices waiting for review found."

            lines = ["Finance invoices waiting for review:"]

            for inv in invoices:
                partner = inv.partner_id.name or "No customer"
                amount = inv.amount_total
                state = dict(inv._fields["finance_review_state"].selection).get(
                    inv.finance_review_state, inv.finance_review_state
                )
                lines.append(
                    f"- {inv.name or 'Draft Invoice'} | Customer: {partner} | Amount: {amount:.3f} | Review: {state}"
                )

            return "\n".join(lines)

        except Exception as e:
            _logger.exception("Finance live data error: %s", e)
            return "I could not load finance invoices. Please check the finance review fields."

    def _safe_get_procurement_pending_approvals(self):
        try:
            PurchaseOrder = request.env["purchase.order"]

            domain = [
                ("financial_approval_state", "=", "to_approve"),
            ]

            orders = PurchaseOrder.search(domain, limit=10, order="create_date desc")

            if not orders:
                return "No procurement approvals are currently pending."

            lines = ["Pending procurement approvals:"]

            for po in orders:
                vendor = po.partner_id.name or "No vendor"
                amount = po.amount_total
                level = dict(po._fields["required_financial_approval_level"].selection).get(
                    po.required_financial_approval_level,
                    po.required_financial_approval_level or "Not specified"
                )
                lines.append(
                    f"- {po.name} | Vendor: {vendor} | Amount: {amount:.3f} | Required approval: {level}"
                )

            return "\n".join(lines)

        except Exception as e:
            _logger.exception("Procurement live data error: %s", e)
            return "I could not load procurement approvals. Please check the procurement fields."

    # ---------------------------------------------------------
    # OPENAI
    # ---------------------------------------------------------

    def _ask_openai(self, message):
        config = request.env["ir.config_parameter"].sudo()
        api_key = config.get_param("openai_api_key")
        model = config.get_param("openai_model") or "gpt-3.5-turbo"

        if not api_key:
            return {
                "success": False,
                "reply": "OpenAI API key is not configured in Odoo system parameters.",
            }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": self._get_ncst_system_prompt()},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.2,
                "max_tokens": 230,
            },
            timeout=30,
        )

        if response.status_code != 200:
            _logger.error("OpenAI API Error: %s", response.text)
            return {
                "success": False,
                "reply": "Sorry, the chatbot could not connect to OpenAI right now.",
            }

        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        return {
            "success": True,
            "reply": reply,
        }

    def _get_ncst_system_prompt(self):
        return """
You are NCST AI Assistant inside the NCST Odoo ERP system.

Answer only based on the custom NCST Odoo system described here.
Keep answers short, clear, and professional.
Use plain text only.
Do not use markdown symbols, stars, bold, headings, or backticks.
Use 3 to 6 short bullet points maximum.
Keep answers under 120 words unless the user asks for more detail.

CRM MODULE:
Purpose:
Manages project requests from website/contact form, review, approval, team assignment, opportunity creation, and project pipeline tracking.

CRM request types:
- General Inquiry: normal inquiry.
- Project Request: uses extra project fields and custom review workflow.

Website project request flow:
- Client submits Contact Us form.
- If Message Type is Project Request, Odoo creates a CRM lead.
- The lead stores client name, email, phone, company, project title, description, budget, duration, and notes.
- New project requests start with intake_state Submitted.

CRM intake states:
- Draft
- Submitted
- Under Review
- Approved
- Rejected

CRM pipeline stages:
- New Inquiry
- Initial Discussion
- Requirement Analysis
- Solution Design
- Proposal Submitted
- Waiting Approval
- Approved
- Rejected

CRM workflow:
- New project request is submitted.
- Project manager starts review.
- Status becomes Under Review.
- Reviewer completes project type, client segment, features, meeting notes, requirements, solution summary, recommendation, and risk notes.
- Approval opens the team assignment wizard.
- After team assignment, the request is approved and connected to assigned team/employees.
- Rejected requests require rejection reason.

CRM technical/proposal flow:
- Start Analysis moves lead to Requirement Analysis.
- Submit Proposal validates feasibility, complexity, duration, deadline, summary, and amount.
- Proposal Submitted then Waiting Approval.
- Approved records store approved by/date.
- Rejected records store rejected by/date and reason.

CRM project resources:
- Project teams contain team name, active status, project types, employees, and notes.
- Team employees are HR employees from AI Research and Development.
- Project assignments connect a lead/opportunity to a selected team and assigned employees.

CRM email/proposal features:
- Proposal PDF can be uploaded and summarized using OpenAI.
- Summary is saved in Proposal Summary.
- Approval/rejection emails can be sent to the client.
- Manual chatter messages can be logged as email logs.

FINANCE REVIEW MODULE:
Purpose:
Controls customer invoice review before posting and checks invoice exceptions.

Finance review states:
- Draft
- Submitted
- Approved
- Rejected

Finance invoice workflow:
- Draft customer invoice is created.
- Finance Invoice User submits it for review.
- Exception checks run before submission.
- Finance Invoice Reviewer approves, rejects, or returns it to draft.
- Invoice cannot be posted unless review state is Approved.

Finance exception checks:
- Customer invoice must have invoice date.
- Customer invoice must have either payment terms or due date.
- Customer invoice lines must include tax.
- Invoice date cannot be later than due date.
- Vendor bills check bill date, due date, vendor reference, tax, duplicate vendor reference, and invalid date sequence.

Finance roles:
- Finance Invoice User can submit invoices for review.
- Finance Invoice Reviewer can approve, reject, and reset to draft.

Finance reports:
- Finance Review Summary Report can be generated for reviewed invoices.

BUDGET MODULE:
Purpose:
Controls department budgets and budget reservations.

Budget reservation states:
- Draft
- Submitted
- Reserved
- Used
- Cancelled

Budget reservation workflow:
- User creates reservation with department, amount, description, and reference.
- If creator is Finance Manager, submission reserves budget directly.
- If normal user submits, it becomes Submitted and waits for Finance Manager approval.
- Finance Manager approves and reserves the amount.
- Reservation can later be marked Used or Cancelled.

Budget rules:
- Reservation amount must be greater than zero.
- Reservation cannot exceed available approved department budget.
- Reservation allocates amount across approved active department budgets.
- Only Finance Manager can approve reservations or reset them to draft.
- Creator or Finance Manager can mark reserved budget as used or cancel it.

EXPENSE MODULE:
Purpose:
Manages employee expense requests and reimbursement workflow.

Expense workflow:
- Draft
- Submitted
- Approved by Manager
- Approved by Finance
- Paid
- Rejected

Expense rules:
- Employee must attach receipt/invoice before submitting.
- Only employee manager can approve or reject submitted expense.
- Rejection requires reason.
- Only Finance can approve after manager approval.
- Finance approval creates a budget reservation automatically.
- Mark Paid changes the expense to Paid and marks related reserved budget as Used.

PROCUREMENT MODULE:
Purpose:
Controls purchase requests, RFQs, quotation evaluation, financial approval, vendor acknowledgment, goods receipt confirmation, vendor bill verification, payment tracking, and closure.

Purchase Request flow:
- Draft
- Waiting Coordinator Approval for teacher requests
- Waiting Academic Principal Approval for teacher requests
- Waiting Department Director Approval for admin requests
- Approved
- Rejected

Purchase Request rules:
- Only Teacher or Administrative Staff can create purchase requests.
- Requester is automatically assigned from logged-in employee.
- Requester category is automatic.
- Teacher requests go to Coordinator then Academic Principal.
- Admin requests go to Department Director.
- Request details cannot be edited after submission.
- Only draft purchase requests can be deleted.

Procurement RFQ/PO flow:
- Approved Purchase Request is linked to RFQs.
- RFQ lines are filled from purchase request lines.
- Vendor selection is limited to vendors that supply all requested products.
- Vendor prices are applied from product vendor price list.
- Technical and commercial evaluations must be accepted.
- One quotation is marked as recommended.
- Financial approval is submitted.
- After approval, RFQ can be confirmed into Purchase Order.
- Vendor acknowledgment is recorded.
- Receipt is completed.
- End user confirms receipt and compliance.
- Vendor bill is verified.
- Payment is tracked.
- Procurement is closed.

Quotation rules:
- Above BD 1000 requires at least 3 quotations.
- If fewer than 3 quotations exist, quotation exception justification is required.
- Only the recommended quotation can be confirmed.
- Technical and commercial evaluation cannot stay pending.

Financial approval rules in procurement:
- Up to BD 5000 requires Director of Finance.
- Up to BD 9999 requires Deputy CEO.
- Above BD 9999 requires CEO.
- Financial approver can approve or reject.
- Rejection requires financial rejection reason.
- Budget reservation is created before financial approval.
- If approved, budget reservation is marked used.
- If rejected, budget reservation is cancelled.

Procurement roles:
- Procurement Officer handles evaluation, recommendation, financial approval submission, vendor acknowledgment, and closure.
- Director of Finance approves lower value requests.
- Deputy CEO approves medium value requests.
- CEO approves high value requests.
- End User Receiver confirms goods receipt compliance.
- Invoice Verifier verifies or rejects vendor bills.

GRN and receipt confirmation:
- Stock receipt has GRN Required.
- Receipt must be Done before end-user confirmation.
- Compliance status must be Compliant or Non-Compliant, not Pending.
- Only End User Receiver can confirm receipt.
- Confirmation stores confirmed by and confirmed date.

Vendor bill verification:
- Vendor bill links to purchase order.
- Vendor bill must match PO vendor.
- Only Invoice Verifier can verify or reject vendor bills.
- Verified bills store verified by/date.
- Rejected bills require rejection reason.

Procurement closure:
- PO must be confirmed.
- Vendor acknowledgment must be received if required.
- Incoming receipts must be Done.
- GRN-required receipts must be confirmed by end user.
- Vendor bills must exist and be verified.
- Vendor bills must be paid.
- Only then procurement can be closed.

HR MODULE:
Purpose:
Supports employee leave management using automatic leave allocation and sequential leave approval.

Automatic leave allocation:
- When a new employee is created, the system automatically creates leave allocations.
- Sick Leave uses the Monthly Sick Leave accrual plan.
- Annual Leave uses the Annual Leave Plan accrual plan.
- Existing accrual allocations are checked first to avoid duplicates.
- Created allocations are automatically approved.

Leave approval flow:
- Employee submits a leave request.
- The assigned supervisor reviews first.
- Supervisor can approve or reject.
- If supervisor approves, the request goes to HR.
- HR gives the final approval or rejection.
- HR approval finalizes the leave using Odoo validation.
- Rejection uses Odoo refusal logic to roll back leave allocation effects.

Leave approval states:
- Supervisor: Pending, Supervisor Approved, Supervisor Rejected.
- HR: Pending, HR Approved, HR Rejected.

HR rules:
- Only the assigned supervisor can perform supervisor approval or rejection.
- HR approval cannot happen before supervisor approval.
- Only HR users can approve or reject at HR stage.
- Only HR Manager can reset the approval workflow.
- Reset returns the request to pending supervisor and HR approval.

Notifications:
- When supervisor approves, HR is notified.
- When HR approves, employee and supervisor are notified.
- When supervisor or HR rejects, the employee is notified.
- Rejection reason can be recorded.

Live data commands available:
- help
- show pending CRM project requests
- show finance invoices waiting for review
- show procurement approvals
- Explain HR leave approval flow
- Explain automatic leave allocation
- Who can approve leave requests?
- What happens when HR rejects leave?
"""