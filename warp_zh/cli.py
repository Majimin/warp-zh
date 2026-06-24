"""Typer CLI 入口：warp-zh apply / status / revert / extract / patch."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import load_config
from .codemod import apply_to_dir, revert_dir
from .extractor import extract_from_dir
from .glossary import Glossary
from .models import TranslationMemory, TranslationUnit
from .patcher import apply_patch, check_patch, check_warp_repo, get_patch_stat
from .translator import Translator

app = typer.Typer(
    name="warp-zh",
    help="Warp 终端简体中文汉化工具链 🇨🇳",
    rich_markup_mode="markdown",
    no_args_is_help=True,
)
console = Console()


def _version_cb(value: bool) -> None:
    if value:
        console.print(f"warp-zh [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def _cb(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V",
        callback=_version_cb, is_eager=True,
        help="显示版本号",
    ),
) -> None:
    """Warp 终端简体中文汉化工具。"""


@app.command()
def apply(
    warp_dir: Path = typer.Argument(..., help="warp 源码目录路径"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="预览变更，不写盘"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """🚀 应用汉化到 warp 源码（优先 git patch，降级到 codemod）。"""
    warp_root = warp_dir.expanduser().resolve()
    ok, msg = check_warp_repo(warp_root)
    if not ok:
        console.print(f"[red]错误：{msg}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]{msg}[/green]")

    cfg = load_config(config)

    # 路径 1：git format-patch（快速、精确）
    patch_dir = Path(__file__).parent.parent / "patches"
    patch_file = patch_dir / "0001-zh-CN-core-ui.patch"

    if patch_file.exists():
        console.print(f"\n[bold cyan]使用预制补丁[/bold cyan]：{patch_file.name}")
        stat = get_patch_stat(patch_file, warp_root)
        if stat:
            console.print(f"[dim]{stat}[/dim]")
        chk = check_patch(patch_file, warp_root)
        if chk.success:
            if dry_run:
                console.print("[yellow]--dry-run：补丁兼容，未写入。[/yellow]")
                raise typer.Exit(0)
            res = apply_patch(patch_file, warp_root)
            if res.success:
                console.print("[bold green]✓ 补丁应用成功！[/bold green]")
                _next_steps(warp_root)
                raise typer.Exit(0)
            else:
                console.print(f"[yellow]补丁失败，降级到 codemod…[/yellow]\n[dim]{res.output[:120]}[/dim]")
        else:
            console.print("[yellow]补丁与当前源码不兼容，降级到 codemod…[/yellow]")

    # 路径 2：逐文件 codemod（兼容任意版本）
    console.print("\n[bold cyan]运行字符串提取器…[/bold cyan]")
    entries = extract_from_dir(warp_root, cfg)
    if not entries:
        console.print("[yellow]未找到可提取的字符串。请确认 warp 目录结构正确。[/yellow]")
        raise typer.Exit(1)
    console.print(f"  提取到 [bold]{len(entries)}[/bold] 条候选字符串")

    glossary = Glossary.load(
        cfg.glossary_path,
        cfg.overrides_path if cfg.overrides_path.exists() else None,
    )
    translator = Translator(glossary)
    memory = TranslationMemory()
    for e in entries:
        memory.add(TranslationUnit(entry=e))

    stats = translator.translate_memory(memory)
    console.print(
        f"  翻译：[green]{stats['translated']}[/green] 条，"
        f"跳过：[dim]{stats['skipped']}[/dim] 条"
    )

    translated = [u for u in memory.units if u.is_translated]
    if not translated:
        console.print("[red]术语表中无匹配译文，请检查 data/glossary.zh-CN.yml。[/red]")
        raise typer.Exit(1)

    results = apply_to_dir(warp_root, translated, dry_run=dry_run)
    n_replaced = sum(r.replaced for r in results)
    n_files    = sum(1 for r in results if r.replaced > 0)

    if dry_run:
        console.print(
            f"\n[yellow]--dry-run：将改写 [bold]{n_replaced}[/bold] 处，"
            f"涉及 [bold]{n_files}[/bold] 个文件（未写盘）。[/yellow]"
        )
    else:
        console.print(
            f"\n[bold green]✓ 汉化完成！[/bold green] "
            f"改写 [bold]{n_replaced}[/bold] 处，涉及 [bold]{n_files}[/bold] 个文件。"
        )
        _next_steps(warp_root)


@app.command()
def status(
    warp_dir: Path = typer.Argument(..., help="warp 源码目录路径"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """📊 查看汉化覆盖率报告。"""
    warp_root = warp_dir.expanduser().resolve()
    ok, msg = check_warp_repo(warp_root)
    if not ok:
        console.print(f"[red]错误：{msg}[/red]")
        raise typer.Exit(1)

    cfg = load_config(config)
    entries = extract_from_dir(warp_root, cfg)
    if not entries:
        console.print("[yellow]未找到可分析的字符串。[/yellow]")
        raise typer.Exit(0)

    glossary = Glossary.load(cfg.glossary_path)
    translator = Translator(glossary)
    memory = TranslationMemory()
    for e in entries:
        memory.add(TranslationUnit(entry=e))
    translator.translate_memory(memory)

    summary  = memory.summary()
    coverage = memory.coverage

    tbl = Table(title="warp-zh 汉化覆盖率报告", show_header=True, header_style="bold cyan")
    tbl.add_column("状态", style="bold")
    tbl.add_column("数量", justify="right")
    tbl.add_row("已翻译（机翻）", str(summary.get("machine", 0)))
    tbl.add_row("已人工审校",     str(summary.get("reviewed", 0)))
    tbl.add_row("未翻译",         str(summary.get("untranslated", 0)))
    tbl.add_row("过期",           str(summary.get("stale", 0)))
    tbl.add_section()
    tbl.add_row("[bold]总计[/bold]",   f"[bold]{summary['total']}[/bold]")
    tbl.add_row("[bold]覆盖率[/bold]", f"[bold]{coverage:.1%}[/bold]")
    console.print(tbl)


@app.command()
def revert(
    warp_dir: Path = typer.Argument(..., help="warp 源码目录路径"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认提示"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """↩️  回滚汉化，恢复英文原文。"""
    warp_root = warp_dir.expanduser().resolve()
    ok, msg = check_warp_repo(warp_root)
    if not ok:
        console.print(f"[red]错误：{msg}[/red]")
        raise typer.Exit(1)

    if not yes:
        if not typer.confirm("确定要回滚全部汉化吗？"):
            console.print("已取消。")
            raise typer.Exit(0)

    cfg = load_config(config)
    entries = extract_from_dir(warp_root, cfg)
    glossary = Glossary.load(cfg.glossary_path)
    translator = Translator(glossary)
    memory = TranslationMemory()
    for e in entries:
        memory.add(TranslationUnit(entry=e))
    translator.translate_memory(memory)
    translated = [u for u in memory.units if u.is_translated]

    results = revert_dir(warp_root, translated)
    total = sum(results.values())
    console.print(f"[bold green]✓ 已回滚 {total} 处，涉及 {len(results)} 个文件。[/bold green]")


@app.command()
def extract(
    warp_dir: Path = typer.Argument(..., help="warp 源码目录路径"),
    output: Path = typer.Option(Path("extracted.yml"), "--output", "-o", help="输出 YAML 文件"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """🔍 提取所有待翻译字符串，输出为 YAML（供人工校对）。"""
    warp_root = warp_dir.expanduser().resolve()
    ok, msg = check_warp_repo(warp_root)
    if not ok:
        console.print(f"[red]错误：{msg}[/red]")
        raise typer.Exit(1)

    cfg = load_config(config)
    entries = extract_from_dir(warp_root, cfg)
    console.print(f"提取到 [bold]{len(entries)}[/bold] 条字符串")

    out: dict[str, str] = {str(e.key): e.source_text for e in entries}
    try:
        import io
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.allow_unicode = True
        buf = io.StringIO()
        yaml.dump(out, buf)
        output.write_text(buf.getvalue(), encoding="utf-8")
    except ImportError:
        lines = [f'{k}: "{v}"\n' for k, v in out.items()]
        output.write_text("".join(lines), encoding="utf-8")

    console.print(f"[green]已写入：{output}[/green]")


@app.command()
def patch(
    warp_dir: Path = typer.Argument(..., help="warp 源码目录路径"),
    patch_file: Optional[Path] = typer.Option(None, "--patch", "-p", help="指定补丁文件路径"),
    check_only: bool = typer.Option(False, "--check", help="只检查兼容性，不实际应用"),
) -> None:
    """🩹 直接应用 git format-patch 补丁（高级用法）。"""
    warp_root = warp_dir.expanduser().resolve()
    ok, msg = check_warp_repo(warp_root)
    if not ok:
        console.print(f"[red]错误：{msg}[/red]")
        raise typer.Exit(1)

    if patch_file is None:
        patch_dir = Path(__file__).parent.parent / "patches"
        patch_file = patch_dir / "0001-zh-CN-core-ui.patch"

    if not patch_file.exists():
        console.print(f"[red]补丁文件不存在：{patch_file}[/red]")
        raise typer.Exit(1)

    stat = get_patch_stat(patch_file, warp_root)
    if stat:
        console.print(f"[bold]补丁摘要：[/bold]\n[dim]{stat}[/dim]\n")

    if check_only:
        res = check_patch(patch_file, warp_root)
        if res.success:
            console.print("[green]✓ 补丁与当前源码兼容。[/green]")
        else:
            console.print(f"[red]✗ 不兼容：{res.output[:200]}[/red]")
            raise typer.Exit(1)
    else:
        res = apply_patch(patch_file, warp_root)
        if res.success:
            console.print("[bold green]✓ 补丁应用成功！[/bold green]")
            _next_steps(warp_root)
        else:
            console.print(f"[red]✗ 失败：{res.output[:200]}[/red]")
            raise typer.Exit(1)


def _next_steps(warp_root: Path) -> None:
    console.print(
        f"\n[bold]下一步：重新编译 warp[/bold]\n"
        f"  [cyan]cd {warp_root}[/cyan]\n"
        f"  [cyan]cargo build --release[/cyan]\n"
        f"  编译产物：[dim]target/release/warp[/dim]"
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
