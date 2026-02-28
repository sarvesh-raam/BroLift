// BroLift — Main JavaScript

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transform = 'translateX(100px)';
      flash.style.transition = 'all 0.4s ease';
      setTimeout(() => flash.remove(), 400);
    }, 5000);
  });

  // Set min datetime for all datetime-local inputs to now
  const dtInputs = document.querySelectorAll('input[type="datetime-local"]');
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  const minStr = now.toISOString().slice(0, 16);
  dtInputs.forEach(inp => { inp.min = minStr; });

  // Animate stats numbers on dashboard
  document.querySelectorAll('.stat-value').forEach(el => {
    const target = parseInt(el.textContent);
    if (!isNaN(target) && target > 0) {
      let current = 0;
      const step = Math.ceil(target / 20);
      const interval = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(interval);
      }, 40);
    }
  });
});

// Highlight active nav link
(function () {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.style.color = 'var(--text-primary)';
      link.style.fontWeight = '700';
    }
  });
})();
