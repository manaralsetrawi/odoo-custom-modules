import logging
import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class NCSTAIChatbotController(http.Controller):

    @http.route("/ncst_ai_chatbot/message", type="json", auth="user")
    def send_message(self, message=None):
        """
        Receives user message from the chatbot popup,
        sends it to OpenAI, and returns the AI response.
        """

        if not message:
            return {"success": False, "reply": "Please write a message first."}

        config = request.env["ir.config_parameter"].sudo()

        api_key = config.get_param("openai_api_key")
        model = config.get_param("openai_model") or "gpt-3.5-turbo"

        if not api_key:
            return {
                "success": False,
                "reply": "OpenAI API key is not configured in Odoo system parameters.",
            }

        system_prompt = """
        You are an AI assistant inside the NCST Odoo ERP system.
        Help users with short, clear answers related to Procurement, Finance, CRM, and general Odoo usage.
        If the user asks for real-time system records, explain that the feature needs backend data integration.
        Keep answers professional and concise.
        """

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
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 300,
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