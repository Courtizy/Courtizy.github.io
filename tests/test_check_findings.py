"""The hub's findings contract, on a trimmed copy of the published Study 01 file (v2, as of 2026-10-30)."""
import copy
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import check_findings as cf  # noqa: E402

GOOD = json.loads((pathlib.Path(__file__).parent / "fixtures" / "forecast_accuracy_v2.json").read_text())


def test_published_file_passes_and_shows_its_denominator():
    problems, shown = cf.check(GOOD)
    assert problems == []
    # Independent of the script: share 0.81605 of 2,305 three-year forecasts rounds to 82%.
    assert shown["value"] == "82%" and shown["n"] == 2305 and shown["companies"] == 319
    assert (shown["below"], shown["above"]) == ("28%", "42%")


def test_renamed_label_fails():
    d = copy.deepcopy(GOOD)
    for k in d["headline"]["kpis"]:
        k["label"] = k["label"].replace("calibrated 80% range", "80% band")
    assert any("labelled" in p for p in cf.check(d)[0])


def test_headline_that_disagrees_with_the_data_fails():
    d = copy.deepcopy(GOOD)
    next(r for r in d["ranges"] if r["h"] == 3)["calibrated"]["80"]["share"] = 0.79
    assert any("does not match" in p for p in cf.check(d)[0])


def test_old_version_or_missing_horizon_fails():
    d = copy.deepcopy(GOOD)
    d["version"] = 1
    d["ranges"] = []
    problems = cf.check(d)[0]
    assert any("version" in p for p in problems) and any("h=3" in p for p in problems)


def test_rounding_matches_js_math_round():
    assert [cf.pct(x) for x in (0.815, 0.8149, 0.005, 0.0)] == ["82%", "81%", "1%", "0%"]


def test_anchor():
    assert cf.check_anchor('<section id="how-wide-does-an-honest-range-have-to-be">') == []
    assert cf.check_anchor("<section id='other'>")
