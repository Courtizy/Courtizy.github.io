"""Check the hub's "Selected findings" card against the research artifact that feeds it.

The hub (index.html) reads https://courtizy.github.io/research/data/forecast_accuracy.json in the browser
and shows one number from it. This script checks the same contract in Python, so a renamed label, a
changed schema or a broken deep link fails CI instead of silently dropping (or misstating) the number.

    python scripts/check_findings.py                      # live research site
    python scripts/check_findings.py --json FILE          # a local copy, no network (tests use this)
    python scripts/check_findings.py --json FILE --notebook FILE

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

SITE = "https://courtizy.github.io/research/"
JSON_URL = SITE + "data/forecast_accuracy.json"
NOTEBOOK_URL = SITE + "notebooks/forecast-accuracy.html"
ANCHOR = "how-wide-does-an-honest-range-have-to-be"   # the hub's "Read the study" deep link
LABEL = re.compile(r"calibrated 80% range")
HORIZON = 3


def pct(x: float) -> str:
    """Same rounding as the hub's JS: Math.round(x * 100) + "%"."""
    return f"{int(x * 100 + 0.5)}%"


def _agrees(value, share: float) -> bool:
    """The hub's rule: the headline value is within rounding (0.5 point) of the structured share."""
    try:
        return abs(float(str(value).rstrip("%")) - share * 100) <= 0.5
    except ValueError:
        return False


def check(d: dict) -> tuple[list[str], dict]:
    """Return (problems, what the hub would display). An empty problem list means the card shows a number."""
    problems: list[str] = []
    if not (isinstance(d.get("version"), (int, float)) and d["version"] >= 2):
        problems.append(f"version must be >= 2, got {d.get('version')!r}")
    kpi = next((k for k in d.get("headline", {}).get("kpis", []) if LABEL.search(k.get("label", ""))), None)
    if kpi is None:
        problems.append("no headline KPI labelled '...calibrated 80% range...'")
    r3 = next((r for r in d.get("ranges", []) if r.get("h") == HORIZON), None)
    c = (r3 or {}).get("calibrated", {}).get("80")
    if c is None:
        problems.append(f"no ranges[h={HORIZON}].calibrated['80']")
    else:
        for f in ("n", "share", "below", "above"):
            if not isinstance(c.get(f), (int, float)):
                problems.append(f"ranges[h={HORIZON}].calibrated['80'].{f} missing or not a number")
        if not isinstance((r3 or {}).get("companies"), int):
            problems.append(f"ranges[h={HORIZON}].companies missing")
    if kpi and c and isinstance(c.get("share"), (int, float)) and not _agrees(kpi.get("value"), c["share"]):
        problems.append(f"headline KPI {kpi.get('value')!r} does not match the structured share {pct(c['share'])}")
    if not d.get("as_of"):
        problems.append("as_of missing")
    shown = {}
    if not problems:
        shown = {"value": kpi["value"], "label": kpi["label"], "n": c["n"], "companies": r3["companies"],
                 "below": pct(c["below"]), "above": pct(c["above"]), "version": d["version"], "as_of": d["as_of"]}
    return problems, shown


def check_anchor(html: str) -> list[str]:
    return [] if re.search(rf'id="{ANCHOR}"', html) else [f"study page has no #{ANCHOR} section"]


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "decision-models-hub-check"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", help="local forecast_accuracy.json instead of the live site")
    ap.add_argument("--notebook", help="local study HTML to check the deep-link anchor")
    a = ap.parse_args(argv)
    d = json.load(open(a.json, encoding="utf-8")) if a.json else json.loads(_get(JSON_URL))
    problems, shown = check(d)
    if a.notebook:
        problems += check_anchor(open(a.notebook, encoding="utf-8").read())
    elif not a.json:
        problems += check_anchor(_get(NOTEBOOK_URL))
    for p in problems:
        print(f"FAIL: {p}")
    if problems:
        return 1
    print(f"OK: {shown['value']} {shown['label']} · n={shown['n']:,} forecasts, {shown['companies']} companies · "
          f"median range -{shown['below']}/+{shown['above']} · v{shown['version']} as of {shown['as_of']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
