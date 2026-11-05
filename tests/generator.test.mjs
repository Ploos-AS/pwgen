import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
globalThis.crypto = webcrypto;
const {generatePassword, SETS, secureIndex} = await import("../src/generator.js");
const {initialLocale, translate} = await import("../src/i18n.js");

test("secureIndex produces values within the requested bound", () => {
  for (let i = 0; i < 1000; i++) {
    const value = secureIndex(27);
    assert.ok(value >= 0 && value < 27);
  }
});
test("password defaults to 20 characters and uses each enabled group", () => {
  const password = generatePassword();
  assert.equal(password.length, 20);
  for (const set of Object.values(SETS)) {
    assert.ok([...password].some((char) => set.includes(char)));
  }
});
test("single-character-set password only contains allowed characters", () => {
  const password = generatePassword({length: 128, lower: false, upper: false, digits: true, symbols: false});
  assert.equal(password.length, 128);
  assert.ok([...password].every((char) => SETS.digits.includes(char)));
});
test("invalid inputs fail", () => {
  assert.throws(() => generatePassword({length: 11}), RangeError);
  assert.throws(() => generatePassword({lower: false, upper: false, digits: false, symbols: false}));
  assert.throws(() => secureIndex(0), RangeError);
});
test("localized defaults by domain", () => {
  assert.equal(initialLocale("www.pwgen.be"), "nl");
  assert.equal(initialLocale("pwgen.es"), "es");
  assert.equal(initialLocale("pwgen.uk"), "en-GB");
  assert.equal(initialLocale("pwgen.pl"), "pl");
  assert.equal(translate("en-GB", "generate"), "Generate password");
});
