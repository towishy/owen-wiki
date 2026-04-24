"""Apply default confidence to wiki pages missing the field.

Default policy:
- auto-hub-* / *-content-hub / *-archives-hub / *-microsoft-documents-hub: 0.55
- summaries (regular): 0.75
- entities, concepts, comparisons, synthesis: 0.75
- ontology: skip (manual curation)

Only writes to files that lack `confidence:` in their YAML frontmatter.
"""
import os
import re
import sys
from datetime import date

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WIKI = "wiki"
TODAY = date.today().isoformat()

fm_re = re.compile(r"\A(---\n.*?\n---\n)", re.DOTALL)

def get_default(fp: str, fm: str) -> float | None:
    name = os.path.basename(fp).lower()
    parent = os.path.basename(os.path.dirname(fp)).lower()
    if parent == "ontology":
        return None
    if any(k in name for k in ("auto-hub-", "-content-hub", "-archives-hub", "-microsoft-documents-hub")):
        return 0.55
    return 0.75


modified = 0
skipped = 0
for root, _, files in os.walk(WIKI):
    for f in files:
        if not f.endswith(".md") or f == "_index.md":
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding="utf-8") as fh:
            text = fh.read()
        m = fm_re.match(text)
        if not m:
            skipped += 1
            continue
        fm = m.group(1)
        if re.search(r"^confidence:", fm, re.M):
            continue
        default = get_default(fp, fm)
        if default is None:
            continue
        # Insert confidence + last_confirmed before closing ---
        new_fm = re.sub(
            r"\n---\n\Z",
            f"\nconfidence: {default}\nlast_confirmed: {TODAY}\n---\n",
            fm,
        )
        if new_fm == fm:
            skipped += 1
            continue
        new_text = new_fm + text[m.end():]
        with open(fp, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        modified += 1

print(f"Confidence applied to {modified} files. Skipped {skipped}.")
