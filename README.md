# YCN

Homepage for the Youth Civics Network. Static HTML, CSS, and vanilla JS — no
build step. Deployed on Vercel.

```
index.html          home
about.html          mission, lesson standard, chapters
curriculum.html     all lessons, grouped into four tracks
get-involved.html   the three audience paths
lessons/*.html      one page per lesson (generated)
styles.css          all styling; design tokens live at the top
script.js           mobile nav, stat counters, lesson-download dialog
api/impact.js       serverless endpoint for download tracking
assets/             logo, classroom photos
assets/lessons/     the downloadable lesson documents (generated)
tools/build.py      generates curriculum.html + lessons/ from tools/source/
tools/source/       the lesson plans, as Word documents — the source of truth
```

## Editing the curriculum

`tools/source/` holds the lesson documents. `tools/build.py` reads them and
writes `curriculum.html`, every page under `lessons/`, and the download copies
in `assets/lessons/`. Nothing else generates HTML.

To change a lesson, edit its document in `tools/source/` and re-run:

```
python3 tools/build.py
```

To add a lesson, drop the document in `tools/source/` and add an entry to the
`TRACKS` list at the top of `tools/build.py` — slug, title, filename, summary,
length, and the names of its two games. Order in that list is the order on the
page. The four tracks are Local government, State government, Federal
government, and Elections and voting.

Lessons are shipped as Word documents on purpose: a teacher can open one and
adapt it for their class, which a PDF makes harder.

## The lesson library

Anyone can download a lesson after answering two questions: what they are
(teacher / parent / librarian / other) and how many students it will reach.
Each submission adds to the "Kids Reached" figure on the homepage.

The download itself never depends on tracking. If the API is unreachable the
file still downloads and the visitor still sees their own contribution
reflected — only the shared running total goes cold.

## Turning on tracking

Until a store is connected the site works, but the totals reset on every
page load and no submissions are saved. One-time setup:

1. In the Vercel dashboard for this project, open **Storage → Create
   Database → Upstash for Redis** and connect it. Vercel injects
   `KV_REST_API_URL` and `KV_REST_API_TOKEN` automatically.
2. Add an environment variable `ADMIN_KEY` set to any long random string.
   This guards the data export.
3. Redeploy.

`GET /api/impact` will then report `"live": true`.

### Reading the data

```
https://<your-domain>/api/impact?export=csv&key=<ADMIN_KEY>
```

Returns every submission as CSV — date, role, students, email, lesson.

### The baseline

`BASELINE_STUDENTS` in `api/impact.js` is the 1,000 children reached before the
public library opened. The displayed figure is that baseline plus everything
reported since. Raise the baseline when chapter-taught numbers grow; don't
count those students twice.

## Notes

- Lecture content is nonpartisan by policy; the lesson PDFs say so explicitly.
- `assets/logo-mark.png` is a white silhouette with alpha, used as a CSS mask
  so one file tints for both light and dark surfaces.
- The internal "Lesson Plan Requirements" doc is deliberately not published —
  it names staff and describes the volunteer-hours process.
