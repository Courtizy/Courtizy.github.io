/* Delta Readiness frame. Include with
     <script src="frame.js" data-page="overview|method|results|signin" data-mode="public|demo|app"></script>
   It adds the hub bar, app header, Overview · Results · Method tabs and footer around whatever the page shows. */
(() => {
  const me = document.currentScript, page = me.dataset.page || "results", mode = me.dataset.mode || "public";
  const base = new URL(".", me.src).href;
  const has = k => { try { return !!localStorage.getItem(k); } catch (e) { return false; } };
  const signedIn = has("fitness-session") || has("fitness-gh-token");
  const R = document.documentElement;
  if (!R.getAttribute("data-theme")) { let t = null; try { t = localStorage.getItem("a-theme"); } catch (e) {} R.setAttribute("data-theme", t || "dark"); }
  if (mode !== "public") R.classList.add("dz-app");
  const results = signedIn ? base : base + "demo.html";
  const tab = (k, href, label) => `<a href="${href}"${k === page ? ' aria-current="page"' : ""}>${label}</a>`;
  const act = mode === "app"
    ? `<button type="button" class="dz-btn" id="dzOut">Sign out</button>`
    : signedIn ? `<a class="dz-btn dz-primary" href="${base}">Open dashboard</a>`
    : page === "signin" ? "" : `<a class="dz-btn dz-primary" href="${base}?signin">Sign in</a>`;
  const theme = mode === "public" ? `<button type="button" class="dz-btn dz-icon" id="dzTheme" aria-label="Switch light or dark"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/></svg></button>` : "";
  const top = `
<div class="dz-hub"><div class="dz-in"><a href="https://courtizy.github.io/">&larr; Decision Models</a><span>Jason C. Courtoy</span></div></div>
<header class="dz-head"><div class="dz-in">
  <div class="dz-tile" aria-hidden="true"><svg viewBox="0 0 64 64" fill="currentColor"><path d="M32 10L54 52H10z"/></svg></div>
  <div class="dz-name"><${page === "overview" ? "h1" : "div"} class="dz-h">Delta Readiness</${page === "overview" ? "h1" : "div"}><p>Am I ready for the PT test?</p></div>
  <div class="dz-right"><span class="dz-status"><i></i>Live</span><div class="dz-acts">${theme}${act}</div></div>
</div></header>
<nav class="dz-tabbar" aria-label="Pages"><div class="dz-in dz-tabs">${tab("overview", base + "overview.html", "Overview")}${tab("results", results, "Results")}${tab("method", base + "overview.html#method", "Method")}</div></nav>
${mode === "demo" ? `<div class="dz-strip"><div class="dz-in"><span class="dz-tag">Demo</span><span>Sample data. Explore freely; nothing is saved.</span></div></div>` : ""}`;
  const foot = `<footer class="dz-foot"><div class="dz-in"><p>Personal project · public or synthetic data only · not medical advice · not endorsed by DoD or the U.S. Air Force</p><p>PT scoring per DAFMAN 36-2905 (PFRA, March 2026).</p></div></footer>`;
  const mount = () => {
    if (document.querySelector(".dz-head")) return;
    document.body.insertAdjacentHTML("afterbegin", top);
    document.body.insertAdjacentHTML("beforeend", foot);
    const out = document.getElementById("dzOut");
    if (out) out.onclick = () => { try { localStorage.removeItem("fitness-session"); localStorage.removeItem("fitness-gh-token"); } catch (e) {} location.href = base + "overview.html"; };
    const th = document.getElementById("dzTheme");
    if (th) th.onclick = () => { const n = R.getAttribute("data-theme") === "light" ? "dark" : "light"; R.setAttribute("data-theme", n); try { localStorage.setItem("a-theme", n); } catch (e) {} };
  };
  /* wait for the whole page so the footer lands after the app */
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount); else mount();
})();
