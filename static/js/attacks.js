/**
 * Live attack demonstrations — each calls the real API and expects a block.
 */
import { buildBallot, generateVoterKeyPair } from "./crypto.js";
import { formatApiError } from "./ui.js";

const API = window.location.origin;

async function register(voter, keys) {
  return fetch(`${API}/api/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: voter.name,
      dob: voter.dob,
      aadhaar: voter.aadhaar,
      constituency_id: voter.constituency_id,
      dilithium_pk: keys.publicKeyHex,
    }),
  });
}

async function castVote(credential, keys, electionId, constituencyOverride) {
  const auth = await fetch(`${API}/api/authorities/public-keys`);
  const authKeys = await auth.json();
  const ballot = await buildBallot({
    voterId: credential.voter_id,
    electionId,
    candidateId: "c1",
    voterSecretKeyHex: keys.secretKeyHex,
    eaPublicKeyHex: authKeys.ea_public_key_hex,
    kemAlgorithm: authKeys.algorithms?.kem,
  });
  return fetch(`${API}/api/vote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ballot,
      constituency_id: constituencyOverride ?? credential.constituency_id,
    }),
  });
}

function result(id, title, expectedStatus, res, body, extra = {}) {
  const status = res?.status ?? null;
  const blocked =
    expectedStatus == null
      ? true
      : status === expectedStatus || (expectedStatus === 403 && status === 403);
  return {
    attack_id: id,
    title,
    expected_status: expectedStatus,
    actual_status: status,
    blocked,
    detail: typeof body?.detail === "string" ? body.detail : body,
    ...extra,
  };
}

export async function runAttack(id, { labVoter, attackVoters, sampleVoters, electionId }) {
  const voterFor = (key) => attackVoters?.[key] ?? labVoter;
  switch (id) {
    case "fake_voter": {
      const keys = await generateVoterKeyPair();
      const res = await register(
        {
          name: "Fake Person",
          dob: "2001-01-01",
          aadhaar: "000000000000",
          constituency_id: "MH-22-Pune",
        },
        keys,
      );
      const body = await res.json();
      return result(id, "Register without electoral roll", 403, res, body);
    }

    case "cross_constituency": {
      const keys = await generateVoterKeyPair();
      const v = sampleVoters[0];
      const res = await register(
        {
          name: v.name,
          dob: v.dob,
          aadhaar: v.aadhaar,
          constituency_id: "DL-07-Delhi",
        },
        keys,
      );
      const body = await res.json();
      return result(id, "Cross-constituency registration", 403, res, body);
    }

    case "double_vote": {
      const keys = await generateVoterKeyPair();
      const reg = await register(voterFor("double_vote"), keys);
      const regBody = await reg.json();
      if (reg.status === 409) {
        return result(id, "Double vote", 409, reg, regBody, {
          blocked: false,
          hint: "Attack Lab Voter already registered. Delete data/ledger.db and refresh, or use a fresh Docker volume.",
        });
      }
      if (!reg.ok) {
        return result(id, "Double vote (register failed)", 409, reg, regBody);
      }
      const cred = regBody.credential;
      const first = await castVote(cred, keys, electionId);
      const firstBody = await first.json();
      if (!first.ok) {
        return result(id, "Double vote (first ballot failed)", 409, first, firstBody, {
          hint: "Voter may have already voted. Reset data/ledger.db to replay.",
        });
      }
      const second = await castVote(cred, keys, electionId);
      const secondBody = await second.json();
      return result(id, "Double vote", 409, second, secondBody, {
        first_vote: firstBody.ballot_id,
      });
    }

    case "forged_signature": {
      const keys = await generateVoterKeyPair();
      const reg = await register(voterFor("forged_signature"), keys);
      const regBody = await reg.json();
      if (reg.status === 409) {
        return result(id, "Forged signature", 400, reg, regBody, {
          blocked: false,
          hint: "Reset data/ledger.db to register Attack Lab with new keys for this demo.",
        });
      }
      if (!reg.ok) {
        return result(id, "Forged signature", 400, reg, regBody);
      }
      const cred = regBody.credential;
      const auth = await fetch(`${API}/api/authorities/public-keys`);
      const authKeys = await auth.json();
      const ballot = await buildBallot({
        voterId: cred.voter_id,
        electionId,
        candidateId: "c1",
        voterSecretKeyHex: keys.secretKeyHex,
        eaPublicKeyHex: authKeys.ea_public_key_hex,
        kemAlgorithm: authKeys.algorithms?.kem,
      });
      ballot.signature = "00" + ballot.signature.slice(2);
      const res = await fetch(`${API}/api/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ballot,
          constituency_id: cred.constituency_id,
        }),
      });
      const body = await res.json();
      return result(id, "Forged ballot signature", 400, res, body);
    }

    case "wrong_constituency_vote": {
      const keys = await generateVoterKeyPair();
      const reg = await register(voterFor("wrong_constituency_vote"), keys);
      const regBody = await reg.json();
      if (!reg.ok) {
        return result(id, "Wrong constituency at vote", 403, reg, regBody, {
          hint: reg.status === 409 ? "Reset data/ledger.db to replay." : undefined,
        });
      }
      const cred = regBody.credential;
      const res = await castVote(cred, keys, electionId, "DL-07-Delhi");
      const body = await res.json();
      return result(id, "Vote with wrong constituency_id", 403, res, body);
    }

    case "unregistered_voter": {
      const keys = await generateVoterKeyPair();
      const auth = await fetch(`${API}/api/authorities/public-keys`);
      const authKeys = await auth.json();
      const ballot = await buildBallot({
        voterId: "00000000-0000-4000-8000-000000000099",
        electionId,
        candidateId: "c1",
        voterSecretKeyHex: keys.secretKeyHex,
        eaPublicKeyHex: authKeys.ea_public_key_hex,
        kemAlgorithm: authKeys.algorithms?.kem,
      });
      const res = await fetch(`${API}/api/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ballot,
          constituency_id: "MH-22-Pune",
        }),
      });
      const body = await res.json();
      return result(id, "Unregistered voter_id", 404, res, body);
    }

    case "quantum_hndl":
      return {
        attack_id: id,
        title: "Harvest now, decrypt later",
        blocked: true,
        educational_only: true,
        detail:
          "Classical RSA/ECDH ballots recorded today could be decrypted by a future CRQC. " +
          "This MVP encrypts with Kyber512 (ML-KEM). Signatures use Dilithium2 (ML-DSA). " +
          "No live API call — migration path for long-retention election data.",
        mitigation:
          "NIST-standardized lattice KEM + signatures; hybrid transition in production.",
      };

    default:
      throw new Error(`Unknown attack: ${id}`);
  }
}

export function formatAttackResult(r) {
  if (r.educational_only) {
    return `✓ ${r.title}\n\n${r.detail}\n\nMitigation: ${r.mitigation}`;
  }
  const icon = r.blocked ? "✓ BLOCKED (defence worked)" : "✗ Unexpected (investigate)";
  const lines = [
    `${icon} — ${r.title}`,
    `Server said no (expected code ${r.expected_status}, got ${r.actual_status})`,
  ];
  if (r.plain_summary) lines.push(`Plain English: ${r.plain_summary}`);
  if (r.detail) lines.push(`Technical detail: ${typeof r.detail === "string" ? r.detail : JSON.stringify(r.detail)}`);
  if (r.hint) lines.push(`Hint: ${r.hint}`);
  if (r.first_vote) lines.push(`First vote succeeded: ${r.first_vote}`);
  return lines.join("\n");
}
