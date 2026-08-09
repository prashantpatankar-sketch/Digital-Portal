(function () {
    function normalizeFloatingPlaceholders(scope) {
        var root = scope || document;
        var fields = root.querySelectorAll('.floating-field .form-control, .floating-field .form-select');

        fields.forEach(function (field) {
            if (field.tagName === 'SELECT') {
                return;
            }

            field.setAttribute('placeholder', ' ');
        });
    }

    function setFloatingState(field) {
        var wrapper = field.closest('.floating-field');
        if (!wrapper) return;

        var value = '';
        if (field.tagName === 'SELECT') {
            value = field.value || '';
        } else {
            value = (field.value || '').trim();
        }

        if (value) {
            wrapper.classList.add('is-active');
        } else {
            wrapper.classList.remove('is-active');
        }
    }

    function initFloatingFields(scope) {
        var root = scope || document;
        normalizeFloatingPlaceholders(root);
        var fields = root.querySelectorAll('.floating-field .form-control, .floating-field .form-select');
        fields.forEach(function (field) {
            setFloatingState(field);
            field.addEventListener('focus', function () {
                var wrapper = field.closest('.floating-field');
                if (wrapper) wrapper.classList.add('is-active');
            });
            field.addEventListener('blur', function () {
                setFloatingState(field);
            });
            field.addEventListener('input', function () {
                setFloatingState(field);
            });
            field.addEventListener('change', function () {
                setFloatingState(field);
            });
        });
    }

    function initPasswordToggles(scope) {
        var root = scope || document;
        var toggles = root.querySelectorAll('[data-password-toggle]');
        toggles.forEach(function (toggle) {
            toggle.addEventListener('click', function () {
                var targetId = toggle.getAttribute('data-password-toggle');
                var field = document.getElementById(targetId);
                if (!field) return;

                var icon = toggle.querySelector('i');
                var hidden = field.type === 'password';
                field.type = hidden ? 'text' : 'password';

                if (icon) {
                    icon.classList.toggle('bi-eye', !hidden);
                    icon.classList.toggle('bi-eye-slash', hidden);
                }
            });
        });
    }

    function setSubmitLoading(form, buttonId) {
        var button = document.getElementById(buttonId);
        if (!form || !button) return;

        form.addEventListener('submit', function () {
            setTimeout(function () {
                if (form.querySelector('.is-invalid')) {
                    return;
                }

                button.disabled = true;
                var text = button.querySelector('.btn-text');
                var loading = button.querySelector('.btn-loading');
                if (text) text.classList.add('d-none');
                if (loading) loading.classList.remove('d-none');
            }, 0);
        });
    }

    window.AuthPremium = {
        normalizeFloatingPlaceholders: normalizeFloatingPlaceholders,
        initFloatingFields: initFloatingFields,
        initPasswordToggles: initPasswordToggles,
        setSubmitLoading: setSubmitLoading,
    };
})();
