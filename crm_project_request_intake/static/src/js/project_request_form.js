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

        const isProjectRequest = requestTypeField.value === 'project_request';
        projectFields.style.display = isProjectRequest ? 'block' : 'none';

        const projectTitle = this.el.querySelector('#intake_project_title');
        const projectDescription = this.el.querySelector('#intake_project_description');

        if (projectTitle) {
            projectTitle.required = isProjectRequest;
        }
        if (projectDescription) {
            projectDescription.required = isProjectRequest;
        }
    },
});