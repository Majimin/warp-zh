"""生成 rust-i18n 兼容的 locale YAML 文件。"""
from __future__ import annotations

from pathlib import Path

from .models import TranslationMemory


def write_locales(
    memory: TranslationMemory,
    output_dir: Path,
    source_locale: str = "en",
    target_locale: str = "zh-CN",
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_dict: dict[str, str] = {}
    target_dict: dict[str, str] = {}

    for unit in memory.units:
        key = f"{unit.entry.context}.{unit.entry.key}"
        source_dict[key] = unit.entry.source_text
        target_dict[key] = unit.target_text or unit.entry.source_text

    en_path = output_dir / f"{source_locale}.yml"
    zh_path = output_dir / f"{target_locale}.yml"

    try:
        import io
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.allow_unicode = True
        yaml.default_flow_style = False
        yaml.width = 120
        for path, data in [(en_path, source_dict), (zh_path, target_dict)]:
            buf = io.StringIO()
            yaml.dump(data, buf)
            path.write_text(buf.getvalue(), encoding="utf-8")
    except ImportError:
        for path, data in [(en_path, source_dict), (zh_path, target_dict)]:
            lines = [f"{k}: {_yaml_str(v)}\n" for k, v in data.items()]
            path.write_text("".join(lines), encoding="utf-8")

    return en_path, zh_path


def _yaml_str(s: str) -> str:
    needs_quote = any(c in s for c in ':#{}[],&*?|<>=!%@`\'"\\')
    if needs_quote or s.startswith(" ") or s.endswith(" "):
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s
