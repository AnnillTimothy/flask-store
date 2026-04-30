/* ============================================================
   The Bodhi Tree — main.js
   Immersive scroll engine · video/audio management · UI
   ============================================================ */

'use strict';

// ─── Loading Screen ───────────────────────────────────────────
// Only shows once per session on qualifying pages (home, experiences).
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

  const brandEl   = screen.querySelector('.loading-brand');
  const taglineEl = screen.querySelector('.loading-tagline');
  const barFill   = screen.querySelector('.loading-bar-fill');
  const barWrap   = screen.querySelector('.loading-bar');
  const counter   = document.getElementById('loading-counter');

  // Disable CSS keyframe animations — we'll drive them with GSAP
  if (barFill)   barFill.style.animation   = 'none';
  if (brandEl)   brandEl.style.animation   = 'none';
  if (taglineEl) taglineEl.style.animation = 'none';

  if (typeof gsap === 'undefined') {
    // Fallback if GSAP somehow not available
    setTimeout(() => screen.classList.add('hide'), 3200);
    setTimeout(() => { if (screen.parentNode) screen.parentNode.removeChild(screen); }, 4000);
    return;
  }

  // ── Split brand name into letter spans ──
  if (brandEl) {
    const text = brandEl.textContent.trim();
    brandEl.textContent = '';
    text.split('').forEach(ch => {
      const span = document.createElement('span');
      span.className = 'll';
      span.style.cssText = ch === ' '
        ? 'display:inline-block;width:0.28em;'
        : 'display:inline-block;';
      span.textContent = ch === ' ' ? '\u00A0' : ch;
      brandEl.appendChild(span);
    });
  }

  // ── Initial states ──
  gsap.set('.ll',      { opacity: 0, y: 28, rotateX: -40 });
  gsap.set(taglineEl,  { opacity: 0, y: 14 });
  gsap.set(barWrap,    { opacity: 0, scaleX: 0.6 });
  gsap.set(barFill,    { width: '0%' });
  if (counter) gsap.set(counter, { opacity: 0 });

  // ── Timeline ──
  const tl = gsap.timeline({
    onComplete: () => {
      // Exit: fade + scale the whole screen down
      gsap.to(screen, {
        opacity: 0,
        scale: 1.04,
        duration: 0.9,
        ease: 'power2.inOut',
        onComplete: () => {
          screen.classList.add('hide');
          if (screen.parentNode) screen.parentNode.removeChild(screen);
        }
      });
    }
  });

  tl
    // Brand letters appear one by one
    .to('.ll', {
      opacity: 1, y: 0, rotateX: 0,
      duration: 0.55, stagger: 0.07,
      ease: 'power3.out',
      transformOrigin: 'bottom center',
    }, 0.5)

    // Tagline rises in
    .to(taglineEl, {
      opacity: 1, y: 0,
      duration: 0.7, ease: 'power2.out'
    }, 1.5)

    // Loading bar appears and fills
    .to(barWrap, {
      opacity: 1, scaleX: 1,
      duration: 0.5, ease: 'power2.out'
    }, 1.9)
    .to(barFill, {
      width: '100%',
      duration: 2.0,
      ease: 'power1.inOut'
    }, 2.0)

    // Counter ticks up to 100
    .to(counter, {
      opacity: 1, duration: 0.3
    }, 2.0)
    .to({ val: 0 }, {
      val: 100,
      duration: 2.0,
      ease: 'power1.inOut',
      onUpdate: function() {
        if (counter) counter.textContent = Math.round(this.targets()[0].val);
      }
    }, 2.0)

    // Brief hold at 100
    .to({}, { duration: 0.55 })
  ;
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
  const AGE_GATE_DELAY = loadingScreen ? 5200 : 200;

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
    const emailInput = form.querySelector('input[type="email"], #popup-email-input');
    const email = emailInput ? emailInput.value.trim() : '';
    if (!email) return;

    // Submit to subscribe endpoint
    fetch('/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
      .catch(() => {}) // best-effort
      .finally(() => {
        popup.style.display = 'none';
        localStorage.setItem('bodhi_email_popup', 'subscribed');
      });
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

// ─── Audio mute toggle ────────────────────────────────────────
let _audioMuted = true; // Start muted — enable on first user click

function initAudioMuteBtn() {
  const btn  = document.getElementById('audio-mute-btn');
  const icon = document.getElementById('audio-icon');
  if (!btn) return;

  // Only show on immersive pages
  if (!document.body.classList.contains('page-immersive')) return;
  btn.style.display = 'flex';

  btn.addEventListener('click', () => {
    _audioMuted = !_audioMuted;
    if (icon) {
      icon.className = _audioMuted ? 'bi bi-volume-mute-fill' : 'bi bi-volume-up-fill';
    }
    // Control the currently active audio track
    if (window._currentAudio) {
      if (_audioMuted) {
        window._currentAudio.pause();
      } else {
        window._currentAudio.play().catch(() => {});
      }
    }
  });
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

  // Expose global for mute button
  window._currentAudio = null;

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
    if (activeIndex < scenes.length - 1) goToScene(activeIndex + 1);
  }
  function prevScene() {
    if (activeIndex > 0) goToScene(activeIndex - 1);
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
    if (window._currentAudio) {
      window._currentAudio.pause();
      window._currentAudio.currentTime = 0;
      window._currentAudio = null;
    }
    if (audioSrc) {
      const audio = new Audio(audioSrc);
      audio.volume = 0.18;
      audio.loop   = true;
      window._currentAudio = audio;
      if (!_audioMuted) {
        audio.play().catch(() => {});
      }
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
      y: 60, opacity: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: el, start: 'top 90%', toggleActions: 'play none none none' }
    });
  });
}

// ─── Store page GSAP ──────────────────────────────────────────
function initStorePage() {
  if (!document.querySelector('.store-hero')) return;
  if (typeof gsap === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);

  // Hero entrance
  const heroTitle = document.querySelector('.store-hero-title');
  const heroSub   = document.querySelector('.store-hero-sub');
  const heroEye   = document.querySelector('.store-hero-eyebrow');
  if (heroTitle) {
    const titleText = heroTitle.textContent.trim();
    heroTitle.textContent = '';
    titleText.split('').forEach(c => {
      const span = document.createElement('span');
      span.className = 'hl';
      span.style.cssText = c === ' '
        ? 'display:inline-block;width:0.2em;'
        : 'display:inline-block;';
      span.textContent = c === ' ' ? '\u00A0' : c;
      heroTitle.appendChild(span);
    });
    gsap.set('.hl', { opacity: 0, y: 40 });
    gsap.to('.hl', {
      opacity: 1, y: 0,
      duration: 0.6, stagger: 0.03,
      ease: 'power3.out',
      delay: 0.2,
    });
  }
  if (heroEye) gsap.from(heroEye, { opacity: 0, y: 20, duration: 0.6, delay: 0.1, ease: 'power2.out' });
  if (heroSub) gsap.from(heroSub, { opacity: 0, y: 20, duration: 0.6, delay: 0.5, ease: 'power2.out' });

  // Store item reveals (already handled by initProductReveal, but add stagger for grids)
  document.querySelectorAll('.store-grid').forEach(grid => {
    const items = grid.querySelectorAll('.store-item');
    gsap.from(items, {
      y: 50, opacity: 0, duration: 0.7, stagger: 0.08, ease: 'power3.out',
      scrollTrigger: { trigger: grid, start: 'top 85%', toggleActions: 'play none none none' }
    });
  });

  // Wisdom text reveals
  document.querySelectorAll('.store-wisdom').forEach(el => {
    const p = el.querySelector('.store-wisdom-text');
    const lines = el.querySelectorAll('.store-wisdom-line');
    gsap.from(lines, {
      scaleX: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: el, start: 'top 80%', toggleActions: 'play none none none' }
    });
    if (p) {
      gsap.from(p, {
        opacity: 0, y: 30, duration: 0.9, ease: 'power3.out',
        scrollTrigger: { trigger: p, start: 'top 82%', toggleActions: 'play none none none' }
      });
    }
  });

  // Editorial close
  const editClose = document.querySelector('.store-editorial-text');
  if (editClose) {
    gsap.from(editClose, {
      opacity: 0, y: 40, duration: 1.0, ease: 'power3.out',
      scrollTrigger: { trigger: editClose, start: 'top 85%', toggleActions: 'play none none none' }
    });
  }

  // Sticky filter bar
  const filterBar = document.getElementById('store-filter-bar');
  if (filterBar) {
    ScrollTrigger.create({
      trigger: filterBar,
      start: 'top top+=68',
      onEnter: () => filterBar.classList.add('is-stuck'),
      onLeaveBack: () => filterBar.classList.remove('is-stuck'),
    });
  }
}

// ─── Store category filter (AJAX — no full-page reload) ──────
function initStoreCategoryFilter() {
  const filterBar = document.getElementById('store-filter-bar');
  const area = document.getElementById('store-products-area');
  if (!filterBar || !area) return;

  function fetchProducts(url, pushState) {
    // Add ajax=1 to request a partial response
    const fetchUrl = url + (url.includes('?') ? '&' : '?') + 'ajax=1';

    // Fade out current content
    area.style.transition = 'opacity 0.18s ease';
    area.style.opacity = '0.3';

    fetch(fetchUrl, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function(r) { return r.text(); })
      .then(function(html) {
        area.innerHTML = html;
        area.style.opacity = '1';

        // Update active pill to match current URL
        const params = new URLSearchParams(url.split('?')[1] || '');
        const cat = params.get('category') || '';
        filterBar.querySelectorAll('.store-filter-pill').forEach(function(p) {
          const pParams = new URLSearchParams(p.href.split('?')[1] || '');
          const pCat = pParams.get('category') || '';
          p.classList.toggle('active', pCat === cat);
        });

        if (pushState) {
          history.pushState({ filterUrl: url }, '', url);
        }

        // Scroll products into view smoothly if needed
        const filterRect = filterBar.getBoundingClientRect();
        if (filterRect.bottom > 0) {
          const scrollTarget = window.scrollY + filterRect.bottom;
          if (window.scrollY < scrollTarget - 20) {
            window.scrollTo({ top: scrollTarget, behavior: 'smooth' });
          }
        }
      })
      .catch(function() {
        // Fallback: navigate normally
        window.location.href = url;
      });
  }

  // Intercept filter pill clicks
  filterBar.addEventListener('click', function(e) {
    const pill = e.target.closest('.store-filter-pill');
    if (!pill) return;
    e.preventDefault();
    fetchProducts(pill.href, true);
  });

  // Handle browser back / forward
  window.addEventListener('popstate', function(e) {
    fetchProducts(window.location.href, false);
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
  initAudioMuteBtn();
  initExperienceReel();
  initBundleHero();
  initProductReveal();
  initStorePage();
  initStoreCategoryFilter();
  initCookieConsent();
  initEmailPopup();
  initAiOrb();
});

// ── AI Magic Orb & Chat ─────────────────────────────────────────
function initAiOrb() {
  const orbBtn = document.getElementById('ai-orb-btn');
  const chatPopup = document.getElementById('ai-chat-popup');
  const closeBtn = document.getElementById('ai-chat-close');
  const input = document.getElementById('ai-chat-input');
  const sendBtn = document.getElementById('ai-chat-send');
  const messagesEl = document.getElementById('ai-chat-messages');

  if (!orbBtn || !chatPopup) return;

  // GSAP floating animation
  if (typeof gsap !== 'undefined') {
    gsap.to(orbBtn, {
      y: -8,
      duration: 2.4,
      ease: 'sine.inOut',
      repeat: -1,
      yoyo: true,
    });
  }

  let history = [];
  let isOpen = false;

  function openChat() {
    chatPopup.style.display = 'block';
    if (typeof gsap !== 'undefined') {
      gsap.from(chatPopup, { opacity: 0, y: 16, duration: 0.3, ease: 'power2.out' });
    }
    isOpen = true;
    input.focus();
  }

  function closeChat() {
    if (typeof gsap !== 'undefined') {
      gsap.to(chatPopup, {
        opacity: 0, y: 16, duration: 0.2, ease: 'power2.in',
        onComplete: () => { chatPopup.style.display = 'none'; chatPopup.style.opacity = 1; }
      });
    } else {
      chatPopup.style.display = 'none';
    }
    isOpen = false;
  }

  orbBtn.addEventListener('click', () => isOpen ? closeChat() : openChat());
  closeBtn.addEventListener('click', closeChat);

  function appendMsg(text, role) {
    const div = document.createElement('div');
    div.className = 'ai-chat-msg ai-chat-msg--' + (role === 'user' ? 'user' : 'bot');
    // Safely escape text then convert newlines to <br>
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/\n/g, '<br>');
    const p = document.createElement('p');
    p.innerHTML = escaped;
    div.appendChild(p);
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text || sendBtn.disabled) return;
    input.value = '';
    sendBtn.disabled = true;

    appendMsg(text, 'user');
    history.push({ role: 'user', content: text });

    const typing = appendMsg('…', 'bot');
    typing.classList.add('ai-chat-msg--typing');

    try {
      const res = await fetch('/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history }),
      });
      const data = await res.json();
      typing.remove();
      const reply = data.reply || 'Something went wrong. Please try again.';
      appendMsg(reply, 'bot');
      history.push({ role: 'assistant', content: reply });
      if (history.length > 20) history = history.slice(-16);
    } catch {
      typing.remove();
      appendMsg('A moment of stillness… please try again shortly. 🌿', 'bot');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
}
