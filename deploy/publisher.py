"""Promote private PWGen staging to a root-controlled release and activate it.

PRIMITIVE ONLY: caller must hold a root-private deployment lock and ensure
all relevant parent directories are root-controlled, non-replaceable, and
not writable by the deploy account. Do not run this on Bragi yet.
"""
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path

from deploy.release_manager import COMMIT, ReleaseError


def _check_tree(staging):
    """Require a private directory containing only regular files/directories."""
    if staging.is_symlink() or not staging.is_dir():
        raise ReleaseError("invalid staging directory")
    if not (staging / "index.html").is_file() or (staging / "index.html").is_symlink():
        raise ReleaseError("missing regular index.html")
    for root, dirs, files in os.walk(staging, followlinks=False):
        for name in dirs + files:
            path = Path(root) / name
            mode = path.lstat().st_mode
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ReleaseError("unexpected staging entry")
            if stat.S_ISREG(mode) and path.stat().st_nlink != 1:
                raise ReleaseError("hardlinked staging file")


def promote_and_activate(staging, base, commit):
    """Install a fresh release and atomically switch app.

    staging and base must be in trusted root-owned trees. The function is
    not safe against another privileged process racing to mutate those trees.
    """
    if not COMMIT.fullmatch(commit):
        raise ReleaseError("invalid commit")
    staging = Path(staging)
    base = Path(base)
    releases = base / "releases"
    app = base / "app"
    if releases.is_symlink() or not releases.is_dir():
        raise ReleaseError("invalid releases directory")
    if app.is_symlink():
        existing = app.resolve(strict=False)
        if not existing.is_relative_to(releases.resolve()):
            raise ReleaseError("app points outside releases")
    elif app.exists():
        raise ReleaseError("app must be a symlink")

    destination = releases / commit
    if destination.exists() or destination.is_symlink():
        raise ReleaseError("release already exists")
    _check_tree(staging)

    # Build in the destination filesystem, then rename to avoid partial releases.
    temporary = Path(tempfile.mkdtemp(prefix=".promote-", dir=releases))
    installed = False
    try:
        for root, dirs, files in os.walk(staging, followlinks=False):
            relative = Path(root).relative_to(staging)
            target_dir = temporary / relative
            target_dir.mkdir(parents=True, exist_ok=True)
            for dirname in dirs:
                (target_dir / dirname).mkdir(exist_ok=True)
            for filename in files:
                source = Path(root) / filename
                target = target_dir / filename
                with source.open("rb") as input_file, target.open("xb") as output:
                    shutil.copyfileobj(input_file, output, length=65536)
                target.chmod(0o644)
        for root, dirs, files in os.walk(temporary, topdown=False):
            for dirname in dirs:
                (Path(root) / dirname).chmod(0o755)
        temporary.chmod(0o755)
        os.rename(temporary, destination)
        installed = True

        next_link = base / (".app-next-" + commit)
        if next_link.exists() or next_link.is_symlink():
            raise ReleaseError("temporary app link exists")
        try:
            next_link.symlink_to(Path("releases") / commit, target_is_directory=True)
            os.replace(next_link, app)
        finally:
            if next_link.is_symlink():
                next_link.unlink()
        return destination
    finally:
        if not installed and temporary.exists():
            shutil.rmtree(temporary)
