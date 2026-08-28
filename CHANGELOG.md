# CHANGELOG · info-extract

## [0.1.0] — 2026-08-28 · 三仓库初始化 + 阶段一落地

### 新增
- **三处仓库初始化**（方案 §0 / D5）：本地仓库 `~/Repositories/info-extract`（git 源）建好；技能仓库 `~/.workbuddy/skills/info-extract` 软链到本地仓库（干净部署副本）；工作空间保留规划文档与开发记忆。
- **技能骨架（D8/D9/D11/D15）**：
  - 主入口 `scripts/router.py`：类型识别 + 按需路由（命中类型才加载模块，未命中不预载重型依赖）。
  - `provider_registry.py`：可插拔 Provider 注册表（默认本地优先、显式指定覆盖、全不可用降级）。
  - `quality_scorer.py`：质量评分驱动自动升级。
  - `skill_bridge.py`：协同能力自检（DESEN/document_text/browser，D9）。
  - `utils`：io（发现+类型识别）、hash_cache（D12·L）、tmp（D12·G 隐私闭环）。
  - `base.py`：标准输出契约 `ExtractResult`（D11 双通道 source/confidence/fields/media_ref/provider_meta）。
  - `SKILL.md` 暴露 `ocr`/`speech_transcription`/`video_transcript` 关键词（D9）；`assets/capabilities.json` 声明能力（含 `ready` 标志）。
- **阶段一 · 音频转录（已实现）**：
  - 本地 Whisper 转录 + 时间戳（SRT/TXT）+ 结构化 JSON/MD（D11）。
  - `FasterWhisperProvider`（默认，faster-whisper，离线）+ `WhisperCppProvider`（可选二进制）。
  - VAD/静音分块长音频（D12·J，内存切片、不落盘临时分块）。
  - 语言/任务轻提示（文件名/对话 hint，D12·K）。
  - 批量输入 + 聚合报告（D12·H，含异常清单）。
  - 哈希缓存（D12·L）、provider_meta 透明回显（D15/§4.7）。
  - 音频解码用 PyAV（自带 ffmpeg），免去系统 ffmpeg 依赖。
- **占位模块**：OCR / 视觉 / 文档抽取 / 在线视频 先置惰性桩，命中即清晰提示「规划中」，不静默失败（D9/D15）。

### 决策落实
- D1–D15 全部收敛（见 `info-extract-方案.md` §5）。
- 复用 DESEN 的 venv/安装范式（CPython 3.13 锁定、隔离 venv、依赖不污染系统）。

### 待办（后续阶段）
- 阶段二/五：视频文案（ffmpeg 抽轨复用音频）、在线/加密视频受限场景。
- 阶段三：OCR（rapidocr+onnxruntime）、PDF 类型探测分流、图像预处理+置信度门控上云。
- 阶段四：本地 VLM 画面解读（档位自适应 D7），与视频帧共用视觉栈。
