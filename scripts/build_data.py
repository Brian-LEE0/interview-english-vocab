"""Merge data/parts/dayDD-{A..D}.json into data/dayDD.json and validate.

Rules come from PLAN.md (§2, §3, §5) and data/GUIDE.md.

usage:
    python scripts/build_data.py            # all days that have parts
    python scripts/build_data.py 1 2 3      # only these days
Exit code 1 if any ERROR. WARN lines are for human review.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "data" / "parts"
OUT = ROOT / "data"
SETS = "ABCD"

LEVEL_SPLIT = {  # per-set (level1, level2, level3)
    1: [(13, 10, 2), (13, 10, 2), (12, 10, 3), (12, 10, 3)],
    2: [(8, 12, 5), (8, 12, 5), (7, 13, 5), (7, 13, 5)],
    3: [(5, 10, 10)] * 4,
}
CAT_SPLIT = {  # per-set (interview, it, negotiation)
    1: [(15, 10, 0)] * 4,
    2: [(13, 10, 2), (13, 10, 2), (12, 10, 3), (12, 10, 3)],
    3: [(5, 6, 14), (5, 6, 14), (5, 7, 13), (5, 6, 14)],
}
CATS = ("interview", "it", "negotiation")
POS = {"noun", "verb", "adjective", "adverb", "phrasal verb", "phrase"}
PART_TYPES = {"prefix", "root", "suffix", "part"}
LEVEL_MARK = {"🟢": 1, "🟡": 2, "🔴": 3}


def key(word):
    """walk through / walkthrough / walk-through count as the same word."""
    return re.sub(r"[^a-z]", "", word.lower())


def period(day):
    return 1 if day <= 10 else 2 if day <= 20 else 3


def load_reps():
    """{day: {word: level}} from the PLAN.md §5 tables."""
    reps = {}
    for line in (ROOT / "PLAN.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*F\d+[^|]*\|(.+)\|\s*$", line)
        if not m or "🟢" not in m.group(2):
            continue
        day, words = int(m.group(1)), {}
        for chunk in re.split(r"\s·\s(?=[🟢🟡🔴])", m.group(2).strip()):
            mark = chunk.strip()[0]
            for w in chunk.strip()[1:].split(","):
                if w.strip():
                    words[w.strip().lower()] = LEVEL_MARK[mark]
        reps[day] = words
    return reps


def check_day(day, reps, seen, errors, warns):
    def err(msg):
        errors.append(f"day{day:02d}: {msg}")

    def warn(msg):
        warns.append(f"day{day:02d}: {msg}")

    words, p = [], period(day)
    for si, s in enumerate(SETS):
        f = PARTS / f"day{day:02d}-{s}.json"
        if not f.exists():
            err(f"missing {f.name}")
            continue
        try:
            items = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(f"{f.name} is not valid JSON: {e}")
            continue
        if len(items) != 25:
            err(f"set {s} has {len(items)} words (need 25)")
        lv = Counter(w.get("level") for w in items)
        ct = Counter(w.get("category") for w in items)
        want_lv, want_ct = LEVEL_SPLIT[p][si], CAT_SPLIT[p][si]
        got_lv, got_ct = tuple(lv[i] for i in (1, 2, 3)), tuple(ct[c] for c in CATS)
        if got_lv != want_lv:
            err(f"set {s} level 1/2/3 = {got_lv}, need {want_lv}")
        if got_ct != want_ct:
            err(f"set {s} interview/it/negotiation = {got_ct}, need {want_ct}")
        for i, w in enumerate(items, 1):
            wid = f"d{day:02d}-{s}{i:02d}"
            if w.get("id") != wid:
                err(f"{s}#{i} id {w.get('id')!r}, expected {wid}")
            if w.get("day") != day or w.get("set") != s:
                err(f"{wid} day/set fields wrong")
            if w.get("pos") not in POS:
                err(f"{wid} pos {w.get('pos')!r}")
            if not re.fullmatch(r"/.+/", w.get("ipa", "")):
                err(f"{wid} ipa {w.get('ipa')!r}")
            for k in ("word", "meaning_ko", "tip", "family"):
                if not w.get(k):
                    err(f"{wid} missing {k}")
            ety = w.get("etymology", {})
            parts = ety.get("parts", [])
            if not parts or not ety.get("story"):
                err(f"{wid} etymology incomplete")
            for pt in parts:
                if pt.get("type") not in PART_TYPES or not pt.get("text") or not pt.get("gloss"):
                    err(f"{wid} bad etymology part {pt}")
            joined = re.sub(r"[^a-z]", "", "".join(pt.get("text", "") for pt in parts).lower())
            plain = re.sub(r"[^a-z]", "", w.get("word", "").lower())
            if joined != plain:
                warn(f"{wid} parts '{joined}' != word '{plain}'")
            ex = w.get("example", {})
            if not all(ex.get(k) for k in ("q", "a", "a_ko")):
                err(f"{wid} example incomplete")
            head = w.get("word", "").lower().split()[0].rstrip("ye")[:5]  # apply -> appl(ied)
            if head and head not in ex.get("a", "").lower():
                warn(f"{wid} '{w.get('word')}' not found in example.a")
            if not (2 <= len(w.get("collocations", [])) <= 3):
                warn(f"{wid} collocations count {len(w.get('collocations', []))}")
            words.append(w)

    names = [key(w.get("word", "")) for w in words]
    for n, c in Counter(names).items():
        if c > 1:
            err(f"duplicate word in day: {n}")
    for n in names:
        if n in seen and seen[n] != day:
            err(f"'{n}' already used on day {seen[n]}")
    for day2, rep in reps.items():
        for rw, lvl in rep.items():
            if day2 == day:
                hit = [w for w in words if key(w.get("word", "")) == key(rw)]
                if not hit:
                    err(f"representative word missing: {rw}")
                elif hit[0].get("level") != lvl:
                    err(f"representative word {rw} level {hit[0].get('level')}, plan says {lvl}")
            elif key(rw) in names:
                err(f"'{rw}' is reserved for day {day2}")
    return words


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    days = [int(a) for a in sys.argv[1:]] or sorted(
        {int(f.name[3:5]) for f in PARTS.glob("day??-?.json")})
    reps, errors, warns, seen = load_reps(), [], [], {}
    # words already in merged days not being rebuilt count as "seen"
    for f in OUT.glob("day??.json"):
        d = int(f.name[3:5])
        if d not in days:
            for w in json.loads(f.read_text(encoding="utf-8")):
                seen[key(w["word"])] = d
    built = {}
    for d in days:
        words = check_day(d, reps, seen, errors, warns)
        for w in words:
            seen.setdefault(key(w.get("word", "")), d)
        built[d] = words
    for d, words in built.items():
        if len(words) == 100 and not any(e.startswith(f"day{d:02d}:") for e in errors):
            (OUT / f"day{d:02d}.json").write_text(
                json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"OK   day{d:02d}.json (100 words)")
    for w in warns:
        print("WARN", w)
    for e in errors:
        print("ERROR", e)
    print(f"\n{len(built)} days checked · {len(errors)} errors · {len(warns)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
