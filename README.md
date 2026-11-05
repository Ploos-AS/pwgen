# PWGen

**A free, privacy-first password generator.** Create strong passwords directly in your browser — without accounts, tracking or sending passwords to a server.

**Try it:** [pwgen.eu](https://pwgen.eu) · [pwgen.es](https://pwgen.es) · [pwgen.uk](https://pwgen.uk)

> **Privacy by design:** Passwords are generated locally using the browser's Web Crypto API (`crypto.getRandomValues`). The application has no password-generation backend.

## Features

- **Simple mode:** Generate a strong 20-character password with one click.
- **Ultimate mode:** Choose a length from 12 to 128 characters and select lowercase, uppercase, numbers and symbols.
- **Cryptographically secure randomness:** Web Crypto with rejection sampling to avoid modulo bias.
- **Private by default:** No analytics, cookies, local storage, external scripts or password uploads.
- **Copy on demand:** Passwords are copied to the clipboard only when requested.
- **Accessible, responsive interface:** Works on desktop and mobile.
- **Multiple languages:** English, British English, German, Dutch, French, Spanish and Polish. German is included in the current development branch and will be available after deployment.

## Domains and languages

PWGen runs from **one codebase**. Each domain has its own default language, and visitors can choose another language in the interface.

| Domain | Default language | Availability |
| --- | --- | --- |
| [pwgen.eu](https://pwgen.eu) | English | Live |
| [pwgen.es](https://pwgen.es) | Spanish | Live |
| [pwgen.uk](https://pwgen.uk) | British English | Live |
| pwgen.be | Dutch; French selectable | Awaiting DNS |
| pwgen.pl | Polish | Awaiting DNS |

Language selection is based on the hostname and the visitor's explicit choice. It does not require tracking or browser storage.

## How it works

The browser creates random values using `crypto.getRandomValues`. PWGen uses these values to select characters for the password locally. Generated passwords are never submitted to a server. The site itself is served as static HTML, CSS and JavaScript.

**Security note:** Clipboard contents may be accessible to other applications or clipboard-history tools on your device. Handle generated passwords as sensitive information.

## Run locally

No build step or backend is required. Use a local web server because the application uses JavaScript modules.

```sh
git clone https://github.com/Ploos-AS/pwgen.git
cd pwgen
python3 -m http.server 8000
```

Open `http://localhost:8000`. Node.js 20+ is needed only to run the JavaScript tests:

```sh
npm test
```

The repository also includes deployment security tests:

```sh
python3 -m unittest discover -s tests/deploy -v
```

## Deployment

PWGen is hosted as static files behind Caddy, with HTTPS and a restricted SSH deployment account. GitHub Actions runs tests before packaging and uploading an immutable release, then atomically activates it. Rollback to a previous release is supported.

Production deployment is currently **manual** via the `Deploy PWGen to Bragi` workflow on `main`. The workflow uses the following GitHub Actions settings:

| Type | Name |
| --- | --- |
| Secret | `DEPLOY_SSH_KEY` |
| Secret | `DEPLOY_KNOWN_HOSTS` |
| Variable | `DEPLOY_HOST` |
| Environment | `pwgen-production` |

Never commit private keys, credentials or server-specific secrets. The production Caddy configuration is managed on the host; `Caddyfile.example` is an example, not an exact snapshot of the live configuration.

## Privacy

PWGen does not store generated passwords, use cookies or load third-party scripts. Ordinary web-server access logs may still contain metadata such as IP addresses and requested paths, depending on hosting configuration; **passwords are not part of those requests**.

The project is designed for transparency and independent inspection. You can review the generator in [`src/generator.js`](src/generator.js) and the interface translations in [`src/i18n.js`](src/i18n.js).

## Project structure

```text
index.html              User interface
styles.css              Styling
src/generator.js        Password generation
src/i18n.js             Translations and domain defaults
src/app.js              Browser interactions
tests/                  Automated tests
deploy/                 Restricted deployment implementation
.github/workflows/      CI and manual production deployment
Caddyfile.example       Example web-server configuration
```

## Contributing and security

Bug reports, accessibility feedback and translation corrections are welcome through [GitHub Issues](https://github.com/Ploos-AS/pwgen/issues). Please **do not post passwords, private keys or sensitive information** in public issues. For a potentially exploitable security vulnerability, contact the maintainers privately rather than publishing exploit details.

## Maintainer

Developed and operated by **[Ploos AS](https://ploos.no/)**.

PWGen is publicly readable on GitHub. No open-source license is asserted here; reuse rights depend on the repository's actual license terms.
