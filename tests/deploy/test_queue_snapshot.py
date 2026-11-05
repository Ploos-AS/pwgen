"""Security tests for snapshotting an attacker-writable upload queue."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deploy.archive_validator import InvalidRelease, MAX_ARCHIVE
from deploy.queue_snapshot import snapshot_queued_archive

COMMIT = "a" * 40
NAME = COMMIT + ".tar.gz"


class QueueSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.queue = root / "queue"
        self.private = root / "private"
        self.queue.mkdir()
        self.private.mkdir(mode=0o700)

    def test_valid_archive_is_copied_to_private_file(self):
        (self.queue / NAME).write_bytes(b"payload")
        commit, snapshot = snapshot_queued_archive(self.queue, self.private, NAME)
        self.addCleanup(snapshot.unlink)
        self.assertEqual(commit, COMMIT)
        self.assertEqual(snapshot.read_bytes(), b"payload")
        self.assertEqual(snapshot.parent, self.private)
        self.assertEqual(snapshot.stat().st_mode & 0o777, 0o600)
        (self.queue / NAME).write_bytes(b"changed")
        self.assertEqual(snapshot.read_bytes(), b"payload")

    def test_invalid_names_rejected(self):
        for name in ("../" + NAME, "x" * 40 + ".tar.gz", COMMIT + ".zip", NAME + "/x"):
            with self.subTest(name=name), self.assertRaises(InvalidRelease):
                snapshot_queued_archive(self.queue, self.private, name)

    def test_symlink_rejected(self):
        target = self.queue / "target"
        target.write_bytes(b"payload")
        (self.queue / NAME).symlink_to(target)
        with self.assertRaises(OSError):
            snapshot_queued_archive(self.queue, self.private, NAME)

    def test_directory_rejected(self):
        (self.queue / NAME).mkdir()
        with self.assertRaises((InvalidRelease, OSError)):
            snapshot_queued_archive(self.queue, self.private, NAME)

    def test_hardlink_rejected(self):
        target = self.queue / "target"
        target.write_bytes(b"payload")
        os.link(target, self.queue / NAME)
        with self.assertRaises(InvalidRelease):
            snapshot_queued_archive(self.queue, self.private, NAME)

    def test_oversized_archive_rejected_without_snapshot(self):
        with (self.queue / NAME).open("wb") as file:
            file.truncate(MAX_ARCHIVE + 1)
        with self.assertRaises(InvalidRelease):
            snapshot_queued_archive(self.queue, self.private, NAME)
        self.assertEqual(list(self.private.iterdir()), [])

    def test_missing_file_rejected(self):
        with self.assertRaises(FileNotFoundError):
            snapshot_queued_archive(self.queue, self.private, NAME)

    def test_private_snapshot_is_removed_on_read_failure(self):
        (self.queue / NAME).write_bytes(b"payload")
        with patch("deploy.queue_snapshot.os.read", side_effect=OSError("read failure")):
            with self.assertRaises(OSError):
                snapshot_queued_archive(self.queue, self.private, NAME)
        self.assertEqual(list(self.private.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
