# PWGen queue lifecycle — security review and release gate

**Status: design/review, not a production-ready queue processor.**

## Current behavior

- The SSH deploy account can write to `incoming/queue`.
- `queue_snapshot.py` opens a named entry without following symlinks and
  copies a bounded snapshot to private storage.
- `queue_dispatcher.py` processes at most eight new entries per run by
  default and skips commits with a private `published` receipt.
- The dispatcher currently leaves the original queue entry in place.
  It does not quarantine failures, remove successful uploads, or cap all
  unrecognized/temporary files in the queue.

## Blocking issues before root execution

1. **Untrusted queue parent:** The PWGen base directory is presently writable
   by `pwgen-deploy`. A root publisher must not traverse attacker-replaceable
   parent components. Migrate ownership and review ACLs before activation.
2. **Mutable source:** An attacker can modify a queue file while it is copied.
   The private copy prevents subsequent mutation, but does not establish that
   it matches a completed, authenticated upload. The restricted SSH receiver
   must publish completed files with an atomic rename, and the publisher must
   validate the snapshot fully.
3. **Receipt crash window:** Promotion currently happens before writing the
   `published` receipt. A crash between those operations leaves an installed
   release without a receipt; retry then fails with 'release already exists'.
   Design idempotent recovery from trusted, root-owned release state.
4. **No quarantine/acknowledgement:** Invalid entries are retried forever and
   successful entries remain in the queue. Introduce bounded quarantine,
   audit records, retention and cleanup. Never follow untrusted symlinks or
   let queue filenames become shell/systemd commands.
5. **Queue exhaustion:** `discover_ready` limits only matching ready entries,
   not partial or maliciously named files. Enforce filesystem quotas or
   bounded upload capacity at the SSH receiver and storage layer.
6. **Trusted code boundary:** Root must execute only root-owned code and fixed
   systemd units. No Python imports from deploy-writable directories.
7. **Race and link audit:** Review descriptor-relative opens for the queue and
   promotion target, directory ownership, hardlinks, symlink replacement,
   and rollback before enabling the privileged service.
8. **Locking:** Discovery currently occurs outside the private coordinator
   lock; per-item publication uses that lock. A full queue runner needs one
   explicit concurrency policy, including receipts and cleanup.

## Proposed state machine

`uploading -> ready -> privately snapshotted -> validated -> published -> acknowledged`

Failures move to `rejected/quarantined` with a bounded, root-private audit
record. A restart must reconcile private receipts and existing root-owned
releases before processing new queue entries. A successful publication must
not depend on the continued presence of an attacker-writable source file.

## Acceptance tests required

- Successful publication and restart with no duplicate work.
- Crash after release promotion but before receipt, followed by recovery.
- Invalid archive quarantine with no repeated activation attempts.
- Queue entry replaced during snapshot, and upload interrupted before rename.
- Symlink, hardlink, FIFO, and directory attacks.
- Disk exhaustion and oversized partial uploads.
- Multiple queue entries, concurrent timer runs, and rollback.
- Caddy read access preserved; deploy account cannot replace root-owned
  `releases`, `app`, or neighboring customer directories.

**Do not install/enable the systemd draft or SSH deploy key until these gates
are implemented and verified.**
