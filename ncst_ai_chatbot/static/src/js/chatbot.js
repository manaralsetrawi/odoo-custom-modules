/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

function createChatbot() {
    if (document.querySelector(".ncst-ai-chatbot-widget")) {
        return;
    }

    const chatbotHTML = `
        <div class="ncst-ai-chatbot-widget">
            <button class="ncst-ai-chatbot-button" title="NCST AI Assistant">
                🎧
            </button>

            <div class="ncst-ai-chatbot-window">
                <div class="ncst-ai-chatbot-header">
                    <div>
                        <strong>NCST AI Assistant</strong>
                        <span>HR • Procurement • Finance • CRM</span>
                    </div>
                    <button class="ncst-ai-chatbot-close">×</button>
                </div>

                <div class="ncst-ai-chatbot-messages">
                    <div class="ncst-ai-message bot welcome">
                        Hello! How can I help you?
                    </div>

                    <div class="ncst-ai-quick-options">
                        <button data-question="Explain HR leave approval flow">HR leave flow</button>
                        <button data-question="Explain procurement workflow">Procurement flow</button>
                        <button data-question="Explain finance invoice review">Finance review</button>
                        <button data-question="Explain CRM workflow">CRM workflow</button>
                        <button data-question="Show pending CRM project requests">Pending CRM requests</button>
                        <button data-question="Help">Show commands</button>
                    </div>
                </div>

                <div class="ncst-ai-chatbot-input-area">
                    <input type="text" class="ncst-ai-chatbot-input" placeholder="Ask something..." />
                    <button class="ncst-ai-chatbot-send">Send</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML("beforeend", chatbotHTML);

    const widget = document.querySelector(".ncst-ai-chatbot-widget");
    const button = widget.querySelector(".ncst-ai-chatbot-button");
    const windowBox = widget.querySelector(".ncst-ai-chatbot-window");
    const closeButton = widget.querySelector(".ncst-ai-chatbot-close");
    const sendButton = widget.querySelector(".ncst-ai-chatbot-send");
    const input = widget.querySelector(".ncst-ai-chatbot-input");
    const messages = widget.querySelector(".ncst-ai-chatbot-messages");
    const optionButtons = widget.querySelectorAll(".ncst-ai-quick-options button");

    button.addEventListener("click", () => {
        windowBox.classList.toggle("active");
        input.focus();
    });

    closeButton.addEventListener("click", () => {
        windowBox.classList.remove("active");
    });

    optionButtons.forEach((option) => {
        option.addEventListener("click", () => {
            const question = option.dataset.question;
            sendMessage(question);
        });
    });

    async function sendMessage(optionText = null) {
        const text = optionText || input.value.trim();

        if (!text) {
            return;
        }

        addMessage(text, "user");
        input.value = "";

        const loadingMessage = addMessage("Typing...", "bot loading");

        try {
            const result = await rpc("/ncst_ai_chatbot/message", {
                message: text,
            });

            loadingMessage.remove();

            if (result && result.reply) {
                addMessage(result.reply, "bot");
            } else {
                addMessage("Sorry, I could not get a response.", "bot");
            }
        } catch (error) {
            loadingMessage.remove();
            addMessage("Connection error. Please try again.", "bot");
            console.error("Chatbot error:", error);
        }
    }

    function addMessage(text, type) {
        const msg = document.createElement("div");
        msg.className = `ncst-ai-message ${type}`;
        msg.textContent = text;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
        return msg;
    }

    sendButton.addEventListener("click", () => sendMessage());

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
}

document.addEventListener("DOMContentLoaded", createChatbot);