// Served from static/vendor — CDN bundles break liboqs WASM loading.
import {
  createKyber512,
  createMLDSA44,
  createMLKEM512,
} from "/vendor/liboqs-js/src/index.js";
import sha3 from "https://cdn.jsdelivr.net/npm/js-sha3@0.9.3/+esm";

const STORAGE_KEY = "pq_voting_voter_keys";

export function canonicalJson(obj) {
  return JSON.stringify(obj, Object.keys(obj).sort());
}

export function sha3Hex(data) {
  if (typeof data === "string") {
    return sha3.sha3_256(data);
  }
  return sha3.sha3_256.array(data);
}

export function biometricHash(name, dob, aadhaar) {
  return sha3.sha3_256(`${name}|${dob}|${aadhaar}`);
}

function bytesToHex(bytes) {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function hexToBytes(hex) {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i += 1) {
    out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return out;
}

function bytesToBase64(bytes) {
  let binary = "";
  bytes.forEach((b) => {
    binary += String.fromCharCode(b);
  });
  return btoa(binary);
}

function base64ToBytes(b64) {
  const binary = atob(b64);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    out[i] = binary.charCodeAt(i);
  }
  return out;
}

export async function generateVoterKeyPair() {
  const sig = await createMLDSA44();
  try {
    const { publicKey, secretKey } = sig.generateKeyPair();
    return {
      publicKeyHex: bytesToHex(publicKey),
      secretKeyHex: bytesToHex(secretKey),
      publicKey,
      secretKey,
    };
  } finally {
    sig.destroy();
  }
}

export async function signPayload(payloadObj, secretKeyHex) {
  const sig = await createMLDSA44();
  try {
    const message = new TextEncoder().encode(canonicalJson(payloadObj));
    const secretKey = hexToBytes(secretKeyHex);
    const signature = sig.sign(message, secretKey);
    return {
      message,
      signatureB64: bytesToBase64(signature),
    };
  } finally {
    sig.destroy();
  }
}

function kemFactory(algorithm) {
  if (algorithm === "ML-KEM-512") return createMLKEM512;
  return createKyber512;
}

/** @param {string} eaPublicKeyHex @param {string} [kemAlgorithm] from /api/authorities/public-keys */
export async function encapsulateKyber(eaPublicKeyHex, kemAlgorithm = "Kyber512") {
  const createKem = kemFactory(kemAlgorithm);
  const kem = await createKem();
  try {
    const publicKey = hexToBytes(eaPublicKeyHex);
    const { ciphertext, sharedSecret } = kem.encapsulate(publicKey);
    return {
      kemCiphertextB64: bytesToBase64(ciphertext),
      sharedSecret,
      sharedSecretFingerprint: sha3.sha3_256.hex(sharedSecret),
    };
  } finally {
    kem.destroy();
  }
}

export async function encryptBallot(sharedSecret, ballotObj) {
  const key = await crypto.subtle.importKey(
    "raw",
    sharedSecret.slice(0, 32),
    { name: "AES-GCM" },
    false,
    ["encrypt"],
  );
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const plaintext = new TextEncoder().encode(canonicalJson(ballotObj));
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce },
    key,
    plaintext,
  );
  return {
    nonceB64: bytesToBase64(nonce),
    ballotCiphertextB64: bytesToBase64(new Uint8Array(ciphertext)),
  };
}

export function saveVoterKeys(voterId, keys) {
  const all = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "{}");
  all[voterId] = keys;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(all));
}

export function loadVoterKeys(voterId) {
  const all = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "{}");
  return all[voterId] || null;
}

export function saveCredential(credential) {
  sessionStorage.setItem("pq_voting_credential", JSON.stringify(credential));
}

export function loadCredential() {
  const raw = sessionStorage.getItem("pq_voting_credential");
  return raw ? JSON.parse(raw) : null;
}

/**
 * Build an encrypted + signed ballot in the browser (Phase 3 production path).
 */
export async function buildBallot({
  voterId,
  electionId,
  candidateId,
  voterSecretKeyHex,
  eaPublicKeyHex,
  kemAlgorithm = "ML-KEM-512",
}) {
  const kem = await encapsulateKyber(eaPublicKeyHex, kemAlgorithm);
  const { nonceB64, ballotCiphertextB64 } = await encryptBallot(kem.sharedSecret, {
    candidate_id: candidateId,
    election_id: electionId,
  });

  const signable = {
    ballot_ciphertext: ballotCiphertextB64,
    election_id: electionId,
    kem_ciphertext: kem.kemCiphertextB64,
    nonce: nonceB64,
    voter_id: voterId,
  };
  const { signatureB64 } = await signPayload(signable, voterSecretKeyHex);

  return {
    ballot_id: crypto.randomUUID(),
    voter_id: voterId,
    election_id: electionId,
    kem_ciphertext: kem.kemCiphertextB64,
    nonce: nonceB64,
    ballot_ciphertext: ballotCiphertextB64,
    signature: signatureB64,
    submitted_at: new Date().toISOString(),
  };
}
