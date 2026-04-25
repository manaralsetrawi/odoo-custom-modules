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

    async openLeads(status = false, priority = false) {
        const action = await this.orm.call(
            "crm.lead",
            "action_open_project_request_leads_from_dashboard",
            [],
            {
                status: status,
                priority: priority,
            }
        );

        this.action.doAction(action);
    }
}

ProjectRequestDashboard.template = "crm_project_request_intake.ProjectRequestDashboard";

registry.category("actions").add(
    "project_request_dashboard_action",
    ProjectRequestDashboard
);