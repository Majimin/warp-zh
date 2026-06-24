"""Git format-patch 操作封装。"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


class PatchResult:
    def __init__(self, success: bool, output: str, returncode: int = 0) -> None:
        self.success = success
        self.output = output
        self.returncode = returncode

    def __bool__(self) -> bool:
        return self.success

    def __repr__(self) -> str:
        return f"PatchResult(success={self.success}, rc={self.returncode})"


def _run(cmd: list[str], cwd: Optional[Path] = None) -> PatchResult:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=60,
        )
        output = (result.stdout + result.stderr).strip()
        return PatchResult(success=result.returncode == 0,
                           output=output, returncode=result.returncode)
    except FileNotFoundError as e:
        return PatchResult(False, f"命令未找到: {e}", -1)
    except subprocess.TimeoutExpired:
        return PatchResult(False, "超时", -1)


def check_warp_repo(warp_root: Path) -> tuple[bool, str]:
    if not warp_root.exists():
        return False, f"目录不存在: {warp_root}"
    if not (warp_root / ".git").exists():
        return False, f"非 git 仓库: {warp_root}"
    cargo = warp_root / "Cargo.toml"
    if cargo.exists():
        content = cargo.read_text(encoding="utf-8", errors="replace").lower()
        if "warp" in content:
            return True, "✓ 确认为 warp 仓库"
        return True, "✓ 检测到 Cargo.toml"
    return False, f"警告：{warp_root} 可能不是 warp 仓库"


def get_current_sha(warp_root: Path) -> Optional[str]:
    result = _run(["git", "rev-parse", "HEAD"], cwd=warp_root)
    return result.output.strip() if result.success else None


def apply_patch(
    patch_file: Path,
    warp_root: Path,
    check_only: bool = False,
    three_way: bool = True,
) -> PatchResult:
    if not patch_file.exists():
        return PatchResult(False, f"补丁文件不存在: {patch_file}")
    cmd = ["git", "apply"]
    if check_only:
        cmd.append("--check")
    if three_way:
        cmd.append("--3way")
    cmd.extend(["--whitespace=nowarn", str(patch_file)])
    return _run(cmd, cwd=warp_root)


def check_patch(patch_file: Path, warp_root: Path) -> PatchResult:
    return apply_patch(patch_file, warp_root, check_only=True)


def generate_patch(
    warp_root: Path,
    output_file: Path,
    base_commit: Optional[str] = None,
) -> PatchResult:
    stage = _run(["git", "add", "-A"], cwd=warp_root)
    if not stage.success:
        return stage
    base = base_commit or "HEAD"
    return _run(
        ["git", "diff", "--cached", base, "--output", str(output_file)],
        cwd=warp_root,
    )


def get_patch_stat(patch_file: Path, warp_root: Path) -> Optional[str]:
    if not patch_file.exists():
        return None
    result = _run(["git", "apply", "--stat", str(patch_file)], cwd=warp_root)
    return result.output if result.success else None
