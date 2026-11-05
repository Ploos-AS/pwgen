"""Tests for private, validated PWGen release staging."""
import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from deploy.archive_validator import InvalidRelease
from deploy.private_release import stage_private_release
from deploy.release_manager import ReleaseError

COMMIT = "b" * 40


def archive_bytes(entries):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tar:
        for name, payload, kind in entries:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = len(payload) if kind == tarfile.REGTYPE else 0
            tar.addfile(info, io.BytesIO(payload) if kind == tarfile.REGTYPE else None)
    return out.getvalue()


class PrivateReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.private = self.root / "private"
        self.private.mkdir(mode=0o700)
        self.archive = self.root / "snapshot.tar.gz"

    def write(self, entries):
        self.archive.write_bytes(archive_bytes(entries))

    def test_valid_nested_files(self):
        self.write([("index.html", b"ok", tarfile.REGTYPE),
                    ("src/app.js", b"hello", tarfile.REGTYPE)])
        staged = stage_private_release(self.archive, self.private, COMMIT)
        self.assertEqual((staged / "index.html").read_bytes(), b"ok")
        self.assertEqual((staged / "src/app.js").read_bytes(), b"hello")
        self.assertEqual((staged / "src/app.js").stat().st_mode & 0o777, 0o644)
        self.assertEqual(staged.stat().st_mode & 0o777, 0o700)

    def test_invalid_commit(self):
        self.write([("index.html", b"ok", tarfile.REGTYPE)])
        with self.assertRaises(ReleaseError):
            stage_private_release(self.archive, self.private, "../bad")

    def test_traversal_rejected_and_cleaned(self):
        self.write([("index.html", b"ok", tarfile.REGTYPE),
                    ("../escape.js", b"bad", tarfile.REGTYPE)])
        with self.assertRaises(InvalidRelease):
            stage_private_release(self.archive, self.private, COMMIT)
        self.assertEqual(list(self.private.iterdir()), [])

    def test_symlink_member_rejected_and_cleaned(self):
        self.write([("index.html", b"ok", tarfile.REGTYPE),
                    ("bad.js", b"", tarfile.SYMTYPE)])
        with self.assertRaises(InvalidRelease):
            stage_private_release(self.archive, self.private, COMMIT)
        self.assertEqual(list(self.private.iterdir()), [])

    def test_missing_index_rejected(self):
        self.write([("app.js", b"ok", tarfile.REGTYPE)])
        with self.assertRaises(InvalidRelease):
            stage_private_release(self.archive, self.private, COMMIT)
        self.assertEqual(list(self.private.iterdir()), [])

    def test_archive_symlink_rejected(self):
        self.write([("index.html", b"ok", tarfile.REGTYPE)])
        link = self.root / "link.tar.gz"
        link.symlink_to(self.archive)
        with self.assertRaises(InvalidRelease):
            stage_private_release(link, self.private, COMMIT)

    def test_corrupt_archive_cleans_up(self):
        self.archive.write_bytes(b"not gzip")
        with self.assertRaises(InvalidRelease):
            stage_private_release(self.archive, self.private, COMMIT)
        self.assertEqual(list(self.private.iterdir()), [])

    def test_duplicate_paths_rejected(self):
        self.write([("index.html", b"one", tarfile.REGTYPE),
                    ("index.html", b"two", tarfile.REGTYPE)])
        with self.assertRaises(InvalidRelease):
            stage_private_release(self.archive, self.private, COMMIT)
        self.assertEqual(list(self.private.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
