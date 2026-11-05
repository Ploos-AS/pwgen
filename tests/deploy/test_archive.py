import io
import tarfile
import unittest

from deploy.archive_validator import (
    InvalidRelease, MAX_FILE, MAX_FILES, MAX_UNPACKED,
    validate_archive, validate_members,
)


def member(name, size=1, kind=tarfile.REGTYPE):
    item = tarfile.TarInfo(name)
    item.size = size
    item.type = kind
    return item


def archive_bytes(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as tar:
        for name, content, kind in entries:
            item = member(name, len(content) if kind == tarfile.REGTYPE else 0, kind)
            tar.addfile(item, io.BytesIO(content) if kind == tarfile.REGTYPE else None)
    output.seek(0)
    return output


class ArchiveValidationTests(unittest.TestCase):
    def test_valid_nested_files(self):
        archive = archive_bytes([
            ("index.html", b"<html></html>", tarfile.REGTYPE),
            ("src/app.js", b"console.log('ok')", tarfile.REGTYPE),
        ])
        self.assertEqual(validate_archive(archive), ["index.html", "src/app.js"])

    def test_symlink_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html"), member("bad.txt", kind=tarfile.SYMTYPE)])

    def test_traversal_rejected(self):
        for name in ("../escape.txt", "src/../escape.txt", "/tmp/escape.txt",
                     "src//app.js", "./index.html", "src/./app.js",
                     "src\\app.js"):
            with self.subTest(name=name), self.assertRaises(InvalidRelease):
                validate_members([member("index.html"), member(name)])

    def test_duplicate_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html"), member("index.html")])

    def test_disallowed_file_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html"), member(".env")])

    def test_missing_index_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("styles.css")])

    def test_large_file_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html", MAX_FILE + 1)])

    def test_total_size_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html")] + [
                member(f"file{i}.js", MAX_FILE) for i in range(5)
            ])

    def test_too_many_files_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html")] + [
                member(f"file{i}.js") for i in range(MAX_FILES)
            ])

    def test_directory_entry_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html"), member("src/", kind=tarfile.DIRTYPE)])

    def test_invalid_gzip_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_archive(io.BytesIO(b"not a gzip archive"))

    def test_control_characters_rejected(self):
        with self.assertRaises(InvalidRelease):
            validate_members([member("index.html"), member("bad\nfile.js")])


if __name__ == "__main__":
    unittest.main()
