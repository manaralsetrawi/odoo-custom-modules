{
    "name": "NCST AI Chatbot",
    "version": "1.0",
    "summary": "Floating OpenAI chatbot for Odoo backend",
    "category": "Productivity",
    "author": "Manar Alsetrawi - NCST",
    "depends": ["web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "ncst_ai_chatbot/static/src/js/chatbot.js",
            "ncst_ai_chatbot/static/src/scss/chatbot.scss",
        ],
    },
    "installable": True,
    "application": False,
}