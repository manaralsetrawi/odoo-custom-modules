/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProjectRequestForm = publicWidget.Widget.extend({
    selector: "#crm_project_request_form",

    start: function () {
        this._toggleProjectFields();
        this._bindEvents();
        return this._super.apply(this, arguments);
    },

    _bindEvents: function () {
        const requestTypeField = this.el.querySelector("#request_type");
        if (requestTypeField) {
            requestTypeField.addEventListener("change", this._toggleProjectFields.bind(this));
        }

        this.el.addEventListener("submit", this._onSubmit.bind(this));

        const fields = this.el.querySelectorAll("input, textarea, select");
        fields.forEach((field) => {
            field.addEventListener("input", this._clearFieldError.bind(this, field));
            field.addEventListener("change", this._clearFieldError.bind(this, field));
        });
    },

    _toggleProjectFields: function () {
        const requestTypeField = this.el.querySelector("#request_type");
        const projectFields = this.el.querySelector("#project_request_fields");

        if (!requestTypeField || !projectFields) {
            return;
        }

        const isProjectRequest = requestTypeField.value === "project_request";
        projectFields.classList.toggle("d-none", !isProjectRequest);

        const conditionalFields = [
            "#intake_company_name",
            "#intake_project_title",
            "#intake_project_description",
            "#intake_requested_budget",
            "#intake_requested_duration",
            "#intake_requested_notes",
        ];

        conditionalFields.forEach((selector) => {
            const field = this.el.querySelector(selector);
            if (field) {
                field.required = isProjectRequest;
                if (!isProjectRequest) {
                    field.setCustomValidity("");
                    field.classList.remove("is-invalid");
                }
            }
        });

        this._hideAlert();
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
        }
    },

    _validateForm: function () {
        const errors = [];
        const requestType = this.el.querySelector("#request_type")?.value || "general_inquiry";

        const requiredFields = [
            "#name",
            "#email",
            "#phone",
            "#request_type",
            "#message",
        ];

        if (requestType === "project_request") {
            requiredFields.push(
                "#intake_company_name",
                "#intake_project_title",
                "#intake_project_description",
                "#intake_requested_budget",
                "#intake_requested_duration",
                "#intake_requested_notes"
            );
        }

        requiredFields.forEach((selector) => {
            const field = this.el.querySelector(selector);
            if (!field) {
                return;
            }

            const value = (field.value || "").trim();
            const label = field.dataset.label || field.name || "This field";

            if (!value) {
                this._setFieldError(field, `${label} is required.`);
                errors.push(`${label} is required.`);
                return;
            }

            if (field.id === "email" && !this._isValidEmail(value)) {
                this._setFieldError(field, "Please enter a valid email address.");
                errors.push("Please enter a valid email address.");
                return;
            }

            if (field.id === "phone" && value.length < 8) {
                this._setFieldError(field, "Please enter a valid phone number.");
                errors.push("Please enter a valid phone number.");
                return;
            }

            if (field.id === "intake_requested_budget") {
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