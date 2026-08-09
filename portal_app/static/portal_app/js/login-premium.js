document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('loginForm');

    if (!form) {
        return;
    }

    if (window.AuthPremium) {
        window.AuthPremium.initFloatingFields(form);
        window.AuthPremium.initPasswordToggles(form);
        window.AuthPremium.setSubmitLoading(form, 'loginSubmitBtn');
    }

    form.addEventListener('submit', function (event) {
        const username = document.getElementById('id_username');
        const password = document.getElementById('id_password');
        let valid = true;

        if (!username || !username.value.trim()) {
            valid = false;
            setFieldError('id_username', 'Email or username is required.');
        } else {
            clearFieldError('id_username');
        }

        if (!password || !password.value.trim()) {
            valid = false;
            setFieldError('id_password', 'Password is required.');
        } else if (password.value.length < 6) {
            valid = false;
            setFieldError('id_password', 'Enter a valid password.');
        } else {
            clearFieldError('id_password');
        }

        if (!valid) {
            event.preventDefault();
            return;
        }
    });

    form.querySelectorAll('input').forEach(function (input) {
        input.addEventListener('input', function () {
            if (this.id) {
                clearFieldError(this.id);
            }
        });
    });

    initializeAutoHideAlerts();
});

/**
 * Auto-hide alerts after 6 seconds with smooth fade out
 */
function initializeAutoHideAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            
            setTimeout(function () {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 500);
        }, 6000);
    });
}

function setFieldError(inputId, message) {
    const input = document.getElementById(inputId);
    const error = document.querySelector('[data-error-for="' + inputId + '"]');
    if (input) {
        input.classList.add('is-invalid');
    }
    if (error) {
        error.textContent = message;
        error.classList.remove('d-none');
    }
}

function clearFieldError(inputId) {
    const input = document.getElementById(inputId);
    const error = document.querySelector('[data-error-for="' + inputId + '"]');
    if (input) {
        input.classList.remove('is-invalid');
    }
    if (error) {
        error.textContent = '';
        error.classList.add('d-none');
    }
}
