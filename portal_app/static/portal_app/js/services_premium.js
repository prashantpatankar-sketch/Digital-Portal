(function () {
    'use strict';

    function createRipple(event) {
        var button = event.currentTarget;
        if (!button) {
            return;
        }

        var rect = button.getBoundingClientRect();
        var ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.width = ripple.style.height = Math.max(rect.width, rect.height) + 'px';
        ripple.style.left = (event.clientX - rect.left - (Math.max(rect.width, rect.height) / 2)) + 'px';
        ripple.style.top = (event.clientY - rect.top - (Math.max(rect.width, rect.height) / 2)) + 'px';

        button.appendChild(ripple);
        window.setTimeout(function () {
            ripple.remove();
        }, 650);
    }

    function staggerCards() {
        var cards = Array.prototype.slice.call(document.querySelectorAll('.service-card-premium'));
        cards.forEach(function (card, index) {
            card.style.transitionDelay = (index * 70) + 'ms';
        });
    }

    function revealPage() {
        document.body.classList.add('services-ready');
    }

    function bindRippleButtons() {
        document.querySelectorAll('.btn-service-apply, .btn-service-secondary').forEach(function (button) {
            button.addEventListener('click', createRipple);
        });
    }

    function init() {
        staggerCards();
        bindRippleButtons();
        window.requestAnimationFrame(revealPage);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
