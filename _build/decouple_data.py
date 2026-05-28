# -*- coding: utf-8 -*-
"""
חד-פעמי: מפריד את MAANIM_RAW האינליין מ-index.html ל-_maanim_inline.js
החל מהפעם הבאה — מערכים את index.html ידנית, ואת הדאטה דרך merge.py בלבד.
"""
import os, sys, io, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REZEF_DIR = os.path.dirname(HERE)
INDEX = os.path.join(REZEF_DIR, "index.html")

with open(INDEX, "r", encoding="utf-8") as f:
    html = f.read()

# החלף את ה-script block המכיל את var MAANIM_RAW בטעינה חיצונית
# חיפוש לא-חמדני אחרי <script>\n...var MAANIM_RAW = [...];\n...</script> שבא מיד אחרי <body>
pattern = re.compile(
    r'<body>\s*<script>\s*var MAANIM_RAW\s*=\s*\[.*?\];\s*'
    r'(if\(typeof initMaanim[^<]*?)</script>',
    re.DOTALL
)

m = pattern.search(html)
if not m:
    print("ERROR: could not find inline MAANIM_RAW block")
    sys.exit(1)

print(f"Found inline block at offset {m.start()}, length {m.end() - m.start()}")

replacement = (
    "<body>\n"
    '<script src="_maanim_inline.js"></script>\n'
    "<script>\n"
    + m.group(1) +
    "</script>"
)

new_html = html[:m.start()] + replacement + html[m.end():]

# backup once
backup = INDEX + ".original"
if not os.path.exists(backup):
    with open(backup, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Backup created: {backup}")

with open(INDEX, "w", encoding="utf-8") as f:
    f.write(new_html)
print(f"Patched: {INDEX}")
print(f"Old size: {len(html):,} chars  →  new size: {len(new_html):,} chars")
