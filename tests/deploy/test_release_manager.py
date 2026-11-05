import fcntl
import multiprocessing
import tempfile
import unittest
from pathlib import Path

from deploy.release_manager import ReleaseError, activate_release, deployment_lock


def try_lock(path, result):
    with Path(path).open("a+b") as file:
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            result.put(False)
        else:
            result.put(True)


class ReleaseManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "releases").mkdir()
        self.one = "1" * 40
        self.two = "2" * 40
        for commit in (self.one, self.two):
            release = self.base / "releases" / commit
            release.mkdir()
            (release / "index.html").write_text(commit)

    def test_activation_and_rollback(self):
        with deployment_lock(self.base):
            activate_release(self.base, self.one)
            self.assertEqual((self.base / "app" / "index.html").read_text(), self.one)
            activate_release(self.base, self.two)
            self.assertEqual((self.base / "app" / "index.html").read_text(), self.two)
            activate_release(self.base, self.one)
            self.assertEqual((self.base / "app" / "index.html").read_text(), self.one)

    def test_refuses_real_app_directory(self):
        (self.base / "app").mkdir()
        with self.assertRaises(ReleaseError):
            activate_release(self.base, self.one)
        self.assertTrue((self.base / "app").is_dir())

    def test_missing_release(self):
        with self.assertRaises(ReleaseError):
            activate_release(self.base, "3" * 40)

    def test_rejects_invalid_commit(self):
        with self.assertRaises(ReleaseError):
            activate_release(self.base, "../" + self.one)

    def test_rejects_release_symlink(self):
        (self.base / "releases" / ("3" * 40)).symlink_to(self.base / "releases" / self.one)
        with self.assertRaises(ReleaseError):
            activate_release(self.base, "3" * 40)

    def test_rejects_symlink_index(self):
        target = self.base / "releases" / self.one / "index.html"
        target.unlink()
        target.symlink_to("/etc/passwd")
        with self.assertRaises(ReleaseError):
            activate_release(self.base, self.one)

    def test_refuses_app_symlink_outside_releases(self):
        (self.base / "app").symlink_to("/tmp")
        with self.assertRaises(ReleaseError):
            activate_release(self.base, self.one)

    def test_lock_blocks_other_process(self):
        ctx = multiprocessing.get_context("spawn")
        result = ctx.Queue()
        with deployment_lock(self.base):
            process = ctx.Process(target=try_lock, args=(str(self.base / ".deploy.lock"), result))
            process.start()
            process.join(timeout=5)
            self.assertEqual(process.exitcode, 0)
            self.assertFalse(result.get(timeout=2))


if __name__ == "__main__":
    unittest.main()
