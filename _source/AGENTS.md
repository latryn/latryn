# AGENTS.md

Instructions for AI coding agents (and humans) working on the Latryn website. Read this before editing anything.

## Project overview

Static marketing site for **Latryn**, a data lab for frontier AI. **Lead offer: egocentric (first-person) video data**, captured with head-mounted cameras and annotated for robotics and embodied AI. Also: evaluation sets, benchmarks, training data and agent environments. No framework, no bundler. Plain HTML, one shared stylesheet, one shared script, and a small Python build step for the blog and agent files.

```
index.html              homepage (self-contained CSS, loads assets/site.js and assets/home.js)
sample-tasks.html       task library preview (CTA target for "Browse sample tasks")
join.html               Lattice application form (generated; posts to Google Apps Script)
privacy.html, terms.html, 404.html
blog/index.html         blog listing
blog/<slug>.html        articles (generated)
blog/<slug>.md          plain-markdown copies for LLMs and agents (generated)
assets/latryn.css       shared styles for every page except index.html
assets/site.js          CONFIG + CTA wiring + forms + smooth scroll + inner-page motion
assets/home.js          homepage scroll story (GSAP ScrollTrigger)
llms.txt, llms-full.txt LLM site guide and full article text (generated)
agents.txt              guide for AI agents acting for a user: offer, routing URLs, facts to keep accurate (generated)
sitemap.xml, robots.txt (generated)
favicon.svg, og-image-1200x630.png
```

The download has the finished site at the top level (open `index.html`). Everything needed to rebuild it is in `_source/`: `content/*.md` (articles), `build_pages.py` (builder), `index_template.html` (homepage source, logo already embedded). Build output goes to `_source/dist/`; copy it to the top level to publish.

## Build and preview

```bash
pip install markdown
python3 build.py          # writes everything to dist/
python3 -m http.server -d dist 8000
```

The site is live at `https://latryn.com`. `BASE_URL` in `build_pages.py` holds it; if the domain changes, edit it there and rebuild. It feeds canonical tags, Open Graph, JSON-LD, `sitemap.xml`, `robots.txt` and `llms.txt`.

## Configuration: every CTA reads from one place

Edit the `window.LATRYN` block at the top of `assets/site.js`:

| Key | Used by |
|---|---|
| `email` | `contact@latryn.com`. Contact form, "Scope a program", "Book a call" fallback, footer email |
| `careersEmail` | `contact@latryn.com`. Shown on `join.html` for application questions and used by its email fallback |
| `latticeEndpoint` | Google Apps Script web app URL for `join.html`. Empty = the application opens an email instead. Setup: `_source/apps-script/README.md` |
| `bookingUrl` | "Book a call". Empty = scrolls to the contact form with "Book a call" preselected |
| `social.linkedin/x/youtube` | Footer links. Empty = link is hidden, never broken |

CTAs declare intent with attributes; do not hard-code mailto links:
- `data-cta="<option text>"` prefills the contact form's "I want to" select. The value must match an `<option>` exactly.
- `data-audience="AI Labs|AI Platforms|Enterprise AI"` prefills audience.
- "Join the Lattice" links go to `join.html`; `join.html?role=<role>` records the role of interest in a hidden field.
- Cross-page links use URL params: `index.html?type=Scope%20a%20program#contact`.

The build also writes the address into every `data-email` link, so it shows without JavaScript; if you change it, update `EMAIL` in `build_pages.py` too.

The contact form has no backend: it composes an email with the answers. To switch it to a form service later, replace `wire()` in `site.js` and keep the field names.

The Lattice application (`join.html`, built by `join()` in `build_pages.py`, behaviour in `lattice()` in `site.js`) posts JSON with the resume as base64 to the Google Apps Script in `_source/apps-script/lattice-apply.gs`. The script saves the resume to Drive, adds a row to the sheet and emails a confirmation to the applicant and a copy to `contact@latryn.com`. If you change an option list in `build_pages.py`, change `OPTIONS` in the script too and redeploy it.

## Egocentric data: how it appears on the site

Egocentric data collection is the lead offer. Keep it first wherever services are listed.

- Homepage: hero lede and note, nav link `#egocentric`, the pinned **Egocentric data** section right after the dark stage (four steps: Capture, Annotate, Segment, Narrate and review), the Latryn Capture practice card, the AI Labs audience card, the capability rows, an FAQ entry and the first blog card.
- `sample-tasks.html#egocentric-sample`: the files delivered with a clip (`clip.mp4`, `capture.json`, `consent/record.pdf`, `labels/hands.jsonl`, `labels/objects.jsonl`, `labels/actions.jsonl`, `labels/narration.txt`, `review/notes.md`).
- Blog: `content/egocentric-data-collection.md` (Ego4D, EPIC-KITCHENS-100, Ego-Exo4D, EgoMimic, all cited).
- Agent files: `llms.txt` (summary, practice list, "Egocentric data" section), `agents.txt`, JSON-LD Organization (`knowsAbout`, Latryn Capture listed first in the offer catalog).
- Wording: say "egocentric" or "first-person video", "head-mounted cameras", "contributors". Do not name camera brands, hours of footage or contributor counts until the business confirms them; use `[NUMBER]` placeholders instead. Consent and privacy are agreed with each client before recording.

## Design system rules (do not break)

Brand source of truth: the Latryn design system (tokens mirrored as CSS variables in `:root`).

- **Colour:** 60% stone grounds (`--paper`, `--raised`, `--sunken`), 30% ink and tints, about 8% verdigris (`--verd`) for actions, at most one ember (`--ember`) accent per view. Cobalt only for "pass" states.
- **Type:** Outfit for display, Schibsted Grotesk for body, JetBrains Mono for labels and file names. Section eyebrows use the pattern `<b>NN</b> / LABEL`.
- **Logo:** always the inline outlined `latryn.` SVG. Never retype the name in a font. The ember square is the full stop.
- **Headings end with** `<span class="dot"></span>` (the ember square), once per heading.
- **Copy:** sentence case, short declaratives, "we" and "you". **No em dashes or en dashes anywhere.** No emoji, no exclamation marks, no invented statistics. Unknown facts stay as visible placeholders like `[NUMBER]`.
- **Motion:** see the motion system below. Everything must respect `prefers-reduced-motion`.

## Motion system

The homepage is a scroll story. Scroll position is the timeline: GSAP ScrollTrigger drives every scroll-linked transition and Lenis supplies the inertial glide (one clock: `site.js` feeds Lenis from `gsap.ticker`). Homepage motion lives in `assets/home.js`; inner pages use only Lenis plus the heading stamp.

| Scene | What happens | Rule |
|---|---|---|
| Hero | Headline letters rise out of a blur, a swash draws under "verify", copy and CTAs follow, the task card rises with three gate chips. Then the "seal and sign" review plays once: brief types, track fills, three gates pass at 420ms intervals, the ember square stamps on the card and on the headline full stop | Plays once on load. "Run the review again" replays it. Never loop it |
| Hero to stage | Scrolling dims and lifts the hero copy; the card stands up from a tilt and lands across the top edge of the dark stage | Scrubbed to scroll |
| Panels | The dark stage, the dark task library and the green contact band open from a rounded inset to full bleed as they arrive, and close again as they leave. The nav turns dark while over them | Clip-path driven by `--xa` (enter) and `--xb` (leave) |
| Statement | Words light up from 14% to full as you read down; two capability rows slide in opposite directions | Scrubbed |
| How it works | Desktop (901px+): the section pins and scrolling moves through five steps. Each step swaps its two-tone headline (masked line rise), text and device card (tilted slide); numbered dots and a filling line show progress and jump to a step. Phones: the five steps stack | Pinned for about 3.6 screens |
| Practices | Desktop: the section pins and the five practice cards travel sideways; each card straightens as it arrives and starts its demo. Phones: vertical stack | Demos run only on cards in view |
| Egocentric data | Desktop: the section pins for about 2.4 screens; the viewfinder adds one layer per step (raw capture, hand and object labels, action timeline, narration and three passed gates) while the step list on the left lights the current step. Clicking a step scrolls to it. Phones: the viewfinder sits above the list and layers add as each step scrolls in | Default markup shows all four layers, so no-JS and reduced motion get the finished frame |
| Audiences | Three sticky cards stack; the one underneath sinks back and dims | Scrubbed (desktop) |
| Quality | Title goes grey to ink word by word; the three gate cards float in tilted and settle; comparison rows slide in and each Latryn row is stamped | |
| Headings | Every `h2` rises word by word from a mask, then its ember full stop stamps | Once, at 86% of the viewport |
| Task library | File window rises, files list like terminal output, verifier line types | Once |
| FAQ | A conversation: choosing a question posts it as a bubble, a typing indicator shows, then the answer arrives | Answers are also in the FAQPage JSON-LD |
| Footer | The wordmark rises letter by letter with the last stretch of scroll | Scrubbed |
| Page change | Cross-document view transitions: 320ms crossfade, nav logo fixed, blog card title morphs into the article `h1` | `view-transition-name` unique per page |

Programmatic scrolls go through `window.__scrollToEl(el, center)` (anchors land 96px below the nav; CTAs centre the form) or `window.__lenis.scrollTo(y)`. Never call `scrollIntoView`. After changing layout above a pinned scene, call `ScrollTrigger.refresh()`.

Do not add: idle infinite loops, bounce easing, parallax on body text, fade-up on every element. Entrances use `expo.out`; responses 150 to 450ms. With `prefers-reduced-motion: reduce` (or if GSAP fails to load) nothing pins or scrubs, everything renders in its final state, and view transitions are off.
- **Accessibility:** WCAG 2.2 AA contrast, real `<button>`/`<a>`/`<label>`, visible focus ring (2px verdigris), touch targets 44px or more, no horizontal scroll at 390px.

## Writing and adding blog articles

1. Add `content/<slug>.md` with front matter: `title`, `dek`, `category`, `read`, `keywords`, and `- ` takeaway lines.
2. Add the slug to `ORDER` in `build_pages.py`.
3. Cite claims inline as `[[n]](#ref-n)` and end with `## References`, each item starting `n. <span id="ref-n"></span>`.
4. **Every factual claim must link to a primary source** (paper, official post). Verify numbers against the source before publishing. Paraphrase; never paste passages.
5. Link to at least one related article and one site section.
6. Run the build. It generates the HTML page, the `.md` copy, schema (BlogPosting with `citation`, BreadcrumbList), sitemap entry and `llms.txt` entry.

## SEO and agent-search checklist

- One `<h1>` per page; descriptive `<title>` under 65 characters; meta description 140 to 160 characters.
- Canonical URL, Open Graph and JSON-LD on every page (Organization, WebSite, FAQPage and HowTo on the homepage).
- Articles open with a "Key takeaways" list: short, quotable answers that search engines and AI assistants can lift.
- `llms.txt` follows the llmstxt.org format: H1, blockquote summary, then H2 link lists, then `## Optional`.
- `robots.txt` allows search and AI crawlers. Do not block them without a business decision.

## Testing before you finish

```bash
python3 check_site.py dist   # broken internal links, missing anchors, dashes, CTA targets
```

Then open the homepage at 390px and 1440px widths, submit both forms once, and confirm no console errors.

## Security and privacy

- No third-party scripts besides Google Fonts. Lenis (smooth scrolling, MIT licence) and GSAP 3.13 with ScrollTrigger (GreenSock standard no-charge licence) are bundled locally in `assets/vendor/`, not loaded from a CDN. Do not add analytics or trackers without updating `privacy.html`.
- Never commit real personal data or client task files into this repo.
