"""配置加载与默认值。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class WarpZhConfig:
    """warp-zh 全局配置。"""
    locale: str = "zh-CN"
    warp_upstream_sha: str = "f7e1d9da06230a32ae650e6d8aa805424252e2a4"
    glossary_path: Path = Path("data/glossary.zh-CN.yml")
    overrides_path: Path = Path("data/overrides.zh-CN.yml")
    patches_dir: Path = Path("patches")
    call_site_patterns: list[str] = field(default_factory=lambda: [
        "ActionButton::new",
        "CompactibleActionButton::new",
        ".with_tooltip(",
        ".with_title(",
        ".with_label(",
        ".with_placeholder(",
        ".with_header(",
        ".with_description(",
        ".with_text(",
        ".text(",
        "tooltip!(",
        "label!(",
        "title!(",
        "menu_item!(",
        "button!(",
    ])
    skip_patterns: list[str] = field(default_factory=lambda: [
        "://",
        "{:?}",
        "RUST_LOG",
        "warp-",
        ".rs",
        "\\n",
        "\\t",
    ])
    min_length: int = 2
    source_dirs: list[str] = field(default_factory=lambda: [
        "app/src",
        "crates",
    ])


def load_config(path: Optional[Path] = None) -> WarpZhConfig:
    """从 YAML 文件加载配置，文件不存在时返回默认配置。"""
    cfg = WarpZhConfig()
    if path is None or not path.exists():
        return cfg
    try:
        from ruamel.yaml import YAML
        yaml = YAML()
        data = yaml.load(path)
        if isinstance(data, dict):
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
    except ImportError:
        pass
    return cfg
