/** Silk layout shell — Stitch-aligned chrome. */

export const SILK_NAV = [
  { id: "register", label: "Register", icon: "person_add", href: "/?view=register", mobile: "Register" },
  { id: "vote", label: "Vote", icon: "how_to_vote", href: "/?view=vote", mobile: "Vote" },
  { id: "verify", label: "Verify Receipt", icon: "receipt_long", href: "/?view=verify", mobile: "Verify" },
  { id: "tally", label: "Admin Tally", icon: "analytics", href: "/tally.html", mobile: "Admin" },
];

export const SILK_EXTRA = [
  { label: "Guide", href: "/demo.html", icon: "menu_book" },
  { label: "Board", href: "/board.html", icon: "public" },
  { label: "Attacks", href: "/attacks.html", icon: "security" },
  { label: "Deck", href: "/deck.html", icon: "slideshow" },
];

export function getActiveView() {
  if (location.pathname.endsWith("tally.html")) return "tally";
  const p = new URLSearchParams(location.search);
  const v = p.get("view") || "register";
  return ["register", "vote", "verify", "tally"].includes(v) ? v : "register";
}

function navLinkClass(id, active) {
  return id === active
    ? "flex items-center gap-3 py-3 rounded-lg bg-surface-container-high text-primary font-bold border-l-4 border-primary pl-3 transition-all duration-200"
    : "flex items-center gap-3 py-3 rounded-lg text-on-surface-variant pl-4 hover:bg-surface-container-high hover:text-on-surface transition-all duration-200";
}

function mobileNavClass(id, active) {
  return id === active
    ? "flex flex-col items-center justify-center text-primary font-bold p-2 rounded-lg min-w-[4rem]"
    : "flex flex-col items-center justify-center text-on-surface-variant p-2 rounded-lg min-w-[4rem] hover:bg-surface-container-low";
}

export function renderSilkShell(activeView) {
  const sideLinks = SILK_NAV.map(
    (n) => `
    <li>
      <a class="${navLinkClass(n.id, activeView)}" href="${n.href}">
        <span class="material-symbols-outlined text-[22px]${n.id === activeView ? " icon-fill" : ""}">${n.icon}</span>
        <span class="text-sm font-medium">${n.label}</span>
      </a>
    </li>`,
  ).join("");

  const mobileLinks = SILK_NAV.map((n) => {
    const on = n.id === activeView;
    return `
    <a class="${mobileNavClass(n.id, activeView)}" href="${n.href}">
      <span class="material-symbols-outlined text-[22px]${on ? " icon-fill" : ""}">${n.icon}</span>
      <span class="text-[10px] font-semibold uppercase mt-1">${n.mobile}</span>
      ${on && n.id === "verify" ? '<span class="absolute -top-0.5 right-2 w-2 h-2 rounded-full bg-primary"></span>' : ""}
    </a>`;
  }).join("");

  const extra = SILK_EXTRA.map(
    (e) =>
      `<a href="${e.href}" class="flex items-center gap-1.5 text-xs text-on-surface-variant hover:text-primary transition-colors"><span class="material-symbols-outlined text-[14px]">${e.icon}</span>${e.label}</a>`,
  ).join("");

  return `
    <header class="bg-surface border-b border-outline-variant sticky top-0 z-50 backdrop-blur-sm bg-surface/95">
      <div class="flex justify-between items-center w-full px-gutter py-3 max-w-container-max mx-auto">
        <a href="/?view=register" class="flex items-center gap-2 group">
          <span class="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/15 transition-colors">
            <span class="material-symbols-outlined text-primary icon-fill">how_to_vote</span>
          </span>
          <span class="text-lg font-semibold text-primary tracking-tight">PQ Voting</span>
        </a>
        <div class="flex items-center gap-3">
          <span class="hidden sm:inline-flex items-center text-label-sm font-semibold uppercase tracking-wide text-on-surface-variant bg-surface-container px-3 py-1.5 rounded-full border border-outline-variant">
            <span class="w-2 h-2 rounded-full bg-primary animate-pulse mr-2"></span>
            General Election 2026 — OPEN
          </span>
          <button type="button" class="p-2 text-on-surface-variant hover:text-primary-container rounded-full hover:bg-surface-container transition-colors" title="Quantum-safe vault">
            <span class="material-symbols-outlined icon-fill text-primary">shield</span>
          </button>
        </div>
      </div>
    </header>
    <div class="flex flex-1 min-h-[calc(100vh-57px)]">
      <nav class="hidden md:flex flex-col w-64 bg-surface-container border-r border-surface-container-highest fixed left-0 top-[57px] bottom-0 z-40 overflow-y-auto custom-scrollbar">
        <div class="px-md pt-6 pb-4 border-b border-outline-variant/60">
          <h2 class="text-headline-md font-semibold text-primary">PQ Voting</h2>
          <p class="text-xs text-on-surface-variant mt-1 font-medium">Secure Digital Vault</p>
        </div>
        <ul class="flex flex-col gap-1 px-2 py-4 flex-1">${sideLinks}</ul>
        <div class="p-4 border-t border-outline-variant flex flex-col gap-2">${extra}</div>
      </nav>
      <div id="silk-main" class="flex-1 w-full md:ml-64 pb-28 md:pb-10 min-h-0"></div>
    </div>
    <nav class="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-2 py-2 md:hidden bg-surface/95 backdrop-blur-md border-t border-outline-variant shadow-[0_-4px_12px_rgba(0,0,0,0.06)] rounded-t-xl">
      ${mobileLinks}
    </nav>`;
}

export function mountShell(activeView) {
  const host = document.getElementById("silk-root");
  if (!host) return null;
  host.innerHTML = renderSilkShell(activeView);
  return document.getElementById("silk-main");
}
