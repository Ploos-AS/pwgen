import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from deploy.archive_validator import InvalidRelease
from deploy.entrypoint import execute
from deploy.release_manager import ReleaseError


def bundle(files):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode="w:gz") as tar:
        for name, data in files:
            item = tarfile.TarInfo(name)
            item.size = len(data)
            tar.addfile(item, io.BytesIO(data))
    result.seek(0)
    return result


class EndToEndDeployTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        (self.base / "releases").mkdir()
        self.one = "a" * 40
        self.two = "b" * 40

    def test_upload_activate_and_rollback(self):
        for commit, value in ((self.one, b"first"), (self.two, b"second")):
            result = execute(self.base, f"upload {commit}",
                             bundle([("index.html", value), ("src/app.js", b"ok")]))
            self.assertIn("uploaded", result)
        execute(self.base, f"activate {self.one}", io.BytesIO())
        self.assertEqual((self.base / "app/index.html").read_bytes(), b"first")
        execute(self.base, f"activate {self.two}", io.BytesIO())
        self.assertEqual((self.base / "app/index.html").read_bytes(), b"second")
        execute(self.base, f"rollback {self.one}", io.BytesIO())
        self.assertEqual((self.base / "app/index.html").read_bytes(), b"first")

    def test_rejects_traversal_without_release(self):
        with self.assertRaises(InvalidRelease):
            execute(self.base, f"upload {self.one}",
                    bundle([("index.html", b"ok"), ("../escape.txt", b"bad")]))
        self.assertFalse((self.base / "releases" / self.one).exists())

    def test_rejects_invalid_command(self):
        with self.assertRaises(ReleaseError):
            execute(self.base, "sh -c id", io.BytesIO())

    def test_rejects_duplicate_release(self):
        execute(self.base, f"upload {self.one}", bundle([("index.html", b"ok")]))
        with self.assertRaises(ReleaseError):
            execute(self.base, f"upload {self.one}", bundle([("index.html", b"again")]))

    def test_rejects_app_directory_without_removing_it(self):
        (self.base / "app").mkdir()
        execute(self.base, f"upload {self.one}", bundle([("index.html", b"ok")]))
        with self.assertRaises(ReleaseError):
            execute(self.base, f"activate {self.one}", io.BytesIO())
        self.assertTrue((self.base / "app").is_dir())


if __name__ == "__main__":
    unittest.main()
