"""Integration tests for the unprivileged publisher orchestration."""
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from deploy.archive_validator import InvalidRelease
from deploy.coordinator import process_ready
from deploy.release_manager import ReleaseError

A = "a" * 40
B = "b" * 40


def make_archive(files):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, data in files:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.queue = root / "queue"
        self.state = root / "state"
        self.base = root / "site"
        for path in (self.queue, self.state, self.base):
            path.mkdir()
        (self.base / "releases").mkdir()

    def put(self, commit, files):
        (self.queue / (commit + ".tar.gz")).write_bytes(make_archive(files))
        return commit + ".tar.gz"

    def test_valid_release_is_activated_and_private_files_removed(self):
        name = self.put(A, [("index.html", b"hello"), ("src/app.js", b"code")])
        destination = process_ready(self.queue, self.state, self.base, name)
        self.assertEqual((destination / "src/app.js").read_bytes(), b"code")
        self.assertEqual((self.base / "app").resolve(), destination)
        self.assertEqual([p.name for p in self.state.iterdir()], ["publisher.lock"])

    def test_invalid_archive_keeps_active_release(self):
        first = self.put(A, [("index.html", b"first")])
        process_ready(self.queue, self.state, self.base, first)
        second = self.put(B, [("index.html", b"second"), ("../bad.js", b"bad")])
        with self.assertRaises(InvalidRelease):
            process_ready(self.queue, self.state, self.base, second)
        self.assertEqual((self.base / "app").resolve().name, A)
        self.assertEqual([p.name for p in self.state.iterdir()], ["publisher.lock"])

    def test_existing_commit_is_not_overwritten(self):
        name = self.put(A, [("index.html", b"first")])
        process_ready(self.queue, self.state, self.base, name)
        with self.assertRaises(ReleaseError):
            process_ready(self.queue, self.state, self.base, name)
        self.assertEqual((self.base / "app" / "index.html").read_bytes(), b"first")

    def test_bad_queue_name_rejected(self):
        with self.assertRaises(InvalidRelease):
            process_ready(self.queue, self.state, self.base, "../bad.tar.gz")


if __name__ == "__main__":
    unittest.main()
