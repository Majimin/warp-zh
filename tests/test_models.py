"""测试 warp_zh.models 模块。"""
from __future__ import annotations
from pathlib import Path
import pytest
from warp_zh.models import (
    SourceLocation, StringEntry, StringId,
    TranslationMemory, TranslationStatus, TranslationUnit,
)


class TestStringId:
    def test_derive_stable(self):
        assert StringId.derive("All", "ctx") == StringId.derive("All", "ctx")

    def test_derive_different_text(self):
        assert StringId.derive("All", "ctx") != StringId.derive("None", "ctx")

    def test_derive_different_context(self):
        assert StringId.derive("All", "a") != StringId.derive("All", "b")

    def test_length(self):
        assert len(StringId.derive("Test", "ctx").value) == 12

    def test_no_prefix_collision(self):
        assert StringId.derive("a", "bc") != StringId.derive("ab", "c")

    def test_str(self):
        sid = StringId.derive("x", "y")
        assert str(sid) == sid.value


class TestSourceLocation:
    def test_valid(self, sample_location):
        assert sample_location.byte_len == 3

    def test_zero_length(self):
        loc = SourceLocation(Path("a.rs"), 1, 1, 5, 5)
        assert loc.byte_len == 0

    def test_invalid_range(self):
        with pytest.raises(ValueError, match="非法字节区间"):
            SourceLocation(Path("a.rs"), 1, 1, 10, 5)


class TestStringEntry:
    def test_key_is_string_id(self, sample_entry):
        assert isinstance(sample_entry.key, StringId)

    def test_key_stable(self, sample_entry):
        assert sample_entry.key == sample_entry.key

    def test_is_format_default_false(self, sample_entry):
        assert sample_entry.is_format is False


class TestTranslationUnit:
    def test_initial_state(self, sample_entry):
        unit = TranslationUnit(entry=sample_entry)
        assert unit.status == TranslationStatus.UNTRANSLATED
        assert not unit.is_translated

    def test_mark_machine(self, sample_entry):
        unit = TranslationUnit(entry=sample_entry)
        unit.mark_machine("全部")
        assert unit.status == TranslationStatus.MACHINE
        assert unit.is_translated

    def test_mark_reviewed(self, sample_entry):
        unit = TranslationUnit(entry=sample_entry)
        unit.mark_reviewed("全部")
        assert unit.status == TranslationStatus.REVIEWED
        assert unit.is_translated

    def test_mark_stale(self, sample_entry):
        unit = TranslationUnit(entry=sample_entry)
        unit.mark_machine("全部")
        unit.mark_stale()
        assert unit.status == TranslationStatus.STALE
        assert not unit.is_translated


class TestTranslationMemory:
    def test_empty_coverage(self):
        assert TranslationMemory().coverage == 0.0

    def test_full_coverage(self, sample_entry):
        m = TranslationMemory()
        u = TranslationUnit(entry=sample_entry)
        u.mark_machine("全部")
        m.add(u)
        assert m.coverage == 1.0

    def test_partial_coverage(self, sample_entry, sample_location):
        m = TranslationMemory()
        u1 = TranslationUnit(entry=sample_entry)
        u1.mark_machine("全部")
        m.add(u1)
        loc2 = SourceLocation(Path("b.rs"), 2, 1, 10, 20)
        e2 = StringEntry("Personal", "ctx", loc2, "ActionButton::new")
        m.add(TranslationUnit(entry=e2))
        assert m.coverage == pytest.approx(0.5)

    def test_find_by_source(self, translated_unit):
        m = TranslationMemory()
        m.add(translated_unit)
        found = m.find_by_source("All")
        assert found is not None
        assert found.target_text == "全部"

    def test_find_miss(self, translated_unit):
        m = TranslationMemory()
        m.add(translated_unit)
        assert m.find_by_source("NotExist") is None

    def test_summary(self, translated_unit):
        m = TranslationMemory()
        m.add(translated_unit)
        s = m.summary()
        assert s["total"] == 1
        assert s.get("machine", 0) == 1

    def test_untranslated_list(self, sample_entry):
        m = TranslationMemory()
        m.add(TranslationUnit(entry=sample_entry))
        assert len(m.untranslated()) == 1
