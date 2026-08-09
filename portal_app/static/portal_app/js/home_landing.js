(function () {
    'use strict';

    var carouselElement = document.getElementById('landingCarousel');
    if (carouselElement && window.bootstrap && bootstrap.Carousel) {
        var carousel = bootstrap.Carousel.getOrCreateInstance(carouselElement, {
            interval: 5000,
            ride: true,
            pause: 'hover',
            wrap: true
        });

        carouselElement.addEventListener('mouseenter', function () {
            carousel.pause();
        });

        carouselElement.addEventListener('mouseleave', function () {
            carousel.cycle();
        });
    }

    var sections = document.querySelectorAll('.reveal-section');
    if (sections.length) {
        var observer = new IntersectionObserver(function (entries, sectionObserver) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    sectionObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.18 });

        sections.forEach(function (section) {
            observer.observe(section);
        });
    }

    var counterValues = document.querySelectorAll('.counter-value');
    if (counterValues.length) {
        var animateCounter = function (node) {
            var target = parseInt(node.getAttribute('data-target'), 10);
            if (!target) {
                node.textContent = '0';
                return;
            }

            var duration = 1400;
            var startTime = null;

            function renderCounter(timestamp) {
                if (!startTime) {
                    startTime = timestamp;
                }
                var progress = Math.min((timestamp - startTime) / duration, 1);
                var eased = 1 - Math.pow(1 - progress, 3);
                var value = Math.floor(eased * target);
                node.textContent = value.toLocaleString();

                if (progress < 1) {
                    window.requestAnimationFrame(renderCounter);
                } else {
                    node.textContent = target.toLocaleString() + '+';
                }
            }

            window.requestAnimationFrame(renderCounter);
        };

        var counterObserver = new IntersectionObserver(function (entries, observerRef) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) {
                    return;
                }
                animateCounter(entry.target);
                observerRef.unobserve(entry.target);
            });
        }, { threshold: 0.45 });

        counterValues.forEach(function (counter) {
            counterObserver.observe(counter);
        });
    }

    var modalElement = document.getElementById('landingLoginModal');
    var modal = modalElement && window.bootstrap && bootstrap.Modal
        ? bootstrap.Modal.getOrCreateInstance(modalElement)
        : null;

    var loginTriggers = document.querySelectorAll('.open-login-modal');
    if (modal && loginTriggers.length) {
        loginTriggers.forEach(function (trigger) {
            trigger.addEventListener('click', function (event) {
                event.preventDefault();
                modal.show();
            });
        });

        // Replace navbar login navigation with modal on landing page.
        document.querySelectorAll('.navbar a[href*="/login/"]').forEach(function (navLogin) {
            navLogin.addEventListener('click', function (event) {
                event.preventDefault();
                modal.show();
            });
        });
    }

    var loginForm = document.getElementById('landingLoginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function (event) {
            var emailField = document.getElementById('id_modal_username');
            var passwordField = document.getElementById('id_modal_password');
            var emailValue = emailField ? emailField.value.trim() : '';
            var passwordValue = passwordField ? passwordField.value : '';
            var validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue);
            var validPassword = passwordValue.length >= 6;

            if (emailField) {
                emailField.classList.toggle('is-invalid', !validEmail);
            }
            if (passwordField) {
                passwordField.classList.toggle('is-invalid', !validPassword);
            }

            if (!validEmail || !validPassword) {
                event.preventDefault();
            }
        });
    }

})();
