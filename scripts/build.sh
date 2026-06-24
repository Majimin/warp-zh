#!/usr/bin/env bash
# warp-zh 构建脚本
set -euo pipefail
echo "=== warp-zh build ==="
pip install --quiet build
rm -rf dist/ build/ *.egg-info
python -m build
echo "构建完成！产物位于 dist/"
ls -lh dist/
