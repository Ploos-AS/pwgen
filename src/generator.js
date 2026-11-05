/**
 * Cryptographically secure unbiased sampling from [0, max).
 * Uses rejection sampling to avoid modulo bias.
 */
export function secureIndex(max) {
  if (!Number.isSafeInteger(max) || max < 1 || max > 0x100000000) {
    throw new RangeError("Invalid random bound");
  }
  const range = 0x100000000;
  const limit = Math.floor(range / max) * max;
  const buffer = new Uint32Array(1);
  let n;
  do {
    globalThis.crypto.getRandomValues(buffer);
    n = buffer[0];
  } while (n >= limit);
  return n % max;
}

export const SETS = Object.freeze({
  lower: "abcdefghijkmnopqrstuvwxyz",
  upper: "ABCDEFGHJKLMNPQRSTUVWXYZ",
  digits: "23456789",
  symbols: "!@#$%^&*()-_=+[]{}:,.?"
});

/** Require at least one character from each enabled character set. */
export function generatePassword({length = 20, lower = true, upper = true, digits = true, symbols = true} = {}) {
  if (!Number.isSafeInteger(length) || length < 12 || length > 128) {
    throw new RangeError("Password length must be 12–128");
  }
  const enabled = Object.entries({lower, upper, digits, symbols})
    .filter(([, active]) => active)
    .map(([name]) => SETS[name]);
  if (!enabled.length) throw new Error("Choose at least one character set");
  const chars = enabled.map((set) => set[secureIndex(set.length)]);
  const alphabet = enabled.join("");
  while (chars.length < length) chars.push(alphabet[secureIndex(alphabet.length)]);
  for (let i = chars.length - 1; i > 0; i--) {
    const j = secureIndex(i + 1);
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }
  return chars.join("");
}
