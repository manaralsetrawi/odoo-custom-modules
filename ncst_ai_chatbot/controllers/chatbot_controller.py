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
            # Help command
            if message_lower in ["help", "commands", "what can you do"]:
                return {"success": True, "reply": self._get_help_message()}

            # Live Odoo data commands
            live_reply = self._handle_live_odoo_question(message_lower)
            if live_reply:
                return {"success": True, "reply": live_reply}

            # Normal AI flow questions
            return self._ask_openai(message)

        except Exception as e:
            _logger.exception("Chatbot main error: %s", e)
            return {
                "success": False,
                "reply": "Sorry, I could not complete this request. Please try another question.",
            }

    # ---------------------------------------------------------
    # HELP MESSAGE
    # ---------------------------------------------------------

    def _get_help_message(self):
        return """You can ask me:

- Explain procurement workflow
- Explain finance invoice review flow
- Explain CRM project request flow
- Show pending CRM project requests
- Show finance invoices waiting for review
- Show procurement approvals

For best results, ask short questions."""

    # ---------------------------------------------------------
    # LIVE ODOO DATA COMMANDS
    # ---------------------------------------------------------

    def _handle_live_odoo_question(self, message_lower):

        if ("crm" in message_lower or "project request" in message_lower) and (
            "pending" in message_lower or "show" in message_lower or "waiting" in message_lower
        ):
            return self._safe_get_pending_crm_requests()

        if ("finance" in message_lower or "invoice" in message_lower or "invoices" in message_lower) and (
            "review" in message_lower or "pending" in message_lower or "waiting" in message_lower
        ):
            return self._safe_get_finance_invoices_waiting_review()

        if ("procurement" in message_lower or "purchase" in message_lower or "approval" in message_lower) and (
            "approval" in message_lower or "pending" in message_lower or "waiting" in message_lower
        ):
            return self._safe_get_procurement_pending_approvals()

        return False

    def _safe_get_pending_crm_requests(self):
        try:
            return self._get_pending_crm_requests()
        except Exception as e:
            _logger.exception("CRM chatbot error: %s", e)
            return "I could not load CRM project requests. Please check the CRM module fields."

    def _safe_get_finance_invoices_waiting_review(self):
        try:
            return self._get_finance_invoices_waiting_review()
        except Exception as e:
            _logger.exception("Finance chatbot error: %s", e)
            return "I could not load finance invoices. Please check the finance review fields."

    def _safe_get_procurement_pending_approvals(self):
        try:
            return self._get_procurement_pending_approvals()
        except Exception as e:
            _logger.exception("Procurement chatbot error: %s", e)
            return "I could not load procurement approvals. Please check the procurement module fields."

    def _get_pending_crm_requests(self):
        Lead = request.env["crm.lead"]

        domain = [
            ("request_type", "=", "project_request"),
            ("intake_state", "in", ["submitted", "under_review"]),
        ]

        leads = Lead.search(domain, limit=10, order="create_date desc")

        if not leads:
            return "No pending CRM project requests found."

        lines = ["Pending CRM project requests:"]

        for lead in leads:
            client = lead.partner_id.name or lead.contact_name or "No client"
            state = dict(lead._fields["intake_state"].selection).get(
                lead.intake_state, lead.intake_state
            )

            lines.append(
                f"- {lead.name} | Client: {client} | Status: {state}"
            )

        return "\n".join(lines)

    def _get_finance_invoices_waiting_review(self):
        Move = request.env["account.move"]

        domain = [
            ("move_type", "in", ["out_invoice", "in_invoice"]),
            ("finance_review_state", "in", ["draft", "submitted"]),
            ("state", "=", "draft"),
        ]

        invoices = Move.search(domain, limit=10, order="invoice_date desc, create_date desc")

        if not invoices:
            return "No finance invoices waiting for review found."

        lines = ["Finance invoices waiting for review:"]

        for inv in invoices:
            partner = inv.partner_id.name or "No partner"
            amount = inv.amount_total
            state = dict(inv._fields["finance_review_state"].selection).get(
                inv.finance_review_state, inv.finance_review_state
            )

            lines.append(
                f"- {inv.name or 'Draft Invoice'} | Partner: {partner} | Amount: {amount:.3f} | Review: {state}"
            )

        return "\n".join(lines)

    def _get_procurement_pending_approvals(self):
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
            level = po.required_financial_approval_level or "Not specified"

            lines.append(
                f"- {po.name} | Vendor: {vendor} | Amount: {amount:.3f} | Required approval: {level}"
            )

        return "\n".join(lines)

    # ---------------------------------------------------------
    # OPENAI CHAT
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
                "max_tokens": 220,
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

Answer only based on the custom NCST Odoo system described below.
Keep answers very short, clear, and professional.
Use plain text only.
Do not use markdown formatting like stars, bold, headings, or backticks.
Use 3 to 5 short bullet points maximum.
Keep answers under 100 words unless the user asks for more details.

PROCUREMENT:
Flow: Purchase Request, RFQs, quotation evaluation, recommended vendor, financial approval if required, purchase order, vendor acknowledgment, goods receipt, end-user confirmation, vendor bill verification, payment, closure.
Rules: Above BD 1000 requires at least 3 quotations. Up to BD 5000 requires Director of Finance. Up to BD 9999 requires Deputy CEO. Above BD 9999 requires CEO. Closure requires acknowledgment, receipt confirmation, invoice verification, and payment.

FINANCE:
Flow: Draft Invoice, Submit for Review, Finance Review, Approved or Rejected, Posting after approval.
Rules: Invoice cannot be posted unless finance review is approved. Reviewer can approve, reject, or return to draft. Rejection reason should be recorded.

CRM:
Purpose: Manages client project requests from website/contact form until opportunity and project resource assignment.

Website flow:
Contact Us form -> Message Type selected.
General Inquiry stays as normal inquiry.
Project Request shows extra project fields and creates CRM lead.

Project request intake flow:
New Inquiry -> Submitted -> Under Review -> Approved or Rejected -> Team Assignment Wizard -> Converted to Opportunity -> Initial Discussion.

Main CRM pipeline stages:
New Inquiry, Initial Discussion, Requirement Analysis, Solution Design, Proposal Submission, Negotiation, Won/Lost.

Project Resource Management:
Project Teams store team name, project types, active status, and team employees.
Project Assignments connect opportunities/projects with selected teams and assigned employees.
Team suggestion is based on project type and availability/capacity.

Important CRM rules:
Only project request leads go through review.
Start Review moves the request to Under Review.
Approval opens team assignment wizard.
After team assignment, the request becomes an opportunity.
Rejected requests should include a rejection reason.

If asked about live records, tell the user to type:
help
"""