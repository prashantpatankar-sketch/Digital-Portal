(function () {
    function setSubmitLoading(form) {
        if (!form) {
            return;
        }

        form.addEventListener('submit', function () {
            var submitButton = form.querySelector('[type="submit"]');
            if (!submitButton) {
                return;
            }
            submitButton.disabled = true;
            submitButton.dataset.originalText = submitButton.textContent;
            submitButton.textContent = 'Please wait...';
        });
    }

    function initPasswordToggles() {
        document.querySelectorAll('[data-toggle-target]').forEach(function (button) {
            button.addEventListener('click', function () {
                var targetId = button.getAttribute('data-toggle-target');
                var field = document.getElementById(targetId);
                if (!field) {
                    return;
                }

                var icon = button.querySelector('i');
                var isPassword = field.getAttribute('type') === 'password';
                field.setAttribute('type', isPassword ? 'text' : 'password');

                if (icon) {
                    icon.className = isPassword ? 'bi bi-eye-slash' : 'bi bi-eye';
                }

                button.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
            });
        });
    }

    function initDatePicker() {
        var dobInput = document.getElementById('id_date_of_birth');
        if (!dobInput) {
            dobInput = document.getElementById('dob');
        }
        if (!dobInput) {
            return;
        }

        try {
            var today = new Date();
            var maxDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
            dobInput.setAttribute('max', maxDate.toISOString().split('T')[0]);
        } catch (error) {
            // Keep graceful fallback.
        }

        var calendarTrigger = document.querySelector('[data-open-date-for="' + dobInput.id + '"]');
        if (calendarTrigger) {
            calendarTrigger.addEventListener('click', function () {
                dobInput.focus();
                if (typeof dobInput.showPicker === 'function') {
                    dobInput.showPicker();
                }
            });
        }
    }

    function initAutoDismissAlerts() {
        var messageBox = document.getElementById('message-box');
        if (!messageBox) {
            return;
        }

        var alerts = messageBox.querySelectorAll('.alert');
        if (!alerts.length) {
            return;
        }

        setTimeout(function () {
            alerts.forEach(function (alert) {
                alert.classList.add('fade-out');
                setTimeout(function () {
                    alert.remove();
                }, 500);
            });
        }, 3000);
    }

    document.addEventListener('DOMContentLoaded', function () {
        initPasswordToggles();
        initDatePicker();
        initAutoDismissAlerts();
        setSubmitLoading(document.getElementById('loginForm'));
        setSubmitLoading(document.getElementById('registerForm'));
    });
})();
