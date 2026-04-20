/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProjectRequestForm = publicWidget.Widget.extend({
    selector: "form",

    start: function () {
        this._toggleProjectFields();
        this._bindEvents();
        return this._super.apply(this, arguments);
    },

    _bindEvents: function () {
        const requestTypeField = this.el.querySelector('#request_type');
        if (requestTypeField) {
            requestTypeField.addEventListener('change', this._toggleProjectFields.bind(this));
        }
    },

    _toggleProjectFields: function () {
        const requestTypeField = this.el.querySelector('#request_type');
        const projectFields = this.el.querySelector('#project_request_fields');

        if (!requestTypeField || !projectFields) {
            return;
        }

        if (requestTypeField.value === 'project_request') {
            projectFields.style.display = 'block';
        } else {
            projectFields.style.display = 'none';
        }
    },
});