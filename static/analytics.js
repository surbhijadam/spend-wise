/* =====================================================
   Analytics.js — SpendWise
   ===================================================== */

/* -------- Global Chart Instances -------- */
let categoryChartInstance = null;
let monthlyChartInstance = null;

/* -------- Error Display Utility -------- */
function showError(msg) {
    const errEl = document.getElementById('analyticsError');
    if (errEl) {
        errEl.style.display = 'block';
        errEl.textContent = 'Error: ' + msg;
    }
    console.error('Analytics Error:', msg);
}

/* -------- Chart Color Palette -------- */
const CHART_COLORS = {
    primary: 'rgb(63, 81, 181)',
    secondary: 'rgb(255, 152, 0)',
    danger: 'rgb(244, 67, 54)',
    success: 'rgb(76, 175, 80)',
    info: 'rgb(0, 188, 212)',
    warning: 'rgb(255, 193, 7)'
};

const CATEGORY_COLORS = [
    CHART_COLORS.primary,
    CHART_COLORS.secondary,
    CHART_COLORS.danger,
    CHART_COLORS.success,
    CHART_COLORS.info,
    CHART_COLORS.warning,
    'rgb(121, 85, 72)',
    'rgb(158, 158, 158)'
];

/* =====================================================
   Category Chart (Doughnut)
   ===================================================== */
function renderCategoryChart(data) {
    const canvas = document.getElementById('categoryChart');
    if (!canvas) {
        showError('Category chart canvas not found');
        return;
    }

    const ctx = canvas.getContext('2d');

    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.category),
            datasets: [{
                label: 'Spending by Category',
                data: data.map(d => d.total_spent),
                backgroundColor: CATEGORY_COLORS.slice(0, data.length),
                borderRadius: 4,
                hoverOffset: 12
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        usePointStyle: true,
                        padding: 14
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.label}: ${new Intl.NumberFormat(
                                'en-IN',
                                { style: 'currency', currency: 'INR' }
                            ).format(context.parsed)}`;
                        }
                    }
                }
            }
        }
    });
}

/* =====================================================
   Monthly Trend Chart (Line)
   ===================================================== */
function renderMonthlyChart(data) {
    const canvas = document.getElementById('monthlyChart');
    if (!canvas) {
        showError('Monthly chart canvas not found');
        return;
    }

    const ctx = canvas.getContext('2d');

    if (monthlyChartInstance) {
        monthlyChartInstance.destroy();
    }

    monthlyChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.month),
            datasets: [{
                label: 'Total Spending',
                data: data.map(d => d.total_spent),
                borderColor: CHART_COLORS.primary,
                backgroundColor: 'rgba(63, 81, 181, 0.2)',
                fill: true,
                tension: 0.3,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value =>
                            new Intl.NumberFormat('en-IN', {
                                style: 'currency',
                                currency: 'INR',
                                minimumFractionDigits: 0
                            }).format(value)
                    },
                    title: {
                        display: true,
                        text: 'Amount (INR)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx =>
                            new Intl.NumberFormat('en-IN', {
                                style: 'currency',
                                currency: 'INR'
                            }).format(ctx.parsed.y)
                    }
                }
            }
        }
    });
}

/* =====================================================
   Main Analytics Loader
   ===================================================== */
window.loadAnalytics = async function () {
    const token = localStorage.getItem('token');

    if (!token) {
        showError('Authentication required. Please log in again.');
        return;
    }

    try {
        const response = await fetch('/api/analytics', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.message || `API error (${response.status})`);
        }

        const data = await response.json();

        /* ---- Summary Cards ---- */
        document.getElementById('total-spent').textContent =
            new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })
                .format(data.total_spent || 0);

        document.getElementById('prediction').textContent =
            new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })
                .format(data.prediction_next_month || 0);

        document.getElementById('top-merchant').textContent =
            data.top_merchant || 'N/A';

        /* ---- Charts ---- */
        if (Array.isArray(data.spending_by_category) && data.spending_by_category.length > 0) {
            renderCategoryChart(data.spending_by_category);
        } else {
            showError('No category spending data available.');
        }

        if (Array.isArray(data.monthly_trend) && data.monthly_trend.length > 0) {
            renderMonthlyChart(data.monthly_trend);
        } else {
            showError('No monthly trend data available.');
        }

    } catch (err) {
        showError(err.message);
    }
};
