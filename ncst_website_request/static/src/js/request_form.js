/** @odoo-module **/

document.addEventListener("DOMContentLoaded", function () {
    const messageTypeField = document.getElementById("message_type");
    const projectFieldsContainer = document.getElementById("project_request_fields");

    if (!messageTypeField || !projectFieldsContainer) {
        return;
    }

    function toggleProjectFields() {
        if (messageTypeField.value === "project_request") {
            projectFieldsContainer.style.display = "block";
        } else {
            projectFieldsContainer.style.display = "none";
        }
    }

    // Run on page load
    toggleProjectFields();

    // Run when dropdown changes
    messageTypeField.addEventListener("change", toggleProjectFields);
});