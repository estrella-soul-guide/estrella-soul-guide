(function () {
  var VIEWS = ["home", "spiritual-mentorship", "soul-journey-retreats", "water-initiation", "dragon-gate", "classes", "healing-sessions", "regression-therapy", "energy-healing", "akashic-reading", "activations", "sacred-bodywork", "becoming-a-channel", "my-timeline", "blog"], SECTIONS = {"offerings": "home", "story": "home", "testimonials": "home", "latest": "home", "post-preview": "home", "contact": "home", "email-text": "home", "gate-stage": "dragon-gate", "gate-video": "dragon-gate", "class-about": "classes", "class-list": "classes", "class-items": "classes", "lemurian": "becoming-a-channel", "post-list": "blog"};
  // Links shared from the earlier one-page site used #addresses; send them to the new pages.
  var h = decodeURIComponent(location.hash.slice(1));
  if (location.pathname === '/' && h) {
    if (h.indexOf('post-') === 0) { location.replace('/blog/' + h.slice(5) + '/'); return; }
    if (h !== 'home' && VIEWS.indexOf(h) > -1) { location.replace('/' + h + '/'); return; }
    if (SECTIONS[h] && SECTIONS[h] !== 'home') { location.replace('/' + SECTIONS[h] + '/#' + h); return; }
  }
  function closeMenu() {
    var m = document.getElementById('menu'), b = document.getElementById('menu-btn');
    if (m) { m.classList.remove('open'); b.setAttribute('aria-expanded', 'false'); }
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-act]'); if (!b) return;
    var act = b.getAttribute('data-act');
    if (act === 'menu') {
      var m = document.getElementById('menu'), open = !m.classList.contains('open');
      m.classList.toggle('open', open); b.setAttribute('aria-expanded', String(open));
    } else if (act === 'copy-email') {
      var t = 'estrellasoulguide@gmail.com';
      var reset = function () { setTimeout(function () { b.textContent = 'Copy'; }, 2000); };
      var fallback = function () {
        var el = document.getElementById('email-text'), r = document.createRange(); r.selectNodeContents(el);
        var sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); b.textContent = 'Selected'; reset();
      };
      try { navigator.clipboard.writeText(t).then(function () { b.textContent = 'Copied'; reset(); }, fallback); } catch (err) { fallback(); }
    } else if (act === 'enter-gate') {
      var stage = document.getElementById('gate-stage');
      if (!stage || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      e.preventDefault();
      if (stage.classList.contains('entering')) return;
      stage.classList.add('entering');
      var href = b.getAttribute('href');
      setTimeout(function () { location.href = href; }, 1100);
    }
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
  window.addEventListener('pageshow', function () {
    var stage = document.getElementById('gate-stage'); if (stage) stage.classList.remove('entering');
    var v = document.getElementById('gate-video'); if (v) { try { var p = v.play(); if (p && p.catch) p.catch(function () {}); } catch (err) {} }
  });
})();
