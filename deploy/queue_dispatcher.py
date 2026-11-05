"""Bounded queue dispatcher for the future root-owned publisher.

A receipt prevents reprocessing an already published commit. This does not
acknowledge or delete queue entries; that requires a separately reviewed
quarantine/retention mechanism.
"""
from pathlib import Path

from deploy.coordinator import process_ready
from deploy.queue_state import discover_ready, read_receipt, write_receipt


def process_queue(queue_dir, state_dir, base, *, limit=8):
    """Process at most limit pending ready entries; stop on first failure.

    Caller must ensure all state and published directories are root-controlled.
    No untrusted path is used as a command. Failures are deliberately surfaced
    rather than permanently marked rejected without an audit trail.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 32:
        raise ValueError("limit must be between 1 and 32")
    queue_dir = Path(queue_dir)
    state_dir = Path(state_dir)
    base = Path(base)
    processed = []
    for name in discover_ready(queue_dir):
        commit = name[:40]
        receipt = read_receipt(state_dir, commit)
        if receipt is not None and receipt.get("status") == "published":
            continue
        if len(processed) >= limit:
            break
        destination = process_ready(queue_dir, state_dir, base, name)
        write_receipt(state_dir, commit, "published")
        processed.append(destination)
    return processed
