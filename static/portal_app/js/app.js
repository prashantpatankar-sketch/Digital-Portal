document.addEventListener('DOMContentLoaded', () => {
    const toastElements = document.querySelectorAll('.gp-toast');
    toastElements.forEach((toastEl) => {
        const delay = parseInt(toastEl.getAttribute('data-bs-delay') || '5000', 10);
        const progress = toastEl.querySelector('.toast-progress');
        if (progress) {
            progress.style.animationDuration = `${delay}ms`;
        }
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    });

    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            document.body.classList.toggle('sidebar-collapsed');
        });
    }
});
