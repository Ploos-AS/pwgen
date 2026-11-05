"""Crash-recovery tests for an installed release missing its receipt."""
import tempfile
import unittest
from pathlib import Path

from deploy.receipt_recovery import recover_active_receipt
from deploy.queue_state import read_receipt, write_receipt
from deploy.release_manager import ReleaseError

A = "a" * 40
B = "b" * 40


class ReceiptRecoveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.base = root / "site"
        self.state = root / "state"
        self.base.mkdir()
        self.state.mkdir()
        (self.base / "releases").mkdir()

    def install(self, commit):
        target = self.base / "releases" / commit
        target.mkdir()
        (target / "index.html").write_text("valid")
        return target

    def test_recovers_active_release_without_receipt(self):
        self.install(A)
        (self.base / "app").symlink_to(Path("releases") / A)
        self.assertTrue(recover_active_receipt(self.base, self.state, A))
        self.assertEqual(read_receipt(self.state, A)["status"], "published")
        self.assertFalse(recover_active_receipt(self.base, self.state, A))

    def test_no_release_does_not_create_receipt(self):
        self.assertFalse(recover_active_receipt(self.base, self.state, A))
        self.assertIsNone(read_receipt(self.state, A))

    def test_inactive_existing_release_is_not_recovered(self):
        self.install(A)
        self.install(B)
        (self.base / "app").symlink_to(Path("releases") / B)
        with self.assertRaises(ReleaseError):
            recover_active_receipt(self.base, self.state, A)
        self.assertIsNone(read_receipt(self.state, A))

    def test_release_symlink_is_rejected(self):
        target = self.install(B)
        (self.base / "releases" / A).symlink_to(target, target_is_directory=True)
        with self.assertRaises(ReleaseError):
            recover_active_receipt(self.base, self.state, A)

    def test_missing_index_is_rejected(self):
        target = self.install(A)
        (target / "index.html").unlink()
        (self.base / "app").symlink_to(Path("releases") / A)
        with self.assertRaises(ReleaseError):
            recover_active_receipt(self.base, self.state, A)

    def test_unexpected_receipt_is_rejected(self):
        write_receipt(self.state, A, "rejected")
        with self.assertRaises(ReleaseError):
            recover_active_receipt(self.base, self.state, A)

    def test_invalid_commit_rejected(self):
        with self.assertRaises(ReleaseError):
            recover_active_receipt(self.base, self.state, "../oops")


if __name__ == "__main__":
    unittest.main()
