# PWGen systemd publisher (design drafts)

**Not production-ready. Do not copy these units to /etc/systemd/system or enable them.**

The service and timer are version-controlled drafts. The service deliberately
references a nonexistent root-owned executable; the current Python coordinator
is **not** a production entrypoint.

Before any installation:
1. Fix the PWGen base-directory ownership: currently `pwgen-deploy` owns
   the base and can rename/replace child entries even if `releases` becomes
   root-owned. Preserve explicit upload and Caddy traversal rights.
2. Install reviewed publisher Python code under a root-owned, non-writable
   import path; never import from the deploy checkout.
3. Implement queue acknowledgement/quarantine and avoid reprocessing a ready
   entry forever. Define bounded queue storage and disk quotas.
4. Ensure the queue snapshot is taken through descriptor-relative opens
   and that the private copy is validated. Review remaining symlink/race
   cases and the promotion module before root execution.
5. Implement the fixed entrypoint with no shell, no attacker-controlled
   command arguments, and a bounded scan. Test concurrent writes and failures.
6. Review the sandbox with `systemd-analyze security`, and check whether
   `ReadWritePaths` can be narrowed to specific root-controlled directories.
7. Confirm test workflows pass and conduct an isolated non-root integration
   run. Only then consider a controlled host migration.

The timer is intended to be root-owned and only enabled after all gates pass.
