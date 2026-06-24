"""核心数据模型：贯穿提取 → 翻译 → 改写 → 打补丁全流程。"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class TranslationStatus(str, Enum):
    UNTRANSLATED = "untranslated"
    MACHINE      = "machine"
    REVIEWED     = "reviewed"
    STALE        = "stale"


@dataclass(frozen=True, slots=True)
class StringId:
    value: str

    @classmethod
    def derive(cls, source_text: str, context: str) -> "StringId":
        raw = f"{context}\x00{source_text}".encode("utf-8")
        return cls(value=hashlib.sha1(raw).hexdigest()[:12])

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"StringId({self.value!r})"


@dataclass(frozen=True, slots=True)
class SourceLocation:
    file: Path
    line: int
    column: int
    byte_start: int
    byte_end: int

    def __post_init__(self) -> None:
        if self.byte_end < self.byte_start:
            raise ValueError(
                f"非法字节区间 [{self.byte_start}, {self.byte_end}) "
                f"@ {self.file}:{self.line}"
            )

    @property
    def byte_len(self) -> int:
        return self.byte_end - self.byte_start


@dataclass(frozen=True, slots=True)
class StringEntry:
    source_text: str
    context: str
    location: SourceLocation
    call_site: str
    is_format: bool = False

    @property
    def key(self) -> StringId:
        return StringId.derive(self.source_text, self.context)


@dataclass(slots=True)
class TranslationUnit:
    entry: StringEntry
    target_text: Optional[str] = None
    status: TranslationStatus = TranslationStatus.UNTRANSLATED
    note: str = ""

    def mark_machine(self, text: str) -> None:
        self.target_text = text
        self.status = TranslationStatus.MACHINE

    def mark_reviewed(self, text: str) -> None:
        self.target_text = text
        self.status = TranslationStatus.REVIEWED

    def mark_stale(self) -> None:
        self.status = TranslationStatus.STALE

    @property
    def is_translated(self) -> bool:
        return bool(self.target_text) and self.status in (
            TranslationStatus.MACHINE,
            TranslationStatus.REVIEWED,
        )


@dataclass
class TranslationMemory:
    units: list[TranslationUnit] = field(default_factory=list)

    def add(self, unit: TranslationUnit) -> None:
        self.units.append(unit)

    def find_by_source(self, source_text: str) -> Optional[TranslationUnit]:
        for u in self.units:
            if u.entry.source_text == source_text:
                return u
        return None

    def find_by_key(self, key: StringId) -> Optional[TranslationUnit]:
        for u in self.units:
            if u.entry.key == key:
                return u
        return None

    @property
    def coverage(self) -> float:
        if not self.units:
            return 0.0
        done = sum(1 for u in self.units if u.is_translated)
        return done / len(self.units)

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {s.value: 0 for s in TranslationStatus}
        for u in self.units:
            counts[u.status.value] += 1
        counts["total"] = len(self.units)
        return counts

    def untranslated(self) -> list[TranslationUnit]:
        return [u for u in self.units if not u.is_translated]
