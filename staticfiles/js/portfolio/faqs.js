document.addEventListener('DOMContentLoaded', function () {
  const faqItems = document.querySelectorAll('.faq-item');

  faqItems.forEach((item) => {
    const button = item.querySelector('button');
    const answer = item.querySelector('.faq-answer');
    const icon = item.querySelector('i');

    button.addEventListener('click', () => {
      const isOpen = answer.classList.contains('hidden');

      // Close all FAQs
      faqItems.forEach((otherItem) => {
        const otherAnswer = otherItem.querySelector('.faq-answer');
        const otherIcon = otherItem.querySelector('i');

        otherAnswer.classList.add('hidden');
        otherIcon.classList.remove('rotate-45');
      });

      // Toggle clicked FAQ
      if (isOpen) {
        answer.classList.remove('hidden');
        icon.classList.add('rotate-45');
      }
    });
  });
});
