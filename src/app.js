import {generatePassword} from "./generator.js";
import {initialLocale, translate} from "./i18n.js";

const $ = (id) => document.getElementById(id);
let locale = initialLocale(location.hostname);
let mode = "simple";

const fields = {
  "language-label":"language", privacy:"privacy", heading:"heading", subheading:"subheading",
  "simple-tab":"simple", "ultimate-tab":"ultimate", "result-label":"result",
  copy:"copy", "simple-hint":"simpleHint", "length-label":"length",
  "lower-label":"lower", "upper-label":"upper", "digits-label":"digits",
  "symbols-label":"symbols", generate:"generate", "footer-privacy":"footerPrivacy",
  "source-link":"source", "ploos-link":"ploos"
};

function renderTranslations() {
  document.documentElement.lang = locale;
  document.title = "PWGen — " + translate(locale, "heading");
  $("language").value = locale;
  for (const [id, key] of Object.entries(fields)) $(id).textContent = translate(locale, key);
}

function setMode(next) {
  mode = next;
  $("simple-panel").hidden = next !== "simple";
  $("ultimate-panel").hidden = next !== "ultimate";
  for (const name of ["simple", "ultimate"]) {
    const active = name === next;
    const button = $(name + "-tab");
    button.classList.toggle("selected", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  }
  newPassword();
}

function options() {
  if (mode === "simple") return {length: 20};
  return {
    length: Number($("length").value),
    lower: $("lower").checked, upper: $("upper").checked,
    digits: $("digits").checked, symbols: $("symbols").checked
  };
}

function newPassword() {
  $("feedback").textContent = "";
  try {
    $("result").value = generatePassword(options());
  } catch {
    $("result").value = "";
    $("feedback").textContent = translate(locale, "choose");
  }
}

$("language").addEventListener("change", (event) => {
  locale = event.target.value;
  renderTranslations();
  $("feedback").textContent = "";
});
$("simple-tab").addEventListener("click", () => setMode("simple"));
$("ultimate-tab").addEventListener("click", () => setMode("ultimate"));
$("length").addEventListener("input", () => {
  $("length-value").textContent = $("length").value;
  newPassword();
});
for (const id of ["lower", "upper", "digits", "symbols"]) $(id).addEventListener("change", newPassword);
$("generate").addEventListener("click", newPassword);
$("copy").addEventListener("click", async () => {
  if (!$("result").value) return;
  try {
    await navigator.clipboard.writeText($("result").value);
    $("feedback").textContent = translate(locale, "copied");
  } catch {
    $("result").focus();
    $("result").select();
    $("feedback").textContent = translate(locale, "copyError");
  }
});

renderTranslations();
newPassword();
