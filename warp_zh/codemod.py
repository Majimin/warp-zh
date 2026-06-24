"""字节级 Rust 源码改写器。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import TranslationUnit


@dataclass
class ApplyResult:
    file: Path
    replaced: int
    skipped: int
    dry_run: bool = False


def apply_to_file(
    file: Path,
    units: list[TranslationUnit],
    dry_run: bool = False,
) -> ApplyResult:
    applicable = [u for u in units if u.is_translated and u.target_text is not None]
    if not applicable:
        return ApplyResult(file=file, replaced=0, skipped=0, dry_run=dry_run)

    try:
        raw = file.read_bytes()
    except OSError:
        return ApplyResult(file=file, replaced=0, skipped=len(applicable), dry_run=dry_run)

    applicable.sort(key=lambda u: u.entry.location.byte_start, reverse=True)

    replaced = skipped = 0
    data = bytearray(raw)

    for u in applicable:
        loc = u.entry.location
        bs, be = loc.byte_start, loc.byte_end
        if bs < 0 or be > len(data) or bs > be:
            skipped += 1
            continue
        current_bytes  = bytes(data[bs:be])
        expected_bytes = u.entry.source_text.encode("utf-8")
        target_bytes   = u.target_text.encode("utf-8")  # type: ignore

        if current_bytes != expected_bytes:
            skipped += 1
            continue
        if current_bytes == target_bytes:
            skipped += 1
            continue

        data[bs:be] = target_bytes
        replaced += 1

    if replaced > 0 and not dry_run:
        file.write_bytes(bytes(data))

    return ApplyResult(file=file, replaced=replaced, skipped=skipped, dry_run=dry_run)


def apply_to_dir(
    warp_root: Path,
    units: list[TranslationUnit],
    dry_run: bool = False,
) -> list[ApplyResult]:
    file_map: dict[Path, list[TranslationUnit]] = {}
    for u in units:
        if not u.is_translated:
            continue
        abs_file = warp_root / u.entry.location.file
        file_map.setdefault(abs_file, []).append(u)

    return [
        apply_to_file(abs_file, file_units, dry_run=dry_run)
        for abs_file, file_units in sorted(file_map.items())
    ]


def revert_file(file: Path, units: list[TranslationUnit]) -> int:
    if not file.exists():
        return 0
    try:
        content = file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0

    reverted = 0
    for u in units:
        if u.target_text and u.target_text in content:
            content = content.replace(u.target_text, u.entry.source_text, 1)
            reverted += 1

    if reverted > 0:
        file.write_text(content, encoding="utf-8")
    return reverted


def revert_dir(
    warp_root: Path,
    units: list[TranslationUnit],
) -> dict[str, int]:
    file_map: dict[Path, list[TranslationUnit]] = {}
    for u in units:
        if u.target_text:
            abs_file = warp_root / u.entry.location.file
            file_map.setdefault(abs_file, []).append(u)

    return {
        str(abs_file): n
        for abs_file, file_units in sorted(file_map.items())
        if (n := revert_file(abs_file, file_units)) > 0
    }
