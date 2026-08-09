document.addEventListener('DOMContentLoaded', function () {
    var floatGroups = document.querySelectorAll('.float-group');

    floatGroups.forEach(function (group) {
        var field = group.querySelector('input, textarea, select');
        if (!field) {
            return;
        }

        var refreshState = function () {
            var value = field.value ? field.value.toString().trim() : '';
            group.classList.toggle('filled', Boolean(value));
        };

        field.addEventListener('focus', function () {
            group.classList.add('active');
        });

        field.addEventListener('blur', function () {
            group.classList.remove('active');
            refreshState();
        });

        field.addEventListener('input', refreshState);
        field.addEventListener('change', refreshState);
        refreshState();
    });

    var toggleButtons = document.querySelectorAll('[data-password-toggle]');
    toggleButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var inputId = button.getAttribute('data-password-toggle');
            var input = document.getElementById(inputId);
            var icon = button.querySelector('i');
            if (!input) {
                return;
            }

            var isPassword = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPassword ? 'text' : 'password');
            if (icon) {
                icon.classList.toggle('bi-eye');
                icon.classList.toggle('bi-eye-slash');
            }
        });
    });

    var passwordInput = document.getElementById('id_password1');
    var strengthValue = document.getElementById('passwordStrengthValue');
    var strengthText = document.getElementById('passwordStrengthText');

    var calculateStrength = function (password) {
        var score = 0;
        if (password.length >= 8) score += 1;
        if (/[A-Z]/.test(password)) score += 1;
        if (/[a-z]/.test(password)) score += 1;
        if (/\d/.test(password)) score += 1;
        if (/[^A-Za-z0-9]/.test(password)) score += 1;
        return score;
    };

    var updateStrengthUI = function () {
        if (!passwordInput || !strengthValue || !strengthText) {
            return;
        }

        var pwd = passwordInput.value || '';
        var score = calculateStrength(pwd);
        var percent = Math.min(100, (score / 5) * 100);

        strengthValue.style.width = percent + '%';

        if (score <= 1) {
            strengthValue.style.background = '#c0382b';
            strengthText.textContent = 'Strength: Weak';
        } else if (score <= 3) {
            strengthValue.style.background = '#d88a0f';
            strengthText.textContent = 'Strength: Medium';
        } else {
            strengthValue.style.background = '#16946e';
            strengthText.textContent = 'Strength: Strong';
        }

        if (!pwd.length) {
            strengthValue.style.width = '0';
            strengthText.textContent = 'Use at least 8 characters with uppercase, number, and symbol.';
        }
    };

    if (passwordInput) {
        passwordInput.addEventListener('input', updateStrengthUI);
        updateStrengthUI();
    }

    var createButton = document.getElementById('createAccountButton');
    if (createButton) {
        createButton.addEventListener('click', function (event) {
            var rect = createButton.getBoundingClientRect();
            var ripple = document.createElement('span');
            var size = Math.max(rect.width, rect.height);
            var x = event.clientX - rect.left - size / 2;
            var y = event.clientY - rect.top - size / 2;

            ripple.classList.add('ripple');
            ripple.style.width = size + 'px';
            ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';

            createButton.appendChild(ripple);
            setTimeout(function () {
                ripple.remove();
            }, 620);
        });
    }
});
