/* ==========================================
   PREMIUM MULTI-STEP REGISTRATION SYSTEM
   Step Logic + Auto-Save + Validation + Preview
   ========================================== */

class RegistrationForm {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.formData = {};
        this.storageKey = 'registrationFormData';
        this.fileData = null;
        
        this.init();
    }

    init() {
        this.loadStoredData();
        this.attachEventListeners();
        this.updateUI();
        this.showAutosaveIndicator();
    }

    // ==========================================
    // STORAGE & DATA MANAGEMENT
    // ==========================================

    /**
     * Load previously saved form data from localStorage
     */
    loadStoredData() {
        const stored = localStorage.getItem(this.storageKey);
        if (stored) {
            try {
                this.formData = JSON.parse(stored);
                this.restoreFormFields();
                this.showToast('Form data restored from last session', 'success');
            } catch (e) {
                console.error('Error loading stored data:', e);
                localStorage.removeItem(this.storageKey);
            }
        }
    }

    /**
     * Restore form field values from stored data
     */
    restoreFormFields() {
        // Step 1 fields
        if (this.formData.username) document.getElementById('username').value = this.formData.username;
        if (this.formData.fullname) document.getElementById('fullname').value = this.formData.fullname;
        if (this.formData.email) document.getElementById('email').value = this.formData.email;
        if (this.formData.mobile) document.getElementById('mobile').value = this.formData.mobile;
        if (this.formData.password1) document.getElementById('password1').value = this.formData.password1;
        if (this.formData.password2) document.getElementById('password2').value = this.formData.password2;

        // Step 2 fields
        if (this.formData.gender) {
            document.querySelector(`input[name="gender"][value="${this.formData.gender}"]`)?.click();
        }
        if (this.formData.dob) document.getElementById('dob').value = this.formData.dob;

        // Step 3 fields
        if (this.formData.address) document.getElementById('address').value = this.formData.address;
        if (this.formData.state) document.getElementById('state').value = this.formData.state;
        if (this.formData.district) document.getElementById('district').value = this.formData.district;
        if (this.formData.pincode) document.getElementById('pincode').value = this.formData.pincode;
    }

    /**
     * Save form data to localStorage
     */
    saveFormData() {
        this.formData = {
            username: document.getElementById('username').value.trim(),
            fullname: document.getElementById('fullname').value.trim(),
            email: document.getElementById('email').value.trim(),
            mobile: document.getElementById('mobile').value.trim(),
            password1: document.getElementById('password1').value,
            password2: document.getElementById('password2').value,
            gender: document.querySelector('input[name="gender"]:checked')?.value || '',
            dob: document.getElementById('dob').value,
            address: document.getElementById('address').value.trim(),
            state: document.getElementById('state').value.trim(),
            district: document.getElementById('district').value.trim(),
            pincode: document.getElementById('pincode').value.trim(),
        };

        localStorage.setItem(this.storageKey, JSON.stringify(this.formData));
        this.showAutosaveIndicator();
    }

    /**
     * Clear stored data
     */
    clearStoredData() {
        localStorage.removeItem(this.storageKey);
        this.formData = {};
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================

    attachEventListeners() {
        // Step navigation
        document.getElementById('nextBtn').addEventListener('click', () => this.nextStep());
        document.getElementById('prevBtn').addEventListener('click', () => this.previousStep());
        document.getElementById('editBtn').addEventListener('click', () => this.goToStep(1));

        // Form submission
        const form = document.getElementById('registrationForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // File upload
        const photoInput = document.getElementById('profilePhoto');
        if (photoInput) {
            const fileUploadArea = document.querySelector('.file-upload-area');
            
            photoInput.addEventListener('change', (e) => this.handleFileUpload(e));
            fileUploadArea.addEventListener('click', () => photoInput.click());

            // Drag and drop
            fileUploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                fileUploadArea.style.borderColor = 'var(--primary-color)';
                fileUploadArea.style.background = 'rgba(79, 70, 229, 0.05)';
            });

            fileUploadArea.addEventListener('dragleave', () => {
                fileUploadArea.style.borderColor = '';
                fileUploadArea.style.background = '';
            });

            fileUploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                fileUploadArea.style.borderColor = '';
                fileUploadArea.style.background = '';
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    photoInput.files = files;
                    this.handleFileUpload({ target: photoInput });
                }
            });
        }

        // Password toggle visibility
        document.querySelectorAll('.password-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => this.togglePassword(e));
        });

        // Password strength meter
        document.getElementById('password1')?.addEventListener('input', (e) => this.updatePasswordStrength(e));

        // Real-time auto-save
        document.querySelectorAll('.form-control, input[type="text"], input[type="email"], input[type="tel"], input[type="date"], textarea').forEach(field => {
            field.addEventListener('change', () => {
                this.saveFormData();
            });
        });

        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.saveFormData();
            });
        });

        // Real-time validation
        document.getElementById('username')?.addEventListener('blur', () => this.validateUsername());
        document.getElementById('email')?.addEventListener('blur', () => this.validateEmail());
        document.getElementById('mobile')?.addEventListener('blur', () => this.validateMobile());
        document.getElementById('password1')?.addEventListener('blur', () => this.validatePassword());
        document.getElementById('password2')?.addEventListener('blur', () => this.validateConfirmPassword());
        document.getElementById('dob')?.addEventListener('blur', () => this.validateDOB());
        document.getElementById('pincode')?.addEventListener('blur', () => this.validatePincode());
    }

    // ==========================================
    // STEP NAVIGATION
    // ==========================================

    nextStep() {
        if (!this.validateCurrentStep()) {
            return;
        }

        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.updateUI();

            if (this.currentStep === this.totalSteps) {
                this.generatePreview();
            }
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.updateUI();
        }
    }

    goToStep(step) {
        if (step >= 1 && step <= 3) {
            this.currentStep = step;
            this.updateUI();
        }
    }

    updateUI() {
        // Hide all steps
        document.querySelectorAll('.form-step').forEach(step => {
            step.classList.remove('active');
        });

        // Show current step
        document.querySelector(`.form-step[data-step="${this.currentStep}"]`)?.classList.add('active');

        // Update progress bar
        const progress = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100;
        document.getElementById('progressFill').style.width = progress + '%';

        // Update step indicators
        document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.remove('active', 'completed');
            
            if (stepNum < this.currentStep) {
                indicator.classList.add('completed');
            } else if (stepNum === this.currentStep) {
                indicator.classList.add('active');
            }
        });

        // Update buttons
        document.getElementById('prevBtn').style.display = this.currentStep > 1 ? 'inline-flex' : 'none';
        document.getElementById('nextBtn').style.display = this.currentStep < this.totalSteps ? 'inline-flex' : 'none';
        document.getElementById('editBtn').style.display = this.currentStep === this.totalSteps ? 'inline-flex' : 'none';
        document.getElementById('submitBtn').style.display = this.currentStep === this.totalSteps ? 'inline-flex' : 'none';

        // Scroll to top
        document.querySelector('.form-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ==========================================
    // VALIDATION
    // ==========================================

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                return this.validateStep1();
            case 2:
                return this.validateStep2();
            case 3:
                return this.validateStep3();
            default:
                return true;
        }
    }

    validateStep1() {
        let isValid = true;

        isValid = this.validateUsername() && isValid;
        isValid = this.validateField('fullname', 'Full name is required', 2) && isValid;
        isValid = this.validateEmail() && isValid;
        isValid = this.validateMobile() && isValid;
        isValid = this.validatePassword() && isValid;
        isValid = this.validateConfirmPassword() && isValid;

        if (!isValid) {
            this.showToast('Please correct the errors in this step', 'error');
        }

        return isValid;
    }

    validateStep2() {
        let isValid = true;
        const gender = document.querySelector('input[name="gender"]:checked');

        if (!gender) {
            this.showValidationError('gender', 'Please select your gender');
            isValid = false;
        } else {
            this.clearValidationError('gender');
        }

        isValid = this.validateDOB() && isValid;

        if (!isValid) {
            this.showToast('Please correct the errors in this step', 'error');
        }

        return isValid;
    }

    validateStep3() {
        let isValid = true;

        isValid = this.validateField('address', 'Address is required', 5) && isValid;
        isValid = this.validateField('state', 'State is required', 2) && isValid;
        isValid = this.validateField('district', 'District is required', 2) && isValid;
        isValid = this.validatePincode() && isValid;

        if (!isValid) {
            this.showToast('Please correct the errors in this step', 'error');
        }

        return isValid;
    }

    validateUsername() {
        const username = document.getElementById('username').value.trim();
        const successElem = document.getElementById('username-success');
        const errorElem = document.getElementById('username-error');

        if (!username) {
            this.showValidationError('username', 'Username is required');
            successElem?.classList.remove('show');
            return false;
        }

        if (!/^[a-zA-Z0-9_]{4,20}$/.test(username)) {
            this.showValidationError('username', 'Username must be 4-20 characters (letters, numbers, underscore)');
            successElem?.classList.remove('show');
            return false;
        }

        this.clearValidationError('username');
        successElem?.classList.add('show');
        successElem.textContent = '✓ Username available';
        return true;
    }

    validateEmail() {
        const email = document.getElementById('email').value.trim().toLowerCase();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!email) {
            this.showValidationError('email', 'Email is required');
            return false;
        }

        if (!emailRegex.test(email)) {
            this.showValidationError('email', 'Please enter a valid email address');
            return false;
        }

        this.clearValidationError('email');
        return true;
    }

    validateMobile() {
        const mobile = document.getElementById('mobile').value.trim();

        if (!mobile) {
            this.showValidationError('mobile', 'Mobile number is required');
            return false;
        }

        if (!/^\d{10}$/.test(mobile)) {
            this.showValidationError('mobile', 'Mobile number must be exactly 10 digits');
            return false;
        }

        if (!/^[6-9]/.test(mobile)) {
            this.showValidationError('mobile', 'Mobile number must start with 6, 7, 8, or 9');
            return false;
        }

        this.clearValidationError('mobile');
        return true;
    }

    validatePassword() {
        const password = document.getElementById('password1').value;
        const errorElem = document.getElementById('password1-error');

        if (!password) {
            this.showValidationError('password1', 'Password is required');
            return false;
        }

        if (password.length < 8) {
            this.showValidationError('password1', 'Password must be at least 8 characters');
            return false;
        }

        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

        if (!hasUppercase || !hasLowercase || !hasNumber) {
            this.showValidationError('password1', 'Password must include uppercase, lowercase, and number');
            return false;
        }

        this.clearValidationError('password1');
        return true;
    }

    validateConfirmPassword() {
        const password1 = document.getElementById('password1').value;
        const password2 = document.getElementById('password2').value;

        if (!password2) {
            this.showValidationError('password2', 'Please confirm your password');
            return false;
        }

        if (password1 !== password2) {
            this.showValidationError('password2', 'Passwords do not match');
            return false;
        }

        this.clearValidationError('password2');
        return true;
    }

    validateDOB() {
        const dob = document.getElementById('dob').value;

        if (!dob) {
            this.showValidationError('dob', 'Date of birth is required');
            return false;
        }

        const birthDate = new Date(dob);
        const today = new Date();
        const age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();

        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }

        if (age < 18) {
            this.showValidationError('dob', 'You must be at least 18 years old');
            return false;
        }

        this.clearValidationError('dob');
        return true;
    }

    validatePincode() {
        const pincode = document.getElementById('pincode').value.trim();

        if (!pincode) {
            this.showValidationError('pincode', 'Pincode is required');
            return false;
        }

        if (!/^\d{6}$/.test(pincode)) {
            this.showValidationError('pincode', 'Pincode must be exactly 6 digits');
            return false;
        }

        this.clearValidationError('pincode');
        return true;
    }

    validateField(fieldId, errorMsg, minLength = 1) {
        const field = document.getElementById(fieldId);
        const value = field.value.trim();

        if (!value || value.length < minLength) {
            this.showValidationError(fieldId, errorMsg);
            return false;
        }

        this.clearValidationError(fieldId);
        return true;
    }

    showValidationError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const wrapper = field?.closest('.input-wrapper') || field?.closest('.form-group');
        const errorElem = document.getElementById(`${fieldId}-error`);

        if (wrapper) {
            wrapper.classList.add('error');
            wrapper.classList.remove('success');
        }

        if (errorElem) {
            errorElem.textContent = message;
            errorElem.classList.add('show');
        }
    }

    clearValidationError(fieldId) {
        const field = document.getElementById(fieldId);
        const wrapper = field?.closest('.input-wrapper') || field?.closest('.form-group');
        const errorElem = document.getElementById(`${fieldId}-error`);

        if (wrapper) {
            wrapper.classList.remove('error');
            wrapper.classList.add('success');
        }

        if (errorElem) {
            errorElem.classList.remove('show');
        }
    }

    // ==========================================
    // PASSWORD & FILE HANDLING
    // ==========================================

    updatePasswordStrength(event) {
        const password = event.target.value;
        const strengthValue = document.getElementById('passwordStrength');
        const strengthText = document.getElementById('strengthText');

        let strength = 0;
        const checks = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
        };

        strength = Object.values(checks).filter(Boolean).length;
        const percentage = (strength / 5) * 100;

        strengthValue.style.width = percentage + '%';

        let strengthLabel = 'Weak';
        let strengthColor = '#ef4444';

        if (strength >= 4) {
            strengthLabel = 'Strong';
            strengthColor = '#10b981';
        } else if (strength >= 3) {
            strengthLabel = 'Good';
            strengthColor = '#f59e0b';
        } else if (strength >= 2) {
            strengthLabel = 'Fair';
            strengthColor = '#f59e0b';
        }

        strengthValue.style.background = strengthColor;
        strengthText.textContent = `Password strength: ${strengthLabel}`;
    }

    togglePassword(event) {
        const targetId = event.currentTarget.dataset.target;
        const field = document.getElementById(targetId);
        const icon = event.currentTarget.querySelector('i');

        if (field.type === 'password') {
            field.type = 'text';
            icon.classList.remove('bi-eye-fill');
            icon.classList.add('bi-eye-slash-fill');
        } else {
            field.type = 'password';
            icon.classList.remove('bi-eye-slash-fill');
            icon.classList.add('bi-eye-fill');
        }
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        const preview = document.getElementById('filePreview');
        const errorElem = document.getElementById('profilePhoto-error');

        if (!file) {
            preview.innerHTML = '';
            preview.classList.remove('active');
            this.fileData = null;
            return;
        }

        // Validate file
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        const maxSize = 5 * 1024 * 1024; // 5MB

        if (!validTypes.includes(file.type)) {
            this.showValidationError('profilePhoto', 'Please upload a valid image (JPEG, PNG, GIF, WebP)');
            return;
        }

        if (file.size > maxSize) {
            this.showValidationError('profilePhoto', 'Image size must be less than 5MB');
            return;
        }

        // Read and preview image
        const reader = new FileReader();
        reader.onload = (e) => {
            this.fileData = e.target.result;
            preview.innerHTML = `<img src="${this.fileData}" alt="Profile preview">`;
            preview.classList.add('active');
            this.clearValidationError('profilePhoto');
        };

        reader.readAsDataURL(file);
    }

    // ==========================================
    // PREVIEW
    // ==========================================

    generatePreview() {
        this.saveFormData();

        // Profile section
        document.getElementById('previewFullname').textContent = this.formData.fullname || '-';
        document.getElementById('previewUsername').textContent = '@' + (this.formData.username || '-');

        const genderText = {
            'male': '♂ Male',
            'female': '♀ Female',
            'other': 'Other'
        };
        document.getElementById('previewGender').textContent = genderText[this.formData.gender] || '-';

        // Profile image
        if (this.fileData) {
            document.getElementById('previewAvatar').style.display = 'none';
            document.getElementById('previewImageFile').innerHTML = `<img src="${this.fileData}" alt="Profile">`;
            document.getElementById('previewImageFile').style.display = 'block';
        } else {
            document.getElementById('previewAvatar').style.display = 'flex';
            document.getElementById('previewImageFile').style.display = 'none';
        }

        // Basic info
        document.getElementById('previewEmail').textContent = this.formData.email || '-';
        document.getElementById('previewMobile').textContent = this.formData.mobile || '-';

        // Personal details
        if (this.formData.dob) {
            const date = new Date(this.formData.dob);
            document.getElementById('previewDOB').textContent = date.toLocaleDateString('en-IN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } else {
            document.getElementById('previewDOB').textContent = '-';
        }

        // Address
        document.getElementById('previewAddress').textContent = this.formData.address || '-';
        document.getElementById('previewState').textContent = this.formData.state || '-';
        document.getElementById('previewDistrict').textContent = this.formData.district || '-';
        document.getElementById('previewPincode').textContent = this.formData.pincode || '-';
    }

    // ==========================================
    // FORM SUBMISSION
    // ==========================================

    handleSubmit(event) {
        event.preventDefault();

        // Populate hidden form fields
        document.getElementById('formUsername').value = this.formData.username;
        document.getElementById('formFullname').value = this.formData.fullname;
        document.getElementById('formEmail').value = this.formData.email;
        document.getElementById('formMobile').value = this.formData.mobile;
        document.getElementById('formPassword1').value = this.formData.password1;
        document.getElementById('formPassword2').value = this.formData.password2;
        document.getElementById('formGender').value = this.formData.gender;
        document.getElementById('formDOB').value = this.formData.dob;
        document.getElementById('formAddress').value = this.formData.address;
        document.getElementById('formState').value = this.formData.state;
        document.getElementById('formDistrict').value = this.formData.district;
        document.getElementById('formPincode').value = this.formData.pincode;

        // Handle file upload
        const photoInput = document.getElementById('profilePhoto');
        if (photoInput.files.length > 0) {
            const formData = new FormData(document.getElementById('registrationForm'));
            formData.append('profile_photo', photoInput.files[0]);
            
            // Submit with AJAX to handle file upload
            this.submitFormAjax(formData);
        } else {
            // Regular form submission
            document.getElementById('registrationForm').submit();
        }
    }

    submitFormAjax(formData) {
        const button = document.getElementById('submitBtn');
        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass me-2"></i>Submitting...';

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => {
            if (response.ok) {
                this.showToast('Registration submitted successfully! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = response.url || '/register/verify-otp/';
                }, 2000);
            } else {
                response.text().then(text => {
                    this.showToast('Error submitting form. Please try again.', 'error');
                    button.disabled = false;
                    button.innerHTML = '<i class="bi bi-check-circle me-2"></i>Confirm & Submit';
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showToast('Network error. Please try again.', 'error');
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-check-circle me-2"></i>Confirm & Submit';
        });
    }

    // ==========================================
    // UTILITIES
    // ==========================================

    showAutosaveIndicator() {
        const indicator = document.querySelector('.autosave-indicator');
        if (indicator) {
            indicator.classList.add('show');
            setTimeout(() => {
                indicator.classList.remove('show');
            }, 3000);
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-exclamation-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };

        toast.innerHTML = `
            <i class="bi ${icons[type] || icons.info}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// ==========================================
// INITIALIZE ON DOM READY
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    window.registrationForm = new RegistrationForm();

    // Handle browser back button
    window.addEventListener('beforeunload', () => {
        // Data is already saved to localStorage
    });
});
