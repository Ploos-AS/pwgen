"""Tests for bounded discovery and root-private receipts."""
import os
import tempfile
import unittest
from pathlib import Path

from deploy.queue_state import (
    QueueLimitError, discover_ready, read_receipt, write_receipt,
    MAX_READY, MAX_QUEUE_BYTES,
)

A = "a" * 40
B = "b" * 40


class QueueStateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.queue = root / "queue"
        self.state = root / "state"
        self.queue.mkdir()
        self.state.mkdir()

    def test_discovers_sorted_ready_names(self):
        for commit in (B, A):
            (self.queue / (commit + ".tar.gz")).write_bytes(b"x")
        (self.queue / "unfinished.tmp").write_bytes(b"x")
        self.assertEqual(discover_ready(self.queue),
                         [A + ".tar.gz", B + ".tar.gz"])

    def test_ignores_symlinks(self):
        target = self.queue / "target"
        target.write_bytes(b"payload")
        (self.queue / (A + ".tar.gz")).symlink_to(target)
        self.assertEqual(discover_ready(self.queue), [])

    def test_ignores_hardlinks(self):
        target = self.queue / "target"
        target.write_bytes(b"payload")
        os.link(target, self.queue / (A + ".tar.gz"))
        self.assertEqual(discover_ready(self.queue), [])

    def test_limits_number_of_ready_entries(self):
        for n in range(MAX_READY + 1):
            (self.queue / (f"{n:040x}" + ".tar.gz")).write_bytes(b"x")
        with self.assertRaises(QueueLimitError):
            discover_ready(self.queue)

    def test_limits_ready_bytes(self):
        with (self.queue / (A + ".tar.gz")).open("wb") as handle:
            handle.truncate(MAX_QUEUE_BYTES + 1)
        with self.assertRaises(QueueLimitError):
            discover_ready(self.queue)

    def test_receipt_roundtrip(self):
        self.assertIsNone(read_receipt(self.state, A))
        write_receipt(self.state, A, "published")
        self.assertEqual(read_receipt(self.state, A),
                         {"commit": A, "status": "published"})
        self.assertEqual((self.state / "receipts" / (A + ".json")).stat().st_mode & 0o777, 0o600)

    def test_receipt_update_is_atomic(self):
        write_receipt(self.state, A, "rejected")
        write_receipt(self.state, A, "published")
        self.assertEqual(read_receipt(self.state, A)["status"], "published")
        self.assertEqual(len(list((self.state / "receipts").iterdir())), 1)

    def test_invalid_receipt_values(self):
        for commit, status in (("../escape", "published"), (A, "arbitrary")):
            with self.assertRaises(ValueError):
                write_receipt(self.state, commit, status)


if __name__ == "__main__":
    unittest.main()
