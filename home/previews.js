// Homepage previews: one small example result per live model, read from what each model already publishes.
// Nothing is calculated here: every number comes from the model's own exported JSON (brand rule 5).
// If a file is missing or its shape changes, the preview quietly falls back to a one-line note and the
// row still works as a plain link. scripts/check_previews.py checks the same contract in CI.
(() => {
  const TPS = "TPS-Monte-Carlo-Simulation/data/";
  const VAL = "valuation/demo/data/";
  const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const LABELS = { dcf: "DCF", comps: "Sector comps", comps_closest: "Closest comps", precedents: "Precedents", lbo: "LBO" };

  const getJSON = (url) => fetch(url, { cache: "no-cache" }).then((r) => {
    if (!r.ok) throw new Error(`${url}: ${r.status}`);
    return r.json();
  });
  const h = (tag, attrs = {}, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "style") Object.assign(el.style, v);
      else el.setAttribute(k, v);
    }
    for (const kid of kids.flat()) if (kid != null) el.append(kid);
    return el;
  };
  const dollars = (x) => "$" + Math.round(x);
  const pct = (x) => Math.round(x * 100) + "%";
  const isNum = (x) => typeof x === "number" && Number.isFinite(x);

  function fail(slot, err) {
    slot.replaceChildren(h("p", { class: "pv__fallback" }, "The example preview didn't load. The model itself is a click away."));
    slot.removeAttribute("aria-busy");
    if (err) console.warn("[home previews]", err.message || err);
  }

  /* ---- Valuation: a compact football field for the synthetic demo company ---- */
  async function valuation(slot) {
    const index = await getJSON(VAL + "index.json");
    const company = index.companies.find((c) => c.ticker === "DEMO") || index.companies[0];
    const run = company.runs[0];
    const cmp = await getJSON(VAL + run.comparison);
    const weighted = cmp.plan.methods.filter((m) => m.ran && m.weight > 0);
    const field = new Map(cmp.football_field.map((f) => [f.model, f]));
    const rows = weighted.map((m) => ({ label: `${LABELS[m.model] || m.name} · ${pct(m.weight)}`, ...field.get(m.model) }))
      .filter((r) => isNum(r.p10) && isNum(r.p50) && isNum(r.p90));
    const blend = cmp.blend;
    if (!rows.length || !blend || ![blend.p10, blend.p50, blend.p90].every(isNum)) throw new Error("valuation: unexpected comparison.json shape");
    rows.push({ label: "Weighted", ...blend, total: true });

    const price = isNum(cmp.price) ? cmp.price : null;
    const lo = Math.floor(Math.min(...rows.map((r) => r.p10), price ?? Infinity) / 5) * 5;
    const hi = Math.ceil(Math.max(...rows.map((r) => r.p90), price ?? -Infinity) / 5) * 5;
    const x = (v) => ((v - lo) / (hi - lo)) * 100 + "%";
    const name = company.name.replace(/\s*\(synthetic\)\s*$/i, "");

    const said = rows.map((r) => `${r.label}: ${dollars(r.p10)} to ${dollars(r.p90)}, median ${dollars(r.p50)}`).join("; ");
    const chart = h("div", { class: "ff", role: "img",
      "aria-label": `Value per share, middle 80% of simulated runs. ${said}.${price ? ` Share price ${dollars(price)}.` : ""}` },
      rows.map((r) => h("div", { class: "ff__row" + (r.total ? " ff__row--total" : ""), "aria-hidden": "true" },
        h("span", { class: "ff__label" }, r.label),
        h("span", { class: "ff__track" },
          h("span", { class: "ff__bar", style: { left: x(r.p10), width: `calc(${x(r.p90)} - ${x(r.p10)})` } }),
          h("span", { class: "ff__mid", style: { left: x(r.p50) } }),
          price ? h("span", { class: "ff__price", style: { left: x(price) } }) : null),
        h("span", { class: "ff__range num" }, `${dollars(r.p10)}–${dollars(r.p90)}`))),
      h("div", { class: "ff__axis", "aria-hidden": "true" },
        h("span", { class: "ff__label" }),
        h("span", { class: "ff__track" },
          h("span", { class: "ff__tick num", style: { left: "0%" } }, dollars(lo)),
          price ? h("span", { class: "ff__tick ff__tick--price num", style: { left: x(price) } }, `price ${dollars(price)}`) : null,
          h("span", { class: "ff__tick ff__tick--end num", style: { left: "100%" } }, dollars(hi))),
        h("span", { class: "ff__range" })));

    slot.replaceChildren(
      h("p", { class: "pv__answer" }, h("span", { class: "num" }, `${dollars(blend.p10)}–${dollars(blend.p90)}`), " a share"),
      h("p", { class: "pv__caption" }, `Example: ${name}, a synthetic company. Value per share, middle 80% of simulated runs.`),
      chart,
      cmp.headlines?.field ? h("p", { class: "pv__note" }, cmp.headlines.field) : null);
    slot.removeAttribute("aria-busy");
  }

  /* ---- Turn Pattern Sustainability: aircraft ready vs needed, Monday to Friday ---- */
  async function tps(slot) {
    const presets = await getJSON(TPS + "presets.json");
    const p = await getJSON(TPS + `preset_${presets.default}.json`);
    const share = p.kpis.weeks_meeting_every_requirement;
    const days = DAYS.map((d) => p.days.find((x) => x.day === d)).filter(Boolean);
    if (!isNum(share) || days.length !== DAYS.length ||
        !days.every((d) => [d.available_p10, d.available_p50, d.available_p90, d.needed].every(isNum)))
      throw new Error("tps: unexpected preset shape");
    // The axis spans the data (not zero): these are ranges against a requirement, not magnitudes.
    const lo = Math.max(0, Math.min(...days.map((d) => Math.min(d.available_p10, d.needed))) - 1);
    const hi = Math.max(...days.map((d) => Math.max(d.available_p90, d.needed))) + 1;
    const y = (v) => ((v - lo) / (hi - lo)) * 100 + "%";

    const said = days.map((d) => `${d.day} ${d.available_p10} to ${d.available_p90} ready (median ${d.available_p50}), ${d.needed} needed${d.status !== "good" ? `, ${d.status_label.toLowerCase()}` : ""}`).join("; ");
    const chart = h("div", { class: "days", role: "img",
      "aria-label": `Aircraft ready at each day's first go against aircraft needed, middle 80% of simulated weeks. ${said}.` },
      h("div", { class: "days__axis", "aria-hidden": "true" },
        h("span", { class: "num" }, String(hi)), h("span", { class: "num" }, String(lo))),
      days.map((d) => h("div", { class: "days__col" + (d.status !== "good" ? " days__col--flag" : ""), "aria-hidden": "true" },
        h("span", { class: "days__plot" },
          h("span", { class: "days__bar", style: { bottom: y(d.available_p10), height: `calc(${y(d.available_p90)} - ${y(d.available_p10)})` } }),
          h("span", { class: "days__mid", style: { bottom: y(d.available_p50) } }),
          h("span", { class: "days__need", style: { bottom: y(d.needed) } })),
        h("span", { class: "days__day" }, d.day),
        h("span", { class: "days__flag" }, d.status !== "good" ? d.status_label : ""))));

    slot.replaceChildren(
      h("p", { class: "pv__answer" }, h("span", { class: "num" }, pct(share)), " of weeks meet the plan"),
      h("p", { class: "pv__caption" }, `Share of simulated weeks that meet every requirement. Example: ${p.unit_name.toLowerCase().replace(/^synthetic/, "a synthetic")}, ${p.scenario_label.toLowerCase()}, ${p.simulation.runs.toLocaleString("en-US")} runs.`),
      chart,
      h("p", { class: "pv__legend", "aria-hidden": "true" },
        h("span", {}, h("span", { class: "key key--bar" }), " aircraft ready, middle 80% of weeks"),
        h("span", {}, h("span", { class: "key key--mid" }), " median"),
        h("span", {}, h("span", { class: "key key--need" }), " aircraft needed")),
      p.binding && isNum(p.binding.p_day_met)
        ? h("p", { class: "pv__note" }, `Binding constraint: ${p.binding.requirement} holds in ${pct(p.binding.p_day_met)} of weeks.`) : null);
    slot.removeAttribute("aria-busy");
  }

  for (const [id, fn] of [["valuation", valuation], ["tps", tps]]) {
    const slot = document.querySelector(`[data-preview="${id}"]`);
    if (slot) fn(slot).catch((e) => fail(slot, e));
  }
})();
