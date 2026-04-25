// /** @odoo-module **/

// import { registry } from "@web/core/registry";
// import { Component, onWillStart, useState } from "@odoo/owl";
// import { useService } from "@web/core/utils/hooks";

// class CrmDashboard extends Component {
//     setup() {
//         this.orm = useService("orm");
//         this.action = useService("action");

//         this.state = useState({
//             data: {
//                 total_requests: 0,
//                 new_inquiries: 0,
//                 waiting_approval: 0,
//                 approved_requests: 0,
//                 rejected_requests: 0,
//                 overdue_followups: 0,
//                 recent_requests: [],
//                 waiting_approval_requests: [],
//                 overdue_requests: [],
//             },
//         });

//         onWillStart(async () => {
//             this.state.data = await this.orm.call(
//                 "crm.dashboard",
//                 "get_dashboard_data",
//                 []
//             );
//         });
//     }

//     openLeadRecord(recordId) {
//         this.action.doAction({
//             type: "ir.actions.act_window",
//             name: "CRM Request",
//             res_model: "crm.lead",
//             res_id: recordId,
//             views: [[false, "form"]],
//             target: "current",
//         });
//     }

//     openFilteredRequests(filterType) {
//         let domain = [];
//         let actionName = "CRM Requests";

//         if (filterType === "new_inquiries") {
//             domain = [["stage_id.name", "=", "New Inquiry"]];
//             actionName = "New Inquiries";
//         } else if (filterType === "waiting_approval") {
//             domain = [["stage_id.name", "=", "Waiting Approval"]];
//             actionName = "Waiting Approval Requests";
//         } else if (filterType === "approved") {
//             domain = [["stage_id.name", "=", "Approved"]];
//             actionName = "Approved Requests";
//         } else if (filterType === "rejected") {
//             domain = [["stage_id.name", "=", "Rejected"]];
//             actionName = "Rejected Requests";
//         } else if (filterType === "overdue_followups") {
//             domain = [["followup_status", "=", "overdue"]];
//             actionName = "Overdue Follow-ups";
//         }

//         this.action.doAction({
//             type: "ir.actions.act_window",
//             name: actionName,
//             res_model: "crm.lead",
//             view_mode: "list,kanban,form",
//             views: [
//                 [false, "list"],
//                 [false, "kanban"],
//                 [false, "form"],
//             ],
//             target: "current",
//             domain: domain,
//         });
//     }
// }

// CrmDashboard.template = "crm_workflow_custom.crm_dashboard_template";

// registry.category("actions").add("crm_dashboard_tag", CrmDashboard);