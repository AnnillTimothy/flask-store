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
  const delay = loadingScreen ? 3600 : 200;

  setTimeout(() => { gate.style.display = ''; }, delay);

  if (confirm) {
    confirm.addEventListener('click', () => {
      localStorage.setItem('bodhi_age_verified', 'true');
      gate.style.display = 'none';
    });
  }

  if (deny) {
    deny.addEventListener('click', () => {
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

  gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

  const scenes      = gsap.utils.toArray('.scene');
  const progressEl  = document.getElementById('scene-progress');
  const nav         = document.getElementById('main-nav');
  if (!scenes.length) return;

  let activeIndex      = 0;
  let emailPopupShown  = false;
  let currentAudio     = null;

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

  // ── Go to a scene (via dot click or keyboard) ──
  function goToScene(index) {
    if (index < 0) index = scenes.length - 1;
    if (index >= scenes.length) index = 0;
    gsap.to(window, {
      scrollTo: { y: scenes[index], autoKill: false },
      duration: 1,
      ease: 'power2.inOut'
    });
  }

  // ── Update progress dots ──
  function updateDots() {
    if (!progressEl) return;
    progressEl.querySelectorAll('.scene-dot').forEach(function(d, i) {
      d.classList.toggle('active', i === activeIndex);
    });
  }

  // ── Video play management ──
  function activateScene(scene) {
    var video = scene.querySelector('video');
    if (video) {
      video.currentTime = 0;
      video.play().catch(function() {});
    }

    // Audio
    var audioSrc = scene.dataset.audioSrc;
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
    }
    if (audioSrc) {
      var audio = new Audio(audioSrc);
      audio.volume = 0.18;
      audio.loop   = true;
      audio.play().catch(function() {});
      currentAudio = audio;
    }
  }

  function deactivateScene(scene) {
    var video = scene.querySelector('video');
    if (video) video.pause();
  }

  // ── GSAP ScrollTrigger for each scene ──
  // Animate content in/out as each scene enters/leaves
  scenes.forEach(function(scene, i) {
    var content = scene.querySelectorAll('.scene-text, .experience-title, .landing-title, .landing-eyebrow, .landing-sub, .landing-actions, .experience-eyebrow, .experience-inner');

    // Entrance animation per scene
    ScrollTrigger.create({
      trigger: scene,
      start: 'top 60%',
      end: 'bottom 40%',
      onEnter: function() { onSceneActive(i); },
      onEnterBack: function() { onSceneActive(i); },
      onLeave: function() { onSceneInactive(i); },
      onLeaveBack: function() { onSceneInactive(i); }
    });

    // Animate text elements on each scene
    if (content.length) {
      gsap.fromTo(content,
        { y: 60, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 1,
          stagger: 0.12,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: scene,
            start: 'top 80%',
            toggleActions: 'play none none reverse'
          }
        }
      );
    }
  });

  function onSceneActive(idx) {
    if (idx === activeIndex) return;
    deactivateScene(scenes[activeIndex]);
    activeIndex = idx;
    activateScene(scenes[activeIndex]);
    updateDots();

    // Trigger email popup when reaching the second experience
    if (idx >= 2 && !emailPopupShown && typeof window._showEmailPopup === 'function') {
      emailPopupShown = true;
      window._showEmailPopup();
    }
  }

  function onSceneInactive() {
    // handled by onSceneActive of the next scene
  }

  // ── GSAP snap — the core scroll-snap behavior ──
  ScrollTrigger.create({
    snap: {
      snapTo: 1 / (scenes.length - 1),
      duration: { min: 0.3, max: 0.8 },
      delay: 0.05,
      ease: 'power2.inOut'
    }
  });

  // Initial activation
  activateScene(scenes[0]);

  // Preload experience videos: make them start loading immediately
  scenes.forEach(function(scene) {
    var video = scene.querySelector('video');
    if (video) {
      video.preload = 'auto';
      video.load();
    }
  });

  // ── Keyboard navigation ──
  document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowDown' || e.key === 'PageDown') {
      e.preventDefault();
      goToScene(activeIndex + 1);
    } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
      e.preventDefault();
      goToScene(activeIndex - 1);
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
