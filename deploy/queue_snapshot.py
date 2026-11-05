"""Copy untrusted queued archives into root-private storage before validation.

The queue is writable by pwgen-deploy. Never validate the queue file directly.
This module does not activate releases or grant privileges.
"""
import os
import re
import stat
import tempfile
from pathlib import Path

from deploy.archive_validator import InvalidRelease, MAX_ARCHIVE

READY_NAME = re.compile(r"([0-9a-f]{40})\.tar\.gz\Z")
CHUNK = 64 * 1024


def snapshot_queued_archive(queue_dir, private_dir, ready_name):
    """Return (commit, private_path) for a bounded, private archive snapshot.

    Caller must remove private_path after processing, including on failure.
    private_dir must be root-owned, mode 0700, and not writable by deploy.
    This function does not itself establish the directory trust boundary.
    """
    match = READY_NAME.fullmatch(ready_name)
    if not match:
        raise InvalidRelease("invalid queue filename")
    queue_dir = Path(queue_dir)
    private_dir = Path(private_dir)

    directory_fd = os.open(queue_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        source_fd = os.open(
            ready_name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory_fd,
        )
    finally:
        os.close(directory_fd)

    private_path = None
    try:
        source_stat = os.fstat(source_fd)
        if not stat.S_ISREG(source_stat.st_mode) or source_stat.st_nlink != 1:
            raise InvalidRelease("queue entry must be an unlinked-to regular file")
        if source_stat.st_size > MAX_ARCHIVE:
            raise InvalidRelease("compressed archive too large")

        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".snapshot-", suffix=".tar.gz",
            dir=private_dir, delete=False,
        ) as private:
            private_path = Path(private.name)
            os.fchmod(private.fileno(), 0o600)
            total = 0
            while True:
                chunk = os.read(source_fd, CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ARCHIVE:
                    raise InvalidRelease("compressed archive too large")
                private.write(chunk)
            private.flush()
            os.fsync(private.fileno())
        return match.group(1), private_path
    except BaseException:
        if private_path is not None:
            private_path.unlink(missing_ok=True)
        raise
    finally:
        os.close(source_fd)
