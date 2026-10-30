#!/usr/bin/env python3
"""Build the live, search-friendly Estrella Soul Guide site.

The design and all content live in src/estrella-site.html (the same file that is
published as the Claude preview). That file is a one-page app that switches
sections with #hash links. This script loads it in a headless browser, renders
every section and blog post, and writes each one out as its own static page
with its own address, title, description and structured data.

Run from anywhere:  python3 src/build.py
Needs: Python 3, Pillow-free, playwright with Chromium.
"""
import base64, hashlib, html, json, os, re, shutil, sys
if not sys.flags.utf8_mode:  # read and write every file as UTF-8, whatever the machine's settings
    os.execv(sys.executable, [sys.executable, '-X', 'utf8'] + sys.argv)
from datetime import date
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src' / 'estrella-site.html'
SITE = 'https://estrellasoulguide.com'
BRAND = 'Estrella Soul Guide'
EMAIL = 'estrellasoulguide@gmail.com'
TODAY = date.today().isoformat()

# Search titles and descriptions for each page (posts get theirs from the post).
SEO = {
    'home': ('Estrella Soul Guide | Spiritual Mentorship & Soul Healing with Genevieve Ivey',
             'Journey to the true nature of your soul with Genevieve Ivey, Soul Guide. Spiritual mentorship, regression, energy healing, Water Initiation and private retreats in Sedona, AZ.'),
    'spiritual-mentorship': ('Spiritual Mentorship | Estrella Soul Guide',
             '1:1 spiritual mentorship with Genevieve Ivey: guidance on the spiritual path, healing from trauma, and purifying your psychic gifts. Online, by phone, or in Sedona, AZ.'),
    'healing-sessions': ('Healing Sessions & Prices | Estrella Soul Guide',
             'Regression therapy, quantum energy healing, Akashic readings, activations and sacred bodywork with Genevieve Ivey. Online, in Sedona, AZ, and in Nevada City, CA.'),
    'regression-therapy': ('Regression Therapy & Quantum Soul Regression | Estrella Soul Guide',
             'Heal trauma and work with your shadow through channeled regression, the Akashic Records and soul retrieval, with 15 years of experience. Online or in person.'),
    'energy-healing': ('Multidimensional Energy Healing | Estrella Soul Guide',
             'Channeled quantum energy healing with your guides, angels and soul. Release stress and trauma, anchor your spirit in your body, and activate your gifts.'),
    'akashic-reading': ('Soul Connection Akashic Reading: Twin Flames & Soulmates | Estrella Soul Guide',
             'Insight and healing for twin flame, divine counterpart, soulmate and karmic relationships through the Akashic Records. A one-hour reading, available online.'),
    'activations': ('Energy Upgrades & Tree of Life Activations | Estrella Soul Guide',
             'Channeled Soul Activations, the Crystal Heart Activation, and the 13-week Tree of Life Activation series with the Elohim. In person or through Zoom.'),
    'sacred-bodywork': ('Sacred Bodywork & Sound Healing in Nevada City, CA | Estrella Soul Guide',
             'Intuitive massage, sound healing, craniosacral therapy, cupping and hot medicine stone ceremony with Genevieve Ivey, in person in Nevada City, California.'),
    'soul-journey-retreats': ('Private Soul Journey Retreats in Sedona, AZ | Estrella Soul Guide',
             'Private healing retreats in the vortex energy of Sedona, Arizona, with your own private casita. Renew your inner guidance and embody your true being.'),
    'water-initiation': ('Water Initiation Ceremony in Sedona, AZ | Estrella Soul Guide',
             'A sacred water ceremony at our private home in Sedona, Arizona, offered as part of our private retreats or booked while you are visiting Sedona.'),
    'dragon-gate': ("The Dragon's Gate | Estrella Soul Guide",
             "Step through the Dragon's Gate into Guide Communication: Purifying the Clairs, a sacred journey to refine and trust your psychic gifts."),
    'classes': ("Guide Communication Through the Dragon's Gate: Purifying the Clairs | Estrella Soul Guide",
             'Purify and recalibrate your clairvoyance, clairaudience, clairsentience and claircognizance. A 1:1, live program with Genevieve Ivey in Sedona, by phone or Zoom.'),
    'becoming-a-channel': ("Becoming a Channel: Genevieve Ivey's Story | Estrella Soul Guide",
             "Genevieve Ivey's journey through Kundalini awakening to embodied star gnosis, her Lemurian starseed awakening, and her training and certifications."),
    'my-timeline': ('My Timeline | Estrella Soul Guide',
             "Genevieve Ivey's soul path, from a highly sensitive childhood and early visions to Glastonbury and the call of the soul."),
    'blog': ('Blog: Awakening, Kundalini & Twin Flames | Estrella Soul Guide',
             'Writings by Genevieve Ivey on Kundalini awakening, twin flames, guide communication, embodiment and the soul’s journey.'),
}

# Old addresses (Wix sites and the earlier one-page version) -> new pages.
OLD_PATHS = {
    '/home-1': '/spiritual-mentorship/', '/home-2': '/soul-journey-retreats/', '/home-3': '/becoming-a-channel/',
    '/home-3-1': '/my-timeline/', '/home-4': '/water-initiation/', '/blog': '/blog/',
    '/post/my-spiritual-delima-after-kundalini-awakening': '/blog/spiritual-dilemma-after-kundalini/',
    '/post/heart-opening-through-awakening': '/blog/heart-opening-through-awakening/',
    '/post/guide-communication': '/blog/guide-communication/',
    '/post/catalyst-twin-flame': '/blog/catalyst-twin-flame/',
    '/post/your-body-as-the-ascension-vehicle': '/blog/your-body-as-the-ascension-vehicle/',
    '/post/twin-flame-pain': '/blog/twin-flame-pain/',
    '/post/the-feminine-chakra-system': '/blog/the-feminine-chakra-system/',
    '/service-page/tell-me-your-story': '/#story', '/service-page/phototherapy': '/#story',
    '/book-online': '/healing-sessions/', '/work-with-me': '/healing-sessions/',
    '/intuitive-massage': '/sacred-bodywork/', '/soul-connection-akashic-reading': '/akashic-reading/',
    '/quantum-energy-healing': '/energy-healing/', '/about-genevieve-loved': '/becoming-a-channel/',
    '/regression-therapy': '/regression-therapy/', '/activations': '/activations/',
}

esc = lambda t: html.escape(t, quote=True)


def plain_excerpt(body, n=155):
    paras = [p.strip() for p in re.split(r'\n{2,}', body) if p.strip()]
    paras = [p for p in paras if not p.startswith('##') and not re.fullmatch(r'\*[^*].*\*', p)]
    t = re.sub(r'^(##\s|>\s?|-\s+)', '', paras[0] if paras else '', flags=re.M)
    t = re.sub(r'\*+', '', t).replace('\n', ' ')
    return t if len(t) <= n else re.sub(r'\s+\S*$', '', t[:n - 1]) + '…'


def main():
    s = SRC.read_text()
    css = re.search(r'<style id="site-style">(.*?)</style>', s, re.S).group(1)
    data = json.loads(re.search(r'<script id="site-data" type="application/json">(.*?)</script>', s, re.S).group(1))
    font_link = re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', s).group(0)

    # 1. Images embedded in the CSS become files; the CSS becomes one shared file.
    assets = ROOT / 'assets'
    shutil.rmtree(assets, ignore_errors=True); assets.mkdir()

    def save_uri(m):
        raw = base64.b64decode(m.group(2))
        name = hashlib.sha1(raw).hexdigest()[:10] + '.' + ('jpg' if m.group(1) == 'jpeg' else m.group(1))
        (assets / name).write_bytes(raw)
        return f'url(/assets/{name})'
    css = re.sub(r'url\(data:image/(\w+);base64,([A-Za-z0-9+/=]+)\)', save_uri, css)
    (assets / 'site.css').write_text(css)
    header_img = re.search(r'\.banner\{[^}]*url\((/assets/[^)]+)\)', css).group(1)
    logo_img = re.search(r'\.brand \.logo\{[^}]*url\((/assets/[^)]+)\)', css).group(1)

    # 2. Render every page in a headless browser (declaring UTF-8 so apostrophes survive).
    render_file = ROOT / 'src' / '.render.html'
    render_file.write_text('<!doctype html><meta charset="utf-8">' + s, encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.route('**/*', lambda r: r.abort() if r.request.url.startswith('http') else r.continue_())
        pg.goto(render_file.as_uri(), wait_until='domcontentloaded')
        pg.wait_for_timeout(300)
        views = pg.evaluate("[...document.querySelectorAll('[data-view]')].map(m => m.dataset.view)")
        sections = pg.evaluate("""() => { const m = {}; document.querySelectorAll('[data-view]').forEach(v => {
            v.querySelectorAll('[id]').forEach(el => { m[el.id] = v.dataset.view; }); }); return m; }""")
        extract = """({views, sections}) => {
          const root = document.getElementById('root').cloneNode(true);
          root.querySelectorAll('[data-view][hidden], .owner-only, #composer').forEach(e => e.remove());
          const rd = root.querySelector('#reader'); if (rd) { if (rd.hidden) rd.remove(); else rd.removeAttribute('hidden'); }
          const pathFor = v => v === 'home' ? '/' : '/' + v + '/';
          root.querySelectorAll('[href^="#"]').forEach(a => {
            const h = decodeURIComponent(a.getAttribute('href').slice(1));
            let url = '#' + h;
            if (!h) url = '/';
            else if (h.startsWith('post-')) url = '/blog/' + h.slice(5) + '/';
            else if (views.includes(h)) url = pathFor(h);
            else if (sections[h]) url = pathFor(sections[h]) + '#' + h;
            a.setAttribute('href', url);
          });
          root.querySelectorAll('video, img').forEach(v => ['src', 'poster'].forEach(k => {
            const val = v.getAttribute(k); if (val && !/^(\\/|https?:)/.test(val)) v.setAttribute(k, '/' + val); }));
          return root.innerHTML;
        }"""
        rendered = {}
        targets = [(v, v) for v in views] + [('post-' + q['id'], 'post:' + q['id']) for q in data['posts']]
        for hash_, key in targets:
            pg.evaluate("h => { location.hash = h; }", hash_)
            pg.wait_for_timeout(60)
            rendered[key] = pg.evaluate(extract, {'views': views, 'sections': sections})
        b.close()
    render_file.unlink()
    assert not any('â€' in v for v in rendered.values()), 'garbled characters in rendered pages'

    # 3. Write the pages.
    manifest = ROOT / 'src' / '.generated.json'
    if manifest.exists():
        for rel in json.loads(manifest.read_text()):
            shutil.rmtree(ROOT / rel, ignore_errors=True)
    generated, sitemap = [], []

    org = {'@type': 'Organization', 'name': BRAND, 'url': SITE + '/', 'logo': SITE + logo_img}
    person = {'@type': 'Person', 'name': 'Genevieve Ivey', 'jobTitle': 'Soul Guide', 'url': SITE + '/becoming-a-channel/'}

    def page(path, title, desc, body, ld, og_type='website', preload=None, image=None):
        url = SITE + path
        og_img = SITE + (image or header_img)
        head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="apple-touch-icon" href="/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{font_link}
<link rel="stylesheet" href="/assets/site.css">
{f'<link rel="preload" as="image" href="{preload}">' if preload else ''}
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')}</script>
</head>
<body>
<div id="root">{body}</div>
<script src="/assets/site.js" defer></script>
</body>
</html>
'''
        out = ROOT / path.strip('/') / 'index.html' if path != '/' else ROOT / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(head)

    for v in views:
        title, desc = SEO.get(v, (f'{v.replace("-", " ").title()} | {BRAND}', ''))
        path = '/' if v == 'home' else f'/{v}/'
        ld = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'url': SITE + path,
              'description': desc, 'isPartOf': {'@type': 'WebSite', 'name': BRAND, 'url': SITE + '/'}}
        if v == 'home':
            ld = {'@context': 'https://schema.org', '@graph': [
                {'@type': 'WebSite', 'name': BRAND, 'url': SITE + '/'},
                {'@type': 'ProfessionalService', 'name': BRAND, 'url': SITE + '/', 'email': EMAIL,
                 'image': SITE + header_img, 'logo': SITE + logo_img, 'description': desc,
                 'founder': person, 'areaServed': ['Sedona, AZ', 'Nevada City, CA', 'Online']}]}
        elif v == 'becoming-a-channel':
            ld = {'@context': 'https://schema.org', '@type': 'ProfilePage', 'url': SITE + path,
                  'mainEntity': dict(person, worksFor=org, email=EMAIL)}
        page(path, title, desc, rendered[v], ld, preload=header_img if v == 'home' else None)
        if v != 'home': generated.append(v)
        sitemap.append((path, TODAY))

    for q in data['posts']:
        path = f"/blog/{q['id']}/"
        desc = plain_excerpt(q['body'])
        img = '/' + q['image'].lstrip('/') if q.get('image') else None
        ld = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': q['title'],
              'datePublished': q['date'], 'author': person, 'publisher': org, 'image': SITE + (img or header_img),
              'mainEntityOfPage': SITE + path, 'description': desc}
        page(path, f"{q['title']} | {BRAND}", desc, rendered['post:' + q['id']], ld, og_type='article', image=img)
        sitemap.append((path, q['date']))

    # 4. Shared script: menu, copy email, the Dragon's Gate portal, and old #links.
    (assets / 'site.js').write_text(SITE_JS.replace('__VIEWS__', json.dumps(views)).replace('__SECTIONS__', json.dumps(sections)))

    # 5. Not-found page that forwards old addresses, sitemap, robots.
    home = rendered['home']
    top = re.search(r'<div class="topbar">.*?</nav></div></div>', home, re.S).group(0)
    foot = re.search(r'<footer class="site">.*?</footer>', home, re.S).group(0)
    nf = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Page not found | {BRAND}</title><meta name="robots" content="noindex">
<script>(function(){{var R={json.dumps(OLD_PATHS)};
var p=location.pathname.toLowerCase().replace(/^\\/(my-site-6|soultosoul2)(?=\\/|$)/,'').replace(/\\/+$/,'')||'/';
var to=R[p]||(p.indexOf('/post/')===0?'/blog/':null);if(to)location.replace(to);}})();</script>
<link rel="icon" type="image/png" href="/favicon.png">{font_link}<link rel="stylesheet" href="/assets/site.css">
<style>body{{margin:0}}[hidden]{{display:none!important}}</style></head>
<body><div id="root">{top}<main><header class="page-hero wrap"><span class="mandala" aria-hidden="true"></span>
<h1 class="script">This path has moved</h1><p class="sub">The page you were looking for isn’t here. It may have a new home on this site.</p></header>
<div class="wrap page-body"><div class="actions"><a class="btn" href="/">Go to the home page</a><a class="btn ghost" href="/healing-sessions/">Healing Sessions</a><a class="btn ghost" href="/blog/">Blog</a></div></div></main>{foot}</div>
<script src="/assets/site.js" defer></script></body></html>
'''
    (ROOT / '404.html').write_text(nf)
    (ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>\n' for u, d in sitemap) + '</urlset>\n')
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nDisallow: /src/\nDisallow: /CLAUDE.md\nDisallow: /README.md\n\nSitemap: {SITE}/sitemap.xml\n')
    generated.append('blog')
    manifest.write_text(json.dumps(sorted(set(generated))))
    print(f'Built {len(sitemap)} pages.')


SITE_JS = r"""(function () {
  var VIEWS = __VIEWS__, SECTIONS = __SECTIONS__;
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
"""

if __name__ == '__main__':
    main()
