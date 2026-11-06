"""Bundle app/index.html + data/dayDD.json into one offline file: dist/index.html

usage: python scripts/build_app.py
Run scripts/build_data.py first so data/dayDD.json is up to date.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = "/*__WORDS__*/[]"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    words = []
    for f in sorted((ROOT / "data").glob("day??.json")):
        words += json.loads(f.read_text(encoding="utf-8"))
    if not words:
        sys.exit("no data/dayDD.json found — run scripts/build_data.py first")
    html = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
    if MARK not in html:
        sys.exit(f"placeholder {MARK} not found in app/index.html")
    blob = json.dumps(words, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = ROOT / "dist" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html.replace(MARK, blob), encoding="utf-8")
    (out.parent / ".nojekyll").touch()  # GitHub Pages: serve as-is
    days = sorted({w["day"] for w in words})
    print(f"dist/index.html · {len(words)} words · Day {days[0]}–{days[-1]} · {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
