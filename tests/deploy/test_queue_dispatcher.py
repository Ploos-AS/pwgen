"""Tests for bounded dispatch and published-commit deduplication."""
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from deploy.queue_dispatcher import process_queue
from deploy.queue_state import read_receipt

A = "a" * 40
B = "b" * 40


def make_archive(payload):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tar:
        info = tarfile.TarInfo("index.html")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    return out.getvalue()


class QueueDispatcherTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.queue = root / "queue"
        self.state = root / "state"
        self.base = root / "site"
        for directory in (self.queue, self.state, self.base):
            directory.mkdir()
        (self.base / "releases").mkdir()

    def put(self, commit, payload):
        (self.queue / (commit + ".tar.gz")).write_bytes(make_archive(payload))

    def test_success_creates_receipt_and_skips_next_run(self):
        self.put(A, b"first")
        self.assertEqual(len(process_queue(self.queue, self.state, self.base)), 1)
        self.assertEqual(read_receipt(self.state, A)["status"], "published")
        self.assertEqual(process_queue(self.queue, self.state, self.base), [])
        self.assertEqual((self.base / "app" / "index.html").read_bytes(), b"first")

    def test_processes_sorted_commits_with_limit(self):
        self.put(B, b"second")
        self.put(A, b"first")
        self.assertEqual(len(process_queue(self.queue, self.state, self.base, limit=1)), 1)
        self.assertEqual((self.base / "app").resolve().name, A)
        self.assertEqual(len(process_queue(self.queue, self.state, self.base, limit=1)), 1)
        self.assertEqual((self.base / "app").resolve().name, B)

    def test_rejects_invalid_limit(self):
        for value in (0, 33, True, "2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                process_queue(self.queue, self.state, self.base, limit=value)

    def test_bad_archive_has_no_success_receipt(self):
        (self.queue / (A + ".tar.gz")).write_bytes(b"not an archive")
        with self.assertRaises(Exception):
            process_queue(self.queue, self.state, self.base)
        self.assertIsNone(read_receipt(self.state, A))
        self.assertFalse((self.base / "app").exists())


if __name__ == "__main__":
    unittest.main()
