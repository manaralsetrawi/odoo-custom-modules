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

        # 1) First check if the user is asking for live Odoo data
        live_reply = self._handle_live_odoo_question(message_lower)
        if live_reply:
            return {"success": True, "reply": live_reply}

        # 2) Otherwise send normal flow/system question to OpenAI
        return self._ask_openai(message)

    # ---------------------------------------------------------
    # LIVE ODOO DATA COMMANDS
    # ---------------------------------------------------------

    def _handle_live_odoo_question(self, message_lower):
        """
        Detects simple user questions and returns real records from Odoo.
        This saves tokens because simple record lists do not need OpenAI.
        """

        if ("crm" in message_lower or "project request" in message_lower) and (
            "pending" in message_lower or "show" in message_lower or "waiting" in message_lower
        ):
            return self._get_pending_crm_requests()

        if ("finance" in message_lower or "invoice" in message_lower or "invoices" in message_lower) and (
            "review" in message_lower or "pending" in message_lower or "waiting" in message_lower
        ):
            return self._get_finance_invoices_waiting_review()

        if ("procurement" in message_lower or "purchase" in message_lower or "approval" in message_lower) and (
            "approval" in message_lower or "pending" in message_lower or "waiting" in message_lower
        ):
            return self._get_procurement_pending_approvals()

        return False

    def _get_pending_crm_requests(self):
        """
        Shows CRM project requests that are not finished yet.
        Adjust field names if your module uses different names.
        """

        Lead = request.env["crm.lead"].sudo()

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
            state = dict(lead._fields["intake_state"].selection).get(lead.intake_state, lead.intake_state)

            lines.append(
                f"- {lead.name} | Client: {client} | Status: {state}"
            )

        return "\n".join(lines)

    def _get_finance_invoices_waiting_review(self):
        """
        Shows invoices waiting for finance approval.
        Uses finance_review_state from your custom finance_review_workflow module.
        """

        Move = request.env["account.move"].sudo()

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
        """
        Shows purchase orders waiting for financial approval.
        Uses financial_approval_state from purchase_execution_workflow.
        """

        PurchaseOrder = request.env["purchase.order"].sudo()

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
    # OPENAI NORMAL CHAT
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

        try:
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
                    "max_tokens": 180,
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

        except Exception as e:
            _logger.exception("Chatbot error: %s", e)
            return {
                "success": False,
                "reply": "An unexpected error happened while contacting the chatbot.",
            }

    def _get_ncst_system_prompt(self):
        return """
You are NCST AI Assistant inside the NCST Odoo ERP system.

Answer only based on the custom NCST Odoo system described below.
Keep answers short, clear, and professional.
Use plain text only.
Do NOT use markdown formatting like bold, stars, headings, or backticks.
Use 3 to 6 short bullet points maximum.
Keep answers under 120 words unless the user asks for details.

PROCUREMENT:
Flow: Purchase Request, RFQs, quotation evaluation, recommended vendor, financial approval if required, purchase order, vendor acknowledgment, goods receipt, end-user confirmation, vendor bill verification, payment, closure.
Rules: Above BD 1000 requires at least 3 quotations. Up to BD 5000 requires Director of Finance. Up to BD 9999 requires Deputy CEO. Above BD 9999 requires CEO. Closure requires acknowledgment, receipt confirmation, invoice verification, and payment.

FINANCE:
Flow: Draft Invoice, Submit for Review, Finance Review, Approved or Rejected, Posting after approval.
Rules: Invoice cannot be posted unless finance review is approved. Reviewer can approve, reject, or return to draft. Rejection reason should be recorded.

CRM:
Flow: Website Contact Form, Project Request, CRM Lead, Submitted, Under Review, Approved or Rejected, Team Assignment Wizard, Opportunity, Initial Discussion.
Rules: Only project requests go through review. Approval opens team assignment. Suggested team is based on project type and availability.

If asked about live records, tell the user they can ask:
show pending CRM project requests
show finance invoices waiting for review
show procurement approvals
"""