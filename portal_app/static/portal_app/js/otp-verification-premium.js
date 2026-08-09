/**
 * OTP Verification Premium JavaScript
 * Handles:
 * - Digit-by-digit input with auto-focus
 * - Paste detection and auto-fill
 * - Timer countdown
 * - Resend OTP with rate limiting
 * - Form validation and submission
 * - Animations and toast notifications
 */

class OTPVerificationManager {
    constructor() {
        this.shell = document.querySelector('.otp-verification-container, .otp-shell, .gov-otp-shell');
        this.inputs = document.querySelectorAll('.otp-input');
        this.form = document.getElementById('otpForm');
        this.otpCodeInput = document.getElementById('otpCode') || document.getElementById('otpCodeHidden');
        this.otpError = document.getElementById('otpError');
        this.verifyBtn = document.getElementById('verifyBtn');
        this.resendBtn = document.getElementById('resendBtn');
        this.resendForm = document.getElementById('resendForm');
        this.toastContainer = document.getElementById('toastContainer');
        this.minutesEl = document.getElementById('minutes');
        this.secondsEl = document.getElementById('seconds');
        this.timerSection = document.querySelector('.otp-timer-section');
        this.otpLength = Number(this.shell?.dataset?.otpLength || this.inputs.length || 6);
        
        this.otpCode = '';
        this.timerInterval = null;
        this.resendCooldown = null;
        this.isSubmitting = false;
        
        this.init();
    }

    /**
     * Initialize event listeners
     */
    init() {
        // Input handling
        this.inputs.forEach((input, index) => {
            input.addEventListener('input', (e) => this.handleInput(e, index));
            input.addEventListener('keydown', (e) => this.handleKeydown(e, index));
            input.addEventListener('paste', (e) => this.handlePaste(e));
            input.addEventListener('focus', (e) => this.handleFocus(e));
        });

        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Resend button
        if (this.resendBtn) {
            this.resendBtn.addEventListener('click', (e) => this.handleResend(e));
        }

        // Start timer
        this.startTimer();
        
        // Auto-focus first input
        this.inputs[0].focus();
    }

    /**
     * Handle digit input
     */
    handleInput(e, index) {
        const input = e.target;
        const value = input.value;

        // Only allow digits
        if (!/^\d*$/.test(value)) {
            input.value = value.replace(/\D/g, '');
            return;
        }

        // Clear error message
        if (this.otpError.textContent) {
            this.otpError.textContent = '';
            this.inputs.forEach(inp => inp.classList.remove('error'));
        }

        // Move to next input
        if (value.length === 1) {
            input.classList.add('filled');
            if (index < this.inputs.length - 1) {
                this.inputs[index + 1].focus();
            }
        } else {
            input.classList.remove('filled');
        }

        // Update hidden input
        this.updateOTPCode();

        // Check if all digits are filled
        if (this.getOTPCode().length === this.otpLength) {
            this.verifyBtn.disabled = false;
        } else {
            this.verifyBtn.disabled = true;
        }
    }

    /**
     * Handle keyboard navigation
     */
    handleKeydown(e, index) {
        const input = e.target;

        switch (e.key) {
            case 'Backspace':
                e.preventDefault();
                input.value = '';
                input.classList.remove('filled');
                this.updateOTPCode();
                
                if (index > 0) {
                    this.inputs[index - 1].focus();
                }
                this.verifyBtn.disabled = true;
                break;

            case 'ArrowLeft':
                if (index > 0) {
                    this.inputs[index - 1].focus();
                }
                break;

            case 'ArrowRight':
                if (index < this.inputs.length - 1) {
                    this.inputs[index + 1].focus();
                }
                break;

            case 'Enter':
                if (this.getOTPCode().length === this.otpLength) {
                    this.form.dispatchEvent(new Event('submit'));
                }
                break;
        }
    }

    /**
     * Handle paste event - auto-fill from clipboard
     */
    handlePaste(e) {
        e.preventDefault();
        
        const pastedText = (e.clipboardData || window.clipboardData).getData('text');
        const digits = pastedText.replace(/\D/g, '').slice(0, this.otpLength);

        if (digits.length > 0) {
            this.otpError.textContent = '';
            this.inputs.forEach((input, index) => {
                input.classList.remove('error');
                if (index < digits.length) {
                    input.value = digits[index];
                    input.classList.add('filled');
                } else {
                    input.value = '';
                    input.classList.remove('filled');
                }
            });

            this.updateOTPCode();

            if (digits.length === this.otpLength) {
                this.verifyBtn.disabled = false;
                // Show toast
                this.showToast('OTP pasted successfully!', 'success');
            } else {
                this.verifyBtn.disabled = true;
            }
        }
    }

    /**
     * Handle input focus - select text
     */
    handleFocus(e) {
        e.target.select();
    }

    /**
     * Update hidden OTP code input
     */
    updateOTPCode() {
        const code = this.getOTPCode();
        this.otpCodeInput.value = code;
    }

    /**
     * Get OTP code from all inputs
     */
    getOTPCode() {
        return Array.from(this.inputs)
            .map(input => input.value)
            .join('');
    }

    /**
     * Handle form submission
     */
    async handleSubmit(e) {
        e.preventDefault();

        if (this.isSubmitting) return;

        const otpCode = this.getOTPCode();

        // Validate OTP
        if (otpCode.length !== this.otpLength) {
            this.showError('Please enter a valid 6-digit OTP');
            this.animateShake();
            return;
        }

        // Submit form
        this.isSubmitting = true;
        this.verifyBtn.disabled = true;
        this.verifyBtn.classList.add('loading');

        try {
            // Submit form to server
            const formData = new FormData(this.form);
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Success
                this.verifyBtn.classList.remove('loading');
                this.verifyBtn.classList.add('success');
                this.verifyBtn.innerHTML = '<i class="bi bi-check-circle"></i><span>OTP Verified!</span>';
                this.showToast('OTP verified successfully!', 'success');

                // Redirect after delay
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/login/';
                }, 1500);
            } else {
                // Error
                this.showError(data.message || 'OTP verification failed');
                this.animateShake();
                this.verifyBtn.classList.remove('loading');
                this.verifyBtn.disabled = false;
                this.isSubmitting = false;
            }
        } catch (error) {
            console.error('Submission error:', error);
            this.showError('An error occurred. Please try again.');
            this.animateShake();
            this.verifyBtn.classList.remove('loading');
            this.verifyBtn.disabled = false;
            this.isSubmitting = false;
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        this.otpError.textContent = message;
        this.inputs.forEach(input => input.classList.add('error'));
    }

    /**
     * Clear error message
     */
    clearError() {
        this.otpError.textContent = '';
        this.inputs.forEach(input => input.classList.remove('error'));
    }

    /**
     * Animate shake on error
     */
    animateShake() {
        const inputsContainer = document.querySelector('.otp-inputs');
        inputsContainer.style.animation = 'none';
        setTimeout(() => {
            inputsContainer.style.animation = 'shake 0.5s ease-out';
        }, 10);
    }

    /**
     * Start countdown timer
     */
    startTimer() {
        let minutes = parseInt(this.minutesEl.textContent);
        let seconds = parseInt(this.secondsEl.textContent);
        const totalSeconds = minutes * 60 + seconds;

        this.timerInterval = setInterval(() => {
            seconds--;

            if (seconds < 0) {
                minutes--;
                seconds = 59;
            }

            // Update display
            this.minutesEl.textContent = minutes;
            this.secondsEl.textContent = String(seconds).padStart(2, '0');

            // Update styling based on remaining time
            const timerCountdown = document.querySelector('.timer-countdown');
            if (minutes === 0 && seconds <= 30) {
                this.timerSection.classList.add('timer-warning');
                this.timerSection.classList.remove('timer-expired');
            }

            // Timer expired
            if (minutes === 0 && seconds === 0) {
                clearInterval(this.timerInterval);
                this.timerSection.classList.remove('timer-warning');
                this.timerSection.classList.add('timer-expired');
                this.inputs.forEach(input => input.disabled = true);
                this.verifyBtn.disabled = true;
                this.showError('OTP has expired. Please request a new one.');
                this.showToast('OTP expired!', 'error');
            }
        }, 1000);
    }

    /**
     * Handle resend OTP
     */
    async handleResend(e) {
        e.preventDefault();

        if (this.resendBtn.disabled) return;

        this.resendBtn.disabled = true;
        const originalHTML = this.resendBtn.innerHTML;

        // Loading state
        this.resendBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Sending...';

        try {
            const response = await fetch(this.resendForm?.action || window.location.href, {
                method: 'POST',
                body: this.resendForm ? new FormData(this.resendForm) : undefined,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.form.elements['csrfmiddlewaretoken'].value,
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showToast('OTP sent successfully!', 'success');
                
                // Reset timer
                clearInterval(this.timerInterval);
                let minutes = data.expiry_minutes || 10;
                let seconds = 0;
                this.minutesEl.textContent = minutes;
                this.secondsEl.textContent = '00';
                this.timerSection.classList.remove('timer-warning', 'timer-expired');
                this.startTimer();

                // Reset inputs
                this.inputs.forEach(input => {
                    input.value = '';
                    input.classList.remove('filled', 'error', 'success');
                    input.disabled = false;
                });
                this.clearError();
                this.inputs[0].focus();

                // Cooldown
                this.startResendCooldown(30);
            } else {
                this.showToast(data.message || 'Failed to resend OTP', 'error');
                this.resendBtn.disabled = false;
                this.resendBtn.innerHTML = originalHTML;
            }
        } catch (error) {
            console.error('Resend error:', error);
            this.showToast('An error occurred. Please try again.', 'error');
            this.resendBtn.disabled = false;
            this.resendBtn.innerHTML = originalHTML;
        }
    }

    /**
     * Start cooldown for resend button
     */
    startResendCooldown(seconds) {
        let remaining = seconds;
        const resendStatus = document.getElementById('resendStatus');
        const originalText = resendStatus.textContent;

        this.resendCooldown = setInterval(() => {
            remaining--;
            resendStatus.textContent = `Resend available after ${remaining}s`;

            if (remaining === 0) {
                clearInterval(this.resendCooldown);
                this.resendBtn.disabled = false;
                resendStatus.textContent = originalText;
            }
        }, 1000);
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success' ? '<i class="bi bi-check-circle"></i>' :
                     type === 'error' ? '<i class="bi bi-exclamation-circle"></i>' :
                     '<i class="bi bi-info-circle"></i>';

        toast.innerHTML = `${icon} ${message}`;

        this.toastContainer.appendChild(toast);

        // Auto-remove
        setTimeout(() => {
            toast.classList.add('exit');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }

    /**
     * Destroy and cleanup
     */
    destroy() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        if (this.resendCooldown) {
            clearInterval(this.resendCooldown);
        }
    }
}

// Initialize on DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    window.otpManager = new OTPVerificationManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.otpManager) {
        window.otpManager.destroy();
    }
});
