"""测试 warp_zh.codemod 模块。"""
from __future__ import annotations
from pathlib import Path
import pytest
from warp_zh.codemod import apply_to_file, apply_to_dir, revert_file
from warp_zh.models import SourceLocation, StringEntry, TranslationUnit


def _unit(source: str, target: str, content: bytes, rs_file: Path) -> TranslationUnit:
    enc = source.encode("utf-8")
    idx = content.find(enc)
    assert idx >= 0, f"{source!r} not in content"
    loc = SourceLocation(rs_file, 1, idx + 1, idx, idx + len(enc))
    entry = StringEntry(source, "ctx", loc, "ActionButton::new")
    unit = TranslationUnit(entry=entry)
    unit.mark_machine(target)
    return unit


class TestApplyToFile:
    def test_basic_replace(self, tmp_path):
        f = tmp_path / "ui.rs"
        content = b'ActionButton::new("Settings");'
        f.write_bytes(content)
        u = _unit("Settings", "设置", content, Path("ui.rs"))
        r = apply_to_file(f, [u])
        assert r.replaced == 1
        assert "设置".encode() in f.read_bytes()

    def test_dry_run(self, tmp_path):
        f = tmp_path / "ui.rs"
        content = b'ActionButton::new("Close");'
        f.write_bytes(content)
        u = _unit("Close", "关闭", content, Path("ui.rs"))
        r = apply_to_file(f, [u], dry_run=True)
        assert r.replaced == 1
        assert r.dry_run is True
        assert f.read_bytes() == content  # not modified

    def test_mismatch_skipped(self, tmp_path):
        f = tmp_path / "ui.rs"
        content = b'ActionButton::new("Other");'
        f.write_bytes(content)
        loc = SourceLocation(Path("ui.rs"), 1, 1, 18, 26)
        entry = StringEntry("Settings", "ctx", loc, "ActionButton::new")
        u = TranslationUnit(entry=entry)
        u.mark_machine("设置")
        r = apply_to_file(f, [u])
        assert r.skipped == 1
        assert r.replaced == 0

    def test_idempotent(self, tmp_path):
        target_bytes = "设置".encode("utf-8")
        f = tmp_path / "ui.rs"
        f.write_bytes(target_bytes)
        loc = SourceLocation(Path("ui.rs"), 1, 1, 0, len(target_bytes))
        entry = StringEntry("设置", "ctx", loc, ".text")
        u = TranslationUnit(entry=entry)
        u.mark_machine("设置")
        r = apply_to_file(f, [u])
        assert r.skipped == 1

    def test_multi_replace(self, tmp_path):
        f = tmp_path / "ui.rs"
        content = b'ActionButton::new("All"); ActionButton::new("Close");'
        f.write_bytes(content)
        u1 = _unit("All",   "全部", content, Path("ui.rs"))
        u2 = _unit("Close", "关闭", content, Path("ui.rs"))
        r = apply_to_file(f, [u1, u2])
        assert r.replaced == 2
        text = f.read_bytes().decode("utf-8")
        assert "全部" in text and "关闭" in text

    def test_untranslated_skipped(self, tmp_path):
        f = tmp_path / "ui.rs"
        content = b'ActionButton::new("Settings");'
        f.write_bytes(content)
        loc = SourceLocation(Path("ui.rs"), 1, 1, 18, 26)
        entry = StringEntry("Settings", "ctx", loc, "ActionButton::new")
        u = TranslationUnit(entry=entry)  # not translated
        r = apply_to_file(f, [u])
        assert r.replaced == 0

    def test_nonexistent_file(self, tmp_path):
        f = tmp_path / "ghost.rs"
        loc = SourceLocation(Path("ghost.rs"), 1, 1, 0, 5)
        entry = StringEntry("Hello", "ctx", loc, ".text")
        u = TranslationUnit(entry=entry)
        u.mark_machine("你好")
        r = apply_to_file(f, [u])
        assert r.skipped == 1


class TestRevertFile:
    def test_basic_revert(self, tmp_path):
        f = tmp_path / "ui.rs"
        f.write_text('ActionButton::new("设置");', encoding="utf-8")
        content = b'ActionButton::new("Settings");'
        u = _unit("Settings", "设置", content, Path("ui.rs"))
        n = revert_file(f, [u])
        assert n == 1
        assert "Settings" in f.read_text(encoding="utf-8")

    def test_revert_nonexistent(self, tmp_path):
        assert revert_file(tmp_path / "ghost.rs", []) == 0
