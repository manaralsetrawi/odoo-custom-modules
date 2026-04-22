/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class CrmDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            data: {
                total_requests: 0,
                new_inquiries: 0,
                waiting_approval: 0,
                approved_requests: 0,
                rejected_requests: 0,
                overdue_followups: 0,
                recent_requests: [],
                waiting_approval_requests: [],
                overdue_requests: [],
            },
        });

        onWillStart(async () => {
            this.state.data = await this.orm.call(
                "crm.dashboard",
                "get_dashboard_data",
                []
            );
        });
    }
}

CrmDashboard.template = "crm_workflow_custom.crm_dashboard_template";

registry.category("actions").add("crm_dashboard_tag", CrmDashboard);