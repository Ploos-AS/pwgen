"""Recover missing publication receipts from trusted, active releases.

Only safe after root ownership of base, releases, app and state has been
verified. This is a primitive, not an independently runnable root service.
Caller MUST hold the root-private publisher lock.
"""
from pathlib import Path

from deploy.release_manager import COMMIT, ReleaseError
from deploy.queue_state import read_receipt, write_receipt


def recover_active_receipt(base, state_dir, commit):
    """Restore a missing receipt only if this exact release is active.

    Return True when a receipt was recovered, False when already present or
    no matching installed release exists. Reject inconsistent filesystem
    state rather than guessing which version should be active.
    """
    if not COMMIT.fullmatch(commit):
        raise ReleaseError("invalid commit")
    base = Path(base)
    releases = base / "releases"
    app = base / "app"
    destination = releases / commit

    receipt = read_receipt(state_dir, commit)
    if receipt is not None:
        if receipt != {"commit": commit, "status": "published"}:
            raise ReleaseError("unexpected existing receipt")
        return False

    if releases.is_symlink() or not releases.is_dir():
        raise ReleaseError("invalid releases directory")
    if destination.is_symlink():
        raise ReleaseError("release is a symlink")
    if not destination.exists():
        return False
    if not destination.is_dir():
        raise ReleaseError("release is not a directory")
    index = destination / "index.html"
    if index.is_symlink() or not index.is_file():
        raise ReleaseError("invalid installed release")
    if not app.is_symlink():
        raise ReleaseError("existing release is not active")
    if app.readlink() != Path("releases") / commit:
        raise ReleaseError("existing release is not active")

    write_receipt(state_dir, commit, "published")
    return True
