"""Bounded queue discovery and private publication receipts.

This module does not delete, rename, or trust attacker-writable queue entries.
A separate reviewed service must own acknowledgements and quarantine.
"""
import json
import os
import re
import stat
import tempfile
from pathlib import Path

from deploy.queue_snapshot import READY_NAME

MAX_READY = 32
MAX_QUEUE_BYTES = 64 * 1024 * 1024
RECEIPT_NAME = re.compile(r"[0-9a-f]{40}\.json\Z")


class QueueLimitError(ValueError):
    pass


def discover_ready(queue_dir):
    """Find bounded, regular, single-link ready entries without following links.

    This is a snapshot of names, not an authorization decision. The later
    descriptor-relative snapshot operation must revalidate each entry.
    """
    queue_dir = Path(queue_dir)
    names = []
    total = 0
    with os.scandir(queue_dir) as entries:
        for entry in entries:
            if not READY_NAME.fullmatch(entry.name):
                continue
            info = entry.stat(follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                continue
            names.append(entry.name)
            total += info.st_size
            if len(names) > MAX_READY or total > MAX_QUEUE_BYTES:
                raise QueueLimitError("ready queue exceeds processing limits")
    return sorted(names)


def read_receipt(state_dir, commit):
    """Read a trusted root-private receipt. Caller enforces directory ownership."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("invalid commit")
    path = Path(state_dir) / "receipts" / (commit + ".json")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None


def write_receipt(state_dir, commit, status):
    """Atomically persist a bounded receipt under a trusted private directory.

    Never accept untrusted status strings or call this from a deploy-writable
    code path. Caller holds the publisher's private lock.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("invalid commit")
    if status not in ("published", "rejected"):
        raise ValueError("invalid status")
    directory = Path(state_dir) / "receipts"
    directory.mkdir(mode=0o700, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".receipt-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump({"commit": commit, "status": status}, handle)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, directory / (commit + ".json"))
    finally:
        if os.path.exists(name):
            os.unlink(name)
