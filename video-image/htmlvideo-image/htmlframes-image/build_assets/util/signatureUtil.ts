import { createHmac } from "node:crypto";
import { config } from "../config/config.js";

function hmacHex(text: string, timestamp: number, secretKey: string): string {
  const signString = `text=${Buffer.from(text, "utf8").toString("hex")}&timestamp=${timestamp}`;
  return createHmac("sha256", secretKey).update(signString).digest("hex");
}

/** Generate signature for text content (generic secret). */
export function generateSignature(text: string, timestamp: number): string {
  return hmacHex(text, timestamp, config.signature.secretKey);
}

/** Generate signature for sound / TTS requests. */
export function generateSoundSignature(text: string, timestamp: number): string {
  return hmacHex(text, timestamp, config.signature.soundSecretKey);
}

/** Generate signature for upload requests. */
export function generateUploadSignature(text: string, timestamp: number): string {
  return hmacHex(text, timestamp, config.signature.uploadSecretKey);
}

/** Generate signature for cover requests. */
export function generateCoverSignature(text: string, timestamp: number): string {
  return hmacHex(text, timestamp, config.signature.coverSecretKey);
}

/**
 * Hook-style wrapper kept for callers that expect useSignature().
 */
export const useSignature = () => ({
  generateSignature,
  generateSoundSignature,
  generateUploadSignature,
  generateCoverSignature,
});
