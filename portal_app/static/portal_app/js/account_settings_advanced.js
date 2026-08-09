(function () {
    var shell = document.querySelector('.settings-shell');
    if (!shell) {
        return;
    }

    var tabs = Array.prototype.slice.call(document.querySelectorAll('[data-settings-tab]'));
    var panels = Array.prototype.slice.call(document.querySelectorAll('[data-tab-panel]'));

    function setActiveTab(tabName) {
        tabs.forEach(function (button) {
            var active = button.getAttribute('data-settings-tab') === tabName;
            button.classList.toggle('active', active);
        });

        panels.forEach(function (panel) {
            var active = panel.getAttribute('data-tab-panel') === tabName;
            panel.classList.toggle('is-active', active);
        });

        shell.setAttribute('data-active-tab', tabName);
    }

    tabs.forEach(function (button) {
        button.addEventListener('click', function () {
            var tabName = button.getAttribute('data-settings-tab');
            setActiveTab(tabName);
        });
    });

    setActiveTab(shell.getAttribute('data-active-tab') || 'profile');

    var fileInput = document.querySelector('input[name="profile_photo"]');
    var preview = document.getElementById('profilePreview');
    var croppedField = document.getElementById('profilePhotoCropped');
    var cropModalElement = document.getElementById('cropperModal');
    var cropImage = document.getElementById('cropperSource');
    var applyCropButton = document.getElementById('applyCropButton');

    var cropModal = null;
    var cropper = null;

    if (cropModalElement && window.bootstrap && window.bootstrap.Modal) {
        cropModal = new window.bootstrap.Modal(cropModalElement);
    }

    function resetCropper() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
    }

    if (fileInput && preview && croppedField && cropImage && cropModal) {
        fileInput.addEventListener('change', function () {
            var file = fileInput.files && fileInput.files[0];
            if (!file) {
                return;
            }

            if (!/^image\//i.test(file.type)) {
                window.alert('Please choose a valid image file.');
                fileInput.value = '';
                return;
            }

            var reader = new FileReader();
            reader.onload = function (event) {
                cropImage.src = event.target.result;
                cropModal.show();
            };
            reader.readAsDataURL(file);
        });

        cropModalElement.addEventListener('shown.bs.modal', function () {
            resetCropper();
            cropper = new window.Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.95,
                responsive: true,
                background: false,
                guides: false,
                checkCrossOrigin: false,
            });
        });

        cropModalElement.addEventListener('hidden.bs.modal', function () {
            resetCropper();
        });

        applyCropButton.addEventListener('click', function () {
            if (!cropper) {
                return;
            }

            var canvas = cropper.getCroppedCanvas({
                width: 420,
                height: 420,
                imageSmoothingQuality: 'high',
            });

            var dataUrl = canvas.toDataURL('image/jpeg', 0.92);
            preview.src = dataUrl;
            croppedField.value = dataUrl;
            cropModal.hide();
        });
    }
})();
