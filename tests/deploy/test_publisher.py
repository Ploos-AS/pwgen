"""Tests for promotion and atomic activation, without elevated privileges."""
import tempfile
import unittest
from pathlib import Path

from deploy.publisher import promote_and_activate
from deploy.release_manager import ReleaseError

A = "a" * 40
B = "b" * 40


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.base = root / "site"
        self.base.mkdir()
        (self.base / "releases").mkdir()
        self.staging = root / "staging"
        self.staging.mkdir()
        (self.staging / "index.html").write_text("hello")
        (self.staging / "src").mkdir()
        (self.staging / "src" / "app.js").write_text("safe")

    def test_promote_and_activate(self):
        destination = promote_and_activate(self.staging, self.base, A)
        self.assertEqual((destination / "index.html").read_text(), "hello")
        self.assertEqual((self.base / "app").resolve(), destination)
        self.assertEqual((destination / "src" / "app.js").stat().st_mode & 0o777, 0o644)

    def test_second_release_switches_atomically(self):
        promote_and_activate(self.staging, self.base, A)
        (self.staging / "index.html").write_text("next")
        promote_and_activate(self.staging, self.base, B)
        self.assertEqual((self.base / "app").resolve(), self.base / "releases" / B)
        self.assertEqual((self.base / "releases" / A / "index.html").read_text(), "hello")

    def test_existing_release_not_overwritten(self):
        promote_and_activate(self.staging, self.base, A)
        with self.assertRaises(ReleaseError):
            promote_and_activate(self.staging, self.base, A)

    def test_invalid_commit_does_not_change_app(self):
        with self.assertRaises(ReleaseError):
            promote_and_activate(self.staging, self.base, "../bad")
        self.assertFalse((self.base / "app").exists())

    def test_symlinked_staging_file_rejected(self):
        (self.staging / "src" / "evil.js").symlink_to(self.staging / "index.html")
        with self.assertRaises(ReleaseError):
            promote_and_activate(self.staging, self.base, A)
        self.assertFalse((self.base / "releases" / A).exists())

    def test_symlinked_releases_rejected(self):
        (self.base / "releases").rmdir()
        (self.base / "releases").symlink_to(self.staging, target_is_directory=True)
        with self.assertRaises(ReleaseError):
            promote_and_activate(self.staging, self.base, A)

    def test_app_outside_releases_rejected(self):
        (self.base / "app").symlink_to(self.staging, target_is_directory=True)
        with self.assertRaises(ReleaseError):
            promote_and_activate(self.staging, self.base, A)

    def test_missing_index_rejected(self):
        (self.staging / "index.html").unlink()
        with self.assertRaises(ReleaseError):
            promote_and_activate(self.staging, self.base, A)


if __name__ == "__main__":
    unittest.main()
