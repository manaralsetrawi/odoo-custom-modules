/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class ProjectRequestDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            data: {},
        });

        onWillStart(async () => {
            this.state.data = await this.orm.call(
                "crm.lead",
                "get_project_request_dashboard_data",
                []
            );
        });
    }

    openLeads(status = false, priority = false) {
        const domain = [
            ["request_type", "=", "project_request"],
            ["type", "=", "lead"],
        ];

        if (status) {
            domain.push(["intake_state", "=", status]);
        }

        if (priority) {
            domain.push(["priority", "=", priority]);
            domain.push(["intake_state", "in", ["submitted", "under_review"]]);
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Project Requests",
            res_model: "crm.lead",
            view_mode: "kanban,list,form",
            views: [
                ["crm.view_crm_lead_kanban", "kanban"],
                [false, "list"],
                [false, "form"],
            ],
            domain: domain,
            context: {
                default_type: "lead",
                default_request_type: "project_request",
                group_by: false,
            },
            target: "current",
        });
    }
}

ProjectRequestDashboard.template = "crm_project_request_intake.ProjectRequestDashboard";

registry.category("actions").add(
    "project_request_dashboard_action",
    ProjectRequestDashboard
);