# -*- coding: utf-8 -*-
"""
Audit: בודק שהפילטר לפי גיל מציג רק תוצאות הגיוניות.
מדפיס לכל קטגוריה×גיל את הרשומות שעלולות להיות שגויות.
"""
import json, os, sys, io, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REZEF_DIR = os.path.dirname(HERE)
INLINE = os.path.join(REZEF_DIR, "_maanim_inline.js")

txt = open(INLINE, encoding="utf-8").read()
data = json.loads(txt[txt.find("["):txt.rfind("]") + 1])

AGES = ['0-3', '3-6', '6-13', '13-18', '18-21', '21+']

# חוקים שבעצם הפילטר קיים: CAT_MIN_AGE
CAT_MIN_AGE = {'שירותים לבוגרים': '18-21'}

# חוקים שכדאי להוסיף לפילטר: צירופים לא הגיוניים
# חיפוש מילים שמעידות שהרשומה ספציפית לגיל מסוים אבל ages רחב
RED_FLAGS = {
    # subcategory/description contains → max age
    'גן תקשורת':       '6-13',
    'גן ילדים':        '3-6',
    'מעון':            '0-3',
    'יסודי':           '6-13',
    'בית ספר יסודי':   '6-13',
    'חט"ב':            '13-18',
    'תיכון':           '18-21',
    'גני תקשורת':      '6-13',
    'קייטנת ילדים':    '6-13',
    'גנון':            '3-6',
}

print(f"Total records: {len(data)}")
print()

# גם נבדוק: כמה רשומות לכל קטגוריה עדיין יש "כל הגילאים" כפי שהוגדר במקור (לפני התיקון)
print("── 1) Records still with literal 'כל הגילאים' in ages ──")
wildcards = {}
for r in data:
    if 'כל הגילאים' in r.get('a', []):
        c = r.get('c', '?')
        wildcards[c] = wildcards.get(c, 0) + 1
for c, n in sorted(wildcards.items(), key=lambda x: -x[1]):
    print(f"  {c:30s} {n}")
print()

# מאיתורי red-flag — רשומות שמופיעות בגיל לא הגיוני
print("── 2) Records likely mis-tagged (educational frameworks @ 21+) ──")
flags = []
for r in data:
    if r.get('c') != 'מסגרות חינוך':
        continue
    if '21+' not in r.get('a', []):
        continue
    name = r.get('n', '')
    sub = r.get('s', '')
    text = name + ' ' + sub + ' ' + r.get('d', '')
    matched_flag = None
    for kw, max_age in RED_FLAGS.items():
        if kw in text:
            matched_flag = (kw, max_age)
            break
    if matched_flag:
        flags.append((name, sub[:60], matched_flag[0]))

print(f"  Found {len(flags)} suspicious records:")
for n, s, kw in flags[:20]:
    print(f"  • {n[:40]:40s} | flag: '{kw}' | sub: {s}")
if len(flags) > 20:
    print(f"  ... and {len(flags) - 20} more")
print()

# בדיקה: כמה אנשי קשר חדשים שמרו "כל הגילאים" מהריצה הראשונה
print("── 3) Tali's new contacts — still with literal 'כל הגילאים' ──")
tali_wildcards = [r for r in data if r.get('a') == ['כל הגילאים']]
print(f"  Found: {len(tali_wildcards)}")
for r in tali_wildcards[:10]:
    print(f"  • {r['n'][:40]:40s} | cat: {r['c']}")
if len(tali_wildcards) > 10:
    print(f"  ... and {len(tali_wildcards) - 10} more")
print()

# בדיקה: צירופים מוזרים נוספים בקטגוריות אחרות
print("── 4) Other category-age sanity checks ──")
# קייטנות ופנאי בגיל 21+ — חשוד
ks = [r for r in data if r.get('c') == 'קייטנות ופנאי' and '21+' in r.get('a', [])]
print(f"  קייטנות ופנאי @ 21+: {len(ks)}")
for r in ks[:5]:
    print(f"    • {r['n'][:50]} | ages: {r['a']}")

# מסגרות חינוך @ 0-3 — צריך להיות רק מעונות/התערבות מוקדמת
e03 = [r for r in data if r.get('c') == 'מסגרות חינוך' and '0-3' in r.get('a', []) and '21+' in r.get('a', [])]
print(f"\n  מסגרות חינוך @ both 0-3 AND 21+ (very broad): {len(e03)}")
for r in e03[:5]:
    print(f"    • {r['n'][:50]} | ages: {r['a']}")
