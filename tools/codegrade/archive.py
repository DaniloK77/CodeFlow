"""Safe, in-memory reading of uploaded ``.zip`` projects.

Nothing is extracted to disk and nothing is executed. The reader defends against:

* zip-slip paths (``../../etc/passwd``, absolute paths, drive letters),
* symbolic links and encrypted members,
* zip bombs: entry-count, per-file, total-size and compression-ratio limits, enforced on
  the bytes actually read rather than on (forgeable) header values.
"""

from __future__ import annotations

import io
import re
import zipfile
import zlib
from dataclasses import dataclass, field

from .discovery import is_excluded_path
from .hygiene import ProjectSnapshot
from .source import SUPPORTED_EXTENSIONS, SourceFile

_SYMLINK_MODE = 0o120000
_FILE_TYPE_MASK = 0o170000
_SOURCE_DIR_NAMES = frozenset(
    {"src", "lib", "app", "components", "pages", "packages", "test", "tests"}
)


class ArchiveError(ValueError):
    """The upload is not a usable archive (corrupt, empty or malicious)."""


class ArchiveTooLargeError(ArchiveError):
    """The archive exceeds a size or count limit."""


@dataclass(frozen=True)
class ArchiveLimits:
    max_entries: int = 20_000  # members inspected, including ignored ones
    max_source_files: int = 400
    max_file_bytes: int = 300_000  # bigger files are almost always generated or minified
    max_total_bytes: int = 20_000_000  # uncompressed bytes actually read
    max_compression_ratio: int = 200


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


@dataclass
class ArchiveContents:
    sources: list[SourceFile]
    snapshot: ProjectSnapshot
    skipped: list[SkippedFile] = field(default_factory=list)


def read_archive(data: bytes, limits: ArchiveLimits | None = None) -> ArchiveContents:
    """Sources, file listing and skipped members of an uploaded .zip, read in memory."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as error:
        raise ArchiveError("the upload is not a valid .zip archive") from error
    with archive:
        return _ArchiveReader(archive, limits or ArchiveLimits()).read()


class _ArchiveReader:
    def __init__(self, archive: zipfile.ZipFile, limits: ArchiveLimits) -> None:
        self.archive = archive
        self.limits = limits
        self.skipped: list[SkippedFile] = []
        self.bytes_read = 0

    def read(self) -> ArchiveContents:
        """Validates every member, then loads the supported source files."""
        members = self._safe_members()
        prefix = _common_root(list(members))
        members = {name[len(prefix) :]: info for name, info in members.items()}

        source_members = {
            name: info
            for name, info in members.items()
            if _extension(name) in SUPPORTED_EXTENSIONS and not is_excluded_path(name)
        }
        if not source_members:
            raise ArchiveError("no supported source files (.js, .jsx, .ts, .tsx, .py) found")
        if len(source_members) > self.limits.max_source_files:
            raise ArchiveTooLargeError(
                f"{len(source_members)} source files found; "
                f"the limit is {self.limits.max_source_files}"
            )

        sources = [
            source
            for name, info in sorted(source_members.items())
            if (source := self._load_source(name, info)) is not None
        ]
        readme_info = members.get("README.md")
        readme = self._read_text("README.md", readme_info) if readme_info else None
        snapshot = ProjectSnapshot(frozenset(members), readme)
        return ArchiveContents(sources, snapshot, self.skipped)

    def _safe_members(self) -> dict[str, zipfile.ZipInfo]:
        infos = self.archive.infolist()
        if len(infos) > self.limits.max_entries:
            raise ArchiveTooLargeError(
                f"archive has {len(infos)} entries; the limit is {self.limits.max_entries}"
            )
        members: dict[str, zipfile.ZipInfo] = {}
        for info in infos:
            name = _normalize(info.filename)
            reason = self._rejection_reason(name, info)
            if reason is not None:
                self.skipped.append(SkippedFile(info.filename, reason))
            elif name is not None and not info.is_dir() and not is_excluded_path(name):
                members[name] = info
        return members

    @staticmethod
    def _rejection_reason(name: str | None, info: zipfile.ZipInfo) -> str | None:
        if name is None:
            return "unsafe path (absolute or contains '..')"
        if (info.external_attr >> 16) & _FILE_TYPE_MASK == _SYMLINK_MODE:
            return "symbolic links are not followed"
        if info.flag_bits & 0x1:
            return "encrypted"
        return None

    def _load_source(self, name: str, info: zipfile.ZipInfo) -> SourceFile | None:
        text = self._read_text(name, info)
        return SourceFile.from_text(name, text) if text is not None else None

    def _read_text(self, name: str, info: zipfile.ZipInfo) -> str | None:
        limit = self.limits.max_file_bytes
        if (
            info.compress_size
            and info.file_size / info.compress_size > self.limits.max_compression_ratio
        ):
            raise ArchiveError(f"suspicious compression ratio in {name} (possible zip bomb)")
        try:
            with self.archive.open(info) as handle:
                payload = handle.read(limit + 1)
        except (zipfile.BadZipFile, zlib.error, NotImplementedError, RuntimeError):
            self.skipped.append(SkippedFile(name, "unreadable or unsupported compression"))
            return None
        if len(payload) > limit:
            self.skipped.append(
                SkippedFile(name, f"larger than {limit // 1000} KB (likely generated)")
            )
            return None
        self.bytes_read += len(payload)
        if self.bytes_read > self.limits.max_total_bytes:
            raise ArchiveTooLargeError("archive expands beyond the uncompressed size limit")
        return payload.decode("utf-8", errors="replace")


def _normalize(name: str) -> str | None:
    """Archive member name as a safe relative POSIX path, or ``None`` if it escapes the root."""
    name = name.replace("\\", "/")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return None
    parts = [part for part in name.split("/") if part not in ("", ".")]
    if not parts or ".." in parts:
        return None
    return "/".join(parts) + ("/" if name.endswith("/") else "")


def _common_root(names: list[str]) -> str:
    """``project-main/`` when every member sits inside one wrapper folder (GitHub zips).

    Conventional source folders are never treated as wrappers: an archive holding only
    ``src/…`` keeps its ``src/`` prefix.
    """
    tops = {name.split("/", 1)[0] for name in names}
    if len(tops) != 1 or not all("/" in name for name in names):
        return ""
    top = tops.pop()
    return "" if top in _SOURCE_DIR_NAMES else f"{top}/"


def _extension(name: str) -> str:
    dot = name.rfind(".")
    return name[dot:].lower() if dot > name.rfind("/") else ""
