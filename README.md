# warp-zh 🇨🇳
> Warp 终端简体中文汉化补丁 — 覆盖 51 个文件、343 处 UI 字符串
[![CI](https://github.com/Majimin/warp-zh/actions/workflows/test.yml/badge.svg)](https://github.com/Majimin/warp-zh/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)

## 快速安装
```bash
# 一键安装（macOS / Linux）
curl -fsSL https://raw.githubusercontent.com/Majimin/warp-zh/main/install.sh | bash
```
或使用 pip：
```bash
pip install git+https://github.com/Majimin/warp-zh.git
warp-zh apply /path/to/warp
```

## 使用方法
```bash
# 应用汉化（优先 git patch，降级到 codemod）
warp-zh apply ~/src/warp
# 预览变更（不写盘）
warp-zh apply ~/src/warp --dry-run
# 查看汉化覆盖率
warp-zh status ~/src/warp
# 回滚到英文
warp-zh revert ~/src/warp
# 提取字符串（高级）
warp-zh extract ~/src/warp --output extracted.yml
```

## 汉化版二进制打包指南

如果你想将汉化后的 Warp 源码直接打包生成二进制文件或安装包，可以按照以下步骤操作：

### 1. 克隆并应用汉化补丁
```bash
# 克隆官方 Warp 源码 (Warp 客户端现已开源)
git clone https://github.com/warpdotdev/warp ~/src/warp

# 应用汉化补丁
warp-zh apply ~/src/warp
```

### 2. 编译汉化版二进制
编译需要配置好 Rust 环境（stable 工具链）：
```bash
cd ~/src/warp
cargo build --release
# 编译完成后的二进制文件位于 target/release/warp
```

### 3. 生成安装包 (可选)

#### Linux (打包为 .deb)
使用 `cargo-deb` 快速打包：
```bash
cargo install cargo-deb
cargo deb
# 产物位于 target/debian/warp_*.deb
```

#### macOS (打包为 .app / .dmg)
使用 `cargo-bundle` 将二进制文件打包为应用包：
```bash
cargo install cargo-bundle
cargo bundle --release
```

## 汉化覆盖范围
| 模块 | 文件数 | 字符串数 |
|------|--------|---------|
| AI 助手管理面板 | 8 | 47 |
| 应用菜单栏 | 6 | 62 |
| 设置界面 | 12 | 89 |
| 标签页右键菜单 | 4 | 28 |
| 命令面板 | 5 | 38 |
| 终端内联横幅 | 7 | 41 |
| 代码审查 | 5 | 23 |
| 其他 | 4 | 15 |
| **合计** | **51** | **343** |

## 开发
```bash
git clone https://github.com/Majimin/warp-zh
cd warp-zh
pip install -e ".[dev]"
make test
```

## 许可证
工具链：MIT © Majimin | 上游 Warp：AGPL-3.0 © warpdotdev
