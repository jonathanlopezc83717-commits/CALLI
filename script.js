/* ============================================================
   CALLI — Estudio de Arquitectura
   Interacciones · v2
   ============================================================ */

(() => {
  'use strict';

  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ----------------------------------------------------------
     1. Scroll progress bar
     ---------------------------------------------------------- */
  const scrollBar = $('#scrollBar');
  let ticking = false;
  function onScroll(){
    if (!ticking){
      requestAnimationFrame(() => {
        const h = document.documentElement;
        const max = h.scrollHeight - h.clientHeight;
        const pct = max > 0 ? h.scrollTop / max : 0;
        if (scrollBar) scrollBar.style.transform = `scaleX(${pct})`;

        // Nav state
        nav?.classList.toggle('is-scrolled', h.scrollTop > 12);

        ticking = false;
      });
      ticking = true;
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ----------------------------------------------------------
     2. Reveal on scroll (IntersectionObserver)
     ---------------------------------------------------------- */
  const revealEls = $$('.reveal');
  revealEls.forEach(el => {
    const delay = el.dataset.delay;
    if (delay) el.style.setProperty('--reveal-delay', `${delay}ms`);
  });

  if ('IntersectionObserver' in window && !reduceMotion){
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting){
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });

    revealEls.forEach(el => io.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  /* ----------------------------------------------------------
     3. Hero counter (01 / 08) tied to scroll progress
     ---------------------------------------------------------- */
  const heroCurrent = $('#heroCurrent');
  const sections = $$('main section[id]');
  if (heroCurrent && sections.length){
    const updateHeroCounter = () => {
      const triggerY = window.innerHeight * 0.45;
      let active = sections[0];
      for (const sec of sections){
        const r = sec.getBoundingClientRect();
        if (r.top <= triggerY) active = sec;
      }
      const idx = sections.indexOf(active) + 1;
      const padded = String(idx).padStart(2, '0');
      if (heroCurrent.textContent !== padded) heroCurrent.textContent = padded;
    };
    window.addEventListener('scroll', updateHeroCounter, { passive: true });
    updateHeroCounter();
  }

  /* ----------------------------------------------------------
     4. Active section in nav
     ---------------------------------------------------------- */
  const nav = $('#nav');
  const navLinks = $$('.nav__links a[data-link]');

  if ('IntersectionObserver' in window && navLinks.length){
    const linkById = new Map(navLinks.map(a => [a.getAttribute('href').slice(1), a]));
    const sectionIo = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting){
          navLinks.forEach(a => a.classList.remove('is-active'));
          const link = linkById.get(entry.target.id);
          if (link) link.classList.add('is-active');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
    sections.forEach(s => sectionIo.observe(s));
  }

  /* ----------------------------------------------------------
     5. Mobile menu
     ---------------------------------------------------------- */
  const menuBtn   = $('#menuBtn');
  const mobileNav = $('#mobileMenu');

  const closeMenu = () => {
    if (!mobileNav) return;
    mobileNav.classList.remove('is-open');
    mobileNav.setAttribute('aria-hidden', 'true');
    menuBtn?.setAttribute('aria-expanded', 'false');
    menuBtn?.setAttribute('aria-label', 'Abrir menú');
    document.documentElement.style.overflow = '';
  };

  const openMenu = () => {
    if (!mobileNav) return;
    mobileNav.classList.add('is-open');
    mobileNav.setAttribute('aria-hidden', 'false');
    menuBtn?.setAttribute('aria-expanded', 'true');
    menuBtn?.setAttribute('aria-label', 'Cerrar menú');
    document.documentElement.style.overflow = 'hidden';
  };

  menuBtn?.addEventListener('click', () => {
    if (mobileNav?.classList.contains('is-open')) closeMenu();
    else openMenu();
  });

  $$('[data-mobile-link]').forEach(a => {
    a.addEventListener('click', () => closeMenu());
  });

  // Close on ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mobileNav?.classList.contains('is-open')) closeMenu();
  });

  /* ----------------------------------------------------------
     6. Copy email button
     ---------------------------------------------------------- */
  const copyBtn = $('#copyEmail');
  const emailLink = $('#emailLink');
  const email = emailLink?.textContent.trim();

  copyBtn?.addEventListener('click', async () => {
    if (!email) return;
    try {
      await navigator.clipboard.writeText(email);
      copyBtn.classList.add('is-copied');
      setTimeout(() => copyBtn.classList.remove('is-copied'), 1800);
    } catch (err){
      // Fallback: select & execCommand
      const tmp = document.createElement('textarea');
      tmp.value = email;
      document.body.appendChild(tmp);
      tmp.select();
      try { document.execCommand('copy'); } catch (_) {}
      tmp.remove();
      copyBtn.classList.add('is-copied');
      setTimeout(() => copyBtn.classList.remove('is-copied'), 1800);
    }
  });

  /* ----------------------------------------------------------
     7. Smooth anchor scroll (with offset for fixed nav)
     ---------------------------------------------------------- */
  $$('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href').slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      const navH = nav?.offsetHeight || 0;
      const y = target.getBoundingClientRect().top + window.scrollY - navH + 1;
      window.scrollTo({ top: y, behavior: reduceMotion ? 'auto' : 'smooth' });
      // Update hash without re-jumping
      history.replaceState(null, '', `#${id}`);
    });
  });

  /* ----------------------------------------------------------
     7b. Service items (expandable details)
     ---------------------------------------------------------- */
  const serviceTriggers = $$('.service-item__trigger');

  function setServiceExpanded(trigger, expanded){
    trigger.setAttribute('aria-expanded', String(expanded));
    const panel = document.getElementById(trigger.getAttribute('aria-controls'));
    if (panel){
      panel.setAttribute('aria-hidden', String(!expanded));
    }
  }

  serviceTriggers.forEach(trigger => {
    // Initialize aria-hidden to match aria-expanded (false by default)
    const panel = document.getElementById(trigger.getAttribute('aria-controls'));
    if (panel){
      panel.setAttribute('aria-hidden', 'true');
    }

    trigger.addEventListener('click', () => {
      const expanded = trigger.getAttribute('aria-expanded') === 'true';

      // Accordion: close all other services when opening one
      if (!expanded){
        serviceTriggers.forEach(other => {
          if (other !== trigger){
            setServiceExpanded(other, false);
          }
        });
      }

      setServiceExpanded(trigger, !expanded);
    });
  });

  /* ----------------------------------------------------------
     8. Subtle parallax for hero title (desktop, no reduced motion)
     ---------------------------------------------------------- */
  if (!reduceMotion && window.matchMedia('(min-width: 720px)').matches){
    const heroTitle = $('.hero__title');
    if (heroTitle){
      let raf = false;
      const onMouse = (e) => {
        if (raf) return;
        raf = true;
        requestAnimationFrame(() => {
          const x = (e.clientX / window.innerWidth - 0.5) * 6;
          const y = (e.clientY / window.innerHeight - 0.5) * 4;
          heroTitle.style.transform = `translate(${x}px, ${y}px)`;
          raf = false;
        });
      };
      window.addEventListener('mousemove', onMouse, { passive: true });
    }
  }

  /* ----------------------------------------------------------
     9. Mode toggle (Render ↔ Plano)
     ---------------------------------------------------------- */
  const modeToggle = $('#modeToggle');
  const modeOptions = $$('.mode-toggle__option');
  const STORAGE_KEY  = 'calli-render-mode';

  function setMode(mode){
    const isPlano = mode === 'plano';
    document.body.classList.toggle('is-plano', isPlano);
    modeToggle?.setAttribute('aria-pressed', String(isPlano));
    modeToggle?.setAttribute('aria-label', isPlano ? 'Cambiar a modo render' : 'Cambiar a modo plano');
    modeOptions.forEach(o => o.classList.toggle('is-active', o.dataset.mode === mode));
    try { localStorage.setItem(STORAGE_KEY, mode); } catch(_) {}
  }

  modeToggle?.addEventListener('click', () => {
    const current = document.body.classList.contains('is-plano') ? 'plano' : 'render';
    setMode(current === 'plano' ? 'render' : 'plano');
  });

  // Allow clicking on the option labels directly too
  modeOptions.forEach(o => {
    o.addEventListener('click', (e) => {
      e.stopPropagation();
      setMode(o.dataset.mode);
    });
  });

  // Initialize from storage (with migration from old keys)
  try {
    let saved = localStorage.getItem(STORAGE_KEY);
    // Migrate old "calli-mode" values
    if (!saved){
      const old = localStorage.getItem('calli-mode');
      if (old === 'blueprint') saved = 'plano';
      else if (old === 'editorial') saved = 'render';
    }
    if (saved === 'plano' || saved === 'render') setMode(saved);
  } catch(_) {}

})();
