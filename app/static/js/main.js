/* ============================================================
   The Bodhi Tree — main.js
   Immersive scroll engine · video/audio management · UI
   ============================================================ */

'use strict';

// ─── Cart badge AJAX ──────────────────────────────────────────
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

// ─── Auto-dismiss alerts ──────────────────────────────────────
function initAlerts() {
  document.querySelectorAll('.alert.alert-dismissible').forEach(el => {
    setTimeout(() => bootstrap?.Alert?.getOrCreateInstance(el)?.close(), 4500);
  });
}

// ─── Burger / mobile menu ─────────────────────────────────────
function initBurger() {
  const burger = document.getElementById('nav-burger');
  const menu   = document.getElementById('mobile-menu');
  if (!burger || !menu) return;

  burger.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    burger.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });

  // Close on link click
  menu.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      menu.classList.remove('open');
      burger.classList.remove('open');
      document.body.style.overflow = '';
    });
  });
}

// ─── Navbar opaque on scroll (non-immersive pages) ───────────
function initNavScroll() {
  const nav = document.getElementById('main-nav');
  if (!nav) return;
  const onScroll = () => {
    nav.classList.toggle('nav-opaque', window.scrollY > 80);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// ─── Immersive experience reel ────────────────────────────────
function initExperienceReel() {
  const body = document.body;
  if (!body.classList.contains('page-immersive')) return;

  // Enable scroll-snap on the html element (the actual scroll container)
  const htmlEl = document.documentElement;
  htmlEl.style.scrollSnapType  = 'y mandatory';
  htmlEl.style.overflowY       = 'scroll';

  const scenes      = Array.from(document.querySelectorAll('.scene'));
  const progressEl  = document.getElementById('scene-progress');
  const nav         = document.getElementById('main-nav');
  if (!scenes.length) return;

  let activeIndex  = 0;
  let isScrolling  = false;
  const SCROLL_CD  = 900; // ms cooldown between snaps

  // ── Build progress dots ──
  if (progressEl) {
    scenes.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.className   = 'scene-dot';
      dot.ariaLabel   = `Go to scene ${i + 1}`;
      dot.addEventListener('click', () => goToScene(i));
      progressEl.appendChild(dot);
    });
    updateDots();
  }

  // ── Active audio context ──
  let currentAudio = null;

  // ── Go to a scene ──
  function goToScene(index) {
    if (index < 0) index = scenes.length - 1;
    if (index >= scenes.length) index = 0;
    activeIndex = index;
    scenes[activeIndex].scrollIntoView({ behavior: 'smooth' });
    updateDots();
  }

  // ── Update progress dots ──
  function updateDots() {
    if (!progressEl) return;
    progressEl.querySelectorAll('.scene-dot').forEach((d, i) => {
      d.classList.toggle('active', i === activeIndex);
    });
  }

  // ── Nav visibility on immersive ──
  function updateNav(index) {
    if (!nav) return;
    // Always keep nav visible but subtle on experience scenes
    nav.style.opacity = '1';
  }

  // ── Video play management ──
  function activateScene(scene) {
    const video = scene.querySelector('video');
    if (video) {
      video.currentTime = 0;
      video.play().catch(() => {});
    }

    // Audio
    const audioSrc = scene.dataset.audioSrc;
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
    }
    if (audioSrc) {
      const audio = new Audio(audioSrc);
      audio.volume = 0.18;
      audio.loop   = true;
      audio.play().catch(() => {});
      currentAudio = audio;
    }
  }

  function deactivateScene(scene) {
    const video = scene.querySelector('video');
    if (video) video.pause();
  }

  // Initial activation
  activateScene(scenes[0]);

  // ── IntersectionObserver — detect active scene ──
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.intersectionRatio >= 0.55) {
        const idx = scenes.indexOf(entry.target);
        if (idx !== -1 && idx !== activeIndex) {
          deactivateScene(scenes[activeIndex]);
          activeIndex = idx;
          activateScene(scenes[activeIndex]);
          updateDots();
          updateNav(activeIndex);
        }
      }
    });
  }, { threshold: 0.55 });

  scenes.forEach(s => observer.observe(s));

  // ── Wheel — infinite loop ──
  window.addEventListener('wheel', (e) => {
    if (isScrolling) { e.preventDefault(); return; }

    const atLast  = activeIndex === scenes.length - 1;
    const atFirst = activeIndex === 0;

    if (e.deltaY > 0 && atLast) {
      e.preventDefault();
      isScrolling = true;
      // Instant jump to start, then re-activate
      scenes[0].scrollIntoView({ behavior: 'instant' });
      deactivateScene(scenes[activeIndex]);
      activeIndex = 0;
      activateScene(scenes[0]);
      updateDots();
      setTimeout(() => { isScrolling = false; }, SCROLL_CD);
    } else if (e.deltaY < 0 && atFirst) {
      e.preventDefault();
      isScrolling = true;
      scenes[scenes.length - 1].scrollIntoView({ behavior: 'instant' });
      deactivateScene(scenes[activeIndex]);
      activeIndex = scenes.length - 1;
      activateScene(scenes[activeIndex]);
      updateDots();
      setTimeout(() => { isScrolling = false; }, SCROLL_CD);
    }
  }, { passive: false });

  // ── Touch — infinite loop ──
  let touchStartY = 0;
  window.addEventListener('touchstart', e => {
    touchStartY = e.touches[0].clientY;
  }, { passive: true });

  window.addEventListener('touchend', e => {
    if (isScrolling) return;
    const dy = touchStartY - e.changedTouches[0].clientY;
    const atLast  = activeIndex === scenes.length - 1;
    const atFirst = activeIndex === 0;

    if (Math.abs(dy) < 30) return; // Ignore tiny swipes

    if (dy > 0 && atLast) {
      isScrolling = true;
      scenes[0].scrollIntoView({ behavior: 'instant' });
      deactivateScene(scenes[activeIndex]);
      activeIndex = 0;
      activateScene(scenes[0]);
      updateDots();
      setTimeout(() => { isScrolling = false; }, SCROLL_CD);
    } else if (dy < 0 && atFirst) {
      isScrolling = true;
      scenes[scenes.length - 1].scrollIntoView({ behavior: 'instant' });
      deactivateScene(scenes[activeIndex]);
      activeIndex = scenes.length - 1;
      activateScene(scenes[activeIndex]);
      updateDots();
      setTimeout(() => { isScrolling = false; }, SCROLL_CD);
    }
  }, { passive: true });

  // ── Keyboard navigation ──
  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'PageDown') {
      e.preventDefault();
      goToScene(activeIndex + 1);
    } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
      e.preventDefault();
      goToScene(activeIndex - 1);
    }
  });

  // ── GSAP text entrance animations ──
  if (typeof gsap !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);

    scenes.forEach(scene => {
      const texts = scene.querySelectorAll('.scene-text');
      const title = scene.querySelector('.experience-title, .landing-title');

      if (title) {
        gsap.fromTo(title,
          { y: 60, opacity: 0 },
          {
            y: 0, opacity: 1, duration: 1.2, ease: 'power3.out',
            scrollTrigger: { trigger: scene, start: 'top 80%', toggleActions: 'play none none none' }
          }
        );
      }

      if (texts.length) {
        texts.forEach((el, i) => {
          if (el === title) return;
          gsap.fromTo(el,
            { y: 40, opacity: 0 },
            {
              y: 0, opacity: 1, duration: 0.85, ease: 'power2.out',
              delay: 0.15 + i * 0.1,
              scrollTrigger: { trigger: scene, start: 'top 80%', toggleActions: 'play none none none' }
            }
          );
        });
      }
    });
  }
}

// ─── Bundle detail – hero parallax ───────────────────────────
function initBundleHero() {
  if (typeof gsap === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);

  const heroBg = document.querySelector('.bundle-hero-bg video, .bundle-hero-bg img');
  if (heroBg) {
    gsap.fromTo(heroBg,
      { scale: 1.1 },
      {
        scale: 1, ease: 'none',
        scrollTrigger: {
          trigger: '.bundle-hero',
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        }
      }
    );
  }

  // Product rows
  gsap.utils.toArray('.bundle-product-row').forEach(row => {
    gsap.from(row.children, {
      y: 60, opacity: 0, duration: 0.85, stagger: 0.12, ease: 'power3.out',
      scrollTrigger: { trigger: row, start: 'top 88%', toggleActions: 'play none none none' }
    });
  });

  // Related cards
  gsap.utils.toArray('.related-card').forEach((card, i) => {
    gsap.from(card, {
      y: 80, opacity: 0, duration: 0.8, ease: 'power3.out', delay: i * 0.1,
      scrollTrigger: { trigger: card, start: 'top 90%', toggleActions: 'play none none none' }
    });
  });
}

// ─── Product grid reveal ──────────────────────────────────────
function initProductReveal() {
  if (typeof gsap === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);
  gsap.utils.toArray('.product-reveal').forEach((el, i) => {
    gsap.from(el, {
      y: 60, opacity: 0, duration: 0.8, ease: 'power3.out', delay: i * 0.08,
      scrollTrigger: { trigger: el, start: 'top 90%', toggleActions: 'play none none none' }
    });
  });
}

// ─── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  refreshCartBadge();
  initAlerts();
  initBurger();
  initNavScroll();
  initExperienceReel();
  initBundleHero();
  initProductReveal();
});
