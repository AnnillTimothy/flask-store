/* ============================================================
   The Bodhi Tree — main.js
   Immersive scroll engine · video/audio management · UI
   ============================================================ */

'use strict';

// ─── Loading Screen ───────────────────────────────────────────
// Only shows once per session on qualifying pages (home, experiences, admin).
// The loading screen element is conditionally rendered by the template.
function initLoadingScreen() {
  const screen = document.getElementById('loading-screen');
  if (!screen) return;

  // If already shown this session, remove immediately
  if (sessionStorage.getItem('bodhi_loaded')) {
    screen.parentNode.removeChild(screen);
    return;
  }

  // Mark as shown for this session
  sessionStorage.setItem('bodhi_loaded', '1');

  // Dismiss after bar animation completes (~2.6s) with a small buffer
  setTimeout(() => {
    screen.classList.add('hide');
  }, 2800);
  // Remove from DOM after transition
  setTimeout(() => {
    if (screen.parentNode) screen.parentNode.removeChild(screen);
  }, 3500);
}

// ─── Cookie Consent ───────────────────────────────────────────
function initCookieConsent() {
  const banner = document.getElementById('cookie-banner');
  const accept = document.getElementById('cookie-accept');
  const decline = document.getElementById('cookie-decline');
  if (!banner) return;

  // If user already made a choice, don't show
  if (localStorage.getItem('bodhi_cookies') !== null) return;

  // Show after a short delay so loading screen clears first
  setTimeout(() => { banner.style.display = ''; }, 3200);

  function dismiss() {
    banner.style.display = 'none';
  }
  if (accept) accept.addEventListener('click', () => {
    localStorage.setItem('bodhi_cookies', 'accepted');
    dismiss();
  });
  if (decline) decline.addEventListener('click', () => {
    localStorage.setItem('bodhi_cookies', 'declined');
    dismiss();
  });
}

// ─── Age Verification Gate ────────────────────────────────────
// Shows after loading screen, before discount popup on homepage.
function initAgeGate() {
  const gate = document.getElementById('age-gate');
  const confirm = document.getElementById('age-gate-confirm');
  const deny = document.getElementById('age-gate-deny');
  if (!gate) return;

  // Already verified
  if (localStorage.getItem('bodhi_age_verified')) return;

  // Calculate delay: show after loading screen finishes
  const loadingScreen = document.getElementById('loading-screen');
  const AGE_GATE_DELAY = loadingScreen ? 3600 : 200;

  setTimeout(() => { gate.style.display = ''; }, AGE_GATE_DELAY);

  if (confirm) {
    confirm.addEventListener('click', () => {
      localStorage.setItem('bodhi_age_verified', 'true');
      gate.style.display = 'none';
    });
  }

  if (deny) {
    deny.addEventListener('click', (e) => {
      e.preventDefault();
      // Redirect away — user is underage
      gate.querySelector('.age-gate-text').innerHTML =
        'Sorry, you must be 18 or older to access this site.';
      gate.querySelector('.age-gate-actions').style.display = 'none';
      gate.querySelector('.age-gate-deny').style.display = 'none';
    });
  }
}

// ─── Email Signup Popup ───────────────────────────────────────
function initEmailPopup() {
  const popup = document.getElementById('email-popup');
  const close = document.getElementById('email-popup-close');
  const form  = document.getElementById('email-popup-form');
  if (!popup) return;

  // Don't show if already seen
  if (localStorage.getItem('bodhi_email_popup') !== null) return;

  // This will be triggered by the experience reel when the user reaches scene 2
  window._showEmailPopup = function() {
    if (localStorage.getItem('bodhi_email_popup') !== null) return;
    // Don't show email popup until age gate is cleared
    if (!localStorage.getItem('bodhi_age_verified')) return;
    popup.style.display = '';
  };

  if (close) close.addEventListener('click', () => {
    popup.style.display = 'none';
    localStorage.setItem('bodhi_email_popup', 'dismissed');
  });

  // Close on overlay click
  popup.addEventListener('click', (e) => {
    if (e.target === popup) {
      popup.style.display = 'none';
      localStorage.setItem('bodhi_email_popup', 'dismissed');
    }
  });

  if (form) form.addEventListener('submit', (e) => {
    e.preventDefault();
    popup.style.display = 'none';
    localStorage.setItem('bodhi_email_popup', 'subscribed');
  });
}

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
  if (typeof gsap === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger, ScrollToPlugin, Observer);

  const scenes      = gsap.utils.toArray('.scene');
  const progressEl  = document.getElementById('scene-progress');
  if (!scenes.length) return;

  let activeIndex      = 0;
  let animating        = false;
  let emailPopupShown  = false;
  let currentAudio     = null;

  // Lock the page — no native scrolling
  body.style.overflow = 'hidden';
  body.style.height   = '100vh';

  // Position all scenes as stacked layers
  scenes.forEach((scene, i) => {
    gsap.set(scene, {
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100vh',
      zIndex: i === 0 ? 1 : 0,
      opacity: i === 0 ? 1 : 0,
      visibility: i === 0 ? 'visible' : 'hidden'
    });
  });

  // ── Build progress dots ──
  if (progressEl) {
    scenes.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.className = 'scene-dot';
      dot.ariaLabel = 'Go to scene ' + (i + 1);
      dot.addEventListener('click', () => goToScene(i));
      progressEl.appendChild(dot);
    });
    updateDots();
  }

  // ── Go to a specific scene ──
  function goToScene(index) {
    if (index < 0 || index >= scenes.length || index === activeIndex || animating) return;
    animating = true;

    const prevIndex = activeIndex;
    activeIndex = index;

    const tl = gsap.timeline({
      onComplete: () => {
        animating = false;
        deactivateScene(scenes[prevIndex]);
        // Hide previous scene fully
        gsap.set(scenes[prevIndex], { visibility: 'hidden', zIndex: 0 });
      }
    });

    // Bring new scene to front and animate in
    gsap.set(scenes[index], { visibility: 'visible', zIndex: 1, opacity: 0 });
    gsap.set(scenes[prevIndex], { zIndex: 0 });

    tl.to(scenes[index], {
      opacity: 1,
      duration: 0.8,
      ease: 'power2.inOut'
    }, 0);

    tl.to(scenes[prevIndex], {
      opacity: 0,
      duration: 0.6,
      ease: 'power2.in'
    }, 0);

    // Animate text content of new scene
    const content = scenes[index].querySelectorAll('.scene-text, .experience-title, .landing-title, .landing-eyebrow, .landing-sub, .landing-actions, .experience-eyebrow, .experience-inner');
    if (content.length) {
      tl.fromTo(content,
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.7, stagger: 0.08, ease: 'power3.out' },
        0.3
      );
    }

    activateScene(scenes[index]);
    updateDots();

    // Trigger email popup when reaching the second experience
    if (index >= 2 && !emailPopupShown && typeof window._showEmailPopup === 'function') {
      emailPopupShown = true;
      window._showEmailPopup();
    }
  }

  // ── Navigate next/prev ──
  function nextScene() {
    if (activeIndex < scenes.length - 1) {
      goToScene(activeIndex + 1);
    }
  }

  function prevScene() {
    if (activeIndex > 0) {
      goToScene(activeIndex - 1);
    }
  }

  // ── Update progress dots ──
  function updateDots() {
    if (!progressEl) return;
    progressEl.querySelectorAll('.scene-dot').forEach((d, i) => {
      d.classList.toggle('active', i === activeIndex);
    });
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

  // ── GSAP Observer — capture wheel, touch, keyboard ──
  Observer.create({
    type: 'wheel,touch,pointer',
    wheelSpeed: -1,
    onDown: () => prevScene(),
    onUp: () => nextScene(),
    tolerance: 50,
    preventDefault: true,
  });

  // ── Keyboard navigation ──
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'PageDown') {
      e.preventDefault();
      nextScene();
    } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
      e.preventDefault();
      prevScene();
    }
  });

  // Initial activation
  activateScene(scenes[0]);

  // Preload experience videos
  scenes.forEach((scene) => {
    const video = scene.querySelector('video');
    if (video) {
      video.preload = 'auto';
      video.load();
    }
  });
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
  initLoadingScreen();
  initAgeGate();
  refreshCartBadge();
  initAlerts();
  initBurger();
  initNavScroll();
  initExperienceReel();
  initBundleHero();
  initProductReveal();
  initCookieConsent();
  initEmailPopup();
});
