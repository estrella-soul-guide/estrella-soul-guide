# Estrella Soul Guide website

Live at https://estrellasoulguide.com (GitHub Pages, branch `main`, root folder).
Owner: Genevieve Ivey, Estrella Soul Guide (estrellasoulguide@gmail.com). Domain registered at Wix; Wix DNS points
the apex A records at GitHub Pages and `www` CNAME at `estrella-soul-guide.github.io`.

## How the site is built

- `src/estrella-site.html` is the single source of truth: design (CSS in `<style id="site-style">`),
  page content (JS constants in `<script id="site-app">`), and blog posts / classes (JSON in
  `<script id="site-data">`). It is a one-page app that switches sections with `#hash` links.
- The same file is published as the Claude preview artifact:
  https://claude.ai/artifact/NtKuJP9js4nNJkwnJDTdxr (publish it with `files` for `dragon-gate.mp4`
  and `dragon-gate-poster.jpg`). Its "New post" / "Add class" buttons save only to that preview.
  If the owner writes a post there, read the artifact and copy its `site-data` JSON back into `src/`.
- `python3 src/build.py` pre-renders every section and post into its own static page
  (`/healing-sessions/`, `/blog/<id>/`, …) with titles, descriptions, canonical URLs, Open Graph
  tags and JSON-LD, extracts the embedded images and CSS to `/assets/`, writes `assets/site.js`,
  `sitemap.xml`, `robots.txt`, and `404.html` (which forwards old Wix addresses). It needs
  Playwright with Chromium. Generated folders are listed in `src/.generated.json`; never hand-edit them.
- SEO titles/descriptions per page live in the `SEO` dict in `src/build.py`; old-address
  forwarding lives in `OLD_PATHS`. Add a new page's entry there whenever a view is added.

## Making a change

1. Edit `src/estrella-site.html`.
2. `python3 src/build.py`
3. Check the result (serve the repo root with `python3 -m http.server` and look at it).
4. Commit and push to `main`; GitHub Pages redeploys in a minute or two.
5. Republish the Claude preview artifact from the same source so both stay in step.

## Content notes

- Text on the site is Genevieve's own writing, carried over from her Wix sites; keep her wording.
- Prices are shown as on her old site. In-person bodywork is in Nevada City, CA; retreats and
  Water Initiation are in Sedona, AZ; most sessions are also online by Zoom or phone.
