(function () {
    'use strict';

    function getCsrfToken() {
        var cookies = document.cookie ? document.cookie.split(';') : [];
        for (var i = 0; i < cookies.length; i += 1) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf('csrftoken=') === 0) {
                return decodeURIComponent(cookie.substring('csrftoken='.length));
            }
        }
        return '';
    }

    function createRipple(event) {
        var button = event.currentTarget;
        if (!button) {
            return;
        }

        var rect = button.getBoundingClientRect();
        var diameter = Math.max(rect.width, rect.height);
        var ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.width = ripple.style.height = diameter + 'px';
        ripple.style.left = (event.clientX - rect.left - diameter / 2) + 'px';
        ripple.style.top = (event.clientY - rect.top - diameter / 2) + 'px';

        button.appendChild(ripple);
        window.setTimeout(function () {
            ripple.remove();
        }, 650);
    }

    function animateCounter(node, target) {
        var duration = 900;
        var start = null;

        function frame(timestamp) {
            if (!start) {
                start = timestamp;
            }
            var progress = Math.min((timestamp - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            node.textContent = Math.round(eased * target).toLocaleString();

            if (progress < 1) {
                window.requestAnimationFrame(frame);
            } else {
                node.textContent = target.toLocaleString();
            }
        }

        node.textContent = '0';
        window.requestAnimationFrame(frame);
    }

    function initCounters() {
        var counters = document.querySelectorAll('.counter-value[data-target]');
        counters.forEach(function (counter) {
            var target = parseInt(counter.getAttribute('data-target'), 10);
            if (!Number.isFinite(target)) {
                return;
            }
            animateCounter(counter, target);
        });
    }

    function initReveal() {
        var nodes = document.querySelectorAll('.fade-enter');
        if (!nodes.length) {
            document.body.classList.add('dashboard-ready');
            return;
        }

        window.requestAnimationFrame(function () {
            document.body.classList.add('dashboard-ready');
        });
    }

    function initRipples() {
        document.querySelectorAll('.btn-service, .quick-action-link, .btn').forEach(function (button) {
            button.addEventListener('click', createRipple);
        });
    }

    function createChart(config) {
        var canvas = document.getElementById(config.canvasId);
        if (!canvas || !window.Chart) {
            return null;
        }

        return new Chart(canvas.getContext('2d'), {
            type: config.type,
            data: {
                labels: config.labels,
                datasets: config.datasets
            },
            options: config.options
        });
    }

    function buildInsightHtml(metrics, role) {
        var totalApplications = Number(metrics.total_applications || 0);
        var pending = Number(metrics.pending_applications || 0);
        var approved = Number(metrics.approved_applications || 0);
        var complaintsOpen = Number(metrics.complaints_open || 0);
        var queueRatio = totalApplications > 0 ? Math.round((pending / totalApplications) * 100) : 0;

        var insights = [
            {
                icon: 'bi-speedometer2',
                title: 'Activity flow',
                message: queueRatio > 40 ? 'Your pending queue is elevated. Prioritize reviews to keep turnaround steady.' : 'The queue is under control and moving at a healthy pace.'
            },
            {
                icon: 'bi-patch-check-fill',
                title: 'Approvals',
                message: approved > pending ? 'Approved volume is ahead of the backlog, which indicates good throughput.' : 'Keep reviewing pending items to raise completion volume.'
            },
            {
                icon: 'bi-bell-fill',
                title: 'Complaints',
                message: complaintsOpen > 0 ? complaintsOpen + ' complaint(s) are still open and need monitoring.' : 'No open complaints are waiting right now.'
            }
        ];

        if (role === 'citizen') {
            insights.unshift({
                icon: 'bi-lightning-charge-fill',
                title: 'Next best action',
                message: 'Open services, bills, or profile settings from the quick action panel.'
            });
        }

        return insights.map(function (item) {
            return '' +
                '<article class="insight-row fade-enter">' +
                    '<span class="badge-shell"><i class="bi ' + item.icon + '"></i></span>' +
                    '<div>' +
                        '<h5>' + item.title + '</h5>' +
                        '<p>' + item.message + '</p>' +
                    '</div>' +
                '</article>';
        }).join('');
    }

    async function loadDashboardData() {
        var root = document.getElementById('dashboardPageRoot');
        if (!root) {
            return;
        }

        var endpoint = root.getAttribute('data-dashboard-api');
        var role = (document.body.getAttribute('data-user-role') || 'citizen').toLowerCase();
        var insightHost = document.getElementById('dashboardInsights');
        var lineChart = document.getElementById('dashboardLineChart');
        var barChart = document.getElementById('dashboardBarChart');
        var pieChart = document.getElementById('dashboardPieChart');
        var chartStatus = document.getElementById('dashboardChartStatus');

        if (!endpoint) {
            return;
        }

        try {
            var response = await fetch(endpoint, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error('Unable to load dashboard analytics.');
            }

            var payload = await response.json();
            var labels = payload.labels || [];
            var lineData = payload.line || [];
            var barData = payload.bar || [];
            var pieData = payload.pie || [];
            var metrics = payload.metrics || {};

            if (insightHost) {
                insightHost.innerHTML = buildInsightHtml(metrics, role);
            }

            createChart({
                canvasId: 'dashboardLineChart',
                type: 'line',
                labels: labels,
                datasets: [{
                    label: role === 'citizen' ? 'Applications' : 'Registrations',
                    data: lineData,
                    borderColor: '#0f4c81',
                    backgroundColor: 'rgba(15, 76, 129, 0.14)',
                    tension: 0.38,
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: '#0f4c81'
                }],
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true, grid: { color: 'rgba(15, 76, 129, 0.08)' } }
                    }
                }
            });

            createChart({
                canvasId: 'dashboardBarChart',
                type: 'bar',
                labels: labels,
                datasets: [{
                    label: 'Applications',
                    data: barData,
                    backgroundColor: 'rgba(28, 122, 140, 0.72)',
                    borderRadius: 12,
                    borderSkipped: false
                }],
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true, grid: { color: 'rgba(15, 76, 129, 0.08)' } }
                    }
                }
            });

            createChart({
                canvasId: 'dashboardPieChart',
                type: 'doughnut',
                labels: ['Approved', 'Pending', 'Rejected'],
                datasets: [{
                    data: pieData,
                    backgroundColor: ['#16a34a', '#f7a100', '#dc2626'],
                    borderWidth: 0,
                    hoverOffset: 8
                }],
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '66%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                usePointStyle: true,
                                padding: 18
                            }
                        }
                    }
                }
            });

            if (chartStatus) {
                var metricLabels = [];
                Object.keys(metrics).forEach(function (key) {
                    metricLabels.push(key.replace(/_/g, ' '));
                });
                chartStatus.textContent = 'Live analytics loaded for ' + role + '. Metrics: ' + metricLabels.join(', ');
            }
        } catch (error) {
            if (chartStatus) {
                chartStatus.textContent = 'Analytics could not be loaded right now.';
            }
            if (insightHost) {
                insightHost.innerHTML = '<div class="insight-row fade-enter"><span class="badge-shell"><i class="bi bi-exclamation-triangle-fill"></i></span><div><h5>Analytics unavailable</h5><p>The dashboard is still usable, but live chart data is temporarily unavailable.</p></div></div>';
            }
        }
    }

    function init() {
        initCounters();
        initReveal();
        initRipples();
        loadDashboardData();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
