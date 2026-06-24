"""测试 warp_zh.glossary 模块。"""
from __future__ import annotations
from pathlib import Path
import pytest
from warp_zh.glossary import BUILTIN_GLOSSARY, Glossary


class TestBuiltinGlossary:
    def test_pr_11960_terms(self):
        assert BUILTIN_GLOSSARY["All"] == "全部"
        assert BUILTIN_GLOSSARY["Personal"] == "个人"
        assert BUILTIN_GLOSSARY["Get started"] == "开始使用"
        assert BUILTIN_GLOSSARY["View Agents"] == "查看 AI 助手"

    def test_common_ui_terms(self):
        for t in ["Settings", "Close", "Cancel", "Save", "Edit"]:
            assert t in BUILTIN_GLOSSARY

    def test_terminal_terms(self):
        for t in ["Terminal", "Tab", "Pane", "Session"]:
            assert t in BUILTIN_GLOSSARY

    def test_minimum_size(self):
        assert len(BUILTIN_GLOSSARY) >= 100

    def test_no_empty_values(self):
        for k, v in BUILTIN_GLOSSARY.items():
            assert v.strip(), f"空译文: {k!r}"


class TestGlossary:
    def test_lookup_exact(self):
        g = Glossary()
        assert g.lookup("All") == "全部"
        assert g.lookup("Settings") == "设置"

    def test_lookup_case_insensitive(self):
        assert Glossary().lookup("all") == "全部"

    def test_lookup_missing(self):
        assert Glossary().lookup("xyz_no_such") is None

    def test_lookup_required_missing(self):
        assert Glossary().lookup_required("xyz") == "xyz"

    def test_extra_terms(self):
        g = Glossary({"MyTerm": "我的术语"})
        assert g.lookup("MyTerm") == "我的术语"

    def test_extra_overrides_builtin(self):
        g = Glossary({"Settings": "首选项"})
        assert g.lookup("Settings") == "首选项"

    def test_len(self):
        assert len(Glossary()) >= 100

    def test_add_term(self):
        g = Glossary()
        g.add("NewTerm", "新术语")
        assert g.lookup("NewTerm") == "新术语"

    def test_load_nonexistent(self, tmp_path: Path):
        g = Glossary.load(tmp_path / "no.yml")
        assert g.lookup("All") == "全部"

    def test_load_yaml(self, tmp_path: Path):
        f = tmp_path / "extra.yml"
        f.write_text("TestKey: 测试值\n", encoding="utf-8")
        try:
            from ruamel.yaml import YAML  # noqa: F401
            g = Glossary.load(f)
            assert g.lookup("TestKey") == "测试值"
        except ImportError:
            pytest.skip("ruamel.yaml not installed")
