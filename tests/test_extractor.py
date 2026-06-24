"""测试 warp_zh.extractor 模块。"""
from __future__ import annotations
from pathlib import Path
import pytest
from warp_zh.extractor import extract_from_dir, extract_from_file

SAMPLE_BASIC = '''
fn ui() {
    let b = ActionButton::new("Settings");
    let b2 = ActionButton::new("Close");
}
'''

SAMPLE_MULTI = '''
fn view() {
    let v = ViewBuilder::new()
        .with_tooltip("Open file")
        .with_title("Main Window")
        .with_label("Submit")
        .with_placeholder("Search here")
        .with_header("Section")
        .with_description("A description");
}
'''

SAMPLE_SKIP = '''
fn misc() {
    ActionButton::new("https://example.com");
    ActionButton::new("已翻译文本");
    ActionButton::new("x");
}
'''

SAMPLE_FORMAT = '''
fn fmt() {
    label!("Hello {}");
    ActionButton::new("No format");
}
'''


def _make(tmp_path: Path, name: str, content: str) -> tuple[Path, Path]:
    root = tmp_path
    (root / ".git").mkdir(exist_ok=True)
    src = root / "app" / "src"
    src.mkdir(parents=True, exist_ok=True)
    f = src / name
    f.write_text(content, encoding="utf-8")
    return root, f


class TestExtractFromFile:
    def test_basic(self, tmp_path):
        root, f = _make(tmp_path, "ui.rs", SAMPLE_BASIC)
        srcs = [e.source_text for e in extract_from_file(f, root)]
        assert "Settings" in srcs
        assert "Close" in srcs

    def test_multi_call_sites(self, tmp_path):
        root, f = _make(tmp_path, "v.rs", SAMPLE_MULTI)
        srcs = [e.source_text for e in extract_from_file(f, root)]
        assert "Open file" in srcs
        assert "Main Window" in srcs
        assert "Submit" in srcs

    def test_skip_url(self, tmp_path):
        root, f = _make(tmp_path, "s.rs", SAMPLE_SKIP)
        srcs = [e.source_text for e in extract_from_file(f, root)]
        assert "https://example.com" not in srcs

    def test_skip_non_ascii(self, tmp_path):
        root, f = _make(tmp_path, "s.rs", SAMPLE_SKIP)
        for e in extract_from_file(f, root):
            assert e.source_text.isascii()

    def test_skip_too_short(self, tmp_path):
        root, f = _make(tmp_path, "s.rs", SAMPLE_SKIP)
        srcs = [e.source_text for e in extract_from_file(f, root)]
        assert "x" not in srcs

    def test_is_format(self, tmp_path):
        root, f = _make(tmp_path, "f.rs", SAMPLE_FORMAT)
        flags = {e.source_text: e.is_format for e in extract_from_file(f, root)}
        assert flags.get("Hello {}") is True
        assert flags.get("No format") is False

    def test_call_site_recorded(self, tmp_path):
        root, f = _make(tmp_path, "ui.rs", SAMPLE_BASIC)
        cs = {e.source_text: e.call_site for e in extract_from_file(f, root)}
        assert cs.get("Settings") == "ActionButton::new"

    def test_byte_offsets_valid(self, tmp_path):
        root, f = _make(tmp_path, "ui.rs", SAMPLE_BASIC)
        raw = f.read_bytes()
        for e in extract_from_file(f, root):
            loc = e.location
            assert raw[loc.byte_start:loc.byte_end].decode("utf-8") == e.source_text

    def test_nonexistent_file(self, tmp_path):
        assert list(extract_from_file(tmp_path / "ghost.rs", tmp_path)) == []


class TestExtractFromDir:
    def test_empty(self, tmp_path):
        (tmp_path / ".git").mkdir()
        assert extract_from_dir(tmp_path) == []

    def test_multiple_files(self, tmp_path):
        (tmp_path / ".git").mkdir()
        src = tmp_path / "app" / "src"
        src.mkdir(parents=True)
        (src / "a.rs").write_text('ActionButton::new("Alpha");', encoding="utf-8")
        (src / "b.rs").write_text('ActionButton::new("Beta");', encoding="utf-8")
        srcs = [e.source_text for e in extract_from_dir(tmp_path)]
        assert "Alpha" in srcs
        assert "Beta" in srcs
