"""Rust 源码字符串提取器（正则近似 AST）。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, Optional

from .config import WarpZhConfig
from .models import StringEntry, SourceLocation

_STR = r'"((?:[^"\\]|\\.)*?)"'

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (name, re.compile(pat, re.MULTILINE))
    for name, pat in [
        ("ActionButton::new",
         r'ActionButton::new\s*\(\s*' + _STR),
        ("CompactibleActionButton::new",
         r'CompactibleActionButton::new\s*\(\s*' + _STR),
        (".with_tooltip",  r'\.with_tooltip\s*\(\s*' + _STR),
        (".with_title",    r'\.with_title\s*\(\s*' + _STR),
        (".with_label",    r'\.with_label\s*\(\s*' + _STR),
        (".with_placeholder", r'\.with_placeholder\s*\(\s*' + _STR),
        (".with_header",   r'\.with_header\s*\(\s*' + _STR),
        (".with_description", r'\.with_description\s*\(\s*' + _STR),
        (".with_text",     r'\.with_text\s*\(\s*' + _STR),
        (".text",          r'\.text\s*\(\s*' + _STR),
        ("tooltip!",       r'tooltip!\s*\(\s*' + _STR),
        ("label!",         r'label!\s*\(\s*' + _STR),
        ("title!",         r'title!\s*\(\s*' + _STR),
        (".to_string()",   _STR + r'\s*\.to_string\s*\(\s*\)'),
    ]
]


def _calc_line_col(text: str, char_offset: int) -> tuple[int, int]:
    before = text[:char_offset]
    line = before.count("\n") + 1
    nl_pos = before.rfind("\n")
    col = (char_offset - nl_pos) if nl_pos >= 0 else char_offset + 1
    return line, col


def _char_to_byte(text: str, char_offset: int) -> int:
    return len(text[:char_offset].encode("utf-8"))


def _derive_context(file: Path, warp_root: Path) -> str:
    try:
        rel = file.relative_to(warp_root)
    except ValueError:
        rel = file
    return ".".join(rel.with_suffix("").parts)


def _should_skip(source: str, cfg: WarpZhConfig) -> bool:
    if len(source) < cfg.min_length:
        return True
    for pat in cfg.skip_patterns:
        if pat in source:
            return True
    if not source.isascii():
        return True
    return False


def extract_from_file(
    file: Path,
    warp_root: Path,
    cfg: Optional[WarpZhConfig] = None,
) -> Iterator[StringEntry]:
    if cfg is None:
        cfg = WarpZhConfig()
    try:
        text = file.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return

    context = _derive_context(file, warp_root)
    seen: set[tuple[str, int]] = set()

    for call_site, pat in _PATTERNS:
        for m in pat.finditer(text):
            source = m.group(1)
            if not source:
                continue
            display = (source.replace('\\"', '"')
                       .replace("\\n", "\n")
                       .replace("\\t", "\t"))
            if _should_skip(display, cfg):
                continue

            char_start = m.start(1)
            char_end   = m.end(1)
            byte_start = _char_to_byte(text, char_start)
            byte_end   = _char_to_byte(text, char_end)

            dedup = (source, byte_start)
            if dedup in seen:
                continue
            seen.add(dedup)

            line, col = _calc_line_col(text, char_start)
            is_format = "{}" in source or "{0}" in source

            try:
                loc = SourceLocation(
                    file=file.relative_to(warp_root),
                    line=line, column=col,
                    byte_start=byte_start, byte_end=byte_end,
                )
            except ValueError:
                continue

            yield StringEntry(
                source_text=source, context=context,
                location=loc, call_site=call_site,
                is_format=is_format,
            )


def extract_from_dir(
    warp_root: Path,
    cfg: Optional[WarpZhConfig] = None,
) -> list[StringEntry]:
    if cfg is None:
        cfg = WarpZhConfig()

    entries: list[StringEntry] = []
    seen_keys: set[str] = set()

    for src_dir in cfg.source_dirs:
        scan_root = warp_root / src_dir
        if not scan_root.exists():
            continue
        for rs_file in sorted(scan_root.rglob("*.rs")):
            for entry in extract_from_file(rs_file, warp_root, cfg):
                key = str(entry.key)
                if key not in seen_keys:
                    seen_keys.add(key)
                    entries.append(entry)

    return entries
