document.addEventListener('DOMContentLoaded', function () {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.panel');

  // Show first panel by default
  panels[0].classList.remove('hidden');
  tabBtns[0].classList.add('bg-primary', 'text-white', 'shadow-md');

  tabBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const target = btn.getAttribute('data-target');

      // Reset all tabs
      tabBtns.forEach((tb) => {
        tb.classList.remove('bg-primary', 'text-white', 'shadow-md');
      });

      // Hide all panels
      panels.forEach((panel) => {
        panel.classList.add('hidden');
      });

      // Activate clicked tab
      btn.classList.add('bg-primary', 'text-white', 'shadow-md');

      // Show target panel
      document.querySelector(`.${target}`).classList.remove('hidden');
    });
  });
});
