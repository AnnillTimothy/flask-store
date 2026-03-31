/* The Bodhi Tree – main.js
   GSAP ScrollTrigger animations + cart badge
   ------------------------------------------------ */

// ---- Cart badge AJAX (preserved) ----
function refreshCartBadge() {
  fetch('/cart/count')
    .then(r => r.json())
    .then(data => {
      const badge = document.getElementById('cart-badge');
      if (!badge) return;
      if (data.count > 0) {
        badge.textContent = data.count;
        badge.style.display = '';
      } else {
        badge.style.display = 'none';
      }
    })
    .catch(() => {});
}

document.addEventListener('DOMContentLoaded', refreshCartBadge);

// Auto-dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert.alert-dismissible').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 4000);
  });
});

// ---- GSAP ScrollTrigger animations ----
document.addEventListener('DOMContentLoaded', () => {
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  /* --- Landing scene entrance --- */
  const landingTitle = document.getElementById('landing-title');
  const landingSub   = document.getElementById('landing-subtitle');
  const scrollInd    = document.getElementById('scroll-indicator');

  if (landingTitle) {
    const tlLanding = gsap.timeline({ delay: 0.3 });
    tlLanding
      .from(landingTitle, { y: 40, opacity: 0, duration: 1.2, ease: 'power3.out' })
      .from(landingSub,   { y: 30, opacity: 0, duration: 0.8, ease: 'power3.out' }, '-=0.6')
      .from(scrollInd,    { opacity: 0, duration: 0.6 }, '-=0.3');
  }

  /* --- Landing parallax fade on scroll --- */
  const sceneLanding = document.getElementById('scene-landing');
  if (sceneLanding) {
    gsap.to(sceneLanding.querySelector('.scene-content'), {
      y: -80,
      opacity: 0,
      ease: 'none',
      scrollTrigger: {
        trigger: sceneLanding,
        start: 'top top',
        end: 'bottom top',
        scrub: true,
      },
    });
  }

  /* --- Experience scenes: pin + animate text --- */
  document.querySelectorAll('.scene-experience').forEach((scene) => {
    const texts = scene.querySelectorAll('.scene-text');
    const bgImg = scene.querySelector('.scene-bg-image');

    // Pin scene during scroll
    ScrollTrigger.create({
      trigger: scene,
      start: 'top top',
      end: '+=100%',
      pin: true,
      pinSpacing: true,
    });

    // Animate text elements in sequence
    if (texts.length) {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: scene,
          start: 'top 80%',
          end: 'top 10%',
          scrub: 1,
        },
      });
      texts.forEach((el, i) => {
        tl.from(el, {
          y: 50,
          opacity: 0,
          duration: 0.5,
          ease: 'power2.out',
        }, i * 0.15);
      });
    }

    // Background parallax
    if (bgImg) {
      gsap.fromTo(bgImg,
        { scale: 1.15 },
        {
          scale: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: scene,
            start: 'top bottom',
            end: 'bottom top',
            scrub: true,
          },
        }
      );
    }
  });

  /* --- Featured products reveal --- */
  gsap.utils.toArray('.product-reveal').forEach((el, i) => {
    gsap.from(el, {
      y: 60,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: el,
        start: 'top 90%',
        toggleActions: 'play none none none',
      },
      delay: i * 0.08,
    });
  });

  /* --- Bundle detail hero parallax --- */
  const bundleHeroBg = document.querySelector('.bundle-hero-bg img');
  if (bundleHeroBg) {
    gsap.fromTo(bundleHeroBg,
      { scale: 1.15 },
      {
        scale: 1,
        ease: 'none',
        scrollTrigger: {
          trigger: '.bundle-hero',
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      }
    );
  }

  /* --- Bundle product rows stagger in --- */
  gsap.utils.toArray('.bundle-product-row').forEach((row) => {
    gsap.from(row.children, {
      y: 60,
      opacity: 0,
      duration: 0.8,
      stagger: 0.15,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: row,
        start: 'top 85%',
        toggleActions: 'play none none none',
      },
    });
  });

  /* --- Related bundles reveal --- */
  gsap.utils.toArray('.related-card').forEach((card, i) => {
    gsap.from(card, {
      y: 80,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: card,
        start: 'top 90%',
        toggleActions: 'play none none none',
      },
      delay: i * 0.1,
    });
  });

  /* --- Navbar background on scroll --- */
  ScrollTrigger.create({
    start: 100,
    onEnter: () => {
      document.getElementById('main-nav')?.classList.add('nav-scrolled');
    },
    onLeaveBack: () => {
      document.getElementById('main-nav')?.classList.remove('nav-scrolled');
    },
  });
});
