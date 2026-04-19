/** @odoo-module **/

document.addEventListener("DOMContentLoaded", function () {
    const messageTypeField = document.getElementById("message_type");
    const projectFieldsContainer = document.getElementById("project_request_fields");

    if (!messageTypeField || !projectFieldsContainer) {
        return;
    }

    const projectInputs = projectFieldsContainer.querySelectorAll("input, textarea, select");

    function toggleProjectFields() {
        const isProjectRequest = messageTypeField.value === "project_request";

        projectFieldsContainer.style.display = isProjectRequest ? "block" : "none";

        // Optional: clear project fields when hidden
        if (!isProjectRequest) {
            projectInputs.forEach((field) => {
                field.value = "";
            });
        }
    }

    toggleProjectFields();
    messageTypeField.addEventListener("change", toggleProjectFields);
});