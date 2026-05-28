# -*- coding: utf-8 -*-
"""
מנקה תיאורים רועשים: שאלות + הכרזות אירוע ספציפיות.
מחליף את התיאור ב-specialty (אם קיים). שומר תמיד את הרשומה — לא מוחק.
משאיר ללא נגיעה: המלצות הורים ("אני ממליצה", "הבת/הבן שלי...").
"""
import json, os, sys, io, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REZEF_DIR = os.path.dirname(HERE)
INLINE = os.path.join(REZEF_DIR, "_maanim_inline.js")
MAANIM_JSON = os.path.join(REZEF_DIR, "maanim.json")

# טעינה
with open(MAANIM_JSON, encoding="utf-8") as f:
    data = json.load(f)

# ── תבניות זיהוי ──
QUESTION_STARTS = (
    'האם ', 'מי מכיר', 'מי יודע', 'מי יכול', 'מי שיודע',
    'לגבי ', 'מישהו ', 'מישהי ', 'אשמח לעזרה', 'צריכה לדעת',
    'תגידו', 'תוכלו', 'יש למישהו', 'אני מחפש', 'אני מחפשת',
    'אשמח אם', 'מה דעתכם', 'מה דעתכן', 'הורה רוצה לדעת',
)

# הכרזות ספציפיות — מילים שבד"כ מסמנות אירוע חולף או הצעת עזרה אישית,
# לא תיאור של שירות. שמים לב לא לפגוע בהמלצות.
ANNOUNCEMENT_STARTS = (
    'מתחילה ', 'מתחיל ',
    'אקיים ', 'אעשה ',
    'אנו רוצים להציג', 'אנו מציעים',
    'בשמחה ובגאווה', 'בשמחה אנו',
    'אני מזמינה ', 'אנו מזמינים',
    'בחודש ', 'השבוע ',
    'אני קורא לכם', 'אני קוראת לכם',
    'הזמנתי ', 'הזמנו ',
)

def is_question(desc):
    if not desc:
        return False
    d = desc.strip()
    if d.endswith('?') or d.endswith('؟'):
        return True
    return any(d.startswith(q) for q in QUESTION_STARTS)

def is_announcement(desc):
    if not desc:
        return False
    d = desc.strip()
    return any(d.startswith(a) for a in ANNOUNCEMENT_STARTS)

# ── עיבוד ──
cleaned_q = 0
cleaned_a = 0
no_replacement = []

for r in data:
    desc = (r.get("description") or "").strip()
    if not desc:
        continue

    noise_type = None
    if is_question(desc):
        noise_type = "question"
    elif is_announcement(desc):
        noise_type = "announcement"
    else:
        continue

    # יש לנו specialty שיכול להחליף?
    spec = (r.get("specialty") or "").strip()
    if spec and len(spec) >= 5:
        r["description"] = spec
        # סמן מקור התיקון לתיעוד פנימי
        r.setdefault("_clean", []).append(noise_type)
        if noise_type == "question":
            cleaned_q += 1
        else:
            cleaned_a += 1
    else:
        # אין specialty — אי אפשר להחליף בלי לאבד מידע
        no_replacement.append({
            "name": r["name"],
            "category": r["category"],
            "type": noise_type,
            "has_phone": bool(r.get("phone")),
            "has_site": bool(r.get("website")),
            "desc": desc[:80],
        })

print(f"Cleaned (question  → specialty): {cleaned_q}")
print(f"Cleaned (announce  → specialty): {cleaned_a}")
print(f"Total cleaned:                   {cleaned_q + cleaned_a}")
print(f"Could not clean (no specialty):  {len(no_replacement)}")
print()

if no_replacement:
    print("── Records without specialty (left untouched) ──")
    for r in no_replacement:
        print(f"  [{r['type']:12s}] {r['name'][:50]}")
        print(f"    cat: {r['category']} · phone: {r['has_phone']} · site: {r['has_site']}")
        print(f"    desc: {r['desc']}")
        print()

# ── שמירה ──
# גיבוי (פעם אחת בלבד)
backup = MAANIM_JSON + ".pre-clean"
if not os.path.exists(backup):
    shutil.copy2(MAANIM_JSON, backup)
    print(f"Backup: {backup}")

with open(MAANIM_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Wrote: {MAANIM_JSON}")

# כתיבת _maanim_inline.js מחדש מהמעודכן
def to_inline(r):
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

backup_inline = INLINE + ".pre-clean"
if not os.path.exists(backup_inline):
    shutil.copy2(INLINE, backup_inline)
    print(f"Backup: {backup_inline}")

compact = [to_inline(r) for r in data]
with open(INLINE, "w", encoding="utf-8") as f:
    f.write("var MAANIM_RAW = ")
    json.dump(compact, f, ensure_ascii=False, separators=(", ", ": "))
    f.write(";\n")
print(f"Wrote: {INLINE}")
