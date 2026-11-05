"""PWGen publisher orchestration (not yet a production service).

All paths must be fixed by root-owned configuration, not derived from queue
metadata. The caller must establish root-controlled parent directories and
execute this module only from a root-owned code installation.
"""
import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

from deploy.archive_validator import InvalidRelease
from deploy.private_release import stage_private_release
from deploy.publisher import promote_and_activate
from deploy.queue_snapshot import READY_NAME, snapshot_queued_archive


@contextmanager
def private_lock(state_dir):
    """Use a root-private lock file, never a lock under the deploy user's tree."""
    lock_path = Path(state_dir) / "publisher.lock"
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def process_ready(queue_dir, state_dir, base, ready_name):
    """Process one ready entry under a private lock.

    A failed publication leaves the active release unchanged. The ready
    entry is deliberately not removed here: a later queue-management layer
    must decide how to quarantine failures and acknowledge successes.
    """
    queue_dir = Path(queue_dir)
    state_dir = Path(state_dir)
    base = Path(base)
    match = READY_NAME.fullmatch(ready_name)
    if match is None:
        raise InvalidRelease("invalid queue filename")
    with private_lock(state_dir):
        snapshot = None
        staging = None
        try:
            commit, snapshot = snapshot_queued_archive(queue_dir, state_dir, ready_name)
            staging = stage_private_release(snapshot, state_dir, commit)
            return promote_and_activate(staging, base, commit)
        finally:
            if staging is not None:
                import shutil
                shutil.rmtree(staging)
            if snapshot is not None:
                snapshot.unlink(missing_ok=True)
