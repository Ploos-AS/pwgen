"""Validate PWGen release archives before extraction.

This module is intentionally independent of the production deployment entrypoint.
"""
from pathlib import PurePosixPath
import tarfile

MAX_ARCHIVE = 10 * 1024 * 1024
MAX_UNPACKED = 20 * 1024 * 1024
MAX_FILE = 5 * 1024 * 1024
MAX_FILES = 100
ALLOWED_EXTENSIONS = frozenset({
    ".html", ".css", ".js", ".json", ".svg", ".png",
    ".jpg", ".jpeg", ".webp", ".ico", ".txt", ".webmanifest",
})


class InvalidRelease(ValueError):
    pass


def validate_members(members):
    """Return validated regular-file members; reject ambiguous paths and metadata."""
    if not 1 <= len(members) <= MAX_FILES:
        raise InvalidRelease("invalid number of archive entries")
    seen = set()
    unpacked = 0
    validated = []
    for member in members:
        name = member.name
        path = PurePosixPath(name)
        parts = name.split("/")
        if (
            not member.isfile()
            or not name
            or name.startswith("/")
            or "\\" in name
            or any(part in ("", ".", "..") for part in parts)
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in name)
        ):
            raise InvalidRelease("unsafe archive entry")
        if name in seen:
            raise InvalidRelease("duplicate archive entry")
        seen.add(name)
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise InvalidRelease("disallowed file type")
        if member.size < 0 or member.size > MAX_FILE:
            raise InvalidRelease("individual file too large")
        unpacked += member.size
        if unpacked > MAX_UNPACKED:
            raise InvalidRelease("unpacked archive too large")
        validated.append(member)
    if "index.html" not in seen:
        raise InvalidRelease("missing index.html")
    return validated


def validate_archive(archive):
    """Validate a seekable gzip tar file object without extracting files."""
    archive.seek(0, 2)
    size = archive.tell()
    if size > MAX_ARCHIVE:
        raise InvalidRelease("compressed archive too large")
    archive.seek(0)
    try:
        with tarfile.open(fileobj=archive, mode="r:gz") as tar:
            return [m.name for m in validate_members(tar.getmembers())]
    except (tarfile.TarError, EOFError, OSError) as exc:
        raise InvalidRelease("invalid archive") from exc
