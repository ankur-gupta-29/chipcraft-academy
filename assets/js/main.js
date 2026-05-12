// Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
      navLinks.classList.remove('open');
    }
  });
}

// Lazy-init AdSense units that enter the viewport
if ('IntersectionObserver' in window) {
  const adObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const ins = entry.target;
        if (!ins.dataset.pushed) {
          (window.adsbygoogle = window.adsbygoogle || []).push({});
          ins.dataset.pushed = 'true';
        }
        adObserver.unobserve(ins);
      }
    });
  }, { rootMargin: '200px' });

  document.querySelectorAll('.adsbygoogle:not([data-pushed])').forEach((ins) => adObserver.observe(ins));
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', (e) => {
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// Active nav link highlight based on scroll position
const sections = document.querySelectorAll('section[id]');
if (sections.length) {
  const highlight = () => {
    const scrollY = window.scrollY;
    sections.forEach((sec) => {
      const top = sec.offsetTop - 80;
      const bottom = top + sec.offsetHeight;
      const link = document.querySelector(`.nav-links a[href="#${sec.id}"]`);
      if (link) link.classList.toggle('active', scrollY >= top && scrollY < bottom);
    });
  };
  window.addEventListener('scroll', highlight, { passive: true });
}
