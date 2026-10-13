/**
 * Impact + lesson-download tracking.
 *
 *   GET  /api/impact              -> { students, downloads, baseline, total }
 *   POST /api/impact              -> record one download, returns updated totals
 *   GET  /api/impact?export=csv&key=…  -> CSV of every submission (needs ADMIN_KEY)
 *
 * Storage is Upstash Redis over its REST API, which Vercel's Upstash
 * integration provisions as KV_REST_API_URL + KV_REST_API_TOKEN. No npm
 * dependency, so this repo stays build-free.
 *
 * With no store connected the endpoint still answers: reads return the
 * baseline and writes report notStored, so the download flow keeps working
 * and only the running total goes cold.
 */

const BASELINE_STUDENTS = 1000; // children reached before the public library opened
const KEY_STUDENTS = "ycn:students";
const KEY_DOWNLOADS = "ycn:downloads";
const KEY_RECORDS = "ycn:records";

const MAX_STUDENTS_PER_SUBMISSION = 2000;
const ROLES = ["teacher", "parent", "librarian", "other"];

const url = process.env.KV_REST_API_URL;
const token = process.env.KV_REST_API_TOKEN;
const hasStore = Boolean(url && token);

async function redis(command) {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(command),
  });
  if (!res.ok) throw new Error(`redis ${res.status}`);
  const json = await res.json();
  return json.result;
}

function totals(students, downloads) {
  const reported = Number(students) || 0;
  return {
    baseline: BASELINE_STUDENTS,
    reported,
    total: BASELINE_STUDENTS + reported,
    downloads: Number(downloads) || 0,
    live: hasStore,
  };
}

function clean(value, max) {
  return String(value == null ? "" : value)
    .replace(/[\r\n\t]+/g, " ")
    .trim()
    .slice(0, max);
}

function csvCell(value) {
  const s = String(value == null ? "" : value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  try {
    if (req.method === "GET") {
      if (req.query && req.query.export === "csv") {
        const adminKey = process.env.ADMIN_KEY;
        if (!adminKey || req.query.key !== adminKey) {
          return res.status(401).json({ error: "Unauthorized." });
        }
        if (!hasStore) return res.status(200).send("");

        const rows = (await redis(["LRANGE", KEY_RECORDS, "0", "-1"])) || [];
        const header = "date,role,students,email,lesson\n";
        const body = rows
          .map((row) => {
            let r;
            try {
              r = JSON.parse(row);
            } catch {
              return "";
            }
            return [r.date, r.role, r.students, r.email, r.lesson]
              .map(csvCell)
              .join(",");
          })
          .filter(Boolean)
          .join("\n");

        res.setHeader("Content-Type", "text/csv; charset=utf-8");
        res.setHeader(
          "Content-Disposition",
          'attachment; filename="ycn-lesson-downloads.csv"'
        );
        return res.status(200).send(header + body);
      }

      if (!hasStore) return res.status(200).json(totals(0, 0));

      const [students, downloads] = await Promise.all([
        redis(["GET", KEY_STUDENTS]),
        redis(["GET", KEY_DOWNLOADS]),
      ]);
      return res.status(200).json(totals(students, downloads));
    }

    if (req.method === "POST") {
      const body =
        typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};

      const students = Math.floor(Number(body.students));
      if (!Number.isFinite(students) || students < 1) {
        return res.status(400).json({ error: "Enter how many students this reaches." });
      }
      if (students > MAX_STUDENTS_PER_SUBMISSION) {
        return res.status(400).json({
          error: `That looks too high — enter ${MAX_STUDENTS_PER_SUBMISSION} or fewer.`,
        });
      }

      const role = ROLES.includes(body.role) ? body.role : "other";
      const email = clean(body.email, 120);
      if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        return res.status(400).json({ error: "Check the email address." });
      }

      if (!hasStore) {
        return res
          .status(200)
          .json({ ...totals(0, 0), notStored: true, added: students });
      }

      const record = JSON.stringify({
        date: new Date().toISOString(),
        role,
        students,
        email,
        lesson: clean(body.lesson, 80),
      });

      const [newStudents, newDownloads] = await Promise.all([
        redis(["INCRBY", KEY_STUDENTS, String(students)]),
        redis(["INCR", KEY_DOWNLOADS]),
        redis(["RPUSH", KEY_RECORDS, record]),
      ]);

      return res.status(200).json({ ...totals(newStudents, newDownloads), added: students });
    }

    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ error: "Method not allowed." });
  } catch (err) {
    // Never block a download because tracking failed.
    return res.status(200).json({ ...totals(0, 0), notStored: true, error: String(err.message || err) });
  }
};
