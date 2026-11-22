"""Check the homepage's two example previews against the JSON the live models publish.

The hub (home/previews.js) reads, in the browser, from the same origin:
  TPS-Monte-Carlo-Simulation/data/presets.json -> preset_<default>.json   (aircraft ready vs needed, Mon-Fri)
  valuation/data/index.json -> AAPL's latest comparison.json            (football field of the weighted methods)
and shows a few numbers from each without recalculating anything. This script checks the same contract in
Python, so a renamed field or a changed file fails CI instead of quietly showing the fallback line.

    python scripts/check_previews.py                       # live site
    python scripts/check_previews.py --fixtures DIR        # local copies, no network (tests use this)

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import urllib.request

SITE = "https://courtizy.github.io/"
TPS = "TPS-Monte-Carlo-Simulation/data/"
VAL = "valuation/data/"
VAL_TICKER = "AAPL"   # the company the Valuation app opens on
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def js_round(x: float) -> int:
    """Math.round: halves round up."""
    return math.floor(x + 0.5)


def check_tps(preset: dict) -> tuple[list[str], dict]:
    problems: list[str] = []
    share = preset.get("kpis", {}).get("weeks_meeting_every_requirement")
    if not _num(share) or not 0 <= share <= 1:
        problems.append("kpis.weeks_meeting_every_requirement missing or not a share")
    days = {d.get("day"): d for d in preset.get("days", [])}
    for day in DAYS:
        d = days.get(day)
        if d is None:
            problems.append(f"days has no {day}")
            continue
        for f in ("available_p10", "available_p50", "available_p90", "needed"):
            if not _num(d.get(f)):
                problems.append(f"days[{day}].{f} missing or not a number")
        if all(_num(d.get(f)) for f in ("available_p10", "available_p50", "available_p90")) and \
                not d["available_p10"] <= d["available_p50"] <= d["available_p90"]:
            problems.append(f"days[{day}] percentiles out of order")
        if d.get("status") not in ("good", "warning", "critical") or not d.get("status_label"):
            problems.append(f"days[{day}].status/status_label missing")
    for f in ("unit_name", "scenario_label"):
        if not isinstance(preset.get(f), str):
            problems.append(f"{f} missing")
    if not _num(preset.get("simulation", {}).get("runs")):
        problems.append("simulation.runs missing")
    shown = {} if problems else {
        "headline": f"{js_round(share * 100)}% of weeks meet the plan",
        "flagged": [d for d in DAYS if days[d]["status"] != "good"],
        "runs": preset["simulation"]["runs"],
    }
    return problems, shown


def check_valuation(index: dict, comparison: dict) -> tuple[list[str], dict]:
    problems: list[str] = []
    companies = index.get("companies") or []
    if not any(c.get("ticker") == VAL_TICKER for c in companies):
        problems.append(f"index has no {VAL_TICKER} (the preview would fall back to the first company)")
    methods = [m for m in comparison.get("plan", {}).get("methods", []) if m.get("ran") and _num(m.get("weight")) and m["weight"] > 0]
    if not methods:
        problems.append("plan.methods has no method that ran with weight > 0")
    field = {f.get("model"): f for f in comparison.get("football_field", [])}
    rows = []
    for m in methods:
        f = field.get(m.get("model"))
        if not f or not all(_num(f.get(k)) for k in ("p10", "p50", "p90")):
            problems.append(f"football_field has no p10/p50/p90 for weighted method {m.get('model')!r}")
        else:
            rows.append((m["model"], f))
    if methods and abs(sum(m["weight"] for m in methods) - 1) > 0.01:
        problems.append(f"weights of the weighted methods sum to {sum(m['weight'] for m in methods):.2f}, not 1")
    blend = comparison.get("blend") or {}
    if not all(_num(blend.get(k)) for k in ("p10", "p50", "p90")):
        problems.append("blend.p10/p50/p90 missing")
    elif not blend["p10"] <= blend["p50"] <= blend["p90"]:
        problems.append("blend percentiles out of order")
    shown = {} if problems else {
        "headline": f"${blend['p10']:.2f}–${blend['p90']:.2f} a share",   # toFixed(2), as the app's headline
        "rows": [m for m, _ in rows],
        "price": comparison.get("price"),
    }
    return problems, shown


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "decision-models-hub-check"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def load(fixtures: pathlib.Path | None):
    if fixtures:
        read = lambda name: json.loads((fixtures / name).read_text(encoding="utf-8"))  # noqa: E731
        return (read("tps_preset_default.json"), read("valuation_aapl_index.json"), read("valuation_aapl_comparison.json"))
    presets = _get(SITE + TPS + "presets.json")
    preset = _get(SITE + TPS + f"preset_{presets['default']}.json")
    index = _get(SITE + VAL + "index.json")
    company = next((c for c in index["companies"] if c.get("ticker") == VAL_TICKER), index["companies"][0])
    return preset, index, _get(SITE + VAL + company["runs"][0]["comparison"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fixtures", type=pathlib.Path, help="folder with local copies instead of the live site")
    a = ap.parse_args(argv)
    preset, index, comparison = load(a.fixtures)
    tp, ts = check_tps(preset)
    vp, vs = check_valuation(index, comparison)
    for p in tp:
        print(f"FAIL tps: {p}")
    for p in vp:
        print(f"FAIL valuation: {p}")
    if tp or vp:
        return 1
    print(f"OK tps: {ts['headline']} ({ts['runs']:,} runs), flagged days: {', '.join(ts['flagged']) or 'none'}")
    print(f"OK valuation: {vs['headline']} from {', '.join(vs['rows'])}, price {vs['price']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
