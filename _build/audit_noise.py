# -*- coding: utf-8 -*-
"""
בודק כמה רשומות הן רעש מהצ'אטים: שאלות, הכרזות, שיחה אישית — לא שירותים אמיתיים.
"""
import json, os, sys, io, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REZEF_DIR = os.path.dirname(HERE)
INLINE = os.path.join(REZEF_DIR, "_maanim_inline.js")

txt = open(INLINE, encoding="utf-8").read()
data = json.loads(txt[txt.find("["):txt.rfind("]") + 1])

# סימני רעש
QUESTION_STARTS = ['האם ', 'מי מכיר', 'מי יודע', 'מי יכול', 'מי שיודע', 'לגבי ',
                   'מישהו ', 'מישהי ', 'אשמח לעזרה', 'צריכה לדעת', 'תגידו', 'תוכלו',
                   'יש למישהו', 'אני מחפש', 'אני מחפשת', 'שאלה', 'אשמח אם']
FIRST_PERSON = ['אני ', 'אנו ', 'אצלי ', 'אצלנו ', 'בתי ', 'בני ', 'הבן שלי',
                'הבת שלי', 'מתחילה ', 'אקיים ', 'אעשה ', 'הזמנתי ']

def classify(d):
    """החזר tuple של (סוג רעש, רמת ודאות) או None."""
    desc = (d.get('d') or '').strip()
    name = (d.get('n') or '')
    sub = (d.get('s') or '')

    flags = []
    # שאלה ברורה
    if desc.endswith('?') or desc.endswith('؟'):
        flags.append('question_mark')
    # תחילית של שאלה
    for q in QUESTION_STARTS:
        if desc.startswith(q):
            flags.append(f'q_start:{q.strip()}')
            break
    # גוף ראשון בתחילת התיאור
    for p in FIRST_PERSON:
        if desc[:40].lstrip().startswith(p) or (' ' + p) in desc[:80]:
            flags.append(f'first_person:{p.strip()}')
            break
    # תת-קטגוריה מטעה
    sub_low = sub.lower()
    if 'שאלה' in sub or 'שאלות' in sub:
        flags.append('sub_question')
    # תיאור קצר מאוד או חסר משמעות
    if len(desc) < 20 and not d.get('p') and not d.get('w'):
        flags.append('thin_no_contact')

    return flags

# סיכום
noise_recs = []
for d in data:
    flags = classify(d)
    if flags:
        noise_recs.append((d, flags))

print(f"Total records:    {len(data)}")
print(f"Suspected noise:  {len(noise_recs)}  ({100*len(noise_recs)/len(data):.1f}%)")
print()

# סטטיסטיקה לפי סוג דגל
from collections import Counter
flag_counts = Counter()
for _, flags in noise_recs:
    for f in flags:
        # קצר את הפרפיקס
        prefix = f.split(':')[0]
        flag_counts[prefix] += 1
print("── Flag distribution ──")
for flag, cnt in flag_counts.most_common():
    print(f"  {flag:25s} {cnt}")
print()

# פילוח לפי קטגוריה
cat_counts = Counter(d['c'] for d, _ in noise_recs)
print("── Noise by category ──")
for cat, cnt in cat_counts.most_common():
    print(f"  {cat:30s} {cnt}")
print()

# 20 דוגמאות
print("── 20 sample noise records ──")
for i, (d, flags) in enumerate(noise_recs[:20], 1):
    desc_short = (d.get('d') or '')[:90]
    print(f"\n{i}. {d['n'][:55]}")
    print(f"   cat: {d['c']} · flags: {', '.join(flags)}")
    print(f"   desc: {desc_short}")
