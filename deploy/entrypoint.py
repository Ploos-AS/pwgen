"""PWGen restricted SSH deployment entrypoint.

Runs as pwgen-deploy via sshd ForceCommand. No sudo, no shell commands.
Deployment credentials must remain disabled until host integration is reviewed.
"""
import os
import re
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

from deploy.archive_validator import InvalidRelease, MAX_ARCHIVE, validate_members
from deploy.release_manager import ReleaseError, activate_release, deployment_lock

BASE = Path("/srv/ploos-hosting/customers/pwgen")
COMMAND = re.compile(r"(upload|activate|rollback) ([0-9a-f]{40})\Z")


def receive_archive(stream):
    """Bound incoming bytes even for a stream without a Content-Length."""
    archive = tempfile.TemporaryFile()
    total = 0
    try:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE:
                raise InvalidRelease("compressed archive too large")
            archive.write(chunk)
        archive.seek(0)
        return archive
    except BaseException:
        archive.close()
        raise


def upload(base, commit, stream):
    releases = base / "releases"
    destination = releases / commit
    if destination.exists() or destination.is_symlink():
        raise ReleaseError("release already exists")

    with receive_archive(stream) as archive:
        try:
            with tarfile.open(fileobj=archive, mode="r:gz") as tar:
                members = validate_members(tar.getmembers())
                with tempfile.TemporaryDirectory(prefix=".upload-", dir=releases) as temp:
                    staging = Path(temp)
                    for member in members:
                        target = staging.joinpath(*member.name.split("/"))
                        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                        # Never trust tar metadata or extract paths using tar.extractall.
                        source = tar.extractfile(member)
                        if source is None:
                            raise InvalidRelease("missing archive data")
                        with source, target.open("xb") as output:
                            shutil.copyfileobj(source, output)
                        target.chmod(0o644)
                    for directory in staging.rglob("*"):
                        if directory.is_dir():
                            directory.chmod(0o755)
                    staging.chmod(0o755)
                    # Publish the complete release only after all files exist.
                    staging.rename(destination)
        except (tarfile.TarError, EOFError) as exc:
            raise InvalidRelease("invalid archive") from exc


def execute(base, original_command, stream):
    match = COMMAND.fullmatch(original_command)
    if not match:
        raise ReleaseError("invalid command")
    action, commit = match.groups()
    with deployment_lock(base):
        if action == "upload":
            upload(base, commit, stream)
            return f"Release uploaded: {commit}"
        activate_release(base, commit)
        return f"Activated release: {commit}"


def main():
    try:
        print(execute(BASE, os.environ.get("SSH_ORIGINAL_COMMAND", ""), sys.stdin.buffer))
    except (InvalidRelease, ReleaseError, OSError) as exc:
        print(f"Deploy rejected: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
