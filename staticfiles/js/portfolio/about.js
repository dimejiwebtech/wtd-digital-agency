document.addEventListener('DOMContentLoaded', function () {
  // Stats Animation
  const stats = document.querySelectorAll('[data-target]');

  stats.forEach((stat) => {
    const target = parseInt(stat.getAttribute('data-target'));
    const increment = target / 200; // Slowed down increment

    function updateCounter() {
      const current = parseInt(stat.innerText);
      if (current < target) {
        stat.innerText = Math.ceil(current + increment);
        setTimeout(updateCounter, 100); // Increased delay
      } else {
        stat.innerText = target + '+';
      }
    }

    // Start animation when element is in view
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            updateCounter();
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );

    observer.observe(stat);
  });

  // Team Slider Touch Scroll
  const slider = document.getElementById('team-slider');
  let isDown = false;
  let startX;
  let scrollLeft;

  slider.addEventListener('mousedown', (e) => {
    isDown = true;
    startX = e.pageX - slider.offsetLeft;
    scrollLeft = slider.scrollLeft;
  });

  slider.addEventListener('mouseleave', () => {
    isDown = false;
  });

  slider.addEventListener('mouseup', () => {
    isDown = false;
  });

  slider.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - slider.offsetLeft;
    const walk = (x - startX) * 2;
    slider.scrollLeft = scrollLeft - walk;
  });
});
