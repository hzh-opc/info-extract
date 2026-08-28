# AGENT_INSTALL.md · info-extract

> 供 Agent / 用户安装与验证本技能的标准指引（跨平台基线，对应 4 级沉淀「config/技能」级）。

## 1. 运行环境要求

- **Python**：标准 CPython **≥3.10 且 <3.14**（onnxruntime 无 free-threaded wheel），锁定 **3.13**。
- **操作系统**：Windows / macOS / Linux；架构 x86_64 与 aarch64（Apple Silicon / ARM）。
- **系统依赖**：**无需系统 ffmpeg**。音频解码使用 PyAV（`av`，自带 ffmpeg 库），OCR 阶段（规划中）用 rapidocr（模型随 wheel 捆绑）。
- **磁盘**：阶段一约 0.5–1 GB（含 Whisper small 模型首次运行时下载，~466 MB）；后续阶段按需增加。

## 2. 安装（一键，隔离 venv）

```bash
# 方式 A：Python 安装脚本（跨平台，推荐）
python3 install.py

# 方式 B：Shell 安装脚本（Linux/macOS）
./install.sh
```

安装脚本会：
1. 在 `scripts/.venv` 创建隔离 venv（可用 `--python /path` 复用现有 3.13 解释器，或 `--venv /path` 指定目录）；
2. 安装 `requirements.txt` 依赖（numpy / av / faster-whisper）；
3. 运行 `--check` 冒烟自检（能力/provider 可用性 + 导入健康度）；
4. 打印完成信息与使用命令。

> 隔离原则：依赖只装进技能私有 `.venv`，**不污染系统 / 用户环境**（与 DESEN 同构）。

## 3. 用法

```bash
# 转录单个音频（自动识别类型 → 音频模块）
python scripts/router.py 录音.mp3
# 批量目录 + 递归 + 指定输出
python scripts/router.py ./音频 --recursive --out ./结果
# 语言/任务轻提示 + 升级模型
python scripts/router.py 会议.m4a --lang 日文 --model medium
# 仅自检
python scripts/router.py --check
```

## 4. 跨平台注意

| 项 | Windows | macOS | Linux |
|----|---------|-------|-------|
| venv | `python -m venv` | 同 | 同（headless 需确保 `build-essential` 类工具链用于编译可选包） |
| 音频解码 | PyAV 自带 ffmpeg ✅ | 同 | 同（无需系统 ffmpeg） |
| Whisper 加速 | CUDA / DirectML | Metal（CoreML 经 CTranslate2） | CUDA / OpenVINO |
| 路径/编码 | 用正斜杠或引号包裹空格路径 | 同 | 同 |

## 5. 验证（Agent 可运行）

```bash
python tests/verify_phase1.py
```

该脚本用合成音频验证：VAD 分块、类型识别、哈希缓存、输出契约、provider 可用性检测、全链路（mock 推理）+ `--check` 自检，无需下载 Whisper 模型即可确认阶段一逻辑正确。

## 6. 卸载

删除技能目录（`~/.workbuddy/skills/info-extract` 软链与其指向的 `~/Repositories/info-extract`）即可；`.venv`/`.cache`/`.tmp` 均为可重建的本地产物。
