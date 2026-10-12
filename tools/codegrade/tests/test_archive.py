import io
import unittest
import zipfile

from tools.codegrade.archive import (
    ArchiveError,
    ArchiveLimits,
    ArchiveTooLargeError,
    read_archive,
)

CLEAN_COMPONENT = "export function Hello() {\n  return <p>Hello</p>;\n}\n"


def build_zip(files: dict[str, str | bytes], *, symlinks: tuple[str, ...] = ()) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            if name in symlinks:
                info.external_attr = 0o120777 << 16
            archive.writestr(info, content)
    return buffer.getvalue()


class ReadArchiveTest(unittest.TestCase):
    def test_strips_the_top_level_folder_and_reads_sources(self) -> None:
        data = build_zip(
            {
                "app-main/src/Hello.tsx": CLEAN_COMPONENT,
                "app-main/README.md": "# App",
                "app-main/tsconfig.json": "{}",
            }
        )

        contents = read_archive(data)

        self.assertEqual([source.label for source in contents.sources], ["src/Hello.tsx"])
        self.assertEqual(contents.snapshot.readme, "# App")
        self.assertTrue(contents.snapshot.has("tsconfig.json"))

    def test_ignores_dependencies_and_macos_metadata(self) -> None:
        data = build_zip(
            {
                "src/Hello.tsx": CLEAN_COMPONENT,
                "node_modules/react/index.js": "var x = 1;",
                "__MACOSX/src/._Hello.tsx": "binary",
            }
        )

        contents = read_archive(data)

        self.assertEqual([source.label for source in contents.sources], ["src/Hello.tsx"])
        self.assertFalse(contents.snapshot.has("node_modules/*"))

    def test_rejects_path_traversal_and_symlinks_without_failing(self) -> None:
        data = build_zip(
            {
                "src/Hello.tsx": CLEAN_COMPONENT,
                "../../etc/evil.js": "debugger;",
                "/abs/evil.js": "debugger;",
                "src/link.js": "/etc/passwd",
            },
            symlinks=("src/link.js",),
        )

        contents = read_archive(data)

        self.assertEqual([source.label for source in contents.sources], ["src/Hello.tsx"])
        reasons = {skipped.reason.split(" ")[0] for skipped in contents.skipped}
        self.assertEqual(reasons, {"unsafe", "symbolic"})

    def test_skips_files_that_are_too_large(self) -> None:
        data = build_zip({"src/Hello.tsx": CLEAN_COMPONENT, "src/big.js": "x" * 2_000})

        contents = read_archive(data, ArchiveLimits(max_file_bytes=1_000))

        self.assertEqual([skipped.path for skipped in contents.skipped], ["src/big.js"])

    def test_detects_zip_bombs_by_compression_ratio(self) -> None:
        data = build_zip({"src/bomb.js": "a" * 1_000_000})

        with self.assertRaisesRegex(ArchiveError, "zip bomb"):
            read_archive(data, ArchiveLimits(max_file_bytes=2_000_000))

    def test_enforces_source_file_and_total_size_limits(self) -> None:
        many = {f"src/file{index}.ts": "export const a = 1;\n" for index in range(5)}
        with self.assertRaises(ArchiveTooLargeError):
            read_archive(build_zip(many), ArchiveLimits(max_source_files=4))
        with self.assertRaises(ArchiveTooLargeError):
            read_archive(build_zip(many), ArchiveLimits(max_total_bytes=50))

    def test_rejects_invalid_or_empty_archives(self) -> None:
        with self.assertRaisesRegex(ArchiveError, "not a valid"):
            read_archive(b"definitely not a zip")
        with self.assertRaisesRegex(ArchiveError, "no supported source files"):
            read_archive(build_zip({"notes.txt": "hello"}))
