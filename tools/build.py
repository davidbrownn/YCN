#!/usr/bin/env python3
"""
Generates the curriculum index and one page per lesson from the source
Word documents in tools/source/.

The site has no build step — this writes plain HTML that is committed
alongside everything else. Re-run it after editing a lesson document:

    python3 tools/build.py
"""

import html
import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "source")
OUT_LESSONS = os.path.join(ROOT, "lessons")
OUT_FILES = os.path.join(ROOT, "assets", "lessons")

# --------------------------------------------------------------------------
# Curriculum manifest — order here is the order on the page.
# --------------------------------------------------------------------------

TRACKS = [
    {
        "id": "local",
        "name": "Local government",
        "blurb": "The decisions closest to a student — who fixes the playground, "
                 "who runs the library, who sets the rules at their own school.",
        "lessons": [
            {
                "slug": "city-councils",
                "title": "City Councils",
                "doc": "Copy of Lesson Plans_ City Council (Week 1).docx",
                "summary": "Who sits on a city council and how they decide what a city "
                           "builds. Students pool a budget they cannot stretch, then argue "
                           "a real problem in front of a student council.",
                "length": "~35 min",
                "games": "The Great Budget Debate · Council Pass",
            },
            {
                "slug": "mayors-office",
                "title": "The Mayor's Office",
                "doc": "Copy of Lesson Plans for Mayor's office.docx",
                "summary": "What a mayor actually does, and why two cities the same size "
                           "can be run completely differently. Compares the strong-mayor "
                           "and city-manager systems.",
                "length": "~35 min",
                "games": "City problem cards · Design your own city",
            },
            {
                "slug": "school-boards",
                "title": "School Boards",
                "doc": "Copy of Lesson Plan 2_ School Boards.docx",
                "summary": "The board that sets the rules of a student's own school — what "
                           "it controls, who serves on it, and why its members aren't teachers.",
                "length": "~35 min",
                "games": "Write a policy · Rapid-fire review",
            },
            {
                "slug": "libraries-and-parks",
                "title": "Public Libraries and Parks",
                "doc": "Copy of Lesson Plans_ Public Libraries and Parks & Recreation Departments (Week 2).docx",
                "summary": "The two public spaces students already use, and the departments "
                           "that keep them open. Sorts fact from fiction about what a library "
                           "is allowed to do.",
                "length": "~35 min",
                "games": "Fiction or Non-Fiction · Design a park",
            },
            {
                "slug": "public-transit",
                "title": "Public Transit Authorities",
                "doc": "Copy of Lesson Plan_ Public Transit Authorities.docx",
                "summary": "The agencies that run buses and trains, and who depends on them. "
                           "Students act out the same trip twice — once with an agency, once "
                           "without.",
                "length": "~35 min",
                "games": "Design a transit agency · With and without",
            },
            {
                "slug": "first-responders",
                "title": "Police and Firefighters",
                "doc": "Copy of Lesson Plan_ Police and Firefighters.docx",
                "summary": "What first responders do and how the two roles differ. Students "
                           "sort real scenarios into police, firefighter, or both — and find "
                           "out how often the answer is both.",
                "length": "~35 min",
                "games": "Draw a first responder · Scenario sort",
            },
        ],
    },
    {
        "id": "state",
        "name": "State government",
        "blurb": "The layer most adults can't name either — legislatures, courts, "
                 "attorneys general, and the agencies that issue a driver's licence.",
        "lessons": [
            {
                "slug": "state-legislatures",
                "title": "State Legislatures",
                "doc": "Copy of Youth Civics Network_ Lesson Plan, State Legislatures.docx",
                "summary": "Students research a real committee in their own state "
                           "legislature, find a bill it is considering, and argue for or "
                           "against it in front of the class.",
                "length": "~40 min",
                "games": "Committee research · Propose and vote",
            },
            {
                "slug": "state-courts-and-attorney-general",
                "title": "State Courts and the Attorney General",
                "doc": "Copy of Lesson Plans_ State Courts and Attorney General (Week 4).docx",
                "summary": "Who enforces a state's laws, and who decides what they mean. "
                           "Opens with a genuinely hard question: would you prosecute your "
                           "own friend?",
                "length": "~35 min",
                "games": "SAG Says · Courtroom roles",
            },
            {
                "slug": "state-agencies",
                "title": "State Agencies",
                "doc": "Copy of Lesson Plan Requirements_ State Agencies.docx",
                "summary": "The DMV, the health department, the transportation department — "
                           "the bodies that carry out state law and touch daily life more "
                           "often than the legislature does.",
                "length": "~35 min",
                "games": "Match the agency · Run your own",
            },
        ],
    },
    {
        "id": "federal",
        "name": "Federal government",
        "blurb": "Congress, the committees where bills actually get written, and the "
                 "departments that carry the results out.",
        "lessons": [
            {
                "slug": "congress",
                "title": "Congress: How a Bill Becomes Law",
                "doc": "Copy of Lesson Plans for 3-5th grade ESD @ Lewisville ISD.docx",
                "summary": "Our fullest unit. Students draw their own districts, put bills "
                           "in a hat, and run a mock Congress through the House, the Senate, "
                           "and a presidential signature — then do it again at state level.",
                "length": "Multi-week series",
                "games": "Draw your district · Mock Congress · State budget",
            },
            {
                "slug": "congressional-committees",
                "title": "Congressional Committees",
                "doc": "Copy of Lesson Plans for Congressional Committees.docx",
                "summary": "Why Congress splits itself into small groups before it votes. "
                           "Students match real bills to the committee that would study them, "
                           "then sit as the committee themselves.",
                "length": "~35 min",
                "games": "Bill-to-committee match · Committee vote",
            },
            {
                "slug": "cabinet-departments",
                "title": "Cabinet Departments",
                "doc": "Copy of Lesson Plans_ Cabinet Departments (Week 3).docx",
                "summary": "The fifteen departments that advise the president and run the "
                           "executive branch, covering the five students are most likely to "
                           "hear about.",
                "length": "~35 min",
                "games": "Department Freeze · Advise the president",
            },
            {
                "slug": "department-of-education",
                "title": "The Department of Education",
                "doc": "Copy of DOE Lesson Plan YCN.docx",
                "summary": "What the federal education department does — and, just as "
                           "usefully, what it doesn't. Students sort decisions between "
                           "Washington, the district, and their own principal.",
                "length": "~35 min",
                "games": "Who decides? · Principal for a day",
            },
            {
                "slug": "health-and-human-services",
                "title": "Health and Human Services",
                "doc": "Copy of Lesson Plan Requirements_ Department of Health and Human Services.docx",
                "summary": "The department behind disease tracking, food and medicine safety, "
                           "and medical research, introduced through the sub-agencies students "
                           "have already heard of.",
                "length": "~35 min",
                "games": "Agency match · Outbreak response",
            },
        ],
    },
    {
        "id": "elections",
        "name": "Elections and voting",
        "blurb": "How a vote turns into an outcome — including the parts of the "
                 "process that surprise adults.",
        "lessons": [
            {
                "slug": "electoral-college",
                "title": "The Electoral College",
                "doc": "Copy of Lesson Plan Requirements_ Electoral College.docx",
                "summary": "Why the person with the most votes doesn't automatically win. "
                           "Walks through electors, the 270 threshold, and what happens in a "
                           "269–269 tie.",
                "length": "~35 min",
                "games": "Mock electoral map · Tiebreaker",
            },
            {
                "slug": "ballot-measures",
                "title": "Ballot Measures and Referendums",
                "doc": "Copy of Lesson Plan_ Ballot Measures and Referendums.docx",
                "summary": "Direct democracy: the questions voters decide themselves, without "
                           "going through a legislature. Opens with a class vote on who really "
                           "makes the decisions.",
                "length": "~35 min",
                "games": "Write a ballot measure · Class referendum",
            },
            {
                "slug": "campaign-finance",
                "title": "Campaign Finance",
                "doc": "Copy of Campaign Finances_ How Candidates Raise and Spend Their Money (Week 5).docx",
                "summary": "Where campaign money comes from, what it buys, and the rules "
                           "around it — starting from the donation ads students have already "
                           "scrolled past.",
                "length": "~35 min",
                "games": "Campaign Signals · The Coin Clapper Election",
            },
        ],
    },
]

SECTION_PATTERNS = [
    ("warmup", re.compile(r"^\s*(?:\d+[\.\)]\s*)?warm[\s\-–]?up\b", re.I)),
    ("lecture", re.compile(r"^\s*(?:\d+[\.\)]\s*)?(?:lecture|lectures|opens\s+w/)", re.I)),
    ("games", re.compile(r"^\s*(?:\d+[\.\)]\s*)?(?:\d+\s+)?(?:interactive\s+)?game", re.I)),
    ("wrapup", re.compile(r"^\s*(?:\d+[\.\)]\s*)?wrap[\s\-–]?up", re.I)),
]

SECTION_LABELS = {
    "warmup": ("Warm-up", "5 min"),
    "lecture": ("Lecture", "10 min"),
    "games": ("Games", "2 activities"),
    "wrapup": ("Wrap-up", "5 min"),
}

URL_RE = re.compile(r"(https?://[^\s<>\"')]+)")


def read_paragraphs(path):
    """Return [(indent_level, text)] for a .docx, preserving list nesting."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf8", "ignore")
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>|<w:p/>", xml, re.S):
        lvl = re.search(r'<w:ilvl w:val="(\d+)"', p)
        numbered = "<w:numPr>" in p
        text = html.unescape(re.sub(r"<[^>]+>", "", p)).replace("\xa0", " ").strip()
        if not text:
            continue
        depth = int(lvl.group(1)) if lvl else 0
        out.append((depth if numbered else -1, text))
    return out


def esc(s):
    return html.escape(s, quote=False)


def linkify(s):
    return URL_RE.sub(
        lambda m: f'<a href="{html.escape(m.group(1))}" rel="nofollow noopener" target="_blank">{esc(m.group(1))}</a>',
        esc(s),
    )


def split_sections(paras):
    """Split a lesson into intro + the four canonical beats."""
    intro, sections, current = [], [], None
    for depth, text in paras:
        matched = None
        if depth <= 0:
            for key, pat in SECTION_PATTERNS:
                if pat.match(text):
                    matched = key
                    break
        if matched:
            # A "Games" heading repeated per game folds into one section.
            if current and current["key"] == matched:
                current["items"].append((0, text))
                continue
            current = {"key": matched, "heading": text, "items": []}
            sections.append(current)
        elif current:
            current["items"].append((max(depth, 0), text))
        else:
            intro.append(text)
    return intro, sections


def render_items(items):
    """Rebuild nested lists from indent levels.

    Source documents sometimes jump a level (0 straight to 2). Each opened
    level therefore carries its own <li>, with an empty wrapper inserted for
    any level that was skipped, so the markup stays balanced.
    """
    out, depths = [], []
    for depth, text in items:
        depth = max(0, depth)
        while len(depths) > depth + 1:
            out.append("</li></ul>")
            depths.pop()
        if len(depths) == depth + 1:
            out.append("</li>")
        while len(depths) < depth + 1:
            out.append(f'<ul class="lp-list lp-list--{min(len(depths), 2)}">')
            depths.append(len(depths))
            if len(depths) < depth + 1:
                out.append('<li class="lp-wrap">')
        out.append(f"<li>{linkify(text)}")
    while depths:
        out.append("</li></ul>")
        depths.pop()
    return "\n".join(out)


# --------------------------------------------------------------------------
# Page shell
# --------------------------------------------------------------------------

def shell(root, title, description, body, active, extra_head=""):
    def r(p):
        return root + p
    nav = [
        ("About", r("about.html"), "about"),
        ("Curriculum", r("curriculum.html"), "curriculum"),
        ("Get Involved", r("get-involved.html"), "get-involved"),
    ]
    CUR = ' aria-current="page"'
    nav_html = "\n".join(
        '        <li><a href="%s"%s>%s</a></li>' % (href, CUR if key == active else "", label)
        for label, href, key in nav
    )
    mob_html = "\n".join(
        '      <li><a href="%s"%s>%s</a></li>' % (href, CUR if key == active else "", label)
        for label, href, key in nav
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<link rel="icon" href="{r('assets/favicon.png')}" type="image/png">
<link rel="apple-touch-icon" href="{r('assets/favicon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r('styles.css')}">{extra_head}
</head>
<body>

<a class="skip-link" href="#main">Skip to main content</a>

<header class="site-header" id="site-header">
  <div class="inner site-header__inner">
    <a class="logo" href="{r('index.html')}" aria-label="Youth Civics Network — home">
      <span class="logo__mark" role="img" aria-hidden="true"></span>
    </a>

    <nav class="site-nav" aria-label="Primary">
      <ul>
{nav_html}
      </ul>
    </nav>

    <a class="btn btn--primary btn--sm site-header__cta" href="mailto:youthcivicsnetwork@gmail.com">Join / Volunteer</a>

    <button class="menu-toggle" id="menu-toggle" aria-expanded="false" aria-controls="mobile-nav">
      <span class="sr-only">Toggle menu</span>
      <span class="menu-toggle__bar"></span>
      <span class="menu-toggle__bar"></span>
      <span class="menu-toggle__bar"></span>
    </button>
  </div>

  <nav class="mobile-nav" id="mobile-nav" aria-label="Mobile">
    <ul>
{mob_html}
      <li><a class="btn btn--primary" href="mailto:youthcivicsnetwork@gmail.com">Join / Volunteer</a></li>
    </ul>
  </nav>
</header>

<main id="main">
{body}
</main>

{footer(root)}
{modal(root)}
<script src="{r('script.js')}" defer></script>
</body>
</html>
"""


def footer(root):
    def r(p):
        return root + p
    return f"""<footer class="site-footer">
  <div class="inner site-footer__grid">
    <div class="site-footer__brand">
      <p class="site-footer__logo">
        <span class="logo__mark logo__mark--light" role="img" aria-hidden="true"></span>
        <span class="sr-only">Youth Civics Network</span>
      </p>
      <p>Nonpartisan civic education for the next generation.</p>
    </div>

    <div>
      <h3>Navigate</h3>
      <ul>
        <li><a href="{r('about.html')}">About</a></li>
        <li><a href="{r('curriculum.html')}">Curriculum</a></li>
        <li><a href="{r('get-involved.html')}">Get Involved</a></li>
      </ul>
    </div>

    <div>
      <h3>Connect</h3>
      <ul>
        <li><a href="https://www.instagram.com/youthcivicsnetwork/">Instagram</a></li>
        <li><a href="https://www.linkedin.com/company/youthcivicsnetwork/">LinkedIn</a></li>
        <li><a href="https://www.tiktok.com/@youthcivicsnetwork">TikTok</a></li>
      </ul>
    </div>

    <div>
      <h3>Support</h3>
      <p>YCN is pursuing 501(c)(3) status. Your support helps us bring civics
         to every classroom.</p>
      <a class="btn btn--outline-light btn--sm" href="mailto:youthcivicsnetwork@gmail.com">Donate</a>
    </div>
  </div>

  <div class="inner site-footer__legal">
    <p>© 2026 Youth Civics Network. All rights reserved.</p>
  </div>
</footer>"""


def modal(root):
    return """<div class="modal" id="download-modal" hidden>
  <div class="modal__scrim" data-modal-close></div>
  <div class="modal__panel" role="dialog" aria-modal="true"
       aria-labelledby="modal-title" aria-describedby="modal-desc">
    <button class="modal__close" type="button" data-modal-close aria-label="Close">
      <span aria-hidden="true">✕</span>
    </button>

    <form class="modal__form" id="download-form" novalidate>
      <p class="eyebrow"><span class="eyebrow__rule" aria-hidden="true"></span>Two questions</p>
      <h2 id="modal-title">Download <span id="modal-lesson">this lesson</span></h2>
      <p class="modal__lede" id="modal-desc">
        Your answers let us count the students this reaches. That total is the number
        on this site — it goes up when you tell us.
      </p>

      <fieldset class="field">
        <legend>You're a…</legend>
        <div class="radio-row">
          <label class="radio"><input type="radio" name="role" value="teacher" checked><span>Teacher</span></label>
          <label class="radio"><input type="radio" name="role" value="parent"><span>Parent</span></label>
          <label class="radio"><input type="radio" name="role" value="librarian"><span>Librarian</span></label>
          <label class="radio"><input type="radio" name="role" value="other"><span>Other</span></label>
        </div>
      </fieldset>

      <div class="field">
        <label for="students">How many students will this reach?</label>
        <input type="number" id="students" name="students" inputmode="numeric"
               min="1" max="2000" step="1" required
               aria-describedby="students-help students-error">
        <p class="field__help" id="students-help">A rough count is fine — one class, one co-op, one club.</p>
        <p class="field__error" id="students-error" role="alert" hidden></p>
      </div>

      <div class="field">
        <label for="email">Email <span class="field__optional">(optional)</span></label>
        <input type="email" id="email" name="email" autocomplete="email"
               aria-describedby="email-help email-error">
        <p class="field__help" id="email-help">Only so we can send updates to this lesson. We don't share it.</p>
        <p class="field__error" id="email-error" role="alert" hidden></p>
      </div>

      <button class="btn btn--primary modal__submit" type="submit" id="download-submit">
        Get the lesson
      </button>
      <p class="modal__fineprint">Free to use and adapt. Please keep it nonpartisan.</p>
    </form>

    <div class="modal__done" id="download-done" hidden>
      <p class="modal__check" aria-hidden="true">↓</p>
      <h2>Your download is starting.</h2>
      <p class="modal__lede" id="download-done-msg"></p>
      <p class="modal__fallback">
        Nothing happened? <a id="download-fallback" href="#" download>Download it directly.</a>
      </p>
      <button class="btn btn--outline-dark" type="button" data-modal-close>Close</button>
    </div>
  </div>
</div>"""


def dl_button(root, lesson, label="Download lesson"):
    return (
        f'<button class="lesson__btn" type="button"\n'
        f'        data-lesson-file="{root}assets/lessons/ycn-{lesson["slug"]}.docx"\n'
        f'        data-lesson-title="{html.escape(lesson["title"])}">\n'
        f'  {label}<span class="lesson__arrow" aria-hidden="true">↓</span>\n'
        f'</button>'
    )


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def build():
    os.makedirs(OUT_LESSONS, exist_ok=True)
    os.makedirs(OUT_FILES, exist_ok=True)

    total = sum(len(t["lessons"]) for t in TRACKS)
    all_lessons = [(t, l) for t in TRACKS for l in t["lessons"]]

    # ---- lesson pages ----
    for idx, (track, lesson) in enumerate(all_lessons):
        src = os.path.join(SRC, lesson["doc"])
        paras = read_paragraphs(src)
        intro, sections = split_sections(paras)

        # ship the source document under a clean name
        shutil.copyfile(src, os.path.join(OUT_FILES, f"ycn-{lesson['slug']}.docx"))

        body = []
        body.append('<article class="lp">')
        body.append('  <div class="inner">')
        body.append('    <nav class="crumbs" aria-label="Breadcrumb"><ol>')
        body.append('      <li><a href="../index.html">Home</a></li>')
        body.append('      <li><a href="../curriculum.html">Curriculum</a></li>')
        body.append(f'      <li aria-current="page">{esc(lesson["title"])}</li>')
        body.append('    </ol></nav>')

        body.append('    <header class="lp__head">')
        body.append(f'      <p class="eyebrow"><span class="eyebrow__rule" aria-hidden="true"></span>{esc(track["name"])}</p>')
        body.append(f'      <h1>{esc(lesson["title"])}</h1>')
        body.append(f'      <p class="lp__summary">{esc(lesson["summary"])}</p>')
        body.append('      <p class="lesson__meta">'
                    '<span>Grades 3–5</span>'
                    f'<span>{esc(lesson["length"])}</span>'
                    '<span>Nonpartisan</span></p>')
        body.append('      <div class="lp__actions">')
        body.append("        " + dl_button("../", lesson, "Download the lesson plan"))
        body.append('        <p class="lp__format">Word document — open it in Word, Pages, or Google Docs and adapt it for your class.</p>')
        body.append('      </div>')
        body.append('    </header>')

        if intro:
            body.append('    <div class="lp__intro">')
            for p in intro[1:] if len(intro) > 1 else intro:
                body.append(f"      <p>{linkify(p)}</p>")
            body.append('    </div>')

        body.append('    <div class="lp__body">')
        for i, sec in enumerate(sections, 1):
            label, dur = SECTION_LABELS.get(sec["key"], ("Section", ""))
            body.append('      <section class="lp__section">')
            body.append('        <div class="lp__marker">')
            body.append(f'          <span class="lp__num">{i:02d}</span>')
            body.append(f'          <span class="lp__label">{esc(label)}</span>')
            if dur:
                body.append(f'          <span class="lp__dur">{esc(dur)}</span>')
            body.append('        </div>')
            body.append('        <div class="lp__content">')
            body.append(f'          <h2>{linkify(sec["heading"])}</h2>')
            if sec["items"]:
                body.append(render_items(sec["items"]))
            body.append('        </div>')
            body.append('      </section>')
        body.append('    </div>')

        # prev / next
        prev_l = all_lessons[idx - 1][1] if idx > 0 else None
        next_l = all_lessons[idx + 1][1] if idx < len(all_lessons) - 1 else None
        body.append('    <nav class="lp__nav" aria-label="More lessons">')
        if prev_l:
            body.append(f'      <a class="lp__nav-link" href="{prev_l["slug"]}.html">'
                        f'<span class="lp__nav-dir">← Previous</span>'
                        f'<span class="lp__nav-title">{esc(prev_l["title"])}</span></a>')
        else:
            body.append('      <span></span>')
        if next_l:
            body.append(f'      <a class="lp__nav-link lp__nav-link--next" href="{next_l["slug"]}.html">'
                        f'<span class="lp__nav-dir">Next →</span>'
                        f'<span class="lp__nav-title">{esc(next_l["title"])}</span></a>')
        else:
            body.append('      <span></span>')
        body.append('    </nav>')
        body.append('  </div>')
        body.append('</article>')

        page = shell(
            "../",
            f'{lesson["title"]} — YCN Curriculum',
            lesson["summary"],
            "\n".join(body),
            "curriculum",
        )
        with open(os.path.join(OUT_LESSONS, f'{lesson["slug"]}.html'), "w") as f:
            f.write(page)

    # ---- curriculum index ----
    body = []
    body.append('<section class="page-head page-head--curriculum">')
    body.append('  <div class="inner">')
    body.append('    <p class="eyebrow"><span class="eyebrow__rule" aria-hidden="true"></span>Open curriculum</p>')
    body.append('    <h1>Every lesson we teach, free to take.</h1>')
    body.append(f'    <p class="page-head__lede">{total} lessons across four tracks, built for grades 3–5 '
                'and written to the same shape: a five-minute warm-up, ten minutes of instruction, '
                'two games, and a wrap-up. You do not need to be a YCN chapter to use any of it.</p>')
    body.append('    <ul class="track-jump">')
    for t in TRACKS:
        body.append(f'      <li><a href="#{t["id"]}">{esc(t["name"])} <span>{len(t["lessons"])}</span></a></li>')
    body.append('    </ul>')
    body.append('  </div>')
    body.append('</section>')

    for t in TRACKS:
        body.append(f'<section class="track" id="{t["id"]}">')
        body.append('  <div class="inner">')
        body.append('    <div class="track__head">')
        body.append(f'      <h2>{esc(t["name"])}</h2>')
        body.append(f'      <p>{esc(t["blurb"])}</p>')
        body.append('    </div>')
        body.append('    <ul class="lesson-list">')
        for l in t["lessons"]:
            body.append('      <li class="lesson">')
            body.append('        <div class="lesson__head">')
            body.append(f'          <p class="lesson__tag">{esc(t["name"])}</p>')
            body.append(f'          <h3><a href="lessons/{l["slug"]}.html">{esc(l["title"])}</a></h3>')
            body.append('        </div>')
            body.append('        <div class="lesson__main">')
            body.append(f'          <p class="lesson__desc">{esc(l["summary"])}</p>')
            body.append('          <p class="lesson__meta">'
                        '<span>Grades 3–5</span>'
                        f'<span>{esc(l["length"])}</span>'
                        f'<span>{esc(l["games"])}</span></p>')
            body.append('        </div>')
            body.append('        <div class="lesson__actions">')
            body.append(f'          <a class="lesson__view" href="lessons/{l["slug"]}.html">Read the plan<span class="lesson__arrow" aria-hidden="true">→</span></a>')
            body.append("          " + dl_button("", l, "Download"))
            body.append('        </div>')
            body.append('      </li>')
        body.append('    </ul>')
        body.append('  </div>')
        body.append('</section>')

    body.append('<section class="cta-band">')
    body.append('  <div class="inner cta-band__inner">')
    body.append('    <h2>Using these with your class?</h2>')
    body.append('    <p>Tell us how it went, or ask for the slide decks that go with a lesson. '
                'We answer every message.</p>')
    body.append('    <a class="btn btn--primary" href="mailto:youthcivicsnetwork@gmail.com">Email the curriculum team</a>')
    body.append('  </div>')
    body.append('</section>')

    with open(os.path.join(ROOT, "curriculum.html"), "w") as f:
        f.write(shell(
            "",
            "Curriculum — Youth Civics Network",
            f"{total} free, nonpartisan civics lessons for grades 3–5, covering local, "
            "state, and federal government plus elections and voting.",
            "\n".join(body),
            "curriculum",
        ))

    print(f"built {total} lesson pages + curriculum.html")


if __name__ == "__main__":
    build()
