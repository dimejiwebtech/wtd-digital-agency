// Cursor effect
const cursor = document.createElement('div');
cursor.classList.add('cursor-dot');
document.body.appendChild(cursor);

const cursorStyle = document.createElement('style');
cursorStyle.textContent = `
                        .cursor-dot {
                        width: 20px;
                        height: 20px;
                        background: linear-gradient(45deg, #005828, #ff7800);
                        border-radius: 50%;
                        position: fixed;
                        z-index: 9999;
                        mix-blend-mode: difference;
                        transition: transform 0.1s ease;
                        opacity: 0;
                        pointer-events: none;
                        }
                        
                        .cursor-dot.active{
                        opacity: 1;}`;

document.head.appendChild(cursorStyle);

// Show Cursor only on Desktop

if (window.innerWidth > 786) {
  document.addEventListener('mousemove', (e) => {
    cursor.style.left = e.clientX - 10 + 'px';
    cursor.style.top = e.clientY - 10 + 'px';
    cursor.classList.add('active');
  });

  document.addEventListener('mouseleave', () => {
    cursor.classList.remove('active');
  });
}

// Scroll Progress
const progressBar = document.createElement('div');
progressBar.style.cssText = `
                            position: fixed;
                            top: 0;
                            left: 0;
                            width: 0%;
                            height: 2px;
                            background: linear-gradient(90deg, #005828, #ff7800);
                            z-index: 9999;
                            transition: width 0.1s ease;
                            `;
document.body.appendChild(progressBar);

window.addEventListener('scroll', () => {
  const scrollTop = window.pageYOffset;
  const docHeight = document.body.offsetHeight - window.innerHeight;
  const scrollPercent = (scrollTop / docHeight) * 100;
  progressBar.style.width = scrollPercent + '%';
});

// Mobile menu toggle
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
const menuOpen = document.getElementById('menu-open');
const menuClose = document.getElementById('menu-close');

mobileMenuBtn.addEventListener('click', () => {
  mobileMenu.classList.toggle('hidden');
  menuOpen.classList.toggle('hidden');
  menuClose.classList.toggle('hidden');
});

// Mobile dropdowns
const mobileBlogToggle = document.getElementById('mobile-blog-toggle');
const mobileBlogMenu = document.getElementById('mobile-blog-menu');
const blogArrow = document.getElementById('blog-arrow');

const mobileServicesToggle = document.getElementById('mobile-services-toggle');
const mobileServicesMenu = document.getElementById('mobile-services-menu');
const servicesArrow = document.getElementById('services-arrow');

mobileBlogToggle.addEventListener('click', () => {
  mobileBlogMenu.classList.toggle('hidden');
  blogArrow.classList.toggle('rotate-180');
});

mobileServicesToggle.addEventListener('click', () => {
  mobileServicesMenu.classList.toggle('hidden');
  servicesArrow.classList.toggle('rotate-180');
});

// Back to Top
const backToTopBtn = document.getElementById('back-to-top');

window.addEventListener('scroll', () => {
  if (window.scrollY > 300) {
    backToTopBtn.classList.remove('opacity-0', 'invisible');
  } else {
    backToTopBtn.classList.add('opacity-0', 'invisible');
  }
});

backToTopBtn.addEventListener('click', () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  });
});

// Changing Words
const wordConfig = [
  { word: 'Websites', prefix: 'Build', showAmazing: true },
  { word: 'Mobile Apps', prefix: 'Build', showAmazing: true },
  { word: 'Solutions', prefix: 'Offer', showAmazing: true },
  { word: 'Experiences', prefix: 'Offer Unique', showAmazing: false },
  { word: 'Brands', prefix: 'Build', showAmazing: true },
];

let currentIndex = 0;
const changingWord = document.getElementById('changing-word');
changingWord.style.transition =
  'opacity 0.3s ease-in-out, transform 0.3s ease-in-out';

function changeWord() {
  changingWord.style.opacity = '0';
  changingWord.style.transform = 'translateY(-10px)';

  setTimeout(() => {
    currentIndex = (currentIndex + 1) % wordConfig.length;
    const config = wordConfig[currentIndex];

    // Update the main heading text based on the current word
    const h1Element = changingWord.closest('h1');
    h1Element.childNodes[0].textContent = `We ${config.prefix} ${
      config.showAmazing ? 'Amazing ' : ''
    }`;

    changingWord.textContent = config.word;
    changingWord.style.opacity = '1';
    changingWord.style.transform = 'translateY(0)';
  }, 300);
}

setInterval(changeWord, 2500);
