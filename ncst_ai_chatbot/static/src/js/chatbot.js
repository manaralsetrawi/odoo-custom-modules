/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

function createChatbot() {
    // -----------------------------------------------------------------
    // SECTION: Guard against duplicate widget
    // -----------------------------------------------------------------
    // Prevent duplicate widget injection if assets reload.
    if (document.querySelector(".ncst-ai-chatbot-widget")) {
        return;
    }

    // -----------------------------------------------------------------
    // SECTION: Widget HTML
    // -----------------------------------------------------------------
    // Static HTML for the floating chat widget.
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
                        <strong>AI Assistant</strong>
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

    // -----------------------------------------------------------------
    // SECTION: DOM cache
    // -----------------------------------------------------------------
    // Cache DOM elements to avoid repeated queries.
    const widget = document.querySelector(".ncst-ai-chatbot-widget");
    const button = widget.querySelector(".ncst-ai-chatbot-button");
    const windowBox = widget.querySelector(".ncst-ai-chatbot-window");
    const closeButton = widget.querySelector(".ncst-ai-chatbot-close");
    const sendButton = widget.querySelector(".ncst-ai-chatbot-send");
    const input = widget.querySelector(".ncst-ai-chatbot-input");
    const messages = widget.querySelector(".ncst-ai-chatbot-messages");
    const optionButtons = widget.querySelectorAll(".ncst-ai-quick-options button");

    // -----------------------------------------------------------------
    // SECTION: Basic UI events
    // -----------------------------------------------------------------
    button.addEventListener("click", () => {
        // Toggle chat window visibility.
        windowBox.classList.toggle("active");
        input.focus();
    });

    closeButton.addEventListener("click", () => {
        // Close the widget panel (keep it in DOM).
        windowBox.classList.remove("active");
    });

    optionButtons.forEach((option) => {
        option.addEventListener("click", () => {
            // Quick-option buttons send predefined questions.
            sendMessage(option.dataset.question);
        });
    });

    // -----------------------------------------------------------------
    // SECTION: Message formatting helpers
    // -----------------------------------------------------------------
    function formatMessage(text) {
        // Minimal HTML-escape + formatting for chatbot output.
        if (!text) {
            return "";
        }

        let formatted = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        formatted = formatted.replace(/\n/g, "<br>");

        return formatted;
    }

    // -----------------------------------------------------------------
    // SECTION: Message rendering
    // -----------------------------------------------------------------
    function addMessage(text, type) {
        // Append a message bubble and keep scroll pinned to the bottom.
        const msg = document.createElement("div");
        msg.className = `ncst-ai-message ${type}`;
        msg.innerHTML = formatMessage(text);

        if (type.includes("bot") && !type.includes("loading") && !type.includes("welcome")) {
            // Add a copy button for bot answers (not for loading/welcome).
            const copyButton = document.createElement("button");
            copyButton.className = "ncst-ai-copy-btn";
            copyButton.title = "Copy response";
            copyButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg"
                    height="18"
                    viewBox="0 -960 960 960"
                    width="18"
                    fill="#0b2c3d">
                    <path d="M360-240q-33 0-56.5-23.5T280-320v-480q0-33 23.5-56.5T360-880h360q33 0 56.5 23.5T800-800v480q0 33-23.5 56.5T720-240H360Zm0-80h360v-480H360v480ZM200-80q-33 0-56.5-23.5T120-160v-560h80v560h440v80H200Zm160-240v-480 480Z"/>
                </svg>
            `;

            copyButton.addEventListener("click", async () => {
                try {
                    // Use Clipboard API when available.
                    await navigator.clipboard.writeText(text);
                    copyButton.innerHTML = "✓";
                    setTimeout(() => {
                        copyButton.innerHTML = `
                            <svg xmlns="http://www.w3.org/2000/svg"
                                height="18"
                                viewBox="0 -960 960 960"
                                width="18"
                                fill="#0b2c3d">
                                <path d="M360-240q-33 0-56.5-23.5T280-320v-480q0-33 23.5-56.5T360-880h360q33 0 56.5 23.5T800-800v480q0 33-23.5 56.5T720-240H360Zm0-80h360v-480H360v480ZM200-80q-33 0-56.5-23.5T120-160v-560h80v560h440v80H200Zm160-240v-480 480Z"/>
                            </svg>
                        `;
                    }, 1200);
                } catch (error) {
                    console.error("Copy failed:", error);
                }
            });

            msg.appendChild(copyButton);
        }

        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
        return msg;
    }

    // -----------------------------------------------------------------
    // SECTION: Send message flow
    // -----------------------------------------------------------------
    async function sendMessage(optionText = null) {
        // Send either the quick-option text or the input value.
        const text = optionText || input.value.trim();

        if (!text) {
            return;
        }

        addMessage(text, "user");
        input.value = "";

        // Show a temporary bot bubble while waiting for the server.
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

    // -----------------------------------------------------------------
    // SECTION: Input events
    // -----------------------------------------------------------------
    sendButton.addEventListener("click", () => sendMessage());

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
}

// Initialize after DOM is ready.
document.addEventListener("DOMContentLoaded", createChatbot);