/** @odoo-module **/

import { Component, onMounted, onPatched, onWillStart, useRef, useState } from "@odoo/owl";
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
            chartError: false,
        });

        onWillStart(async () => {
            this.state.data = await this.orm.call(
                "finance.kpi.dashboard",
                "get_finance_dashboard_data",
                []
            );
        });

        onMounted(() => {
            this.renderBudgetChart();
        });

        onPatched(() => {
            this.renderBudgetChart();
        });
    }

    renderBudgetChart() {
        const ChartLib = globalThis.Chart;

        if (!this.state.data || !this.chartRef.el) {
            return;
        }

        if (!ChartLib) {
            console.error("Chart.js is not loaded.");
            this.state.chartError = true;
            return;
        }

        this.state.chartError = false;

        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }

        const budgetChart = this.state.data.budget_chart;
        const currencySymbol = this.state.data.currency_symbol;
        const ctx = this.chartRef.el.getContext("2d");

        this.chartInstance = new ChartLib(ctx, {
            type: "bar",
            data: {
                labels: budgetChart.labels,
                datasets: [
                    {
                        label: "Budget Overview",
                        data: budgetChart.values,
                        backgroundColor: ["#9ec5f0", "#5d8fc9", "#1f5b99"],
                        borderColor: ["#9ec5f0", "#5d8fc9", "#1f5b99"],
                        borderWidth: 1,
                        borderRadius: 8,
                        maxBarThickness: 70,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: {
                    legend: {
                        display: true,
                        position: "top",
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${currencySymbol}${context.raw}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return `${currencySymbol}${value}`;
                            },
                        },
                    },
                },
            },
        });
    }

    willUnmount() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }
}

registry.category("actions").add(
    "ncst_budget_management.finance_dashboard_client",
    FinanceDashboardClient
);