/** Shared UI — chrome, nav, tables. */

const LOGO_SVG = `<svg viewBox="0 0 24 24" aria-hidden="true">
  <path d="M12 2L4 6v6c0 5 3.5 9.5 8 10 4.5-.5 8-5 8-10V6l-8-4z"/>
  <path d="M9 12l2 2 4-4"/>
</svg>`;

const NAV_LINKS = [
  { href: "/", label: "Vote", id: "vote-home", icon: "🗳️" },
  { href: "/demo.html", label: "Guide", id: "demo", icon: "📋" },
  { href: "/attacks.html", label: "Attacks", id: "attacks", icon: "🛡️" },
  { href: "/pitch.html", label: "Pitch", id: "pitch", icon: "🎯" },
  { href: "/deck.html", label: "Deck", id: "deck", icon: "📽️" },
  { href: "/board.html", label: "Board", id: "board", icon: "📢" },
  { href: "/tally.html", label: "Tally", id: "tally", icon: "📊" },
  { href: "/interop.html", label: "Interop", id: "interop", icon: "🔗" },
];

/**
 * Mount branded header, sticky nav, and footer.
 * @param {{ title: string, tagline?: string, active?: string, wide?: boolean }} opts
 */
export function initPage({ title, tagline = "", active = "", wide = false }) {
  if (wide) document.body.classList.add("page-wide");

  const headerEl = document.getElementById("site-chrome");
  const navEl = document.getElementById("nav");
  const footerEl = document.getElementById("site-footer");

  if (headerEl) {
    headerEl.innerHTML = renderSiteHeader(title, tagline);
  }
  if (navEl) {
    navEl.innerHTML = `<div class="nav-shell">${renderNav(active)}</div>`;
  }
  if (footerEl) {
    footerEl.innerHTML = renderFooter();
  }

  document.title = `${title} · QuantumX PQ Voting`;
}

export function renderSiteHeader(title, tagline) {
  return `
    <header class="site-chrome">
      <div class="brand-bar">
        <a href="/" class="brand">
          <div class="brand-mark">${LOGO_SVG}</div>
          <div class="brand-text">
            <h1 class="brand-title">${title}</h1>
            ${tagline ? `<p class="brand-tagline">${tagline}</p>` : ""}
          </div>
        </a>
        <div class="badge-row">
          <span class="badge badge-pq">Post-quantum</span>
          <span class="badge badge-sdg">SDG 16</span>
          <span class="badge badge-demo">Hackathon demo</span>
        </div>
      </div>
    </header>`;
}

export function renderNav(active = "") {
  return `<nav class="top-nav" aria-label="Main">${NAV_LINKS.map(
    (l) =>
      `<a href="${l.href}" class="${active === l.id ? "active" : ""}" title="${l.label}">${l.icon} ${l.label}</a>`,
  ).join("")}</nav>`;
}

export function renderFooter() {
  return `
    <footer class="site-footer">
      <div class="footer-links">
        <a href="/demo.html">Judge guide</a>
        <a href="/attacks.html">Attack lab</a>
        <a href="/pitch.html">Pitch</a>
        <a href="/docs">API docs</a>
      </div>
      <p>QuantumX · Post-quantum secure e-voting MVP · Kyber + Dilithium · Not for production use</p>
    </footer>`;
}

export function renderHeroStats() {
  return `
    <div class="hero-strip">
      <div class="hero-stat"><div class="num">5</div><div class="lbl">Step demo flow</div></div>
      <div class="hero-stat"><div class="num">PQ</div><div class="lbl">Quantum-safe crypto</div></div>
      <div class="hero-stat"><div class="num">3</div><div class="lbl">Sample voters</div></div>
      <div class="hero-stat"><div class="num">7+</div><div class="lbl">Attack scenarios</div></div>
    </div>`;
}

export function formatApiError(body, status) {
  if (typeof body === "string") return body;
  const detail = body?.detail;
  if (typeof detail === "string") return `HTTP ${status}: ${detail}`;
  return `HTTP ${status}: ${JSON.stringify(body, null, 2)}`;
}

export function renderEligibleVotersTable(voters) {
  if (!voters?.length) {
    return "<p class='copy-hint'>No sample voters configured.</p>";
  }
  const rows = voters
    .map(
      (v, i) => `
    <tr data-idx="${i}">
      <td><span class="badge badge-demo" style="text-transform:none;font-size:0.7rem">${v.label || "Voter"}</span></td>
      <td><strong>${v.name}</strong></td>
      <td class="mono">${v.dob}</td>
      <td class="mono">${v.aadhaar}</td>
      <td class="mono">${v.constituency_id}</td>
      <td><button type="button" class="secondary btn-sm fill-row" data-idx="${i}">Use</button></td>
    </tr>`,
    )
    .join("");

  return `
    <p class="copy-hint">Match a row exactly, or click <strong>Use</strong> to fill the form.</p>
    <div class="table-wrap">
      <table class="data" id="eligibleTable">
        <thead>
          <tr>
            <th>Label</th><th>Name</th><th>DOB</th><th>ID</th><th>Area</th><th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

export function wireEligibleVoterButtons(voters, onSelect) {
  document.querySelectorAll(".fill-row").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = voters[Number(btn.dataset.idx)];
      if (v) onSelect(v);
    });
  });
}
