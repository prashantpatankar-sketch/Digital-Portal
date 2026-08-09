(function () {
    'use strict';

    var body = document.body;
    var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function getStoredTheme() {
        try {
            return localStorage.getItem('gp_theme_dark');
        } catch (err) {
            return null;
        }
    }

    function saveStoredTheme(isDark) {
        try {
            localStorage.setItem('gp_theme_dark', isDark ? '1' : '0');
        } catch (err) {
            // Storage may be disabled.
        }
    }

    function updateThemeButtons(isDark) {
        document.querySelectorAll('[data-theme-toggle]').forEach(function (toggle) {
            var icon = toggle.querySelector('i');
            if (icon) {
                icon.className = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
            }
        });
    }

    function setTheme(isDark, persist) {
        body.classList.toggle('theme-dark', isDark);
        updateThemeButtons(isDark);
        if (persist !== false) {
            saveStoredTheme(isDark);
        }
        document.dispatchEvent(new CustomEvent('gp-theme-changed', { detail: { isDark: isDark } }));
    }

    function initTheme() {
        var stored = getStoredTheme();
        var prefersDark = false;
        try {
            prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        } catch (err) {
            prefersDark = false;
        }
        setTheme(stored === null ? prefersDark : stored === '1', false);
    }

    function initThemeToggles() {
        document.querySelectorAll('[data-theme-toggle]').forEach(function (toggle) {
            toggle.addEventListener('click', function () {
                setTheme(!body.classList.contains('theme-dark'));
            });
        });
    }

    function initLoader() {
        var loader = document.getElementById('pageLoader');
        if (!loader) {
            return;
        }

        var hideLoader = function () {
            loader.classList.add('hidden');
            window.setTimeout(function () {
                loader.style.display = 'none';
                body.classList.add('page-ready');
            }, 340);
        };

        if (document.readyState === 'complete') {
            hideLoader();
            return;
        }

        window.addEventListener('load', hideLoader);
    }

    function shouldTransitionLink(link) {
        if (!link || !link.href) {
            return false;
        }
        if (link.target && link.target !== '_self') {
            return false;
        }
        if (link.hasAttribute('download') || link.getAttribute('data-bs-toggle')) {
            return false;
        }

        var href = link.getAttribute('href') || '';
        if (!href || href.startsWith('#') || href.startsWith('javascript:')) {
            return false;
        }

        try {
            var targetUrl = new URL(link.href, window.location.origin);
            if (targetUrl.origin !== window.location.origin) {
                return false;
            }
            if (targetUrl.pathname === window.location.pathname && targetUrl.search === window.location.search && targetUrl.hash) {
                return false;
            }
        } catch (err) {
            return false;
        }

        return true;
    }

    function initPageTransitions() {
        if (prefersReduced) {
            body.classList.add('page-ready');
            return;
        }

        body.classList.add('page-ready');

        document.addEventListener('click', function (event) {
            if (event.defaultPrevented) {
                return;
            }

            var link = event.target.closest('a');
            if (!shouldTransitionLink(link)) {
                return;
            }

            event.preventDefault();
            body.classList.add('page-leave');
            var destination = link.href;

            window.setTimeout(function () {
                window.location.href = destination;
            }, 220);
        });
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i += 1) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function normalizeToastType(type) {
        if (!type) {
            return 'info';
        }
        var normalized = String(type).toLowerCase();
        if (normalized === 'error') {
            return 'danger';
        }
        if (['success', 'warning', 'danger', 'info', 'primary', 'secondary'].indexOf(normalized) !== -1) {
            return normalized;
        }
        return 'info';
    }

    function toastIcon(type) {
        if (type === 'success') {
            return 'check-circle-fill';
        }
        if (type === 'danger') {
            return 'x-octagon-fill';
        }
        if (type === 'warning') {
            return 'exclamation-triangle-fill';
        }
        return 'info-circle-fill';
    }

    function ensureToastStack() {
        var stack = document.getElementById('toastStack');
        if (stack) {
            return stack;
        }
        stack = document.createElement('div');
        stack.className = 'toast-container position-fixed top-0 end-0 p-3';
        stack.id = 'toastStack';
        stack.setAttribute('aria-live', 'polite');
        stack.setAttribute('aria-atomic', 'true');
        body.appendChild(stack);
        return stack;
    }

    function activateToast(toastEl, delay) {
        if (!toastEl || !window.bootstrap || !bootstrap.Toast) {
            return;
        }
        var parsedDelay = Number(delay) || Number(toastEl.getAttribute('data-bs-delay')) || 4600;
        toastEl.setAttribute('data-bs-delay', String(parsedDelay));
        toastEl.style.setProperty('--toast-delay', parsedDelay + 'ms');

        toastEl.addEventListener('hidden.bs.toast', function () {
            toastEl.remove();
        }, { once: true });

        var instance = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: parsedDelay
        });
        instance.show();
    }

    function showToast(message, type, options) {
        if (!message) {
            return;
        }
        var opts = options || {};
        var toastType = normalizeToastType(type || opts.type);
        var delay = Number(opts.delay) || 4600;
        var stack = ensureToastStack();

        var toast = document.createElement('div');
        toast.className = 'toast gp-toast align-items-center text-bg-' + toastType + ' border-0';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.setAttribute('data-bs-delay', String(delay));
        toast.innerHTML = '' +
            '<div class="d-flex align-items-start">' +
                '<div class="toast-body">' +
                    '<i class="bi bi-' + toastIcon(toastType) + ' me-2"></i>' +
                    String(message) +
                '</div>' +
            '</div>' +
            '<div class="toast-progress"></div>';

        stack.appendChild(toast);
        activateToast(toast, delay);
    }

    function initToastSystem() {
        if (!window.bootstrap || !bootstrap.Toast) {
            return;
        }

        var stack = ensureToastStack();
        stack.querySelectorAll('.gp-toast').forEach(function (toastEl) {
            var cls = toastEl.className;
            if (cls.indexOf('text-bg-danger') === -1 && cls.indexOf('text-bg-success') === -1 && cls.indexOf('text-bg-warning') === -1 && cls.indexOf('text-bg-info') === -1) {
                toastEl.classList.add('text-bg-info');
            }
            activateToast(toastEl, toastEl.getAttribute('data-bs-delay'));
        });

        document.addEventListener('gp:toast', function (event) {
            if (!event.detail) {
                return;
            }
            showToast(event.detail.message, event.detail.type, { delay: event.detail.delay });
        });

        window.GPToast = {
            show: showToast
        };

        if (body.getAttribute('data-authenticated') !== '1') {
            return;
        }

        var role = (body.getAttribute('data-user-role') || '').toLowerCase();
        var userName = body.getAttribute('data-user-name') || 'User';
        var path = window.location.pathname;
        var inDashboard = path.indexOf('/dashboard') !== -1 || path.indexOf('/staff') !== -1 || path.indexOf('/admin') !== -1;
        if (!inDashboard) {
            return;
        }

        var key = 'gp_role_toast_seen_' + role;
        try {
            if (window.sessionStorage.getItem(key) === '1') {
                return;
            }
        } catch (err) {
            // Session storage may be disabled.
        }

        var roleConfig = {
            admin: { type: 'info', message: 'Admin control center is ready. Monitor approvals and system activity.' },
            staff: { type: 'success', message: 'Staff workspace loaded. Review pending citizen requests efficiently.' },
            citizen: { type: 'info', message: 'Welcome ' + userName + '. You can apply certificates, pay bills, and file complaints.' }
        };
        var payload = roleConfig[role] || roleConfig.citizen;
        showToast(payload.message, payload.type, { delay: 4200 });

        try {
            window.sessionStorage.setItem(key, '1');
        } catch (err) {
            // no-op
        }
    }

    function initNotifications() {
        var list = document.getElementById('notificationList');
        var count = document.getElementById('notificationCount');
        var markAllBtn = document.getElementById('markAllNotifications');

        if (!list || !count) {
            return;
        }

        function renderItems(data) {
            if (!data.items || data.items.length === 0) {
                list.innerHTML = '<div class="text-center text-muted py-3 small">No notifications yet.</div>';
            } else {
                list.innerHTML = data.items.map(function (item) {
                    var safeUrl = item.target_url || '#';
                    var unreadClass = item.is_read ? '' : ' unread';
                    return '' +
                        '<a href="' + safeUrl + '" class="notification-item' + unreadClass + '" data-notification-id="' + item.id + '">' +
                            '<div class="d-flex justify-content-between align-items-start gap-2">' +
                                '<div>' +
                                    '<strong class="d-block small">' + item.title + '</strong>' +
                                    '<p class="mb-1">' + item.message + '</p>' +
                                    '<small>' + item.created_at + '</small>' +
                                '</div>' +
                            '</div>' +
                        '</a>';
                }).join('');
            }

            if (data.unread_count > 0) {
                count.textContent = data.unread_count > 99 ? '99+' : String(data.unread_count);
                count.classList.remove('d-none');
            } else {
                count.classList.add('d-none');
            }
        }

        function fetchNotifications() {
            fetch('/api/notifications/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (response) { return response.json(); })
                .then(renderItems)
                .catch(function () { /* Fail silently for robustness. */ });
        }

        list.addEventListener('click', function (event) {
            var item = event.target.closest('[data-notification-id]');
            if (!item) {
                return;
            }
            var notificationId = item.getAttribute('data-notification-id');
            fetch('/api/notifications/' + notificationId + '/read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }).catch(function () { /* no-op */ });
        });

        if (markAllBtn) {
            markAllBtn.addEventListener('click', function () {
                fetch('/api/notifications/read-all/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                    .then(function () { fetchNotifications(); })
                    .catch(function () { /* no-op */ });
            });
        }

        fetchNotifications();
        window.setInterval(fetchNotifications, 30000);
    }

    function initSmartSearch() {
        var input = document.getElementById('smartSearchInput');
        var results = document.getElementById('smartSearchResults');
        if (!input || !results) {
            return;
        }

        var debounceTimer = null;

        function hideResults() {
            results.classList.add('d-none');
            results.innerHTML = '';
        }

        function renderResults(items) {
            if (!items || items.length === 0) {
                results.innerHTML = '<div class="px-3 py-2 text-muted small">No results found.</div>';
                results.classList.remove('d-none');
                return;
            }

            results.innerHTML = items.map(function (item) {
                return '' +
                    '<a class="smart-search-item" href="' + item.url + '">' +
                        '<div class="kind">' + (item.kind || 'item') + '</div>' +
                        '<div class="fw-semibold">' + item.title + '</div>' +
                        (item.subtitle ? '<small class="text-muted">' + item.subtitle + '</small>' : '') +
                    '</a>';
            }).join('');
            results.classList.remove('d-none');
        }

        input.addEventListener('input', function () {
            var query = input.value.trim();
            if (debounceTimer) {
                window.clearTimeout(debounceTimer);
            }

            if (query.length < 2) {
                hideResults();
                return;
            }

            debounceTimer = window.setTimeout(function () {
                fetch('/api/search/?q=' + encodeURIComponent(query), {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                    .then(function (response) { return response.json(); })
                    .then(function (data) { renderResults(data.results || []); })
                    .catch(function () { hideResults(); });
            }, 220);
        });

        document.addEventListener('click', function (event) {
            if (!event.target.closest('#smartSearchInput') && !event.target.closest('#smartSearchResults')) {
                hideResults();
            }
        });
    }

    function initNavbarActiveLink() {
        var currentPath = window.location.pathname;
        document.querySelectorAll('.navbar .nav-link').forEach(function (link) {
            var href = link.getAttribute('href');
            if (!href || href === '#') {
                return;
            }
            link.classList.remove('active');

            if (href === '/' && currentPath === '/') {
                link.classList.add('active');
                return;
            }

            if (href !== '/' && currentPath.indexOf(href) === 0) {
                link.classList.add('active');
            }
        });
    }

    function initRippleEffects() {
        document.addEventListener('click', function (event) {
            var target = event.target.closest('.gp-ripple, .btn');
            if (!target) {
                return;
            }

            var rect = target.getBoundingClientRect();
            var size = Math.max(rect.width, rect.height);
            var ripple = document.createElement('span');
            ripple.className = 'gp-ripple-wave';
            ripple.style.width = size + 'px';
            ripple.style.height = size + 'px';
            ripple.style.left = (event.clientX - rect.left - (size / 2)) + 'px';
            ripple.style.top = (event.clientY - rect.top - (size / 2)) + 'px';

            target.appendChild(ripple);
            window.setTimeout(function () {
                ripple.remove();
            }, 640);
        });
    }

    initTheme();
    initThemeToggles();
    initLoader();
    initPageTransitions();
    initToastSystem();
    initNotifications();
    initSmartSearch();
    initNavbarActiveLink();
    initRippleEffects();

    window.GPTheme = {
        set: setTheme,
        toggle: function () {
            setTheme(!body.classList.contains('theme-dark'));
        },
        isDark: function () {
            return body.classList.contains('theme-dark');
        }
    };
})();
