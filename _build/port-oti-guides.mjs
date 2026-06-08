#!/usr/bin/env node
/**
 * port-oti-guides.mjs
 *
 * ממיר את 11 מדריכי האוטי המקוריים ל-12 מדריכי רצף בעטיפת הסגנון הסגול.
 * השינוי המינימלי האפשרי כדי לא לסכן את התוכן או את ה-JS הספציפי לכל מדריך:
 *   1) מחליף את 3 קבצי ה-CSS של אוטי בקובץ אחד: rezef-guides.css
 *   2) מחליף את <nav class="navbar"> בנאב של רצף (.rezef-nav)
 *   3) מחליף את שני הפוטרים (.author-footer + .guide-footer) בפוטר של רצף + breadcrumb
 *
 * תוצאה נכתבת לשני מקומות:
 *   - docs/rezef/guides/        (עותק חי לתצוגה)
 *   - _drafts/rezef-from-liron/guides/  (הכנה ל-PR ללירון)
 */

import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT       = join(__dirname, '..', '..', '..');
const SRC_DIR    = join(ROOT, 'docs', 'autism', 'oti', 'guides');
const DOCS_DEST  = join(ROOT, 'docs', 'rezef', 'guides');
const DRAFT_DEST = join(ROOT, '_drafts', 'rezef-from-liron', 'guides');

const GUIDES = [
  'after-disclosure.html',
  'bureaucracy.html',
  'diagnosis-received.html',
  'hygiene.html',
  'independent-living.html',
  'job-interview.html',
  'parent-guide.html',
  'sensory-overload.html',
  'sexuality.html',
  'small-talk.html',
  'vaada-talking.html',
];

/* ─────────── REPLACEMENTS ─────────── */

const REZEF_NAV = `<nav class="rezef-nav">
  <a href="../index.html#" class="logo">
    <svg class="logo-svg" viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <path d="M4 36 C4 16 20 10 20 10 C20 10 36 16 36 36" stroke="#A78BFA" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      <path d="M8.5 36 C8.5 19 20 14 20 14 C20 14 31.5 19 31.5 36" stroke="#312E81" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      <path d="M13 36 C13 22 20 18 20 18 C20 18 27 22 27 36" stroke="#7C3AED" stroke-width="3.5" stroke-linecap="round" fill="none"/>
      <circle cx="20" cy="36" r="2.8" fill="#7C3AED"/>
    </svg>
    <div>
      <div class="logo-name">רֶצֶף</div>
      <div class="logo-tag">מענים לקהילה האוטיסטית ובני משפחותיהם לאורך כל שלבי החיים</div>
    </div>
  </a>
  <ul class="nav-links">
    <li><a href="../index.html#ages">רצף גילאי</a></li>
    <li><a href="../index.html#svc">רצף מענים</a></li>
    <li><a href="../index.html#articles">רצף כתבות</a></li>
    <li><a href="index.html" class="active">רצף מדריכים</a></li>
    <li><a href="../index.html#about">אודות</a></li>
  </ul>
  <a href="../index.html#ages" class="nav-cta">מצאו מענה</a>
</nav>`;

const REZEF_FOOTER = `<footer class="guide-footer">
  <a href="index.html" class="back">← חזרה לכל המדריכים</a>
</footer>

<footer class="rezef-footer">
  <div class="ft-links">
    <a href="../index.html#about">אודות רצף</a>
    <a href="../index.html#svc">רצף מענים</a>
    <a href="../index.html#articles">רצף כתבות</a>
  </div>
  <p class="ft-note">© רצף · מדריכים מבוססי מחקר לקהילה האוטיסטית · נכתבו ע"י מיטל פלג</p>
</footer>`;

const BREADCRUMB = (titleHe) => `<nav class="rezef-breadcrumb" aria-label="פירורי לחם">
  <a href="../index.html">רצף</a>
  <span class="sep">›</span>
  <a href="index.html">מדריכים</a>
  <span class="sep">›</span>
  <span class="current">${titleHe}</span>
</nav>`;

/* ─────────── TRANSFORM ─────────── */

function rewrite(html, titleHe) {
  let out = html;

  /* 1. בקובצי CSS — להסיר את 3 קבצי האוטי + הפונטים של אוטי, להחליף ב-rezef-guides.css */
  // ה-link של גוגל פונטס (Assistant/Heebo/Bellefair/Playpen) — להסיר; הפונטים מ-rezef-guides.css מספיקים
  out = out.replace(/<link\s+href="https:\/\/fonts\.googleapis\.com[^"]*"\s+rel="stylesheet"\s*\/?>\s*/g, '');
  // ה-3 קבצי CSS של אוטי
  out = out.replace(/<link\s+rel="stylesheet"\s+href="\.\.\/\.\.\/assets\/style\.css"\s*\/?>\s*/g, '');
  out = out.replace(/<link\s+rel="stylesheet"\s+href="\.\.\/assets\/oti-theme\.css"\s*\/?>\s*/g, '');
  out = out.replace(/<link\s+rel="stylesheet"\s+href="_shared\.css"\s*\/?>\s*/g, '');

  // להוסיף את ה-CSS שלנו לפני סגירת ה-</head>
  if (!out.includes('rezef-guides.css')) {
    out = out.replace(/<\/head>/i, '<link rel="stylesheet" href="rezef-guides.css">\n</head>');
  }

  /* 2. nav של אוטי — להחליף בנאב של רצף */
  // הנאב במקור: <nav class="navbar">...<\/nav>
  out = out.replace(/<nav\s+class="navbar"[\s\S]*?<\/nav>/, REZEF_NAV);

  /* 3. footer של אוטי — שלב 1: להסיר את ה-author-footer (קיים גם כ-<footer> וגם כ-<div>) */
  out = out.replace(/<footer\s+class="author-footer"[\s\S]*?<\/footer>\s*/g, '');
  out = out.replace(/<div\s+class="author-footer"[\s\S]*?<\/div>\s*/g, '');

  /* שלב 2: להחליף את <footer class="guide-footer"> בפוטר רצף המאוחד.
     אם אין guide-footer בכלל — להזריק לפני </body> או </main>. */
  if (/<footer\s+class="guide-footer"/.test(out)) {
    out = out.replace(/<footer\s+class="guide-footer"[\s\S]*?<\/footer>\s*/, REZEF_FOOTER + '\n\n');
  } else {
    out = out.replace(/(<\/main>|<\/body>)/, `${REZEF_FOOTER}\n\n$1`);
  }

  /* 4. להוסיף breadcrumb אחרי הנאב, לפני <main> או <div class="guide-wrap"> */
  if (!out.includes('rezef-breadcrumb')) {
    out = out.replace(
      /(<\/nav>)\s*(<main\s+class="guide-wrap"|<div\s+class="guide-wrap"|<main>|<main\s)/,
      `$1\n\n${BREADCRUMB(titleHe)}\n\n$2`
    );
  }

  return out;
}

/* ─────────── TITLE EXTRACTION ─────────── */

function extractTitle(html) {
  // מוציא את הכותרת מ-<title> או מ-h1
  const titleMatch = html.match(/<title>([^<]+)<\/title>/);
  if (titleMatch) {
    // <title>שם המדריך | תיאור</title>  → לוקח את החלק הראשון
    return titleMatch[1].split('|')[0].trim();
  }
  const h1Match = html.match(/<h1[^>]*>([^<]+)<\/h1>/);
  return h1Match ? h1Match[1].trim() : 'מדריך';
}

/* ─────────── MAIN ─────────── */

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function processGuide(file) {
  const src  = join(SRC_DIR, file);
  const html = await fs.readFile(src, 'utf-8');
  const titleHe = extractTitle(html);
  const out  = rewrite(html, titleHe);

  for (const dest of [DOCS_DEST, DRAFT_DEST]) {
    await fs.writeFile(join(dest, file), out, 'utf-8');
  }

  return { file, titleHe, sizeBefore: html.length, sizeAfter: out.length };
}

async function copyCss() {
  // מעתיק את rezef-guides.css גם ל-_drafts (קיים כבר ב-docs/rezef/guides/)
  const css = await fs.readFile(join(DOCS_DEST, 'rezef-guides.css'), 'utf-8');
  await fs.writeFile(join(DRAFT_DEST, 'rezef-guides.css'), css, 'utf-8');
}

async function main() {
  await ensureDir(DOCS_DEST);
  await ensureDir(DRAFT_DEST);

  console.log('המרת מדריכי אוטי לעטיפת רצף');
  console.log(`source:  ${SRC_DIR}`);
  console.log(`docs:    ${DOCS_DEST}`);
  console.log(`drafts:  ${DRAFT_DEST}`);
  console.log('');

  const results = [];
  for (const file of GUIDES) {
    try {
      const r = await processGuide(file);
      results.push(r);
      console.log(`✓ ${file.padEnd(28)} ${r.titleHe.padEnd(36)} ${r.sizeBefore}→${r.sizeAfter} bytes`);
    } catch (err) {
      console.error(`✗ ${file}: ${err.message}`);
      throw err;
    }
  }

  await copyCss();
  console.log('');
  console.log(`✓ ${GUIDES.length} מדריכים הומרו בהצלחה ל-2 יעדים.`);
  console.log(`✓ rezef-guides.css הועתק ל-_drafts.`);
}

main().catch((e) => { console.error(e); process.exit(1); });
