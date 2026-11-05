# PWGen

A minimal, privacy-first password generator operated by Ploos AS.

## Features

- **Simple**: secure 20-character password in one click.
- **Ultimate**: 12–128 characters and selectable character groups.
- Uses the browser's Web Crypto API and unbiased rejection sampling.
- No backend, third-party JavaScript, trackers, fonts, cookies, or local storage.
- No generated passwords sent over the network.
- One static app for `pwgen.be`, `pwgen.eu`, `pwgen.es`, `pwgen.uk`, and (once activated) `pwgen.pl`.
- Locale defaults by hostname; selectable language, including French for Belgium.
- Discreet footer links to the [source code](https://github.com/Ploos-AS/pwgen) and [Ploos AS](https://ploos.no/).

## Development

Requires Node.js 20+ for tests; Node.js is **not** required on the production webserver.

```sh
npm test
python3 -m http.server 8000
```

Open `http://localhost:8000` in a browser for local review.

## Deployment

Publish `index.html`, `styles.css`, and `src/` as static files. The provided `Caddyfile.example` shows a hardened configuration for Bragi. Validate the site, TLS, and DNS before cutover. Only add `pwgen.pl` when it becomes active.

If the static webroot is served by Caddy on Bragi, grant the `caddy` account read/traverse permission only for this customer's subtree (and traverse permission on the parent), as with M68K.

## Privacy and security

Generated passwords are handled in browser memory. Clipboard copying happens only when the user presses Copy. The application does not set cookies, write to storage, call an API, or load remote JavaScript. A self-hosted static site has ordinary webserver access logs unless the operator disables or minimizes them; those logs may contain visitor IP addresses, but must **never** contain generated passwords.

The project avoids third-party assets and suggests security headers, including a restrictive CSP. Review, test and audit before calling the service production-ready. Hostname-based language selection is not authentication or security-sensitive.

## Old installations

Legacy PWGen directories on Odin are **not** a source for the new implementation. Archive them separately, verify the off-server copies, then retire them only after the new service is verified. Do not store backups, old secrets, or visitor data in this public repository.

## Project status

Initial implementation on a feature branch; review and merge before production deployment.
