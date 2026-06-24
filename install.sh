#!/usr/bin/env bash
set -euo pipefail
REPO="https://github.com/Majimin/warp-zh.git"
echo "==============================="
echo "  warp-zh 汉化补丁安装程序"
echo "==============================="
if ! command -v python3 &>/dev/null; then
    echo "错误：需要 Python 3.11+"; exit 1
fi
PY_OK=$(python3 -c "import sys; print('ok' if sys.version_info >= (3,11) else 'fail')")
if [ "$PY_OK" != "ok" ]; then
    echo "错误：需要 Python 3.11+"; python3 --version; exit 1
fi
echo "正在安装 warp-zh..."
pip install --quiet "git+${REPO}"
echo ""
echo "✓ 安装完成！"
echo ""
echo "使用方法："
echo "  warp-zh apply /path/to/warp-source"
echo "  warp-zh apply /path/to/warp-source --dry-run"
echo "  warp-zh status /path/to/warp-source"
echo "  warp-zh revert /path/to/warp-source"
