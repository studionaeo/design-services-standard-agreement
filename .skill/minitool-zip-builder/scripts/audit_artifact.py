#!/usr/bin/env python3
"""Audit deterministic mini-tool package and text-file size limits."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path, PurePosixPath

MIB = 1024 * 1024
ZIP_LIMIT = 10 * MIB
ZIP_RECOMMENDED = 2 * MIB
TEXT_FILE_WARNING = 2 * MIB
TEXT_TOTAL_WARNING = 5 * MIB
TEXT_SUFFIXES = {".html", ".css", ".js", ".json"}


def format_size(size: int) -> str:
    return f"{size / MIB:.2f} MiB"


def audit_entries(entries: list[tuple[str, int]]) -> list[str]:
    warnings: list[str] = []
    text_total = 0
    for name, size in entries:
        if PurePosixPath(name).suffix.lower() not in TEXT_SUFFIXES:
            continue
        text_total += size
        if size > TEXT_FILE_WARNING:
            warnings.append(
                f"{name}: text file is {format_size(size)}; review parse and memory cost"
            )

    if text_total > TEXT_TOTAL_WARNING:
        warnings.append(
            f"uncompressed HTML/CSS/JS/JSON total is {format_size(text_total)}; "
            "review for embedded databases or generated content"
        )
    return warnings


def read_directory(path: Path) -> list[tuple[str, int]]:
    return [
        (file.relative_to(path).as_posix(), file.stat().st_size)
        for file in sorted(path.rglob("*"))
        if file.is_file() and ".git" not in file.relative_to(path).parts
    ]


def read_zip(path: Path) -> tuple[list[tuple[str, int]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if path.stat().st_size > ZIP_LIMIT:
        errors.append(
            f"{path.name}: zip is {format_size(path.stat().st_size)}; hard limit is 10 MiB"
        )
    elif path.stat().st_size > ZIP_RECOMMENDED:
        warnings.append(
            f"{path.name}: zip is {format_size(path.stat().st_size)}; recommended target is 2 MiB"
        )

    with zipfile.ZipFile(path) as archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        entries = [(info.filename, info.file_size) for info in infos]
    return entries, errors, warnings


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 audit_artifact.py <artifact-directory-or-zip>")
        return 2

    path = Path(sys.argv[1]).resolve()
    if not path.exists():
        print(f"ERROR: path not found: {path}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    try:
        if path.is_dir():
            entries = read_directory(path)
        elif zipfile.is_zipfile(path):
            entries, zip_errors, zip_warnings = read_zip(path)
            errors.extend(zip_errors)
            warnings.extend(zip_warnings)
        else:
            print(f"ERROR: expected a directory or zip file: {path}")
            return 2
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"ERROR: cannot inspect {path}: {exc}")
        return 2

    warnings.extend(audit_entries(entries))

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: {len(entries)} file(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
