"""Render the share preview image: design/og.html -> app/og-image.png (1200x630).

usage: python scripts/build_og.py
Needs Chrome or Edge (headless) and internet for the web fonts.
build_app.py copies app/og-image.png into dist/.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "msedge",
]


def main():
    exe = next((b for b in BROWSERS if Path(b).exists() or shutil.which(b)), None)
    if not exe:
        sys.exit("Chrome/Edge not found")
    out = ROOT / "app" / "og-image.png"
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=1200,630", "--virtual-time-budget=8000",
                    f"--screenshot={out}", (ROOT / "design" / "og.html").as_uri()],
                   check=True, capture_output=True)
    print(f"{out.relative_to(ROOT)} · {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
