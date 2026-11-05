export const messages = {
  en: {
    language:"Language", privacy:"Generated on your device • Never sent to a server",
    heading:"Create a secure password", subheading:"Free, private password generation using cryptographically secure randomness.",
    simple:"Simple", ultimate:"Ultimate", result:"Generated password", copy:"Copy", copied:"Copied!",
    simpleHint:"One click generates a strong 20-character password.",
    length:"Length", lower:"Lowercase", upper:"Uppercase", digits:"Numbers", symbols:"Symbols",
    generate:"Generate password", choose:"Select at least one character type.",
    copyError:"Copy failed. Please select and copy the password manually.",
    footerPrivacy:"No analytics. No password storage. No third-party scripts.",
    source:"View source on GitHub", ploos:"A service by Ploos AS"
  },
  "en-GB": {},
  de: {
    language:"Sprache", privacy:"Auf deinem Gerät erstellt • Niemals an einen Server gesendet",
    heading:"Ein sicheres Passwort erstellen", subheading:"Kostenlose, private Passwortgenerierung mit kryptografisch sicherem Zufall.",
    simple:"Einfach", ultimate:"Erweitert", result:"Generiertes Passwort", copy:"Kopieren", copied:"Kopiert!",
    simpleHint:"Mit einem Klick ein starkes Passwort mit 20 Zeichen erstellen.",
    length:"Länge", lower:"Kleinbuchstaben", upper:"Großbuchstaben", digits:"Zahlen", symbols:"Sonderzeichen",
    generate:"Passwort generieren", choose:"Wähle mindestens einen Zeichentyp aus.",
    copyError:"Kopieren fehlgeschlagen. Bitte wähle das Passwort aus und kopiere es manuell.",
    footerPrivacy:"Keine Analyse-Tools. Keine Passwortspeicherung. Keine Skripte von Drittanbietern.",
    source:"Quellcode auf GitHub ansehen", ploos:"Ein Dienst von Ploos AS"
  },

  nl: {
    language:"Taal", privacy:"Op je apparaat gegenereerd • Niets naar een server verzonden",
    heading:"Maak een veilig wachtwoord", subheading:"Gratis, privé en met cryptografisch veilige willekeurige getallen.",
    simple:"Eenvoudig", ultimate:"Uitgebreid", result:"Gegenereerd wachtwoord", copy:"Kopiëren", copied:"Gekopieerd!",
    simpleHint:"Met één klik een sterk wachtwoord van 20 tekens.",
    length:"Lengte", lower:"Kleine letters", upper:"Hoofdletters", digits:"Cijfers", symbols:"Symbolen",
    generate:"Genereer wachtwoord", choose:"Selecteer minstens één tekentype.",
    copyError:"Kopiëren mislukt. Selecteer en kopieer het wachtwoord handmatig.",
    footerPrivacy:"Geen analytics. Geen wachtwoordopslag. Geen scripts van derden.",
    source:"Bekijk de broncode op GitHub", ploos:"Een dienst van Ploos AS"
  },
  fr: {
    language:"Langue", privacy:"Généré sur votre appareil • Rien n'est envoyé au serveur",
    heading:"Créez un mot de passe sûr", subheading:"Génération gratuite et privée avec un aléa cryptographiquement sûr.",
    simple:"Simple", ultimate:"Avancé", result:"Mot de passe généré", copy:"Copier", copied:"Copié !",
    simpleHint:"Un mot de passe solide de 20 caractères en un clic.",
    length:"Longueur", lower:"Minuscules", upper:"Majuscules", digits:"Chiffres", symbols:"Symboles",
    generate:"Générer un mot de passe", choose:"Sélectionnez au moins un type de caractère.",
    copyError:"Copie impossible. Sélectionnez et copiez le mot de passe manuellement.",
    footerPrivacy:"Sans analyse d'audience. Aucun stockage de mots de passe. Aucun script tiers.",
    source:"Code source sur GitHub", ploos:"Un service de Ploos AS"
  },
  es: {
    language:"Idioma", privacy:"Generado en tu dispositivo • Nunca enviado a un servidor",
    heading:"Crea una contraseña segura", subheading:"Generación gratuita y privada con aleatoriedad criptográficamente segura.",
    simple:"Sencillo", ultimate:"Avanzado", result:"Contraseña generada", copy:"Copiar", copied:"¡Copiado!",
    simpleHint:"Una contraseña segura de 20 caracteres con un clic.",
    length:"Longitud", lower:"Minúsculas", upper:"Mayúsculas", digits:"Números", symbols:"Símbolos",
    generate:"Generar contraseña", choose:"Selecciona al menos un tipo de carácter.",
    copyError:"No se pudo copiar. Selecciona y copia la contraseña manualmente.",
    footerPrivacy:"Sin analíticas. Sin almacenar contraseñas. Sin scripts externos.",
    source:"Código fuente en GitHub", ploos:"Un servicio de Ploos AS"
  },
  pl: {
    language:"Język", privacy:"Generowane na Twoim urządzeniu • Bez wysyłania na serwer",
    heading:"Utwórz bezpieczne hasło", subheading:"Bezpłatne, prywatne generowanie z kryptograficznie bezpieczną losowością.",
    simple:"Prosty", ultimate:"Zaawansowany", result:"Wygenerowane hasło", copy:"Kopiuj", copied:"Skopiowano!",
    simpleHint:"Silne 20-znakowe hasło jednym kliknięciem.",
    length:"Długość", lower:"Małe litery", upper:"Wielkie litery", digits:"Cyfry", symbols:"Symbole",
    generate:"Generuj hasło", choose:"Wybierz co najmniej jeden zestaw znaków.",
    copyError:"Nie udało się skopiować. Zaznacz i skopiuj hasło ręcznie.",
    footerPrivacy:"Bez analityki. Bez zapisywania haseł. Bez skryptów firm trzecich.",
    source:"Kod źródłowy na GitHubie", ploos:"Usługa Ploos AS"
  }
};

export const defaultLocales = Object.freeze({
  "pwgen.be": "nl",
  "pwgen.eu": "en",
  "pwgen.es": "es",
  "pwgen.uk": "en-GB",
  "pwgen.pl": "pl"
});

export function initialLocale(hostname) {
  return defaultLocales[hostname.toLowerCase().replace(/^www\./, "")] ?? "en";
}

export function translate(locale, key) {
  return messages[locale]?.[key] ?? messages.en[key] ?? key;
}
