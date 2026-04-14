/** @odoo-module **/

import { Component, onWillStart, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class FinanceDashboardClient extends Component {
    static template = "ncst_budget_management.FinanceDashboardClient";

    setup() {
        this.orm = useService("orm");
        this.chartRef = useRef("budgetChart");
        this.chartInstance = null;

        this.state = useState({
            data: null,
        });

        onWillStart(async () => {
            this.state.data = await this.orm.call(
                "finance.kpi.dashboard",
                "get_finance_dashboard_data",
                []
            );
        });
    }

    mounted() {
        this.renderBudgetChart();
    }

    patched() {
        this.renderBudgetChart();
    }

    renderBudgetChart() {
        if (!this.state.data || !this.chartRef.el || typeof Chart === "undefined") {
            return;
        }

        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        const budgetChart = this.state.data.budget_chart;
        const currencySymbol = this.state.data.currency_symbol;
        const ctx = this.chartRef.el.getContext("2d");

        this.chartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: budgetChart.labels,
                datasets: [{
                    label: "Budget Overview",
                    data: budgetChart.values,
                    borderWidth: 1,
                    borderRadius: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${currencySymbol}${context.raw}`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    }
}

registry.category("actions").add(
    "ncst_budget_management.finance_dashboard_client",
    FinanceDashboardClient
);