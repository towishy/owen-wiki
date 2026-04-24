"""Fix broken wikilinks across wiki/ via global aliases.

For each (file, broken_target) pair in BROKEN_MAP, replace [[broken_target]] and
[[broken_target|alias]] with [[replacement|alias-or-broken-target]] so that the
rendered text remains the same (preserves the original term as display text).
"""
import os
import re
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# broken_target -> replacement_page
ALIASES = {
    "intune": "microsoft-intune",
    "cae": "conditional-access",
    "cnapp-comparison": "defender-for-cloud-vs-wiz-vs-prisma",
    "siem-comparison": "sentinel-vs-splunk-vs-chronicle",
    "zero-trust-overview": "zero-trust",
    "log-analytics": "microsoft-sentinel",
    "purview-data-security": "microsoft-purview",
    "mde-school": "secmde-tactical-scenarios-hub",
    "ninja-microsoft-defender-for-endpoint": "microsoft-defender-for-endpoint",
    "mslearn-security-labs-hub": "mslearn-security-courses",
    "ai-security-key-concepts": "ai-security-overview",
    "fy26-readiness-portal-overview": "fy26-readiness-extras-hub",
    "fy26-techconnect-skilling-roadmap": "fy26-techconnect-sessions-hub",
}

# Image embeds: [[image.png]] should become ![[raw/assets/image.png]] or removed.
# We convert them to markdown image links pointing to raw/assets.
IMAGE_TARGETS = {
    "gsa-utr-infographic.png": "raw/assets/gsa-utr-infographic.png",
    "zt-5product-security-model.png": "raw/assets/zt-5product-security-model.png",
}

WIKI = "wiki"
total_fixes = 0
for root, _, files in os.walk(WIKI):
    for f in files:
        if not f.endswith(".md"):
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding="utf-8") as fh:
            text = fh.read()
        original = text
        for old, new in ALIASES.items():
            # [[old]] -> [[new|old]]  (preserve display)
            text = re.sub(
                rf"\[\[{re.escape(old)}\]\]",
                f"[[{new}|{old}]]",
                text,
            )
            # [[old|display]] or [[old\|display]] (markdown table escape) -> [[new|display]]
            text = re.sub(
                rf"\[\[{re.escape(old)}\\?\|([^\]]+)\]\]",
                lambda m: f"[[{new}\\|{m.group(1)}]]" if "\\|" in m.group(0) else f"[[{new}|{m.group(1)}]]",
                text,
            )
        for img, path in IMAGE_TARGETS.items():
            # [[image.png]] -> ![image.png](raw/assets/image.png)
            text = re.sub(
                rf"!?\[\[{re.escape(img)}\]\]",
                f"![{img}]({path})",
                text,
            )
        if text != original:
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write(text)
            # count differences in wikilink count
            diff = original.count("[[") - text.count("[[")
            print(f"fixed: {fp}")
            total_fixes += 1

print(f"\nTotal files modified: {total_fixes}")
