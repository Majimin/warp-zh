"""pytest fixtures shared across all test modules."""
from __future__ import annotations
from pathlib import Path
import pytest
from warp_zh.models import SourceLocation, StringEntry, TranslationUnit


@pytest.fixture
def tmp_warp_dir(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "app" / "src").mkdir(parents=True)
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "warp"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def sample_location(tmp_warp_dir: Path) -> SourceLocation:
    return SourceLocation(
        file=Path("app/src/test.rs"), line=1, column=1, byte_start=0, byte_end=3,
    )


@pytest.fixture
def sample_entry(sample_location: SourceLocation) -> StringEntry:
    return StringEntry(
        source_text="All", context="app.src.test",
        location=sample_location, call_site="ActionButton::new",
    )


@pytest.fixture
def translated_unit(sample_entry: StringEntry) -> TranslationUnit:
    unit = TranslationUnit(entry=sample_entry)
    unit.mark_machine("全部")
    return unit
