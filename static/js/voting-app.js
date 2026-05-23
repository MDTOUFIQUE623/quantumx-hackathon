/**
 * Silk UI (Stitch theme) + PQ voting API.
 */
import {
  buildBallot,
  generateVoterKeyPair,
  loadCredential,
  loadVoterKeys,
  saveCredential,
  saveVoterKeys,
} from "./crypto.js";
import { formatApiError, renderEligibleVotersTable, wireEligibleVoterButtons } from "./ui.js";
import { getActiveView, mountShell } from "./silk-shell.js";

const API = window.location.origin;
let cfg = null;
let selectedCandidateId = null;
let selectedCandidateName = "";
let voteWizardStep = 1;

function shortHex(s, n = 8) {
  if (!s || s.length <= n * 2) return s || "—";
  return `${s.slice(0, n)}…${s.slice(-n)}`;
}

function maskAadhaar(val) {
  const d = String(val || "").replace(/\D/g, "");
  if (d.length < 4) return d ? "••••" : "";
  return `XXXX-XXXX-${d.slice(-4)}`;
}

function previewUuid() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return "pending-registration";
}

function showView(name) {
  mountShell(name);
  const main = document.getElementById("silk-main");
  if (!main) return;
  if (name === "register") main.innerHTML = renderRegisterView();
  else if (name === "vote") main.innerHTML = renderVoteView();
  else if (name === "verify") main.innerHTML = renderVerifyView();
  wireView(name);
}

function renderRegisterView() {
  const pendingId = previewUuid();
  return `
    <div class="p-4 md:p-8 lg:p-10 max-w-container-max mx-auto">
      <div id="registration-view" class="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10">
        <div class="lg:col-span-7 flex flex-col gap-6">
          <div>
            <h1 class="text-headline-lg text-on-surface mb-2">Voter Registration</h1>
            <p class="text-body-md text-on-surface-variant">Complete your cryptographic identity binding to participate in the upcoming election.</p>
          </div>
          <div class="card-surface rounded-xl p-6 md:p-8 flex flex-col gap-5">
            <div class="flex flex-col gap-2">
              <label class="silk-label" for="demoVoter">Quick-fill demo voter</label>
              <div class="input-bg rounded-lg flex items-center px-3 py-2">
                <select id="demoVoter" class="bg-transparent w-full outline-none text-on-surface text-sm"></select>
              </div>
            </div>
            <div id="eligibleTableWrap" class="text-sm -mt-1"></div>
            <div class="flex flex-col gap-2">
              <label class="silk-label" for="name">Full name (as per ID)</label>
              <div class="input-bg rounded-lg flex items-center px-3 py-2.5">
                <input id="name" type="text" placeholder="e.g. Ananya Desai" class="bg-transparent w-full outline-none text-on-surface" autocomplete="name" />
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="flex flex-col gap-2">
                <label class="silk-label" for="dob">Date of birth</label>
                <div class="input-bg rounded-lg flex items-center px-3 py-2.5">
                  <input id="dob" type="date" class="bg-transparent w-full outline-none text-on-surface" />
                </div>
              </div>
              <div class="flex flex-col gap-2">
                <label class="silk-label" for="constituency">Constituency</label>
                <div class="input-bg rounded-lg flex items-center px-3 py-2.5">
                  <select id="constituency" class="bg-transparent w-full outline-none text-on-surface text-sm appearance-none"></select>
                </div>
              </div>
            </div>
            <div class="flex flex-col gap-2">
              <label class="silk-label" for="aadhaar">National ID (Aadhaar-like)</label>
              <div class="input-bg rounded-lg flex items-center px-3 py-2.5 bg-surface-container-low">
                <span class="material-symbols-outlined text-on-surface-variant mr-2 text-lg">badge</span>
                <input id="aadhaar" type="text" inputmode="numeric" class="bg-transparent w-full outline-none text-on-surface font-crypto" placeholder="12-digit ID" />
              </div>
              <p id="aadhaarMask" class="text-xs text-on-surface-variant font-crypto pl-1"></p>
            </div>
            <div class="flex flex-col gap-2">
              <label class="silk-label">Assigned voter ID (preview)</label>
              <div class="bg-surface-container-low border border-dashed border-outline-variant rounded-lg px-3 py-2.5 flex items-center justify-between">
                <span id="voterIdPreview" class="font-crypto text-on-surface-variant">${pendingId}</span>
                <span class="material-symbols-outlined text-primary-container text-lg">lock</span>
              </div>
            </div>
            <p id="regStatus" class="text-sm text-on-surface-variant hidden rounded-lg px-3 py-2 bg-surface-container-low"></p>
            <div class="pt-4 border-t border-surface-container-highest flex justify-end">
              <button id="registerBtn" type="button" class="silk-btn-primary">
                Register voter
                <span class="material-symbols-outlined text-lg">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
        <div class="lg:col-span-5 flex flex-col gap-4">
          <div class="card-surface rounded-xl p-6">
            <h3 class="font-semibold text-on-surface flex items-center gap-2 mb-5">
              <span class="material-symbols-outlined text-primary">info</span>
              How registration works
            </h3>
            <div class="silk-timeline pl-1">
              <div class="silk-timeline-step">
                <div class="silk-timeline-num">1</div>
                <div>
                  <h4 class="silk-label text-on-surface">Identity binding</h4>
                  <p class="text-sm text-on-surface-variant mt-1">Demographic data is bound to your national ID hash on the electoral roll.</p>
                </div>
              </div>
              <div class="silk-timeline-step">
                <div class="silk-timeline-num">2</div>
                <div>
                  <h4 class="silk-label text-on-surface">Key generation</h4>
                  <p class="text-sm text-on-surface-variant mt-1">A post-quantum Dilithium keypair is generated locally in your browser.</p>
                </div>
              </div>
              <div class="silk-timeline-step">
                <div class="silk-timeline-num">3</div>
                <div>
                  <h4 class="silk-label text-on-surface">Credential signing</h4>
                  <p class="text-sm text-on-surface-variant mt-1">The IA signs your public key — your anonymous voting token.</p>
                </div>
              </div>
            </div>
          </div>
          <div class="rounded-xl p-5 border border-tertiary-fixed/40 bg-surface-container">
            <h4 class="silk-label text-on-surface flex items-center gap-2 mb-2">
              <span class="material-symbols-outlined text-primary text-base icon-fill">verified_user</span>
              Quantum safe
            </h4>
            <p class="text-xs text-on-surface-variant leading-relaxed">
              Lattice-based Kyber512 + Dilithium2 — designed to resist attacks from future quantum computers.
            </p>
          </div>
        </div>
      </div>
      <div id="success-view" class="hidden flex flex-col items-center py-10 max-w-3xl mx-auto w-full silk-fade-in"></div>
    </div>`;
}

function voteStepNavHtml(step) {
  const steps = [
    { n: 1, label: "Authenticate" },
    { n: 2, label: "Choose candidate" },
    { n: 3, label: "Confirm & submit" },
  ];
  const parts = [];
  steps.forEach((s, i) => {
    let dotClass = "step-dot";
    let inner = String(s.n);
    if (s.n < step) {
      dotClass += " done";
      inner = '<span class="material-symbols-outlined text-base">check</span>';
    } else if (s.n === step) dotClass += " active";
    const labelClass = s.n === step ? "text-on-surface font-semibold" : "text-on-surface-variant";
    parts.push(`
      <div class="flex flex-col items-center gap-2 flex-1 min-w-0 relative z-10">
        <div class="${dotClass}" id="icon-step-${s.n}">${inner}</div>
        <span class="text-[10px] sm:text-xs uppercase font-semibold text-center leading-tight px-1 ${labelClass}">${s.label}</span>
      </div>`);
    if (i < steps.length - 1) {
      parts.push('<div class="flex-1 h-px bg-outline-variant mx-1 mt-4 shrink"></div>');
    }
  });
  return `<div class="vote-step-nav flex items-start bg-surface-container-lowest p-4 rounded-xl border border-outline-variant mb-6 shadow-silk">${parts.join("")}</div>`;
}

function renderVoteView() {
  const cred = loadCredential();
  voteWizardStep = cred ? 2 : 1;

  return `
    <div class="p-4 md:p-8 max-w-[720px] mx-auto flex flex-col gap-6">
      ${voteStepNavHtml(voteWizardStep)}
      <div id="vote-step-1" class="flex flex-col gap-4 step-transition ${voteWizardStep === 1 ? "show-step" : "hide-step"}">
        <div class="card-surface rounded-xl p-6 md:p-8 flex flex-col gap-4">
          <h2 class="text-lg font-semibold text-on-surface">Voter authentication</h2>
          <p class="text-sm text-on-surface-variant">Your credential is stored in this browser after registration.</p>
          ${
            cred
              ? `<div class="bg-primary/5 border border-primary/25 rounded-lg p-4">
              <p class="silk-label text-primary mb-2">Active credential</p>
              <p class="font-crypto text-primary break-all">${cred.voter_id}</p>
              <p class="text-sm text-on-surface-variant mt-2">${cred.constituency_id}</p>
            </div>`
              : `<div class="bg-error-container/40 border border-error/30 rounded-lg p-4 flex gap-3">
              <span class="material-symbols-outlined text-error">warning</span>
              <p class="text-sm text-on-error-container">Register first to receive your IA-signed credential.</p>
            </div>
            <a href="/?view=register" class="silk-btn-primary w-full sm:w-auto">Go to registration</a>`
          }
          <div class="flex justify-end mt-2">
            <button id="authNextBtn" type="button" class="silk-btn-primary" ${cred ? "" : "disabled"}>
              Continue <span class="material-symbols-outlined text-lg">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
      <div id="vote-step-2" class="flex-col gap-4 step-transition ${voteWizardStep === 2 ? "show-step" : "hide-step"}">
        <h2 class="text-lg font-semibold text-on-surface">Select candidate</h2>
        <div class="card-surface rounded-xl p-6">
          <label class="silk-label mb-2 block" for="election">Election</label>
          <div class="input-bg rounded-lg flex items-center px-3 py-2.5 mb-5">
            <select id="election" class="bg-transparent w-full outline-none text-sm"></select>
          </div>
          <div id="candidateCards" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
        </div>
        <div class="flex justify-between gap-3">
          <button id="voteBack1" type="button" class="silk-btn-outline flex-1">Back</button>
          <button id="toConfirmBtn" type="button" class="silk-btn-primary flex-1">Review selection</button>
        </div>
      </div>
      <div id="vote-step-3" class="flex-col gap-4 hide-step step-transition">
        <div class="card-surface rounded-xl p-6 md:p-8 relative overflow-hidden">
          <div id="processing-overlay" class="hide-step absolute inset-0 bg-background/85 backdrop-blur-sm z-20 flex flex-col items-center justify-center rounded-xl">
            <div class="flex flex-col gap-3 w-72">
              <div class="proc-row flex items-center gap-2 text-primary font-semibold text-xs uppercase" data-step="1">
                <span class="material-symbols-outlined text-lg animation-pulse">key</span>
                <span>Encapsulating key (ML-KEM)</span>
              </div>
              <div class="proc-row flex items-center gap-2 text-on-surface-variant opacity-50 text-xs uppercase" data-step="2">
                <span class="material-symbols-outlined text-lg">lock</span>
                <span>Encrypting ballot</span>
              </div>
              <div class="proc-row flex items-center gap-2 text-on-surface-variant opacity-50 text-xs uppercase" data-step="3">
                <span class="material-symbols-outlined text-lg">draw</span>
                <span>Signing payload (ML-DSA)</span>
              </div>
              <div class="proc-row flex items-center gap-2 text-on-surface-variant opacity-50 text-xs uppercase" data-step="4">
                <span class="material-symbols-outlined text-lg">cloud_upload</span>
                <span>Submitting to ledger</span>
              </div>
            </div>
          </div>
          <h2 class="text-lg font-semibold border-b border-outline-variant pb-3 mb-4">Review &amp; encrypt</h2>
          <div class="bg-surface-container-low rounded-lg border border-outline-variant p-4 flex justify-between items-center mb-4">
            <div>
              <p class="silk-label mb-1">Selected candidate</p>
              <p id="review-candidate-name" class="text-lg font-semibold text-primary-container">—</p>
            </div>
            <span class="material-symbols-outlined text-outline text-3xl">verified_user</span>
          </div>
          <div class="grid grid-cols-2 gap-3 mb-6">
            <div>
              <p class="silk-label mb-1">Encryption</p>
              <span class="font-crypto bg-surface-container-low px-2 py-1 rounded border border-outline-variant inline-block">ML-KEM-512</span>
            </div>
            <div>
              <p class="silk-label mb-1">Signature</p>
              <span class="font-crypto bg-surface-container-low px-2 py-1 rounded border border-outline-variant inline-block">ML-DSA-44</span>
            </div>
          </div>
          <div class="flex gap-3 pt-4 border-t border-outline-variant">
            <button id="backVoteBtn" type="button" class="silk-btn-outline flex-1">Back</button>
            <button id="castVoteBtn" type="button" class="silk-btn-primary flex-1">
              <span class="material-symbols-outlined">lock</span> Cast vote
            </button>
          </div>
        </div>
      </div>
      <div id="vote-receipt" class="hide-step flex-col gap-4 step-transition silk-fade-in">
        <div class="card-surface rounded-xl border-2 border-dashed border-primary p-8 text-center">
          <div class="w-16 h-16 rounded-full bg-primary/15 text-primary flex items-center justify-center mx-auto mb-4">
            <span class="material-symbols-outlined text-4xl icon-fill">check_circle</span>
          </div>
          <h2 class="text-xl font-semibold mb-2">Ballot cast successfully</h2>
          <p class="text-sm text-on-surface-variant mb-6 max-w-sm mx-auto">Your vote is encrypted and on the public ledger. Keep this receipt to verify inclusion.</p>
          <div class="text-left bg-surface-container-low rounded-lg border border-outline-variant p-4 mb-3 group relative">
            <span class="silk-label">Ballot tracking ID</span>
            <p id="receipt-ballot-id" class="font-crypto text-on-surface mt-1 break-all tracking-wide"></p>
          </div>
          <div class="text-left bg-surface-container-low rounded-lg border border-outline-variant p-4 mb-6">
            <span class="silk-label">Ledger chain hash</span>
            <p id="receipt-chain-hash" class="font-crypto text-[11px] leading-relaxed text-on-surface mt-1 break-all"></p>
          </div>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <button type="button" id="copyReceipt" class="silk-btn-outline">Copy ballot ID</button>
            <a href="/?view=verify" class="silk-btn-primary">Verify receipt</a>
          </div>
        </div>
      </div>
    </div>`;
}

function renderVerifyView() {
  return `
    <div class="p-4 md:p-8 max-w-[640px] mx-auto space-y-8">
      <div class="text-center space-y-3">
        <h1 class="text-headline-lg text-on-surface">Cryptographic verification</h1>
        <p class="text-body-md text-on-surface-variant">Confirm your ballot is recorded on the immutable public ledger.</p>
      </div>
      <div class="card-surface rounded-xl p-6 md:p-8">
        <div class="space-y-4">
          <div>
            <label class="silk-label block mb-2" for="verifyId">Ballot tracking ID</label>
            <div class="input-bg rounded-lg px-4 py-3">
              <input id="verifyId" type="text" class="bg-transparent w-full outline-none font-crypto text-on-surface" placeholder="e.g. from vote receipt" />
            </div>
          </div>
          <div>
            <label class="silk-label block mb-2" for="chainHash">Chain hash (optional)</label>
            <div class="input-bg rounded-lg px-4 py-3">
              <input id="chainHash" type="text" class="bg-transparent w-full outline-none font-crypto text-on-surface" placeholder="64-char SHA3-256" />
            </div>
          </div>
          <button id="verifyBtn" type="button" class="silk-btn-primary w-full">
            <span class="material-symbols-outlined">search</span>
            Verify inclusion
          </button>
        </div>
      </div>
      <div id="verify-result" class="hidden silk-fade-in"></div>
      <div class="space-y-4 pt-6 border-t border-outline-variant">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-on-surface">Public ledger feed</h3>
          <span class="flex items-center gap-2 silk-label text-primary normal-case">
            <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            Live
          </span>
        </div>
        <div id="ledgerFeed" class="card-surface rounded-xl overflow-hidden">
          <p class="p-6 text-sm text-on-surface-variant text-center">Loading recent ballots…</p>
        </div>
        <a href="/board.html" class="flex justify-center silk-label text-primary normal-case hover:text-primary-container transition-colors gap-1">
          View full bulletin board
          <span class="material-symbols-outlined text-sm">open_in_new</span>
        </a>
      </div>
    </div>`;
}

function setVoteStep(step) {
  voteWizardStep = step;
  [1, 2, 3].forEach((n) => {
    const el = document.getElementById(`vote-step-${n}`);
    if (!el) return;
    if (n === step) {
      el.classList.remove("hide-step");
      el.classList.add("show-step", "flex");
    } else {
      el.classList.add("hide-step");
      el.classList.remove("show-step", "flex");
    }
  });
  const nav = document.querySelector(".vote-step-nav");
  if (nav) nav.outerHTML = voteStepNavHtml(step);
}

function animateProcessing() {
  const overlay = document.getElementById("processing-overlay");
  overlay.classList.remove("hide-step");
  overlay.classList.add("flex");
  const rows = overlay.querySelectorAll(".proc-row");
  const delays = [0, 900, 1800, 2700];
  delays.forEach((ms, idx) => {
    setTimeout(() => {
      rows.forEach((r) => {
        r.classList.add("opacity-50", "text-on-surface-variant");
        r.classList.remove("text-primary");
        r.querySelector(".material-symbols-outlined")?.classList.remove("animation-pulse");
      });
      const active = rows[idx];
      if (active) {
        active.classList.remove("opacity-50", "text-on-surface-variant");
        active.classList.add("text-primary");
        active.querySelector(".material-symbols-outlined")?.classList.add("animation-pulse");
      }
    }, ms);
  });
  return () => {
    overlay.classList.add("hide-step");
    overlay.classList.remove("flex");
  };
}

function fillVoterForm(v) {
  document.getElementById("name").value = v.name;
  document.getElementById("dob").value = v.dob;
  document.getElementById("aadhaar").value = v.aadhaar;
  document.getElementById("constituency").value = v.constituency_id;
  const mask = document.getElementById("aadhaarMask");
  if (mask) mask.textContent = mask ? `Masked: ${maskAadhaar(v.aadhaar)}` : "";
  const demo = document.getElementById("demoVoter");
  const idx = window.__demoVoters?.findIndex(
    (x) => x.aadhaar === v.aadhaar && x.constituency_id === v.constituency_id,
  );
  if (demo && idx >= 0) demo.value = String(idx);
}

function showRegistrationSuccess(body) {
  const cred = body.credential;
  document.getElementById("registration-view").classList.add("hidden");
  const sv = document.getElementById("success-view");
  sv.classList.remove("hidden");
  sv.classList.add("flex");
  const constLabel =
    cfg?.constituencies?.find((c) => c.id === cred.constituency_id)?.name || cred.constituency_id;
  sv.innerHTML = `
    <div class="bg-primary/10 rounded-full p-4 mb-6">
      <span class="material-symbols-outlined text-5xl text-primary icon-fill">check_circle</span>
    </div>
    <h2 class="text-headline-lg text-on-surface mb-2 text-center">Registration complete</h2>
    <p class="text-on-surface-variant text-center mb-8 max-w-md">Your cryptographic voting credential has been securely generated and saved in this browser.</p>
    <div class="w-full card-surface rounded-xl p-6 md:p-8 relative overflow-hidden mb-8 text-left">
      <div class="credential-glow"></div>
      <div class="flex justify-between items-center border-b border-surface-container-highest pb-4 mb-5 relative z-10">
        <span class="silk-label tracking-widest">Digital voting credential</span>
        <span class="material-symbols-outlined text-on-surface-variant">fingerprint</span>
      </div>
      <div class="space-y-4 relative z-10 text-sm">
        <div class="grid grid-cols-3 gap-3 items-baseline">
          <span class="silk-label col-span-1">Voter ID</span>
          <span class="font-crypto text-primary col-span-2 break-all">${body.voter_id}</span>
        </div>
        <div class="grid grid-cols-3 gap-3 items-baseline">
          <span class="silk-label col-span-1">Constituency</span>
          <span class="font-crypto col-span-2">${constLabel}</span>
        </div>
        <div class="grid grid-cols-3 gap-3 items-baseline pt-3 border-t border-surface-container-highest">
          <span class="silk-label col-span-1">Biometric hash</span>
          <span class="font-crypto text-on-surface-variant col-span-2 break-all text-xs">${cred.biometric_hash}</span>
        </div>
        <div class="grid grid-cols-3 gap-3 items-baseline">
          <span class="silk-label col-span-1">IA signature</span>
          <span class="font-crypto text-on-surface-variant col-span-2 break-all text-xs">${shortHex(cred.ia_signature, 20)}</span>
        </div>
      </div>
    </div>
    <div class="flex flex-col sm:flex-row gap-4 w-full max-w-lg">
      <button type="button" id="dlCred" class="silk-btn-outline flex-1">
        <span class="material-symbols-outlined text-lg">download</span>
        Download JSON
      </button>
      <a href="/?view=vote" class="silk-btn-primary flex-1">Proceed to vote</a>
    </div>`;
  document.getElementById("dlCred")?.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(body, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `credential-${body.voter_id}.json`;
    a.click();
  });
}

async function loadConfig() {
  const res = await fetch(`${API}/api/demo/config`);
  cfg = await res.json();
  window.__demoVoters = cfg.sample_eligible_voters || cfg.demo_voters;
  window.__elections = cfg.elections;
}

function wireRegister() {
  const voters = window.__demoVoters || [];
  document.getElementById("eligibleTableWrap").innerHTML = renderEligibleVotersTable(voters);
  wireEligibleVoterButtons(voters, fillVoterForm);

  const sel = document.getElementById("constituency");
  cfg.constituencies.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = `${c.id} — ${c.name}`;
    sel.appendChild(opt);
  });

  const demo = document.getElementById("demoVoter");
  demo.innerHTML = '<option value="">— manual entry —</option>';
  voters.forEach((v, i) => {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = v.label;
    demo.appendChild(opt);
  });
  demo.addEventListener("change", (e) => {
    if (e.target.value === "") return;
    fillVoterForm(voters[Number(e.target.value)]);
  });

  document.getElementById("aadhaar")?.addEventListener("input", (e) => {
    const m = document.getElementById("aadhaarMask");
    if (m) m.textContent = e.target.value ? `Masked: ${maskAadhaar(e.target.value)}` : "";
  });

  document.getElementById("registerBtn").addEventListener("click", async () => {
    const status = document.getElementById("regStatus");
    status.classList.remove("hidden", "text-error", "bg-error-container/30");
    status.classList.add("bg-surface-container-low");
    status.textContent = "Generating Dilithium keys in browser…";
    try {
      const keys = await generateVoterKeyPair();
      const res = await fetch(`${API}/api/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: document.getElementById("name").value.trim(),
          dob: document.getElementById("dob").value.trim(),
          aadhaar: document.getElementById("aadhaar").value.trim(),
          constituency_id: document.getElementById("constituency").value,
          dilithium_pk: keys.publicKeyHex,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        status.textContent = formatApiError(body, res.status);
        status.classList.add("text-error", "bg-error-container/30");
        return;
      }
      saveVoterKeys(body.voter_id, {
        secretKeyHex: keys.secretKeyHex,
        publicKeyHex: keys.publicKeyHex,
      });
      saveCredential(body.credential);
      document.getElementById("voterIdPreview").textContent = body.voter_id;
      showRegistrationSuccess(body);
    } catch (err) {
      status.textContent = `Error: ${err.message}`;
      status.classList.add("text-error");
    }
  });
}

function renderCandidateCards() {
  const electionId = document.getElementById("election")?.value;
  const election = window.__elections?.find((e) => e.election_id === electionId);
  const wrap = document.getElementById("candidateCards");
  if (!wrap) return;
  wrap.innerHTML = "";
  selectedCandidateId = null;
  const icons = ["account_balance", "groups", "person", "flag"];
  (election?.candidates || []).forEach((c, i) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className =
      "candidate-card text-left card-surface rounded-xl p-5 border border-outline-variant";
    card.dataset.id = c.candidate_id;
    card.innerHTML = `
      <div class="flex justify-between items-start mb-4">
        <div class="w-12 h-12 rounded-lg bg-surface-container-low flex items-center justify-center">
          <span class="material-symbols-outlined text-primary-container text-2xl">${icons[i % icons.length]}</span>
        </div>
        <div class="selection-ring w-6 h-6 rounded-full border-2 border-outline-variant flex items-center justify-center">
          <div class="inner-dot w-3 h-3 rounded-full bg-primary-container opacity-0 transition-opacity"></div>
        </div>
      </div>
      <h3 class="font-semibold text-on-surface text-lg">${c.name}</h3>
      <p class="silk-label mt-1 normal-case">${c.candidate_id}</p>`;
    card.addEventListener("click", () => {
      wrap.querySelectorAll(".candidate-card").forEach((el) => {
        el.classList.remove("selected");
        el.querySelector(".selection-ring")?.classList.remove("selected");
        el.querySelector(".inner-dot")?.classList.remove("opacity-100");
      });
      card.classList.add("selected");
      card.querySelector(".selection-ring")?.classList.add("selected");
      card.querySelector(".inner-dot")?.classList.add("opacity-100");
      selectedCandidateId = c.candidate_id;
      selectedCandidateName = c.name;
    });
    wrap.appendChild(card);
  });
}

function wireVote() {
  document.getElementById("authNextBtn")?.addEventListener("click", () => setVoteStep(2));

  const electionSel = document.getElementById("election");
  if (!electionSel) return;
  electionSel.innerHTML = "";
  window.__elections?.forEach((e) => {
    const opt = document.createElement("option");
    opt.value = e.election_id;
    opt.textContent = e.title;
    electionSel.appendChild(opt);
  });
  electionSel.addEventListener("change", renderCandidateCards);
  renderCandidateCards();

  document.getElementById("voteBack1")?.addEventListener("click", () => setVoteStep(1));

  document.getElementById("toConfirmBtn")?.addEventListener("click", () => {
    if (!loadCredential()) {
      alert("Register first.");
      return;
    }
    if (!selectedCandidateId) {
      alert("Select a candidate.");
      return;
    }
    document.getElementById("review-candidate-name").textContent = selectedCandidateName;
    setVoteStep(3);
  });

  document.getElementById("backVoteBtn")?.addEventListener("click", () => setVoteStep(2));

  document.getElementById("castVoteBtn")?.addEventListener("click", async () => {
    const cred = loadCredential();
    const keys = loadVoterKeys(cred?.voter_id);
    if (!cred || !keys) return;

    animateProcessing();

    try {
      const electionId = document.getElementById("election").value;
      const auth = await fetch(`${API}/api/authorities/public-keys`);
      const authKeys = await auth.json();
      const ballot = await buildBallot({
        voterId: cred.voter_id,
        electionId,
        candidateId: selectedCandidateId,
        voterSecretKeyHex: keys.secretKeyHex,
        eaPublicKeyHex: authKeys.ea_public_key_hex,
        kemAlgorithm: authKeys.algorithms?.kem,
      });
      const res = await fetch(`${API}/api/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ballot, constituency_id: cred.constituency_id }),
      });
      const body = await res.json();
      document.getElementById("processing-overlay")?.classList.add("hide-step");
      if (!res.ok) {
        alert(formatApiError(body, res.status));
        return;
      }
      sessionStorage.setItem("pq_last_ballot_id", body.ballot_id);
      sessionStorage.setItem("pq_last_chain_hash", body.chain_hash || "");
      setVoteStep(3);
      document.getElementById("vote-step-3").classList.add("hide-step");
      const receipt = document.getElementById("vote-receipt");
      receipt.classList.remove("hide-step");
      receipt.classList.add("flex");
      document.getElementById("receipt-ballot-id").textContent = body.ballot_id;
      document.getElementById("receipt-chain-hash").textContent = body.chain_hash;
      document.getElementById("copyReceipt")?.addEventListener("click", () => {
        navigator.clipboard?.writeText(body.ballot_id);
      });
      const nav = document.querySelector(".vote-step-nav");
      if (nav) {
        const dot = document.getElementById("icon-step-3");
        if (dot) {
          dot.className = "step-dot done";
          dot.innerHTML = '<span class="material-symbols-outlined text-base">check</span>';
        }
      }
    } catch (err) {
      document.getElementById("processing-overlay")?.classList.add("hide-step");
      alert(err.message);
    }
  });
}

async function loadLedgerFeed() {
  const wrap = document.getElementById("ledgerFeed");
  if (!wrap) return;
  try {
    const elections = await fetch(`${API}/api/board/elections`).then((r) => r.json());
    const eid = elections.elections?.[0]?.election_id;
    if (!eid) {
      wrap.innerHTML = '<p class="p-6 text-sm text-center text-on-surface-variant">No elections on board yet.</p>';
      return;
    }
    const board = await fetch(`${API}/api/board/${eid}`).then((r) => r.json());
    const rows = (board.ballots || [])
      .slice(-8)
      .reverse()
      .map((b) => {
        const ts = b.submitted_at ? new Date(b.submitted_at).toISOString().slice(11, 19) : "—";
        const trunc = shortHex(b.ballot_id, 4);
        return `
        <tr class="hover:bg-surface-container-high transition-colors">
          <td class="p-4 font-mono text-sm">${trunc}</td>
          <td class="p-4 text-sm text-on-surface-variant">${eid.split("-").pop()}</td>
          <td class="p-4 font-mono text-sm text-on-surface-variant">${ts}</td>
          <td class="p-4"><span class="badge-secured"><span class="material-symbols-outlined text-xs">lock</span> Secured</span></td>
        </tr>`;
      })
      .join("");
    wrap.innerHTML = `
      <div class="overflow-x-auto custom-scrollbar">
        <table class="w-full text-left">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th class="p-4 silk-label text-primary">Ballot ID</th>
              <th class="p-4 silk-label text-primary">Election</th>
              <th class="p-4 silk-label text-primary">Time (UTC)</th>
              <th class="p-4 silk-label text-primary">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant">${rows || '<tr><td colspan="4" class="p-6 text-center text-sm text-on-surface-variant">No ballots yet — cast a vote first.</td></tr>'}</tbody>
        </table>
      </div>`;
  } catch {
    wrap.innerHTML = '<p class="p-6 text-sm text-center text-error">Could not load ledger feed.</p>';
  }
}

function wireVerify() {
  const saved = sessionStorage.getItem("pq_last_ballot_id");
  const hash = sessionStorage.getItem("pq_last_chain_hash");
  if (saved) document.getElementById("verifyId").value = saved;
  if (hash) document.getElementById("chainHash").value = hash;

  loadLedgerFeed();

  document.getElementById("verifyBtn")?.addEventListener("click", async () => {
    const id = document.getElementById("verifyId").value.trim();
    if (!id) return;
    const res = await fetch(`${API}/api/verify/${id}`);
    const body = await res.json();
    const box = document.getElementById("verify-result");
    box.classList.remove("hidden");
    const chainInput = document.getElementById("chainHash").value.trim();
    const hashOk = !chainInput || body.chain_hash === chainInput;

    if (res.ok && body.on_board && hashOk) {
      const ts = body.submitted_at
        ? new Date(body.submitted_at).toISOString().replace("T", " ").slice(0, 19) + " UTC"
        : "—";
      box.innerHTML = `
        <div class="card-surface rounded-xl border-2 border-primary p-6 md:p-8 relative overflow-hidden silk-fade-in">
          <div class="absolute top-0 right-0 p-4 opacity-[0.07] pointer-events-none">
            <span class="material-symbols-outlined text-[7rem] text-primary">verified_user</span>
          </div>
          <div class="relative z-10 flex flex-col items-center text-center gap-4">
            <div class="h-16 w-16 bg-primary/15 rounded-full flex items-center justify-center border border-primary">
              <span class="material-symbols-outlined text-4xl text-primary icon-fill">check_circle</span>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-primary tracking-wide uppercase">Ballot confirmed in ledger</h3>
              <p class="text-sm text-on-surface-variant mt-2">Your vote is secured and counted in the tally pool.</p>
            </div>
          </div>
          <div class="mt-6 pt-6 border-t border-outline-variant space-y-4 relative z-10">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="silk-label block mb-1">Recorded</span>
                <span class="font-mono">${ts}</span>
              </div>
              <div>
                <span class="silk-label block mb-1">Election</span>
                <span>${body.election_id || "—"}</span>
              </div>
            </div>
            <div class="p-4 bg-surface-container-low border border-dashed border-outline-variant rounded-lg flex justify-between gap-3 items-start">
              <div class="min-w-0">
                <span class="silk-label block mb-1">Block hash</span>
                <span class="font-mono text-xs break-all">${body.chain_hash || "—"}</span>
              </div>
              <button type="button" class="copy-hash shrink-0 p-2 text-on-surface-variant hover:text-primary" title="Copy">
                <span class="material-symbols-outlined">content_copy</span>
              </button>
            </div>
          </div>
        </div>`;
      box.querySelector(".copy-hash")?.addEventListener("click", () => {
        navigator.clipboard?.writeText(body.chain_hash || "");
      });
    } else if (res.ok && body.on_board && !hashOk) {
      box.innerHTML = `<div class="rounded-xl p-4 border border-error bg-error-container/30 text-sm text-on-error-container">Ballot found but chain hash does not match.</div>`;
    } else {
      box.innerHTML = `<div class="rounded-xl p-4 border border-error bg-error-container/30 text-sm font-mono overflow-auto">${formatApiError(body, res.status)}</div>`;
    }
  });
}

function wireView(name) {
  if (name === "register") wireRegister();
  else if (name === "vote") wireVote();
  else if (name === "verify") wireVerify();
}

async function init() {
  await loadConfig();
  showView(getActiveView());
}

init();
