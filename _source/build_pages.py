"""Builds Latryn inner pages, blog, sitemap and agent files from content/*.md.
Run: python3 build_pages.py  (BASE_URL below is the only value to change for production)."""
import os, re, json, glob, html, datetime, markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'dist')
BASE_URL = 'https://latryn.com'        # live domain; change here and rebuild if it ever moves
EMAIL = 'contact@latryn.com'           # keep in sync with window.LATRYN in assets/site.js
PUBLISHED = '2026-10-24'
LOGO = open(os.path.join(ROOT, 'logo_inner.txt')).read().strip()
ORDER = ['egocentric-data-collection', 'trustworthy-ai-benchmarks', 'rlhf-preference-data-guide', 'building-agent-environments',
         'quality-over-quantity-training-data', 'expert-vs-crowd-annotation', 'red-teaming-language-models']

def parse(path):
    raw = open(path, encoding='utf-8').read()
    _, fm, body = raw.split('---', 2)
    meta, take, key = {}, [], None
    for line in fm.strip().splitlines():
        if line.startswith('- '):
            take.append(line[2:].strip())
        else:
            k, v = line.split(':', 1); meta[k.strip()] = v.strip()
    meta['takeaways'] = take
    meta['slug'] = os.path.splitext(os.path.basename(path))[0]
    meta['body'] = body.strip()
    return meta

POSTS = {p['slug']: p for p in (parse(f) for f in glob.glob(os.path.join(ROOT, 'content', '*.md')))}
POSTS = [POSTS[s] for s in ORDER]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700&family=Schibsted+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">')

def head(title, desc, path, pre, extra='', og_type='website'):
    url = BASE_URL + '/' + path
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Latryn">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE_URL}/og-image-1200x630.png">
<meta name="twitter:card" content="summary_large_image">
<script>document.documentElement.classList.add("js")</script>
<meta name="theme-color" content="#f5f2ec">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="text/plain" title="LLM site guide" href="{pre}llms.txt">
{FONTS}
<link rel="stylesheet" href="{pre}assets/vendor/lenis.css">
<link rel="stylesheet" href="{pre}assets/latryn.css">
{extra}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="progress" aria-hidden="true"></div>'''

def nav(pre, current=''):
    def cur(n): return ' aria-current="page"' if n == current else ''
    return f'''<header class="nav" id="nav"><nav class="nav-in" aria-label="Main">
<a href="{pre}index.html" class="logo" aria-label="Latryn home"><svg viewBox="0 0 292 94" width="87" height="28" aria-hidden="true">{LOGO}</svg></a>
<div class="nav-links"><a href="{pre}index.html#egocentric">Egocentric</a><a href="{pre}index.html#build">Services</a><a href="{pre}index.html#quality">Quality</a><a href="{pre}sample-tasks.html"{cur('tasks')}>Sample tasks</a><a href="{pre}blog/index.html"{cur('blog')}>Blog</a><a href="{pre}index.html#lattice"{cur('join')}>Careers</a></div>
<a class="btn btn-ink" href="{pre}index.html?type=Scope%20a%20program#contact" style="min-height:44px;padding:11px 18px;font-size:15px">Scope a program <span class="sq" aria-hidden="true"></span></a>
</nav></header>'''

def footer(pre):
    posts = ''.join(f'<a href="{pre}blog/{p["slug"]}.html">{html.escape(short(p["title"]))}</a>' for p in POSTS[:4])
    return f'''<footer><div class="wrap">
<div class="fgrid">
<p style="margin:0;font-family:var(--disp);font-size:22px;line-height:1.35;color:var(--paper);max-width:340px">Egocentric and expert-built data for frontier AI.</p>
<div class="fcols">
<div><span class="h">PRACTICES</span><a href="{pre}index.html#build">Latryn Eval</a><a href="{pre}index.html#build">Latryn Train</a><a href="{pre}index.html#build">Latryn Env</a><a href="{pre}index.html#egocentric">Latryn Capture</a><a href="{pre}index.html#build">Latryn Review</a></div>
<div><span class="h">BLOG</span>{posts}<a href="{pre}blog/index.html">All articles</a></div>
<div><span class="h">COMPANY</span><a href="{pre}index.html#quality">Quality process</a><a href="{pre}sample-tasks.html">Sample tasks</a><a href="{pre}index.html#lattice">Careers</a><a href="{pre}index.html#contact">Contact</a></div>
<div><span class="h">SOCIAL</span><a data-social="linkedin" href="#">LinkedIn</a><a data-social="x" href="#">X</a><a data-social="youtube" href="#">YouTube</a><a data-email="general" href="#"></a></div>
</div></div>
<div class="legal"><span>© 2026 Latryn · Bengaluru, India</span><span style="display:flex;gap:20px"><a href="{pre}privacy.html">Privacy</a><a href="{pre}terms.html">Terms</a></span></div>
</div></footer>
<script src="{pre}assets/vendor/lenis.min.js"></script>
<script src="{pre}assets/site.js"></script>
</body>
</html>'''

def short(t):
    if t.startswith('Egocentric data collection'): return 'Egocentric data collection'
    return t.split(':')[0].split('?')[0] if len(t) > 34 else t

def ld(obj): return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>'

ORG = {"@type": "Organization", "name": "Latryn", "url": BASE_URL + "/", "logo": BASE_URL + "/favicon.svg"}

def refs_from(body):
    out = []
    for m in re.finditer(r'^\d+\. <span id="ref-\d+"></span>(.+)$', body, re.M):
        line = m.group(1)
        u = re.search(r'\((https?://[^)]+)\)', line)
        name = re.sub(r'\*', '', line.split('[')[0]).strip()
        out.append({"@type": "ScholarlyArticle", "name": name, "url": u.group(1) if u else None})
    return out

def article(p):
    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    body, refs = p['body'].split('## References')
    body_html = md.convert(body)
    body_html = re.sub(r'<a href="#ref-(\d+)">\[(\d+)\]</a>', r'<sup><a href="#ref-\1" aria-label="Reference \2">[\2]</a></sup>', body_html)
    refs_html = markdown.markdown(refs)
    refs_html = refs_html.replace('<a href="http', '<a rel="noopener" target="_blank" href="http')
    words = len(re.findall(r'\w+', p['body']))
    related = [q for q in POSTS if q['slug'] != p['slug']][:3]
    schema = [
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p['title'], "description": p['dek'],
         "datePublished": PUBLISHED, "dateModified": PUBLISHED, "author": {"@type": "Organization", "name": "Latryn Research Team"},
         "publisher": ORG, "mainEntityOfPage": f"{BASE_URL}/blog/{p['slug']}.html", "image": BASE_URL + "/og-image-1200x630.png",
         "keywords": p['keywords'], "articleSection": p['category'], "wordCount": words, "abstract": " ".join(p['takeaways']),
         "citation": refs_from(p['body'])},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE_URL + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p['title'], "item": f"{BASE_URL}/blog/{p['slug']}.html"}]}]
    extra = f'<meta name="keywords" content="{html.escape(p["keywords"])}"><meta property="article:published_time" content="{PUBLISHED}"><link rel="alternate" type="text/markdown" href="{p["slug"]}.md">' + ''.join(ld(s) for s in schema)
    take = ''.join(f'<li>{html.escape(t)}</li>' for t in p['takeaways'])
    rel = ''.join(card(q, '') for q in related)
    return (head(f"{p['title']} | Latryn", p['dek'], f"blog/{p['slug']}.html", '../', extra, 'article') + nav('../', 'blog') + f'''
<main id="main">
<article class="narrow">
<header class="article-head rv">
<div class="crumbs"><a href="../index.html">Home</a> / <a href="index.html">Blog</a> / {html.escape(p['category'])}</div>
<h1 style="view-transition-name:t-{p['slug']}">{html.escape(p['title'])}<span class="dot"></span></h1>
<p class="dek">{html.escape(p['dek'])}</p>
<div class="byline"><span>Latryn Research Team</span><span><time datetime="{PUBLISHED}">24 Oct 2026</time></span><span>{html.escape(p['read'])} read</span><span>{len(refs_from(p['body']))} cited sources</span></div>
</header>
<aside class="tldr rv" aria-label="Key takeaways"><h2>Key takeaways</h2><ul>{take}</ul></aside>
<div class="prose">{body_html}</div>
<section class="cta-box rv" aria-label="Work with Latryn">
<h2>Need data built to this standard?</h2>
<p>Tell us the benchmark, task format or dataset you need. We agree scope and acceptance checks before any work starts.</p>
<div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn btn-paper" href="../index.html?type=Scope%20a%20program#contact">Scope a program <span class="arr" aria-hidden="true">→</span></a><a class="btn" style="color:var(--raised);border-color:var(--tint)" href="../sample-tasks.html">See sample tasks</a></div>
</section>
<section class="refs prose" id="references" aria-label="References"><h2>References</h2>{refs_html}</section>
</article>
<section class="wrap related"><h2>Keep reading<span class="dot"></span></h2><div class="posts stagger" style="padding-bottom:0">{rel}</div></section>
</main>''' + footer('../'))

def card(p, cls):
    return f'''<a class="post-card {cls}" href="{'' if cls!='x' else ''}{p['slug']}.html"><span class="corner" aria-hidden="true"></span><span class="eyebrow">{html.escape(p['category'])}</span><h2 style="view-transition-name:t-{p['slug']}">{html.escape(p['title'])}</h2><p>{html.escape(p['dek'])}</p><span class="meta">{html.escape(p['read'])} read · {len(refs_from(p['body']))} sources</span></a>'''

def blog_index():
    cards = card(POSTS[0], 'feature') + ''.join(card(p, '') for p in POSTS[1:])
    schema = {"@context": "https://schema.org", "@type": "Blog", "name": "Latryn Blog", "url": BASE_URL + "/blog/", "publisher": ORG,
              "blogPost": [{"@type": "BlogPosting", "headline": p['title'], "url": f"{BASE_URL}/blog/{p['slug']}.html", "datePublished": PUBLISHED} for p in POSTS]}
    return (head('Blog: AI evaluation, training data and data collection | Latryn',
                 'Research-backed articles on AI benchmarks, RLHF and preference data, agent environments, red teaming and expert data collection.',
                 'blog/', '../', ld(schema)) + nav('../', 'blog') + f'''
<main id="main" class="wrap">
<header class="page-hero rv"><div class="crumbs"><a href="../index.html">Home</a> / Blog</div>
<h1>Notes on building better AI data<span class="dot"></span></h1>
<p>Practical, research-backed articles on evaluation, training data and the human work behind both. Every claim links to its source.</p></header>
<div class="posts stagger">{cards}</div>
</main>''' + footer('../'))

TASKS = [
    ('Egocentric · Capture', 'Make tea, recorded from the POV', 'A contributor wearing a head-mounted camera makes a cup of tea in their own kitchen. Reviewers mark hand keypoints and object contact, split the clip into labelled actions (reach, grasp, pour, place) and write a plain-language narration.',
     ['clip.mp4', 'capture.json', 'consent/record.pdf', 'labels/hands.jsonl', 'labels/objects.jsonl', 'labels/actions.jsonl', 'labels/narration.txt', 'review/notes.md'], ['Head-mounted camera', 'Hand and object labels', 'Action segments'], 'egocentric-sample', '$ validate labels → schema and timing checks passed'),
    ('Coding · Terminal', 'Repair a failing CI build', 'An agent must diagnose why a Python package fails to build in a pinned container, fix the dependency conflict without changing public APIs, and prove the fix with the project test suite.',
     ['instruction.md', 'task.toml', 'environment/Dockerfile', 'solution/solve.sh', 'tests/verifier.py', 'review/notes.md'], ['Docker', 'Python', 'Build systems']),
    ('Evaluation · Rubric', 'Grade a multi-step data migration', 'Reviewers score model outputs that migrate records between two schemas, using a five-dimension rubric: correctness, edge cases, data loss, idempotency and explanation quality.',
     ['instruction.md', 'rubric.json', 'fixtures/source.csv', 'fixtures/expected.csv', 'review/scores.jsonl'], ['Rubrics', 'Data engineering', 'Scoring']),
    ('Preference · RLHF', 'Rank two explanations of a proof', 'A mathematician compares two model explanations of the same proof, picks the better one and writes a short rationale naming the step where the weaker answer goes wrong.',
     ['prompt.md', 'response_a.md', 'response_b.md', 'judgement.json', 'review/notes.md'], ['Mathematics', 'Preference data', 'Rationales']),
]

def sample_tasks():
    items = ''
    for row in TASKS:
        cat, t, d, files, chips = row[:5]
        aid = f' id="{row[5]}"' if len(row) > 5 else ''
        okline = row[6] if len(row) > 6 else '$ run verifier → all checks passed'
        tree = ''.join(f'<div>{html.escape(f)}</div>' for f in files)
        ch = ''.join(f'<span class="chip">{c}</span>' for c in chips)
        items += f'<article class="task rv"{aid}><span class="eyebrow">{cat}</span><h2>{t}</h2><p>{d}</p><div class="tree">{tree}<div class="ok">{okline}</div></div><div class="chips">{ch}</div></article>'
    return (head('Sample tasks | Latryn', 'Examples of what Latryn delivers: egocentric video clips with labels, briefs, environments, verifiers and review notes.', 'sample-tasks.html', '') + nav('', 'tasks') + f'''
<main id="main" class="narrow">
<header class="page-hero rv"><div class="crumbs"><a href="index.html">Home</a> / Sample tasks</div>
<h1>Sample tasks<span class="dot"></span></h1>
<p>Every task we deliver ships with the files behind it, so your team can read the brief, inspect the labels, rebuild the environment and run the checks. These examples show the structure. The full library is shared with clients during scoping.</p></header>
{items}
<section class="cta-box rv"><h2>Want the full task library?</h2><p>We share [NUMBER] samples across [NUMBER] categories with teams during scoping.</p><div><a class="btn btn-paper" href="index.html?type=Scope%20a%20program#contact">Request access <span class="arr" aria-hidden="true">→</span></a></div></section>
<p style="margin:0 0 96px;color:var(--body)">Related reading: <a href="blog/building-agent-environments.html">How to build agent environments that test real work</a>.</p>
</main>''' + footer(''))

QUALIFICATIONS = ['Diploma', 'Bachelors', 'Masters', 'PhD']
SPECIALIZATIONS = [
    'Physical Sciences (Physics, Chemistry, Astronomy, Earth Sciences)',
    'Life Sciences (Biology, Zoology, Botany, Genetics, Ecology)',
    'Health & Medical Sciences (Medicine, Nursing, Pharmacology, Neuroscience)',
    'Computing & Data (Computer Science, Data Analytics, AI, Cloud Computing)',
    'Development & Networks (Software Engineering, Web Development, Cybersecurity, Network Administration)',
    'Core Engineering (Mechanical, Electrical, Civil, Chemical)',
    'Advanced Engineering (Aerospace, Biomedical, Environmental, Robotics)',
    'Visual Arts (Graphic Design, Fine Arts, Painting, Photography, Sculpture)',
    'Media & Digital Arts (Animation, UI/UX Design, Game Design, Video Production, Digital Illustration)',
    'Performing Arts (Music Production, Sound Design, Theater, Choreography)',
    'Design & Architecture (Industrial Design, Fashion Design, Urban Planning, Architecture)',
    'Humanities & Communication (Technical Writing, Ethics in Technology, Language Arts, History)',
    'Pure Mathematics (Algebra, Calculus, Geometry, Number Theory)',
    'Applied Mathematics (Statistics, Actuarial Science, Cryptography, Quantitative Finance)',
    'Other']
STREAMS = ['Science', 'Commerce', 'Arts', 'Engineering', 'Other']
WORK_TYPES = ['Writing / Content', 'Design', 'Development', 'Data / Research', 'Teaching / Tutoring', 'Other']
AVAILABILITY = ['Part-time', 'Full-time', 'Weekends only']

def join():
    """Lattice application page. The form posts to the Google Apps Script in apps-script/ (see its README)."""
    def select(name, label, opts, msg, full=False):
        o = ''.join(f'<option>{html.escape(x)}</option>' for x in opts)
        return (f'<div class="field{" full" if full else ""}" data-field data-msg="{msg}"><label for="{name}">{label}</label>'
                f'<select id="{name}" name="{name}" required aria-describedby="e-{name}"><option value="">Select</option>{o}</select>'
                f'<p class="err" id="e-{name}" aria-live="polite"></p></div>')
    def text(name, label, msg, attrs='', full=False, opt=False):
        req = '' if opt else ' required'
        tag = ' <span class="opt">Optional</span>' if opt else ''
        return (f'<div class="field{" full" if full else ""}" data-field data-msg="{msg}"><label for="{name}">{label}{tag}</label>'
                f'<input id="{name}" name="{name}"{req} {attrs} aria-describedby="e-{name}">'
                f'<p class="err" id="e-{name}" aria-live="polite"></p></div>')
    work = ''.join(f'<label class="pick"><input type="checkbox" name="workTypes" value="{html.escape(w)}"><span>{html.escape(w)}</span></label>' for w in WORK_TYPES)
    avail = ''.join(f'<label class="pick"><input type="radio" name="availability" value="{a}" required><span>{a}</span></label>' for a in AVAILABILITY)
    desc = "Apply to join the Lattice, Latryn's vetted network of experts who build AI evaluation, training and egocentric data. Share your background and resume."
    return (head('Apply to the Lattice | Latryn', desc, 'join.html', '') + nav('', 'join') + f'''
<main id="main" class="wrap join">
<div class="join-grid">
<aside class="join-intro">
<div class="crumbs"><a href="index.html">Home</a> / <a href="index.html#lattice">The Lattice</a> / Apply</div>
<h1>Apply to the Lattice<span class="dot"></span></h1>
<p class="lede">Our vetted network of engineers, researchers and specialists. Tell us what you know and the work you want. We read every application.</p>
<ol class="join-steps">
<li><b>01</b><div><strong>Apply</strong><span>Share your background and resume. You get a confirmation email straight away.</span></div></li>
<li><b>02</b><div><strong>Assessment</strong><span>A two-part timed assessment: an auto-scored technical section and a scenario section reviewed by our team.</span></div></li>
<li><b>03</b><div><strong>Join</strong><span>Clear both and we match you to programs in your field.</span></div></li>
</ol>
<p class="join-mail">Questions? <a data-email="careers" href="#"></a></p>
</aside>
<div class="join-card">
<form class="form jform" id="apply-form" aria-label="Lattice application" novalidate>
<div class="jprog" aria-hidden="true"><span class="mono"><b id="jcount">0</b> of 10 answered</span><span class="track"><i id="jbar"></i></span></div>
<fieldset><legend class="eyebrow"><b>01</b> / About you</legend><div class="fgrid2">
{text('firstName', 'First name', 'Enter your first name', 'autocomplete="given-name" maxlength="80"')}
{text('lastName', 'Last name', 'Enter your last name', 'autocomplete="family-name" maxlength="80"')}
{text('email', 'Email', 'Enter your email address', 'type="email" autocomplete="email" maxlength="160" placeholder="name@example.com"')}
{text('phone', 'Phone number', 'Enter your phone number', 'type="tel" inputmode="numeric" autocomplete="tel-national" pattern="[0-9]{10}" maxlength="10" placeholder="10 digits"')}
</div></fieldset>
<fieldset><legend class="eyebrow"><b>02</b> / Education</legend><div class="fgrid2">
{select('qualification', 'Qualification', QUALIFICATIONS, 'Choose your highest qualification')}
{select('stream', 'Stream', STREAMS, 'Choose your stream')}
{select('specialization', 'Specialization', SPECIALIZATIONS, 'Choose your specialization', True)}
</div></fieldset>
<fieldset><legend class="eyebrow"><b>03</b> / Work</legend><div class="fgrid2">
<fieldset class="field full" data-field data-group="workTypes" data-msg="Choose at least one type of work" aria-describedby="e-workTypes"><legend class="lbl">Type of freelance work <span class="opt">Choose all that apply</span></legend><div class="picks">{work}</div><p class="err" id="e-workTypes" aria-live="polite"></p></fieldset>
<fieldset class="field full" data-field data-group="availability" data-msg="Choose your availability" aria-describedby="e-availability"><legend class="lbl">Availability</legend><div class="picks">{avail}</div><p class="err" id="e-availability" aria-live="polite"></p></fieldset>
{text('portfolio', 'Portfolio or LinkedIn link', 'Enter a full link, for example https://linkedin.com/in/you', 'type="url" inputmode="url" autocomplete="url" maxlength="300" placeholder="https://"', True, True)}
</div></fieldset>
<fieldset><legend class="eyebrow"><b>04</b> / Resume</legend>
<div class="field" data-field data-msg="Upload your resume">
<label class="drop" for="resume"><input type="file" id="resume" name="resume" required accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" aria-describedby="h-resume e-resume">
<span class="drop-ic" aria-hidden="true"><svg class="up" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 16V4m0 0-5 5m5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg><svg class="ck" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg></span>
<span class="drop-t"><strong>Choose a file</strong> or drop it here</span>
<span class="drop-h mono" id="h-resume">PDF or Word document, one file, up to 10 MB</span>
<span class="drop-file mono" hidden></span></label>
<p class="err" id="e-resume" aria-live="polite"></p></div>
</fieldset>
<input type="hidden" name="role">
<label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
<div class="jsubmit"><button class="btn btn-verd" type="submit">Submit application <span class="arr" aria-hidden="true">→</span></button><span class="note">We store your answers and resume to review your application. See our <a href="privacy.html">privacy policy</a>.</span></div>
<p class="form-ok" hidden role="status"></p>
</form>
<div class="jdone" hidden tabindex="-1">
<span class="stamp" aria-hidden="true"></span>
<span class="eyebrow"><b>Received</b> / Lattice application</span>
<h2>Thanks, <span id="jname">we have it</span><span class="dot"></span></h2>
<p>Your application is in. We sent a confirmation to <strong id="jmail">your email</strong>. If your background fits a current program, we will email you the assessment.</p>
<div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn btn-ink" href="index.html">Back to the homepage</a><a class="btn btn-ghost" href="blog/index.html">Read the blog</a></div>
</div>
</div>
</div>
</main>''' + footer(''))

def legal(kind):
    if kind == 'privacy':
        title, body = 'Privacy policy', '''<p>This website does not use cookies, analytics or advertising trackers.</p>
<h2>What we collect</h2><p>When you use the contact form, your email app opens with a message addressed to us. We only receive what you choose to send, such as your name, email address, company and message.</p>
<p>When you apply to the Lattice, we receive the answers you enter (name, email, phone number, education, specialization, type of work, availability and any profile link) and the resume you upload. They are stored in our Google Workspace account (Google Sheets and Google Drive), and we send a confirmation to the email address you give.</p>
<h2>How we use it</h2><p>We use your message to reply to you and to discuss a possible project or role. We use applications only to assess you for the Lattice and to contact you about it. We do not sell your information or share it for marketing.</p>
<h2>Retention and your rights</h2><p>We keep correspondence for as long as needed to respond and to meet legal obligations. You can ask us to access, correct or delete your information at any time by emailing <a data-email="general" href="#"></a>.</p>
<h2>Third parties</h2><p>Fonts are loaded from Google Fonts, which receives standard request information such as your IP address. Lattice applications are processed by Google Workspace on our behalf.</p>'''
    else:
        title, body = 'Terms of use', '''<p>By using this website you agree to these terms.</p>
<h2>Content</h2><p>Articles are provided for information. We link to the original research for every cited claim, and those works belong to their authors.</p>
<h2>Sample tasks</h2><p>Sample tasks are illustrative. Client deliverables are governed by a separate written agreement.</p>
<h2>Contact</h2><p>Questions about these terms: <a data-email="general" href="#"></a>.</p>
<p><em>[Review these terms with your legal adviser before launch.]</em></p>'''
    return (head(f'{title} | Latryn', f'Latryn {title.lower()}.', f'{kind}.html', '') + nav('') +
            f'<main id="main" class="narrow"><header class="page-hero"><div class="crumbs"><a href="index.html">Home</a> / {title}</div><h1>{title}<span class="dot"></span></h1><p>Last updated {"28" if kind == "privacy" else "24"} October 2026.</p></header><div class="prose" style="padding-bottom:96px">{body}</div></main>' + footer(''))

def not_found():
    return (head('Page not found | Latryn', 'This page does not exist.', '404.html', '/') + nav('/') +
            '<main id="main" class="narrow"><header class="page-hero"><h1>Page not found<span class="dot"></span></h1><p>The link may be old or mistyped.</p><p style="margin-top:24px"><a class="btn btn-verd" href="/index.html">Go to the homepage</a></p></header></main>' + footer('/'))

def write(rel, text):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(text)

def build():
    for p in POSTS:
        write(f"blog/{p['slug']}.html", article(p))
        md_txt = f"# {p['title']}\n\n> {p['dek']}\n\nPublished {PUBLISHED} by the Latryn Research Team. Canonical: {BASE_URL}/blog/{p['slug']}.html\n\n## Key takeaways\n\n" + '\n'.join('- ' + t for t in p['takeaways']) + '\n\n' + re.sub(r'<span id="ref-\d+"></span>', '', p['body']) + '\n'
        write(f"blog/{p['slug']}.md", md_txt)
    write('blog/index.html', blog_index())
    write('sample-tasks.html', sample_tasks())
    write('privacy.html', legal('privacy'))
    write('terms.html', legal('terms'))
    write('join.html', join())
    write('404.html', not_found())
    urls = ['', 'blog/', 'sample-tasks.html', 'join.html', 'privacy.html', 'terms.html'] + [f"blog/{p['slug']}.html" for p in POSTS]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          ''.join(f'  <url><loc>{BASE_URL}/{u}</loc><lastmod>{PUBLISHED}</lastmod></url>\n' for u in urls) + '</urlset>\n')
    write('robots.txt', f'''# Latryn welcomes search engines and AI assistants.
User-agent: *
Allow: /

# AI crawlers and assistants (explicitly allowed for answer-engine visibility)
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
# Site guide for language models: {BASE_URL}/llms.txt
# Guide for AI agents acting for a user: {BASE_URL}/agents.txt
''')
    posts_list = '\n'.join(f"- [{p['title']}]({BASE_URL}/blog/{p['slug']}.md): {p['dek']}" for p in POSTS)
    write('llms.txt', f'''# Latryn

> Latryn is a data lab for frontier AI based in Bengaluru, India. It collects egocentric (first-person) video of real human tasks through head-mounted cameras and annotates it for robotics and embodied AI, and it builds benchmarks, training data and agent environments with vetted engineers, researchers and domain experts. Every task and clip passes three review gates (automated screen, structured scoring, human sign-off) before delivery.

Latryn works with AI labs, robotics and embodied AI teams, AI platforms and enterprise AI teams. It has five practices:

- Latryn Capture: egocentric video recorded by consenting contributors wearing head-mounted cameras while they do real tasks, to a capture protocol agreed with the client; annotated with hand keypoints, object boxes and contact, action segments with start and end times, and narration
- Latryn Eval: benchmarks and model evaluation
- Latryn Train: SFT, chain of thought, RLHF and preference data
- Latryn Env: Docker and terminal environments, agent and MCP tool-use tasks, verifiers
- Latryn Review: technical QA and red teaming

Work follows a five-step process: Scope, Calibrate, Build, Verify, Deliver. Experts join its network, the Lattice, after a two-part timed assessment.

## Egocentric data

- [Egocentric data on the homepage]({BASE_URL}/#egocentric): Capture, annotate, segment, narrate and review
- [Sample egocentric clip]({BASE_URL}/sample-tasks.html#egocentric-sample): Files delivered with a clip (video, capture metadata, consent record, hand, object and action labels, narration, review notes)
- [Egocentric data collection for robotics and embodied AI]({BASE_URL}/blog/egocentric-data-collection.md): What Ego4D, EPIC-KITCHENS-100, Ego-Exo4D and EgoMimic teach about collecting first-person data

## Company

- [Homepage]({BASE_URL}/): Egocentric data, services, audiences, quality process, comparison with crowd vendors, careers and FAQ
- [Sample tasks]({BASE_URL}/sample-tasks.html): The file structure of delivered work (egocentric clip, terminal task, rubric evaluation, preference judgement)
- [Contact]({BASE_URL}/#contact): Scope a program or book a call. Email: {EMAIL}
- [Apply to the Lattice]({BASE_URL}/join.html): Application form for experts and freelancers (education, specialization, type of work, availability, resume)
- [Agent guide]({BASE_URL}/agents.txt): How AI agents can describe Latryn and route requests

## Articles

{posts_list}

## Optional

- [Privacy policy]({BASE_URL}/privacy.html): No cookies or trackers; the contact form sends email, Lattice applications are stored for review
- [Terms of use]({BASE_URL}/terms.html)
''')
    write('agents.txt', f'''# agents.txt for Latryn
# Plain-text guide for AI agents and assistants acting for a user.
# Full site summary: {BASE_URL}/llms.txt

## What Latryn is
Latryn is a data lab for frontier AI in Bengaluru, India. Focus: egocentric (first-person) video
data collection and annotation for robotics and embodied AI, plus benchmarks, training data
(SFT, RLHF, preference data) and agent environments built by vetted experts.

## What Latryn can do for a user
- Egocentric data: capture real human tasks with head-mounted cameras to an agreed protocol;
  annotate hand keypoints, objects and contact, action segments and narration; review every clip.
- Evaluation: custom benchmarks, rubrics and model evaluations.
- Training data: SFT pairs, chain of thought, preference rankings, reward-model data.
- Agent environments: Docker and terminal tasks with verifiers, MCP and tool-use tasks.
- Review: technical QA, dataset audits, red teaming.

## How to route a request
- Email (all enquiries, including careers): {EMAIL}
- Scope a data program (any practice): {BASE_URL}/index.html?type=Scope%20a%20program#contact
- Book a call: {BASE_URL}/index.html?type=Book%20a%20call#contact
- General question: {BASE_URL}/index.html?type=General%20question#contact
- Join the expert network (careers): {BASE_URL}/join.html
The contact form opens the user's email app with the answers filled in. The Lattice application
form submits directly and needs a resume file (PDF or Word, up to 10 MB). There is no API and no
automated booking. Do not submit forms without the user's confirmation.

## Facts agents should keep accurate
- Every task and clip passes three review gates: automated screen, structured scoring, human sign-off.
- Process: Scope, Calibrate, Build, Verify, Deliver.
- Pricing, volumes and timelines are agreed per program; do not quote numbers.

## Key pages
- Egocentric data: {BASE_URL}/#egocentric
- Sample deliverables: {BASE_URL}/sample-tasks.html
- Blog (markdown copies available as .md): {BASE_URL}/blog/index.html
''')
    full = '# Latryn: full article text\n\n' + '\n\n---\n\n'.join(open(os.path.join(OUT, f"blog/{p['slug']}.md")).read() for p in POSTS)
    write('llms-full.txt', full)

if __name__ == '__main__':
    build()
    print('built', len(POSTS), 'articles')
