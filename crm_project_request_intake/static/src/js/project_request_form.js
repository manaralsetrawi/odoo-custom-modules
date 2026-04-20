/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProjectRequestForm = publicWidget.Widget.extend({
    selector: "#crm_project_request_form",

    start: function () {
        this._bindEvents();
        return this._super.apply(this, arguments);
    },

    _bindEvents: function () {
        this.el.addEventListener("submit", this._onSubmit.bind(this));

        const fields = this.el.querySelectorAll("input, textarea, select");
        fields.forEach((field) => {
            field.addEventListener("input", () => {
                this._clearFieldError(field);
                this._refreshAlertState();
            });
            field.addEventListener("change", () => {
                this._clearFieldError(field);
                this._refreshAlertState();
            });
        });
    },

    _onSubmit: function (ev) {
        const errors = this._validateForm();

        if (errors.length) {
            ev.preventDefault();
            this._showAlert(errors);
            const firstInvalid = this.el.querySelector(".is-invalid");
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
                firstInvalid.focus();
            }
            return;
        }

        this._hideAlert();

        const submitBtn = this.el.querySelector("#pr_submit_btn");
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting...";
        }
    },

    _validateForm: function () {
        const errors = [];
        const requiredFields = [
            "#pr_name",
            "#pr_email",
            "#pr_phone",
            "#pr_request_type",
            "#pr_message",
            "#pr_company_name",
            "#pr_project_title",
            "#pr_project_description",
            "#pr_requested_budget",
            "#pr_requested_duration",
            "#pr_requested_notes",
        ];

        requiredFields.forEach((selector) => {
            const field = this.el.querySelector(selector);
            if (!field) {
                return;
            }

            const value = (field.value || "").trim();
            const label = field.dataset.label || "This field";

            if (!value) {
                this._setFieldError(field, `${label} is required.`);
                errors.push(`${label} is required.`);
                return;
            }

            if (field.id === "pr_email" && !this._isValidEmail(value)) {
                this._setFieldError(field, "Please enter a valid email address.");
                errors.push("Please enter a valid email address.");
                return;
            }

            if (field.id === "pr_phone" && value.length < 8) {
                this._setFieldError(field, "Please enter a valid phone number.");
                errors.push("Please enter a valid phone number.");
                return;
            }

            if (field.id === "pr_requested_budget") {
                const budget = parseFloat(value);
                if (isNaN(budget) || budget <= 0) {
                    this._setFieldError(field, "Expected Budget must be greater than 0.");
                    errors.push("Expected Budget must be greater than 0.");
                    return;
                }
            }

            this._clearFieldError(field);
        });

        return [...new Set(errors)];
    },

    _setFieldError: function (field, message) {
        field.classList.add("is-invalid");
        field.setCustomValidity(message);
    },

    _clearFieldError: function (field) {
        field.classList.remove("is-invalid");
        field.setCustomValidity("");
    },

    _refreshAlertState: function () {
        const currentErrors = this.el.querySelectorAll(".is-invalid");
        if (currentErrors.length === 0) {
            this._hideAlert();
        }
    },

    _showAlert: function (errors) {
        const alertBox = this.el.querySelector("#form_validation_alert");
        if (!alertBox) {
            return;
        }

        const items = errors.map((error) => `<li>${error}</li>`).join("");
        alertBox.innerHTML = `
            <strong>Please correct the following:</strong>
            <ul class="mb-0 mt-2">${items}</ul>
        `;
        alertBox.classList.remove("d-none");
    },

    _hideAlert: function () {
        const alertBox = this.el.querySelector("#form_validation_alert");
        if (alertBox) {
            alertBox.classList.add("d-none");
        }
    },

    _isValidEmail: function (email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },
});