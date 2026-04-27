/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

function createChatbot() {
    if (document.querySelector(".ncst-ai-chatbot-widget")) {
        return;
    }

    const chatbotHTML = `
        <div class="ncst-ai-chatbot-widget">
                <button class="ncst-ai-chatbot-button" title="NCST AI Assistant">
                    <svg xmlns="http://www.w3.org/2000/svg"
                        height="30"
                        viewBox="0 -960 960 960"
                        width="30"
                        fill="#ffffff"
                        aria-hidden="true">
                        <path d="m480-80-10-120h-10q-142 0-241-99t-99-241q0-142 99-241t241-99q71 0 132.5 26.5t108 73q46.5 46.5 73 108T800-540q0 75-24.5 144t-67 128q-42.5 59-101 107T480-80Zm80-146q71-60 115.5-140.5T720-540q0-109-75.5-184.5T460-800q-109 0-184.5 75.5T200-540q0 109 75.5 184.5T460-280h100v54Zm-72-107q12-12 12-29t-12-29q-12-12-29-12t-29 12q-12 12-12 29t12 29q12 12 29 12t29-12Zm-58-115h60q0-30 6-42t38-44q18-18 30-39t12-45q0-51-34.5-76.5T460-720q-44 0-74 24.5T344-636l56 22q5-17 19-33.5t41-16.5q27 0 40.5 15t13.5 33q0 17-10 30.5T480-558q-35 30-42.5 47.5T430-448Zm30-65Z"/>
                    </svg>
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
                        Hi! Choose an option or ask me anything.
                    </div>

                    <div class="ncst-ai-quick-options">
                        <button data-question="Explain HR leave approval flow">HR leave flow</button>
                        <button data-question="Explain procurement workflow">Procurement flow</button>
                        <button data-question="Explain finance invoice review">Finance review</button>
                        <button data-question="Explain CRM workflow">CRM workflow</button>
                        <button data-question="Show pending CRM project requests">Pending CRM requests</button>
                        <button data-question="Who is absent today?">Absent employees today</button>
                        <button data-question="Paused projects for all">Paused projects today</button>
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