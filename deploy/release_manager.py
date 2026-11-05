"""PWGen release activation primitives.

No privileged operations. The caller must provide an isolated, dedicated base
directory; production integration is deliberately separate.
"""
import fcntl
import os
import re
from contextlib import contextmanager
from pathlib import Path

COMMIT = re.compile(r"[0-9a-f]{40}\Z")


class ReleaseError(ValueError):
    pass


@contextmanager
def deployment_lock(base):
    """Serialize uploads and activations for this deployment root."""
    base = Path(base)
    with (base / ".deploy.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def activate_release(base, commit):
    """Atomically switch app symlink to an existing validated release.

    Caller holds deployment_lock and has verified release contents on upload.
    Rejects a non-symlink app path instead of removing any directory.
    """
    if not COMMIT.fullmatch(commit):
        raise ReleaseError("invalid commit")
    base = Path(base)
    releases = base / "releases"
    destination = releases / commit
    if destination.is_symlink() or not destination.is_dir():
        raise ReleaseError("release missing or is a symlink")
    if (destination / "index.html").is_symlink() or not (destination / "index.html").is_file():
        raise ReleaseError("invalid release")
    app = base / "app"
    if app.exists() and not app.is_symlink():
        raise ReleaseError("app is not a symlink")
    if app.is_symlink() and not app.resolve(strict=False).is_relative_to(releases.resolve()):
        raise ReleaseError("app points outside releases")
    temp = base / f".app-next-{os.getpid()}"
    if temp.exists() or temp.is_symlink():
        raise ReleaseError("temporary link already exists")
    try:
        temp.symlink_to(Path("releases") / commit, target_is_directory=True)
        os.replace(temp, app)
    finally:
        if temp.is_symlink():
            temp.unlink()
    return commit
