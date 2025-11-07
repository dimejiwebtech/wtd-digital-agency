document.addEventListener('DOMContentLoaded', function () {
  const slider = document.getElementById('projects-slider');
  const container = document.getElementById('projects-container');
  const projects = document.querySelectorAll('.project-item');
  const projectCount = projects.length / 2; // Divide by 2 because we cloned them
  let currentIndex = 0;
  let isScrolling = false;

  // Enable touch scrolling
  let startX;
  let scrollLeft;
  let isDragging = false;

  container.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.pageX - container.offsetLeft;
    scrollLeft = container.scrollLeft;
  });

  container.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const x = e.pageX - container.offsetLeft;
    const walk = (x - startX) * 2;
    container.scrollLeft = scrollLeft - walk;
  });

  container.addEventListener('mouseup', () => {
    isDragging = false;
  });

  container.addEventListener('mouseleave', () => {
    isDragging = false;
  });

  // Touch events
  container.addEventListener('touchstart', (e) => {
    isDragging = true;
    startX = e.touches[0].pageX - container.offsetLeft;
    scrollLeft = container.scrollLeft;
  });

  container.addEventListener('touchmove', (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const x = e.touches[0].pageX - container.offsetLeft;
    const walk = (x - startX) * 2;
    container.scrollLeft = scrollLeft - walk;
  });

  container.addEventListener('touchend', () => {
    isDragging = false;
  });

  function scrollProjects() {
    if (isScrolling) return;

    const projectWidth = projects[0].offsetWidth + 24; // Width + gap
    currentIndex++;

    isScrolling = true;
    slider.style.transform = `translateX(-${currentIndex * projectWidth}px)`;
    slider.style.transition = 'transform 500ms ease-in-out';

    // Reset position when reaching the cloned set
    if (currentIndex >= projectCount) {
      setTimeout(() => {
        slider.style.transition = 'none';
        currentIndex = 0;
        slider.style.transform = `translateX(0)`;
        setTimeout(() => {
          slider.style.transition = 'transform 500ms ease-in-out';
          isScrolling = false;
        }, 50);
      }, 500);
    } else {
      setTimeout(() => {
        isScrolling = false;
      }, 500);
    }
  }

  // Auto scroll every 20 seconds
  setInterval(scrollProjects, 20000);

  // Handle manual scroll snap
  container.addEventListener('scroll', () => {
    if (!isDragging) {
      const projectWidth = projects[0].offsetWidth + 24;
      const scrollPos = container.scrollLeft;
      const targetIndex = Math.round(scrollPos / projectWidth);

      container.scrollTo({
        left: targetIndex * projectWidth,
        behavior: 'smooth',
      });
    }
  });
});
