// caluma.mjs — Caluma / internal genaudio TTS transport for the aiflow audio engine.
// Requires the process to be started with `node --experimental-strip-types`
// so `./signatureUtil.ts` can be imported.

import { generateSoundSignature } from "./signatureUtil.ts";
import { config } from "../config/config.js";

export function parseCalumaVoice(voiceId) {
  const raw = String(voiceId || config.tts.defaultVoice || "english|voice-lady-female");
  const [modelcat, modelname] = raw.split("|");
  if (!modelcat || !modelname) {
    throw new Error(
      `invalid caluma voice "${raw}" — expected modelcat|modelname (e.g. english|voice-lady-female)`,
    );
  }
  return { modelcat, modelname };
}

/** Unix timestamp in seconds (UTC). */
function utcTimestampSeconds() {
  return Math.floor(Date.now() / 1000);
}

export function buildGenAudioBody({ text, voiceId, tstamp = utcTimestampSeconds() }) {
  const { modelcat, modelname } = parseCalumaVoice(voiceId);
  return {
    domain: config.tts.domain,
    email: config.tts.email,
    modelcat,
    modelname,
    snature: generateSoundSignature(text, tstamp),
    subscript: config.tts.subscript,
    t: config.tts.t,
    text,
    tstamp,
    userid: config.tts.userid,
  };
}

/** POST /api/genaudio; throws on HTTP or ret !== 0. */
export async function calumaJSON(body, deps = {}) {
  const fetchImpl = deps.fetch ?? fetch;
  const url = `${config.host}${config.apiMethod}`;
  const res = await fetchImpl(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Referer: "caluma.ai",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      `Caluma POST ${config.apiMethod} → HTTP ${res.status}${detail ? `\n${detail.slice(0, 300)}` : ""}`,
    );
  }
  const payload = await res.json();
  if (payload?.ret !== 0) {
    throw new Error(
      `Caluma genaudio ret=${payload?.ret ?? "?"} msg=${payload?.msg ?? "(none)"}`,
    );
  }
  if (!payload.uri) {
    throw new Error("Caluma genaudio returned no uri");
  }
  return payload;
}

/** GET ${host}${uri} → Buffer. */
export async function downloadAudio(uri, deps = {}) {
  const fetchImpl = deps.fetch ?? fetch;
  const url = `${config.host}${uri}`;
  const res = await fetchImpl(url);
  if (!res.ok) {
    throw new Error(`Caluma audio download HTTP ${res.status}: ${url.slice(0, 120)}`);
  }
  return Buffer.from(await res.arrayBuffer());
}
