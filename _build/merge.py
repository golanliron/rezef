# -*- coding: utf-8 -*-
"""
מצליב את maanim.json של רצף עם all-enriched.json של אוטי,
מעשיר ב-kupot + url_status, ומוסיף את אנשי הקשר של טלי.
מוציא: ../_maanim_inline.js  ו-../maanim.json (גרסאות חדשות)
"""
import json, sys, io, os, shutil, re, unicodedata

# ── force UTF-8 stdout (Windows-safe) ──
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REZEF_DIR = os.path.dirname(HERE)
PROJECT_ROOT = os.path.abspath(os.path.join(REZEF_DIR, "..", ".."))
OTI_DATA = os.path.join(PROJECT_ROOT, "docs", "autism", "oti", "data", "all-enriched.json")

# ── load Oti enriched data ──
with open(OTI_DATA, encoding="utf-8") as f:
    OTI = json.load(f)

# ── load rezef maanim.json (the "rich" version with id, specialty, frequency) ──
with open(os.path.join(REZEF_DIR, "maanim.json"), encoding="utf-8") as f:
    REZEF = json.load(f)

# ── load new contacts from Tali's list ──
sys.path.insert(0, HERE)
from new_contacts import CONTACTS as NEW_CONTACTS

print(f"Oti records:    {len(OTI)}")
print(f"Rezef records:  {len(REZEF)}")
print(f"New contacts:   {len(NEW_CONTACTS)}")


# ─────────────────────────────────────────────────────────
# Step 1: build a name → Oti record lookup for enrichment
# ─────────────────────────────────────────────────────────
def normalize_name(s):
    """ניקוי חזק לצורכי השוואה."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    # הסר ציטוטים / גרשיים / נקודות / סוגריים
    s = re.sub(r"[\"'״׳.\(\)]", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

OTI_BY_NAME = {}
for r in OTI:
    nm = normalize_name(r.get("שם", ""))
    if nm:
        OTI_BY_NAME[nm] = r


# ─────────────────────────────────────────────────────────
# הוריסטיקה לרשומות בלי ageGroups (מילות מפתח בשם/תת-קטגוריה)
# ─────────────────────────────────────────────────────────
# הסדר חשוב — הראשון שמתאים זוכה. ספציפי לפני כללי.
AGE_KEYWORDS = [
    # גילאים מאוד צעירים
    ("מעון",            ["0-3"]),
    ("גנון",            ["3-6"]),
    ("גני תקשורת",      ["3-6"]),
    ("גן תקשורת",       ["3-6"]),
    ("גנים תקשורתיים", ["3-6"]),
    ("גן ילדים",        ["3-6"]),
    # יסודי
    ("בית ספר יסודי", ["6-13"]),
    ("יסודי",           ["6-13"]),
    # חט"ב/תיכון
    ('חט"ב',            ["13-18"]),
    ("חטיבת ביניים",  ["13-18"]),
    ("תיכון",           ["13-18", "18-21"]),
    # בוגרים
    ("מכינה",           ["18-21"]),
    ("בוגרים",          ["18-21", "21+"]),
    ("מבוגרים",         ["18-21", "21+"]),
    ("דיור בקהילה",   ["21+"]),
    ("דיור מוגן",       ["21+"]),
    # ── ברירת מחדל לבתי ספר ולכיתות שלא תאמו תבנית ספציפית ──
    # חינוך מיוחד בישראל הולך עד 21 — לא כולל 21+
    ("בית ספר",         ["6-13", "13-18", "18-21"]),
    ('בי"ס',            ["6-13", "13-18", "18-21"]),
    ("בית חינוך",      ["6-13", "13-18", "18-21"]),
    ("כיתת תקשורת",   ["6-13", "13-18", "18-21"]),
    ("כיתה מקדמת",    ["6-13", "13-18", "18-21"]),
    ("תוכנית בית ספרית", ["6-13", "13-18", "18-21"]),
    ("מסגרת חינוך",    ["3-6", "6-13", "13-18", "18-21"]),
]

def infer_ages_from_text(rz):
    """החזר ageGroups מוערך לפי מילים בשם/תת-קטגוריה/תיאור."""
    text = " ".join([
        rz.get("name") or "",
        rz.get("subcategory") or "",
        rz.get("specialty") or "",
        rz.get("description") or "",
    ])
    for kw, ages in AGE_KEYWORDS:
        if kw in text:
            return ages
    return None


# ─────────────────────────────────────────────────────────
# Step 2: enrich rezef records with kupot + url_status from Oti
# ─────────────────────────────────────────────────────────
matched = 0
got_kupot = 0
got_url = 0

for rz in REZEF:
    nm = normalize_name(rz.get("name", ""))
    oti = OTI_BY_NAME.get(nm)
    if not oti:
        rz["kupot"] = []
        rz["url_status"] = "unknown"
        rz["topics"] = []
        continue
    matched += 1
    kupot = oti.get("kupot") or []
    rz["kupot"] = kupot
    if kupot:
        got_kupot += 1
    url_status = oti.get("url_status", "no-url")
    rz["url_status"] = url_status
    if url_status in ("ok", "broken", "uncertain", "partial"):
        got_url += 1
    rz["topics"] = oti.get("topics") or []
    # קריטי: ageGroups של אוטי מנורמל ל-6 קבוצות הגיל הקנוניות.
    # לירון השאירה "כל הגילאים" גם למסגרות שספציפיות לגיל מסוים — מה שיוצר false positives.
    # מחליפים תמיד ב-ageGroups של אוטי כשקיים.
    oti_age_groups = oti.get("ageGroups") or []
    if oti_age_groups:
        rz["ages"] = oti_age_groups
    else:
        # Oti לא יודע את הגיל המדויק → הוריסטיקה לפי מילים בתת-קטגוריה/שם
        inferred = infer_ages_from_text(rz)
        if inferred:
            rz["ages"] = inferred



print(f"Matched to Oti:  {matched}/{len(REZEF)}")
print(f"With kupot:      {got_kupot}")
print(f"With url_status: {got_url}")


# ─────────────────────────────────────────────────────────
# Step 3: handle new contacts — UPDATE existing tali entries, ADD new ones
# (חשוב: אחרת שינויים ב-new_contacts.py לא יחלחלו לרשומות שכבר נוספו)
# ─────────────────────────────────────────────────────────
rezef_by_name = {normalize_name(r["name"]): r for r in REZEF}
new_to_add = []
updated_tali = 0
for c in NEW_CONTACTS:
    nm = normalize_name(c["n"])
    existing = rezef_by_name.get(nm)
    if existing and existing.get("source_type") == "tali_list":
        # רשומה של טלי שכבר נוספה — עדכן ages וכל מה שמגיע מ-new_contacts.py
        existing["ages"] = c["a"]
        existing["ages_raw"] = " / ".join(c["a"])
        existing["subcategory"] = c["s"]
        existing["specialty"] = c.get("sp", "")
        existing["region"] = c["r"] or "ארצי"
        existing["phone"] = c["p"]
        existing["website"] = c.get("w", "")
        existing["email"] = c.get("e", "")
        existing["description"] = c.get("d", c.get("sp", ""))
        updated_tali += 1
    elif existing:
        # רשומה שכבר קיימת ממקור אחר — אל תיגע
        pass
    else:
        new_to_add.append(c)

print(f"\nTali contacts updated in-place: {updated_tali}")
print(f"New contacts to add:             {len(new_to_add)}")


# ─────────────────────────────────────────────────────────
# Step 4: convert new contacts to maanim.json schema
# ─────────────────────────────────────────────────────────
next_id = max((r.get("id") or 0) for r in REZEF) + 1
for c in new_to_add:
    rec = {
        "id": next_id,
        "name": c["n"],
        "category": c["c"],
        "subcategory": c["s"],
        "specialty": c.get("sp", ""),
        "ages": c["a"],
        "ages_raw": " / ".join(c["a"]),
        "region": c["r"] or "ארצי",
        "phone": c["p"],
        "website": c.get("w", ""),
        "email": c.get("e", ""),
        "recommendation": c.get("rec", "positive"),
        "description": c.get("d", c.get("sp", "")),
        "frequency": "1",
        "kupot": c.get("k", []),
        "url_status": c.get("u", "no-url"),
        "topics": [],
        "source_type": "tali_list",
    }
    REZEF.append(rec)
    next_id += 1

print(f"\nFinal total records: {len(REZEF)}")


# ─────────────────────────────────────────────────────────
# Step 5: write maanim.json (full schema, for inspection)
# ─────────────────────────────────────────────────────────
OUT_JSON = os.path.join(REZEF_DIR, "maanim.json")
BACKUP_JSON = OUT_JSON + ".original"
if not os.path.exists(BACKUP_JSON):
    shutil.copy2(OUT_JSON, BACKUP_JSON)
    print(f"\nBackup created: {BACKUP_JSON}")

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(REZEF, f, ensure_ascii=False, indent=2)
print(f"Wrote: {OUT_JSON}")


# ─────────────────────────────────────────────────────────
# Step 6: write _maanim_inline.js (compact runtime format)
# ─────────────────────────────────────────────────────────
def to_inline(r):
    """המרה לפורמט מקוצר ל-runtime."""
    out = {
        "n":   r["name"],
        "c":   r["category"],
        "s":   r["subcategory"],
        "a":   r["ages"],
        "r":   r["region"],
        "p":   r["phone"],
        "w":   r["website"],
        "rec": r["recommendation"],
        "d":   r["description"],
    }
    # שדות חדשים — נוסיף רק אם יש בהם ערך, כדי לא לנפח את הקובץ
    if r.get("kupot"):
        out["k"] = r["kupot"]
    if r.get("url_status") and r["url_status"] not in ("no-url", "unknown"):
        out["u"] = r["url_status"]
    if r.get("email"):
        out["e"] = r["email"]
    if r.get("specialty"):
        out["sp"] = r["specialty"]
    if r.get("topics"):
        out["t"] = r["topics"]
    return out

OUT_INLINE = os.path.join(REZEF_DIR, "_maanim_inline.js")
BACKUP_INLINE = OUT_INLINE + ".original"
if not os.path.exists(BACKUP_INLINE):
    shutil.copy2(OUT_INLINE, BACKUP_INLINE)
    print(f"Backup created: {BACKUP_INLINE}")

compact = [to_inline(r) for r in REZEF]
with open(OUT_INLINE, "w", encoding="utf-8") as f:
    f.write("var MAANIM_RAW = ")
    json.dump(compact, f, ensure_ascii=False, separators=(", ", ": "))
    f.write(";\n")
print(f"Wrote: {OUT_INLINE}")

# סטטיסטיקה אחרונה
print("\n── Summary ──")
print(f"Records:                    {len(compact)}")
print(f"  with kupot:               {sum(1 for r in compact if r.get('k'))}")
print(f"  with url_status=ok:       {sum(1 for r in compact if r.get('u') == 'ok')}")
print(f"  with url_status=broken:   {sum(1 for r in compact if r.get('u') == 'broken')}")
print(f"  with url_status=uncertain:{sum(1 for r in compact if r.get('u') == 'uncertain')}")
print(f"  with email:               {sum(1 for r in compact if r.get('e'))}")
print(f"  with specialty:           {sum(1 for r in compact if r.get('sp'))}")
print(f"  with topics:              {sum(1 for r in compact if r.get('t'))}")
