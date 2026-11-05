# PWGen deployment v2 — privilege boundary

Status: design proposal; NOT installed on Bragi. Existing SSH entrypoint remains a prototype.

## Threat model

The `pwgen-deploy` account and anything in its writable directories are untrusted.
It must never control root execution, active symlink, release contents, or other
customers' files. GitHub's SSH key is not enabled until the replacement is tested.

## Ownership and paths

- `incoming/queue/`: `pwgen-deploy`, mode 0700; **untrusted input only**.
- `/var/lib/ploos-deploy/pwgen/`: root, mode 0700; lock and private staging.
- `releases/`: root-owned, not writable by deploy user.
- `app`: root-managed symlink, points only to a verified release.
- Caddy: read/execute access to published files only, never write.

**Important:** The existing PWGen base directory is owned and writable by
`pwgen-deploy`. Before enabling any root publisher, the base directory AND
every ancestor traversed by the publisher must be root-controlled (or otherwise
proved non-replaceable), with separate explicit ACLs for deploy upload and Caddy
read. A root-owned `releases` directory alone is insufficient: a writable
parent allows renaming or replacing it. Recheck all symlink and ACL boundaries.

## Proposed flow

1. Restricted SSH command accepts only a 40-character lowercase commit SHA and
   a bounded archive stream. It writes a uniquely named temporary file in the
   queue and atomically renames it to a ready name **after** closing the file.
   The SSH process has no authority to publish or activate.
2. A fixed, root-owned systemd service (triggered by a root-owned timer or
   trusted root-owned watcher) scans for ready entries. No untrusted file
   content or filename becomes a shell command or systemd unit argument.
3. Publisher opens each ready file without following symlinks and copies bytes
   into a root-private temporary file with a size cap. Validate the **private
   snapshot**, not the attacker-writable original. Never use `tar.extractall`.
4. Publisher validates the commit identifier, archive paths, file types, counts,
   sizes, and extracted content. Build a private staging tree and install a
   complete root-owned release with read-only files. Reject existing releases;
   never overwrite an existing commit.
5. Publisher atomically updates the `app` symlink only after verifying that
   the destination is inside the expected root-owned release tree. The update
   must not follow attacker-controlled symlinks. Record result in root-private
   state; retain prior releases for rollback.
6. On failure, leave the active release unchanged. Apply bounded queue size,
   bounded processing time, disk-space checks, logs, and retention controls.

## Privilege and service constraints

- No `sudo` for `pwgen-deploy`; no dynamic `systemd-run` command from SSH.
- The systemd unit and executable are root-owned and not writable by deploy.
- Use `ProtectSystem=strict`, `NoNewPrivileges=yes`, `PrivateTmp=yes`,
  `ProtectHome=yes`, `RestrictAddressFamilies=AF_UNIX`, and narrow
  `ReadWritePaths=` only after verifying they work with Caddy and the host.
- A root publisher must not import Python modules from a deploy-writable path.
  Install reviewed code in a root-owned directory and run via a fixed interpreter.
- Keep deploy and publisher locking in root-private state; never trust a lock
  file under a deploy-writable directory for privileged coordination.

## Migration / acceptance checklist

1. Add tests for hostile queue entries, symlinks, partial writes, archive
   replacement races, duplicate commits, bad tar entries, rollback, and failed
   publication; run on CI.
2. Install root-owned executable and fixed systemd unit; review with
   `systemd-analyze security` and verify filesystem permissions.
3. Back up existing test releases; migrate base ownership and ACLs while SSH
   deploy access remains disabled. Confirm Caddy still reads the active site.
4. Test a valid release, invalid release, rollback, and isolation against
   another customer **without** GitHub SSH credentials.
5. Only then add the restricted deploy public key, configure GitHub Secrets,
   and enable the production workflow on the protected default branch.

This document intentionally does not grant privileges or change the host.
