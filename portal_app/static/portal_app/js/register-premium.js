document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registerForm');
    if (!form) {
        return;
    }

    if (window.AuthPremium) {
        window.AuthPremium.initFloatingFields(form);
        window.AuthPremium.initPasswordToggles(form);
        window.AuthPremium.setSubmitLoading(form, 'createAccountButton');
    }

    initializeDateOfBirthPicker();
    initializePasswordStrength();
    initializeFieldValidation(form);
});

function initializeDateOfBirthPicker() {
    var el = document.getElementById('dob');
    if (!el) {
        el = document.getElementById('id_date_of_birth') || document.querySelector('input[name="date_of_birth"]');
    }

    if (!el) {
        return;
    }

    el.id = 'dob';
    el.setAttribute('placeholder', 'DD-MM-YYYY');
    el.setAttribute('autocomplete', 'off');

    if (!window.flatpickr || el._flatpickr) {
        return;
    }

    flatpickr(el, {
        dateFormat: 'd-m-Y',
        allowInput: true,
        maxDate: 'today',
        clickOpens: true,
    });

    el.addEventListener('click', function () {
        if (el._flatpickr) {
            el._flatpickr.open();
        }
    });

    el.addEventListener('focus', function () {
        if (el._flatpickr) {
            el._flatpickr.open();
        }
    });

    var icon = document.getElementById('dobCalendarIcon');
    if (icon) {
        icon.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            if (el._flatpickr) {
                el._flatpickr.open();
            }
        });
    }
}

function initializePasswordStrength() {
    const passwordField = document.getElementById('id_password1');
    const strengthValue = document.getElementById('passwordStrengthValue');
    const strengthText = document.getElementById('passwordStrengthText');

    if (!passwordField || !strengthValue || !strengthText) {
        return;
    }

    const updateStrength = function () {
        const password = passwordField.value;
        let score = 0;

        if (password.length >= 8) score += 25;
        if (/[A-Z]/.test(password)) score += 20;
        if (/[a-z]/.test(password)) score += 20;
        if (/\d/.test(password)) score += 20;
        if (/[^A-Za-z0-9]/.test(password)) score += 15;

        const safeScore = Math.min(score, 100);
        strengthValue.style.width = safeScore + '%';

        if (safeScore < 40) {
            strengthText.textContent = 'Weak password. Use more characters and variety.';
            return;
        }
        if (safeScore < 70) {
            strengthText.textContent = 'Moderate password. Add uppercase, numbers, and symbols.';
            return;
        }
        strengthText.textContent = 'Strong password.';
    };

    passwordField.addEventListener('input', updateStrength);
    updateStrength();
}

function initializeFieldValidation(form) {
    const watched = form.querySelectorAll('input, textarea, select');

    watched.forEach(function (field) {
        field.addEventListener('blur', function () {
            validateField(field);
        });

        field.addEventListener('input', function () {
            if (field.classList.contains('is-invalid')) {
                validateField(field);
            }
        });

        field.addEventListener('change', function () {
            validateField(field);
        });
    });

    form.addEventListener('submit', function (event) {
        let isValid = true;
        watched.forEach(function (field) {
            const ok = validateField(field);
            if (!ok) {
                isValid = false;
            }
        });

        if (!isValid) {
            event.preventDefault();
            const firstInvalid = form.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.focus();
            }
        }
    });
}

function validateField(field) {
    const name = field.getAttribute('name') || '';
    const rawValue = field.value || '';
    const value = rawValue.trim();

    if (field.closest('.flatpickr-calendar')) {
        return true;
    }

    if (field.type === 'hidden' || field.type === 'file') {
        return true;
    }

    let valid = true;
    let message = '';

    if (field.required && !value) {
        valid = false;
        message = 'This field is required.';
    }

    if (valid && name === 'email' && value) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(value)) {
            valid = false;
            message = 'Enter a valid email address.';
        }
    }

    if (valid && name === 'phone_number' && value) {
        if (!/^[6-9]\d{9}$/.test(value)) {
            valid = false;
            message = 'Enter a valid 10-digit mobile number.';
        }
    }

    if (valid && name === 'pincode' && value) {
        if (!/^\d{6}$/.test(value)) {
            valid = false;
            message = 'Enter a valid 6-digit pincode.';
        }
    }

    if (valid && name === 'password1' && value) {
        if (value.length < 8) {
            valid = false;
            message = 'Password must be at least 8 characters.';
        }
    }

    if (valid && name === 'password2' && value) {
        const pass1 = document.getElementById('id_password1');
        if (pass1 && value !== pass1.value) {
            valid = false;
            message = 'Passwords do not match.';
        }
    }

    if (valid && name === 'date_of_birth' && value) {
        const parsed = parseDob(value);
        if (!parsed) {
            valid = false;
            message = 'Use DD-MM-YYYY format.';
        } else {
            const now = new Date();
            if (parsed > now) {
                valid = false;
                message = 'Date of birth cannot be in the future.';
            } else if (calculateAge(parsed, now) < 18) {
                valid = false;
                message = 'Minimum age is 18 years.';
            }
        }
    }

    applyValidationState(field, valid, message);
    return valid;
}

function applyValidationState(field, valid, message) {
    const wrapper = field.closest('.col-md-6, .col-md-4, .col-12') || field.parentElement;
    if (!wrapper) {
        return;
    }

    let errorNode = wrapper.querySelector('.client-field-error');
    if (errorNode) {
        errorNode.remove();
    }

    if (valid) {
        field.classList.remove('is-invalid');
        return;
    }

    field.classList.add('is-invalid');
    errorNode = document.createElement('div');
    errorNode.className = 'field-error client-field-error';
    errorNode.textContent = message;
    wrapper.appendChild(errorNode);
}

function parseDob(input) {
    const value = (input || '').trim();

    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        const [y, m, d] = value.split('-').map(Number);
        const isoDate = new Date(y, m - 1, d);
        if (
            isoDate.getFullYear() === y &&
            isoDate.getMonth() === m - 1 &&
            isoDate.getDate() === d
        ) {
            return isoDate;
        }
    }

    const parts = value.split('-');
    if (parts.length !== 3) {
        return null;
    }

    const day = Number(parts[0]);
    const month = Number(parts[1]);
    const year = Number(parts[2]);
    if (!day || !month || !year) {
        return null;
    }

    const date = new Date(year, month - 1, day);
    if (
        date.getFullYear() !== year ||
        date.getMonth() !== month - 1 ||
        date.getDate() !== day
    ) {
        return null;
    }

    return date;
}

function calculateAge(dob, now) {
    let age = now.getFullYear() - dob.getFullYear();
    const monthDiff = now.getMonth() - dob.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && now.getDate() < dob.getDate())) {
        age -= 1;
    }
    return age;
}
