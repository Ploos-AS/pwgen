"""Build a validated release tree from a private, immutable archive snapshot.

This is a staging primitive, NOT a root service or production entrypoint.
The caller must provide trusted, root-controlled private and destination parents.
"""
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from deploy.archive_validator import InvalidRelease, MAX_ARCHIVE, validate_members
from deploy.release_manager import COMMIT, ReleaseError


def stage_private_release(archive_path, private_staging_root, commit):
    """Extract a validated archive into a new private staging directory.

    Returns the directory path; the caller owns its cleanup and any later
    promotion. Never pass an attacker-writable staging root or archive path.
    """
    if not COMMIT.fullmatch(commit):
        raise ReleaseError("invalid commit")
    archive_path = Path(archive_path)
    private_staging_root = Path(private_staging_root)
    if archive_path.is_symlink() or not archive_path.is_file():
        raise InvalidRelease("archive must be a regular file")
    if archive_path.stat().st_size > MAX_ARCHIVE:
        raise InvalidRelease("compressed archive too large")

    staging = Path(tempfile.mkdtemp(prefix=".release-", dir=private_staging_root))
    try:
        try:
            with tarfile.open(archive_path, mode="r:gz") as archive:
                members = validate_members(archive.getmembers())
                for member in members:
                    target = staging.joinpath(*member.name.split("/"))
                    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    source = archive.extractfile(member)
                    if source is None:
                        raise InvalidRelease("missing archive data")
                    with source, target.open("xb") as output:
                        remaining = member.size
                        while remaining:
                            chunk = source.read(min(65536, remaining))
                            if not chunk:
                                raise InvalidRelease("truncated archive member")
                            output.write(chunk)
                            remaining -= len(chunk)
                        if source.read(1):
                            raise InvalidRelease("archive member exceeds declared size")
                    target.chmod(0o644)
        except (tarfile.TarError, EOFError) as exc:
            raise InvalidRelease("invalid archive") from exc

        # Keep staging private until a separate privileged promotion step.
        return staging
    except BaseException:
        shutil.rmtree(staging)
        raise
