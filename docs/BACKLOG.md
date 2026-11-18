# Decision Models: suite backlog

One ordered backlog for the whole suite. Labels name the project: `hub`, `valuation`, `tps`, `research`, `roi`, `core`, `delta` (hub link and shared assets only). Each run starts here: inspect what changed since the last review, revisit open items, continue the active Sprint Goal.

Last review: 2026-11-18 (first run).

## Product Goal

Help a finance, analytics or operations reviewer move from a real decision to a working model, an interpretable result, and evidence of how well the method performs.

## Definition of Done

1. The user-facing acceptance criteria are met.
2. The affected model or study has an independent check (hand calculation, analytical case, published reference, or a separate implementation).
3. The normal browser or reproduction journey works.
4. Published claims match the underlying results.
5. Documentation is current.
6. Cleanup was reviewed.
7. Performance changes carry comparable before/after measurements.

Implementation, verification and deployment are reported separately. Merging, publishing and destructive changes need Jason's authorization.

## Inventory (2026-11-18)

| Project | Maturity | Live route | Repository @ main | Deployed by | Checks that run |
|---|---|---|---|---|---|
| Hub | Live | courtizy.github.io/ | `Courtizy.github.io` @ `b71624b` | GitHub's built-in Pages build from `main` (deployed `b71624b`) | None before this sprint; `Checks` workflow added in this sprint's PR |
| Valuation Model | Live (LBO scaffolded only) | /valuation/ | `valuation` @ `3784c1d`, v0.10.1 | `Pages` workflow (deployed `3784c1d`, 2026-11-09) | `Tests`, `Pipeline`, `Refresh` (weekly; cancelled 11-02 and 11-16) |
| Turn Pattern Sustainability | Live in the browser (Pyodide); public inputs only | /TPS-Monte-Carlo-Simulation/ | `TPS-Monte-Carlo-Simulation` @ `167075b` | `Test and publish` (deployed `167075b`) | 140 tests incl. golden outputs, seeds, convergence, model-logic doc |
| Research & Analysis | Live: Study 01 final (v2); Study 02 planned | /research/ | `research` @ `85a3370` | `Pages` workflow renders notebooks over committed JSON (deployed `85a3370`) | `Tests` (21), `Study` (manual full rerun on SEC data) |
| Project ROI | Planned: no repository or code | none | none | none | none |
| Shared Core | Planned. Prototype exists as `valuation/src/valuation/_core/` | none | inside `valuation` | none | covered by valuation tests |
| Delta Readiness | Live (separate workstream) | /fitness/ | private `fitness` + hub `fitness/` | hub Pages build | out of scope; `fitness/` doesn't load the hub's `brand/`, so hub brand changes don't reach it |

Data flows between repositories:

- `research` pins the Valuation engine at `ENGINE` = `34e3852` (v0.9.0). The live Valuation Model is v0.10.1.
- The hub reads `research/site/data/forecast_accuracy.json` in the browser for the findings card.
- `valuation` reads the research calibration tables (`site/data/calibration/*.json`) for its revenue ranges.

Fresh-checkout reproduction on 2026-11-18 (Python 3.13, Linux): `research` 21 passed (20 s); `valuation` 291 passed, 15 skipped (134 s); TPS 140 passed (21 s). Full Study 01 rerun needs SEC access (not reachable from the review container); its last run was Actions run 41097931174 on 2026-10-30.

## Sprint 1 (2026-11-18)

**Sprint Goal:** a reviewer can trace the homepage forecast-coverage finding to its exact study section, denominator, horizon, interval width and data version in one click, and the card never shows a stale or mismatched number when the research file is missing or changed.

Baseline: the card showed "82%" with no denominator or width; "Read the study" landed on the study index (two clicks to the evidence, then a scroll); a missing file left a "Final results pending" pill although the final study is published; any label change silently dropped the number; no CI watched the contract.

| Item | State |
|---|---|
| Deep link to the study's range section, with descriptive link names | Review (PR) |
| Show n, companies, test window, median range width, study version and as-of date from the JSON | Review (PR) |
| Show the KPI only when it agrees with the structured share; neutral fallback copy | Review (PR) |
| `scripts/check_findings.py` + offline contract tests + weekly `Checks` workflow | Review (PR) |
| Project ROI pill: "In development" to "Planned" (no code exists) | Review (PR) |

Independent checks: the point-in-time quantile sweep (`known_quantiles`) matched a brute-force reimplementation on 1,780 synthetic test rows with 0 mismatches. The hub's 82% equals the structured share 0.8161 of 2,305 three-year forecasts from 319 companies.

## Ordered backlog

Ranked by consequence for analytical correctness, then reviewer understanding, reproducibility, reliability and maintenance cost.

1. **`valuation` DCF timing convention overstates value by about one year of discounting.** Default `closing_year_zero` discounts year 1 (the fiscal year in progress) with exponent 0 and the terminal value at N-1. Hand check, 5 years of FCF 100, WACC 10%, g 0: end-of-year EV 1,000 (exact perpetuity), mid-year 1,018.5, closing-year-zero 1,100. So public-company values run about +10% vs end-of-year and about +8% vs mid-year at a 10% WACC. It is disclosed on the page ("Year 1 is the undiscounted closing year"). Decision needed (Jason): keep the course convention for public companies, or default public cases to mid-year and show the difference. Acceptance: a failing example with the hand-calculated values above, then the chosen default, with the football field and sensitivity grid updated.
2. **`research` / `valuation` engine drift.** Study 01 scored engine v0.9.0 (`34e3852`); the live model is v0.10.1. Decide whether the study page should say "scored against v0.9.0" or rerun against the current engine. Acceptance: the notebook page names the engine version and commit it scored (it shows neither today).
3. **`research` reproducibility on the page.** The study page shows "Published October 30, 2026" but no data version, engine commit or results file link. Add a "Reproduce this number" block (JSON path, engine commit, run id 41097931174).
4. **`hub` one-screen rule.** Brand rule: no scrolling at 1280×800. The page is 1,060 px tall before this sprint (the findings section pushed it over) and 1,086 px after. Decision needed: accept a short scroll for findings, or compact the card.
5. **`research` privacy: contact email in a public workflow file.** `study.yml` has the SEC User-Agent default with a personal email. Jason to add the `SEC_USER_AGENT` secret; then remove the literal in a one-line PR.
6. **`all` brand drift.** `brand/css/brand.css`, `build.py`, `README.md`, `example.html` and `core-mark.svg` differ between the hub and each app repo (`palette.py` matches). Rule: copies stay identical. Investigate which is newest, then sync. Delta is unaffected.
7. **`valuation` weekly Refresh cancelled twice** (2026-11-02, 2026-11-16); Pages skipped on 11-16. Timebox 30 min: find the cause (timeout vs SEC rate limit).
8. **`tps` simulation review** (not done this run beyond test inventory): deterministic and boundary cases, Monte Carlo error vs inherent uncertainty on the Results page, profile a representative run before any trial-count change.
9. **`valuation` comparables review**: peer selection, multiple definitions, denominator dates, negative multiples, against a worked example.
10. **`research` calibration weak spots** (from Study 01 limits): ranges built in shock years (2014, 2020) held about 65%; volatility scaling slightly over-corrects.
11. **`profile` cleanup:** `Courtizy/Courtizy` has an empty file `test` (created 2026-10-03, referenced nowhere). Remove with Jason's OK.
12. **`core` extraction ADR**: before moving `valuation/_core/` into `courtoy-core`, record actual duplication with TPS, consumers (valuation, research via the engine) and migration cost.
13. **`roi`**: no work until Shared Core exists (build order). Keep the hub card "Planned".

## Cleanup review log

- 2026-11-18: inventoried all five repositories. Candidates: empty `Courtizy/test` (item 11). Kept: `research/site/forecast-accuracy/index.html` (redirect from the study's old URL), `private/*.example.json` in valuation and TPS (documented templates, no data). Nothing removed this run.

## Retrospective notes

- 2026-11-18: the review container can't reach `*.github.io` or the SEC, so live pages were checked through a fetch agent and a local mirror of the four sites. Next run: plan the full Study 01 rerun through the `Study` workflow in Actions instead of locally.
