"""The homepage preview contract, on trimmed copies of what the models published (TPS v0.13.0, Valuation demo as of 2026-09-30)."""
import copy
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import check_previews as cp  # noqa: E402

FIX = pathlib.Path(__file__).parent / "fixtures" / "previews"
PRESET, INDEX, COMPARISON = cp.load(FIX)


def test_published_files_pass_and_show_the_engine_numbers():
    tp, ts = cp.check_tps(PRESET)
    vp, vs = cp.check_valuation(INDEX, COMPARISON)
    assert tp == [] and vp == []
    # Independent of the script: 0.935 of 2,000 weeks rounds to 94%; Wednesday is the one day TPS marks "At risk".
    assert ts["headline"] == "94% of simulated weeks" and ts["flagged"] == ["Wed"] and ts["runs"] == 2000
    # Blend p10 34.36 and p90 53.88 round to $34 and $54; DCF (60%) and sector comps (40%) carry the weight.
    assert vs["headline"] == "$34–$54 a share" and vs["rows"] == ["dcf", "comps"] and vs["price"] == 45.0


def test_js_round_matches_math_round_on_halves():
    assert cp.js_round(93.5) == 94 and cp.js_round(42.5) == 43 and cp.js_round(-0.5) == 0


def test_missing_day_or_renamed_field_fails():
    p = copy.deepcopy(PRESET)
    p["days"] = [d for d in p["days"] if d["day"] != "Wed"]
    p["days"][0]["available_p50"] = None
    problems = cp.check_tps(p)[0]
    assert any("no Wed" in x for x in problems) and any("available_p50" in x for x in problems)


def test_percentiles_out_of_order_fail():
    p = copy.deepcopy(PRESET)
    p["days"][1]["available_p10"] = 99
    assert any("out of order" in x for x in cp.check_tps(p)[0])


def test_valuation_without_weighted_methods_or_blend_fails():
    c = copy.deepcopy(COMPARISON)
    for m in c["plan"]["methods"]:
        m["weight"] = 0
    c["blend"] = None
    problems = cp.check_valuation(INDEX, c)[0]
    assert any("weight > 0" in x for x in problems) and any("blend" in x for x in problems)


def test_weighted_method_missing_from_football_field_fails():
    c = copy.deepcopy(COMPARISON)
    c["football_field"] = [f for f in c["football_field"] if f["model"] != "comps"]
    assert any("'comps'" in x for x in cp.check_valuation(INDEX, c)[0])


def test_fixture_files_are_small():
    assert all(f.stat().st_size < 5000 for f in FIX.iterdir())
    json.loads((FIX / "tps_presets.json").read_text())
