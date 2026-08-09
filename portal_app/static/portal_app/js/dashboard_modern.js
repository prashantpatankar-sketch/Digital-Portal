(function () {
    'use strict';

    function safeNumber(value) {
        var numeric = Number(String(value).replace(/[^0-9.-]/g, ''));
        return Number.isFinite(numeric) ? numeric : 0;
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function getRole() {
        return (document.body.getAttribute('data-user-role') || 'citizen').toLowerCase();
    }

    function getTimeBucket() {
        var hour = new Date().getHours();
        if (hour >= 17 && hour <= 22) {
            return 'Evening';
        }
        if (hour >= 12 && hour < 17) {
            return 'Afternoon';
        }
        if (hour >= 6 && hour < 12) {
            return 'Morning';
        }
        return 'Night';
    }

    function getMetricSnapshot() {
        return Array.from(document.querySelectorAll('.metric-card')).map(function (card) {
            var valueNode = card.querySelector('h3');
            var labelNode = card.querySelector('p');
            return {
                label: labelNode ? labelNode.textContent.trim() : '',
                value: valueNode ? safeNumber(valueNode.textContent) : 0,
                node: valueNode
            };
        });
    }

    function animateMetricCounter(node, finalValue) {
        if (!node) {
            return;
        }

        var duration = 900;
        var startTime = null;

        function frame(timestamp) {
            if (!startTime) {
                startTime = timestamp;
            }

            var progress = Math.min((timestamp - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            node.textContent = Math.round(eased * finalValue).toLocaleString();

            if (progress < 1) {
                window.requestAnimationFrame(frame);
            } else {
                node.textContent = finalValue.toLocaleString();
            }
        }

        node.textContent = '0';
        window.requestAnimationFrame(frame);
    }

    function animateCounters() {
        getMetricSnapshot().forEach(function (metric) {
            if (!metric.node || metric.value <= 0) {
                return;
            }
            animateMetricCounter(metric.node, metric.value);
        });
    }

    function loadPreviousSnapshot(role) {
        try {
            var raw = localStorage.getItem('gp_dashboard_snapshot_' + role);
            return raw ? JSON.parse(raw) : null;
        } catch (error) {
            return null;
        }
    }

    function saveSnapshot(role, payload) {
        try {
            localStorage.setItem('gp_dashboard_snapshot_' + role, JSON.stringify(payload));
        } catch (error) {
            // Ignore storage issues.
        }
    }

    function roleActions(role, urls) {
        if (role === 'admin') {
            return [
                { title: 'Review pending applications', href: urls.reviewApplications, icon: 'bi-clipboard-check' },
                { title: 'Open complaint queue', href: urls.complaints, icon: 'bi-megaphone-fill' },
                { title: 'Manage users', href: urls.users, icon: 'bi-people-fill' }
            ];
        }

        if (role === 'staff') {
            return [
                { title: 'Approve pending requests', href: urls.reviewApplications, icon: 'bi-check2-square' },
                { title: 'Resolve complaints', href: urls.complaints, icon: 'bi-chat-dots-fill' },
                { title: 'Open settings', href: urls.settings, icon: 'bi-gear-fill' }
            ];
        }

        return [
            { title: 'Apply for certificate', href: urls.applyCertificate, icon: 'bi-file-earmark-text-fill' },
            { title: 'Check application status', href: urls.myApplications, icon: 'bi-search' },
            { title: 'Open account settings', href: urls.settings, icon: 'bi-person-gear' }
        ];
    }

    function roleInsights(role, metrics, previousSnapshot) {
        var totalApplications = metrics.find(function (item) {
            return /total applications/i.test(item.label);
        }) || metrics[0] || { value: 0 };

        var pendingMetric = metrics.find(function (item) {
            return /pending/i.test(item.label);
        });

        var approvedMetric = metrics.find(function (item) {
            return /approved/i.test(item.label);
        });

        var trendText = 'Dashboard activity is stable.';
        if (previousSnapshot && typeof previousSnapshot.totalApplications === 'number') {
            if (totalApplications.value > previousSnapshot.totalApplications) {
                trendText = 'User registrations increased this month.';
            } else if (totalApplications.value < previousSnapshot.totalApplications) {
                trendText = 'User registrations slowed compared with your last visit.';
            } else {
                trendText = 'User registrations are unchanged since the last snapshot.';
            }
        } else if (role === 'citizen') {
            trendText = 'Your service usage is steady and ready for quick action.';
        } else {
            trendText = 'Operational flow is steady and ready for review.';
        }

        var serviceText = role === 'citizen' ? 'Most used service: Income Certificate' : 'Most used service: Application Review';
        var peakText = 'Peak usage time: ' + getTimeBucket();
        var queueText = 'Pending queue is balanced.';

        if (pendingMetric && approvedMetric) {
            if (pendingMetric.value > approvedMetric.value) {
                queueText = 'Pending queue needs attention before it grows further.';
            } else if (pendingMetric.value === 0) {
                queueText = 'No pending requests are waiting right now.';
            } else {
                queueText = 'Approval flow is moving faster than the backlog.';
            }
        } else if (pendingMetric) {
            queueText = pendingMetric.value > 0 ? 'Pending queue needs attention before it grows further.' : 'No pending requests are waiting right now.';
        }

        return [
            {
                tag: 'Trend',
                title: 'Activity trend',
                message: trendText,
                accent: 'primary'
            },
            {
                tag: 'Service',
                title: 'Top service',
                message: serviceText,
                accent: 'accent'
            },
            {
                tag: 'Usage',
                title: 'Peak time',
                message: peakText,
                accent: 'warning'
            },
            {
                tag: 'Queue',
                title: 'Backlog health',
                message: queueText,
                accent: 'success'
            }
        ];
    }

    function buildSmartDashboard() {
        var panel = document.getElementById('smartDashboardPanel');
        var insightHost = document.getElementById('smartInsightCards');
        var suggestionHost = document.getElementById('smartSuggestionList');

        if (!panel || !insightHost || !suggestionHost) {
            return;
        }

        var role = getRole();
        var metrics = getMetricSnapshot();
        var previousSnapshot = loadPreviousSnapshot(role) || {};

        var urls = {
            reviewApplications: panel.getAttribute('data-review-url') || '#',
            complaints: panel.getAttribute('data-complaints-url') || '#',
            users: panel.getAttribute('data-users-url') || '#',
            settings: panel.getAttribute('data-settings-url') || '#',
            applyCertificate: panel.getAttribute('data-apply-url') || '#',
            myApplications: panel.getAttribute('data-applications-url') || '#'
        };

        var insights = roleInsights(role, metrics, previousSnapshot);
        var actions = roleActions(role, urls);

        insightHost.innerHTML = insights.map(function (item) {
            return '' +
                '<article class="smart-insight-card smart-insight-' + item.accent + '">' +
                    '<div class="smart-meta"><i class="bi bi-stars"></i>' + escapeHtml(item.tag) + '</div>' +
                    '<h4>' + escapeHtml(item.title) + '</h4>' +
                    '<p>' + escapeHtml(item.message) + '</p>' +
                '</article>';
        }).join('');

        suggestionHost.innerHTML = '' +
            '<div class="smart-suggestion-card mb-0">' +
                '<div class="smart-meta"><i class="bi bi-lightning-charge-fill"></i>Smart suggestions</div>' +
                '<h4>Recommended next actions</h4>' +
                '<p class="mb-3">These are generated from your role, queue state, and recent dashboard activity.</p>' +
                '<div class="d-grid gap-2">' +
                    actions.map(function (action) {
                        return '<a class="suggestion-chip" href="' + escapeHtml(action.href) + '"><span><i class="bi ' + action.icon + ' me-2"></i>' + escapeHtml(action.title) + '</span><i class="bi bi-arrow-right-short"></i></a>';
                    }).join('') +
                '</div>' +
            '</div>';

        panel.classList.add('is-loaded');
        saveSnapshot(role, {
            totalApplications: metrics.length ? metrics[0].value : 0,
            capturedAt: Date.now()
        });
    }

    function initBottomNav() {
        var bottomNav = document.getElementById('mobileBottomNav');
        if (!bottomNav) {
            return;
        }

        function normalizePath(pathValue) {
            var path = String(pathValue || '/').split('?')[0].split('#')[0];
            if (!path.startsWith('/')) {
                path = '/' + path;
            }
            return path.replace(/\/+$/, '') || '/';
        }

        var currentPath = normalizePath(window.location.pathname);
        var activeLink = null;
        var bestMatchLength = -1;

        bottomNav.querySelectorAll('[data-bottom-nav]').forEach(function (link) {
            link.classList.remove('active');
            var href = link.getAttribute('href') || '';
            var normalizedHref = normalizePath(href);

            if (normalizedHref === '/logout') {
                return;
            }

            var isExactMatch = currentPath === normalizedHref;
            var isNestedMatch = currentPath.indexOf(normalizedHref + '/') === 0;

            if ((isExactMatch || isNestedMatch) && normalizedHref.length > bestMatchLength) {
                bestMatchLength = normalizedHref.length;
                activeLink = link;
            }
        });

        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    function initSortableTables() {
        var tables = Array.prototype.slice.call(document.querySelectorAll('table[data-sortable]'));
        if (!tables.length) {
            return;
        }

        function normalizeValue(cell, type) {
            if (!cell) {
                return '';
            }

            var raw = cell.getAttribute('data-sort-value') || cell.textContent || '';
            var text = String(raw).trim().toLowerCase();

            if (type === 'date') {
                var timestamp = Date.parse(raw);
                return Number.isFinite(timestamp) ? timestamp : 0;
            }

            if (type === 'number') {
                var numeric = Number(String(raw).replace(/[^0-9.-]/g, ''));
                return Number.isFinite(numeric) ? numeric : 0;
            }

            return text;
        }

        tables.forEach(function (table) {
            var headers = Array.prototype.slice.call(table.querySelectorAll('thead th[data-sort]'));
            var tbody = table.querySelector('tbody');
            if (!headers.length || !tbody) {
                return;
            }

            headers.forEach(function (header, index) {
                header.addEventListener('click', function () {
                    var type = header.getAttribute('data-sort') || 'text';
                    var currentDir = header.getAttribute('data-sort-dir') || 'desc';
                    var nextDir = currentDir === 'asc' ? 'desc' : 'asc';

                    headers.forEach(function (item) {
                        item.classList.remove('sort-asc', 'sort-desc');
                        item.removeAttribute('data-sort-dir');
                    });

                    header.setAttribute('data-sort-dir', nextDir);
                    header.classList.add(nextDir === 'asc' ? 'sort-asc' : 'sort-desc');

                    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
                    rows.sort(function (rowA, rowB) {
                        var valueA = normalizeValue(rowA.children[index], type);
                        var valueB = normalizeValue(rowB.children[index], type);

                        if (valueA < valueB) {
                            return nextDir === 'asc' ? -1 : 1;
                        }
                        if (valueA > valueB) {
                            return nextDir === 'asc' ? 1 : -1;
                        }
                        return 0;
                    });

                    rows.forEach(function (row) {
                        tbody.appendChild(row);
                    });
                });
            });
        });
    }

    function hideSkeletons() {
        var panel = document.getElementById('smartDashboardPanel');
        if (panel) {
            panel.classList.add('is-loaded');
            var skeleton = panel.querySelector('.smart-skeleton');
            if (skeleton) {
                skeleton.remove();
            }
        }
    }

    function assistantServiceMap(panel) {
        return {
            income_certificate: {
                title: 'Income Certificate Application',
                url: panel.getAttribute('data-income-url') || '#',
                steps: [
                    'Step 1: Confirm applicant details',
                    'Step 2: Enter income and address details',
                    'Step 3: Upload required documents',
                    'Step 4: Review and submit'
                ]
            },
            birth_certificate: {
                title: 'Birth Certificate Application',
                url: panel.getAttribute('data-birth-url') || '#',
                steps: [
                    'Step 1: Fill child details',
                    'Step 2: Add parent information',
                    'Step 3: Upload proofs',
                    'Step 4: Verify and submit'
                ]
            },
            death_certificate: {
                title: 'Death Certificate Application',
                url: panel.getAttribute('data-death-url') || '#',
                steps: [
                    'Step 1: Fill deceased details',
                    'Step 2: Add informant details',
                    'Step 3: Upload documents',
                    'Step 4: Review and submit'
                ]
            },
            complaint: {
                title: 'Complaint Registration',
                url: panel.getAttribute('data-complaint-url') || '#',
                steps: [
                    'Step 1: Choose complaint category',
                    'Step 2: Describe issue clearly',
                    'Step 3: Upload evidence if available',
                    'Step 4: Submit grievance'
                ]
            },
            electricity_bill: {
                title: 'Electricity Bill Service',
                url: panel.getAttribute('data-electricity-url') || '#',
                steps: [
                    'Step 1: Enter consumer number',
                    'Step 2: Verify bill details',
                    'Step 3: Continue to payment'
                ]
            },
            water_bill: {
                title: 'Water Bill Service',
                url: panel.getAttribute('data-water-url') || '#',
                steps: [
                    'Step 1: Enter connection number',
                    'Step 2: Verify bill details',
                    'Step 3: Continue to payment'
                ]
            },
            property_tax: {
                title: 'Property Tax Service',
                url: panel.getAttribute('data-property-url') || '#',
                steps: [
                    'Step 1: Search property record',
                    'Step 2: Confirm owner and amount',
                    'Step 3: Complete payment process'
                ]
            },
            bill_request: {
                title: 'Bill Request Service',
                url: panel.getAttribute('data-bill-request-url') || '#',
                steps: [
                    'Step 1: Select request type',
                    'Step 2: Enter bill reference and details',
                    'Step 3: Submit request'
                ]
            }
        };
    }

    function detectAssistantIntent(query, panel) {
        var text = String(query || '').toLowerCase();
        var services = assistantServiceMap(panel);
        var wantsApply = /\b(apply|open|start|file|pay|submit)\b/.test(text);

        if (!wantsApply) {
            return null;
        }

        if (text.indexOf('income') !== -1 && text.indexOf('certificate') !== -1) {
            return { key: 'income_certificate', prefill: true };
        }
        if (text.indexOf('birth') !== -1 && text.indexOf('certificate') !== -1) {
            return { key: 'birth_certificate', prefill: true };
        }
        if (text.indexOf('death') !== -1 && text.indexOf('certificate') !== -1) {
            return { key: 'death_certificate', prefill: true };
        }
        if (text.indexOf('complaint') !== -1 || text.indexOf('grievance') !== -1 || text.indexOf('issue') !== -1) {
            return { key: 'complaint', prefill: true };
        }
        var hasBillKeyword = text.indexOf('bill') !== -1;
        var electricityKeywords = ['electricity', 'light', 'power', 'current'];
        var hasElectricityKeyword = electricityKeywords.some(function (word) {
            return text.indexOf(word) !== -1;
        });

        if (hasElectricityKeyword && hasBillKeyword) {
            return { key: 'electricity_bill', prefill: true };
        }
        if (text.indexOf('water') !== -1 && hasBillKeyword) {
            return { key: 'water_bill', prefill: true };
        }
        if (((text.indexOf('property') !== -1 || text.indexOf('tax') !== -1) && text.indexOf('bill') !== -1) || text.indexOf('property tax') !== -1) {
            return { key: 'property_tax', prefill: true };
        }
        if (text.indexOf('bill request') !== -1 || (text.indexOf('bill') !== -1 && text.indexOf('request') !== -1)) {
            return { key: 'bill_request', prefill: true };
        }

        return null;
    }

    function assistantPrefillPayload() {
        return {
            name: document.body.getAttribute('data-user-full-name') || document.body.getAttribute('data-user-name') || '',
            email: document.body.getAttribute('data-user-email') || '',
            phone: document.body.getAttribute('data-user-phone') || ''
        };
    }

    function renderAssistantMessage(host, text, error) {
        if (!host) {
            return;
        }
        host.textContent = text || '';
        host.style.color = error ? '#b91c1c' : '';
    }

    function openAssistantForm(intentInfo, panel) {
        var services = assistantServiceMap(panel);
        var service = services[intentInfo.key];
        if (!service || !service.url || service.url === '#') {
            return;
        }

        var frame = document.getElementById('assistantFormFrame');
        var guide = document.getElementById('assistantGuide');
        var title = document.getElementById('assistantModalTitle');
        var modalElement = document.getElementById('assistantFormModal');
        if (!frame || !modalElement || !window.bootstrap || !window.bootstrap.Modal) {
            window.location.href = service.url;
            return;
        }

        var payload = assistantPrefillPayload();
        try {
            sessionStorage.setItem('gp_assistant_prefill', JSON.stringify(payload));
            sessionStorage.setItem('gp_assistant_steps', JSON.stringify(service.steps || []));
        } catch (error) {
            // Ignore storage issues.
        }

        var joiner = service.url.indexOf('?') === -1 ? '?' : '&';
        frame.src = service.url + joiner + 'assistant=1';

        if (title) {
            title.textContent = service.title;
        }
        if (guide) {
            guide.innerHTML = '<strong>Guided steps:</strong> ' + (service.steps || []).map(function (item, index) {
                return '<span class="me-2">' + (index + 1) + '. ' + escapeHtml(item.replace(/^Step\s+\d+:\s*/i, '')) + '</span>';
            }).join('');
        }

        var modal = window.bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();
    }

    function askChatbot(panel, message) {
        var endpoint = panel.getAttribute('data-chatbot-url');
        if (!endpoint) {
            return Promise.resolve({ reply: '' });
        }

        return fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Unable to reach assistant service.');
                }
                return response.json();
            })
            .then(function (payload) {
                return {
                    reply: String(payload.reply || '').trim(),
                    action: payload.action || null
                };
            })
            .catch(function () {
                return { reply: '' };
            });
    }

    function initSmartAssistant() {
        var panel = document.getElementById('smartDashboardPanel');
        var input = document.getElementById('assistantQueryInput');
        var sendButton = document.getElementById('assistantSendBtn');
        var output = document.getElementById('assistantInlineResponse');
        var quickActions = Array.prototype.slice.call(document.querySelectorAll('[data-assist-query]'));

        if (!panel || !input || !sendButton || !output) {
            return;
        }

        function runAssistant(query) {
            var prompt = String(query || '').trim();
            if (!prompt) {
                renderAssistantMessage(output, 'Please type your request, for example: Apply income certificate.', true);
                return;
            }

            renderAssistantMessage(output, 'Processing your request...');

            var localIntent = detectAssistantIntent(prompt, panel);

            askChatbot(panel, prompt).then(function (result) {
                var backendIntent = result && result.action ? { key: result.action.service, prefill: true } : null;
                var intentToOpen = backendIntent || localIntent;

                if (intentToOpen) {
                    openAssistantForm(intentToOpen, panel);
                }

                if (result && result.reply) {
                    renderAssistantMessage(output, result.reply);
                } else if (intentToOpen) {
                    renderAssistantMessage(output, 'Opened the correct form with guided assist. I also prefilled known profile details where fields matched.');
                } else {
                    renderAssistantMessage(output, 'I can open services for certificates, bills, and complaints. Try: Apply income certificate');
                }
            });
        }

        sendButton.addEventListener('click', function () {
            runAssistant(input.value);
        });

        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                runAssistant(input.value);
            }
        });

        quickActions.forEach(function (button) {
            button.addEventListener('click', function () {
                var query = button.getAttribute('data-assist-query') || '';
                input.value = query;
                runAssistant(query);
            });
        });
    }

    function initAssistantGuidedForm() {
        var params = new URLSearchParams(window.location.search);
        if (params.get('assistant') !== '1') {
            return;
        }

        var form = document.querySelector('form[method="post"], form[action]');
        if (!form) {
            return;
        }

        var prefill = { name: '', email: '', phone: '' };
        var steps = [];

        try {
            prefill = JSON.parse(sessionStorage.getItem('gp_assistant_prefill') || '{}') || prefill;
            steps = JSON.parse(sessionStorage.getItem('gp_assistant_steps') || '[]') || [];
        } catch (error) {
            prefill = { name: '', email: '', phone: '' };
            steps = [];
        }

        var tip = document.createElement('div');
        tip.className = 'gp-assistant-tip';
        tip.innerHTML = '<strong>Smart Assistant:</strong> Required fields are highlighted. Use Next Step to jump field by field.';
        form.parentNode.insertBefore(tip, form);

        function findField(patterns, allowedTypes) {
            var fields = Array.prototype.slice.call(form.querySelectorAll('input, textarea, select'));
            return fields.find(function (field) {
                var type = (field.getAttribute('type') || '').toLowerCase();
                if (allowedTypes && allowedTypes.length && allowedTypes.indexOf(type) === -1 && type !== '') {
                    return false;
                }
                var key = ((field.name || '') + ' ' + (field.id || '') + ' ' + (field.getAttribute('placeholder') || '')).toLowerCase();
                return patterns.some(function (p) { return key.indexOf(p) !== -1; });
            });
        }

        function setIfEmpty(field, value) {
            if (!field || !value) {
                return;
            }
            if (!String(field.value || '').trim()) {
                field.value = value;
                field.dispatchEvent(new Event('input', { bubbles: true }));
                field.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }

        var nameField = findField(['full_name', 'fullname', 'applicant_name', 'name'], ['text']);
        var firstNameField = findField(['first_name', 'firstname'], ['text']);
        var lastNameField = findField(['last_name', 'lastname'], ['text']);
        var emailField = findField(['email'], ['email', 'text']);
        var phoneField = findField(['phone', 'mobile', 'contact'], ['tel', 'text', 'number']);

        if (nameField) {
            setIfEmpty(nameField, prefill.name);
        }

        if (!nameField && (firstNameField || lastNameField) && prefill.name) {
            var parts = String(prefill.name).trim().split(/\s+/);
            var first = parts.shift() || '';
            var last = parts.join(' ');
            setIfEmpty(firstNameField, first);
            setIfEmpty(lastNameField, last);
        }

        setIfEmpty(emailField, prefill.email);
        setIfEmpty(phoneField, prefill.phone);

        var requiredFields = Array.prototype.slice.call(
            form.querySelectorAll('input[required], textarea[required], select[required]')
        ).filter(function (field) {
            return field.offsetParent !== null;
        });

        requiredFields.forEach(function (field) {
            field.classList.add('gp-required-highlight');
        });

        if (requiredFields.length) {
            var controlBar = document.createElement('div');
            controlBar.style.marginTop = '0.5rem';
            controlBar.innerHTML = '' +
                '<button type="button" class="btn btn-sm btn-outline-primary me-2" id="gpPrevStep">Previous</button>' +
                '<button type="button" class="btn btn-sm btn-primary me-2" id="gpNextStep">Next Step</button>' +
                '<span class="small text-muted" id="gpStepLabel"></span>';
            tip.appendChild(controlBar);

            var current = 0;

            function focusStep(index) {
                requiredFields.forEach(function (field) {
                    field.classList.remove('gp-current-step');
                });

                current = Math.max(0, Math.min(index, requiredFields.length - 1));
                var target = requiredFields[current];
                if (!target) {
                    return;
                }

                target.classList.add('gp-current-step');
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                target.focus({ preventScroll: true });

                var stepLabel = document.getElementById('gpStepLabel');
                if (stepLabel) {
                    var stepName = target.getAttribute('placeholder') || target.name || target.id || ('Required field ' + (current + 1));
                    stepLabel.textContent = 'Step ' + (current + 1) + ' of ' + requiredFields.length + ': ' + stepName;
                }
            }

            var prevBtn = document.getElementById('gpPrevStep');
            var nextBtn = document.getElementById('gpNextStep');
            if (prevBtn) {
                prevBtn.addEventListener('click', function () {
                    focusStep(current - 1);
                });
            }
            if (nextBtn) {
                nextBtn.addEventListener('click', function () {
                    focusStep(current + 1);
                });
            }

            focusStep(0);
        }

        form.addEventListener('submit', function (event) {
            Array.prototype.slice.call(form.querySelectorAll('.gp-validation-msg')).forEach(function (node) {
                node.remove();
            });

            if (form.checkValidity()) {
                return;
            }

            event.preventDefault();

            var invalid = Array.prototype.slice.call(form.querySelectorAll(':invalid'));
            invalid.forEach(function (field) {
                var message = document.createElement('div');
                message.className = 'gp-validation-msg';
                message.textContent = field.validationMessage || 'This field is required.';
                field.parentNode.appendChild(message);
            });

            if (invalid.length) {
                invalid[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                invalid[0].focus();
            }
        });

        if (steps.length) {
            var stepsText = document.createElement('div');
            stepsText.className = 'small mt-2';
            stepsText.innerHTML = '<strong>Suggested flow:</strong> ' + steps.join(' | ');
            tip.appendChild(stepsText);
        }
    }

    function init() {
        initAssistantGuidedForm();
        animateCounters();
        buildSmartDashboard();
        initSmartAssistant();
        initBottomNav();
        initSortableTables();
        window.setTimeout(hideSkeletons, 280);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();