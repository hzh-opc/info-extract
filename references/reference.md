# info-extract · 设计参考（按需读取，不自动加载）

> 本文件是模块契约与架构的单一事实来源，供实现阶段参考；日常使用请看 `SKILL.md`。

## 1. 三处仓库与部署关系

- `~/Repositories/info-extract`：git 源（开发副本 / GitHub 唯一提交副本），含全部技能源码。
- `~/.workbuddy/skills/info-extract`：**软链**到本地仓库（部署=干净副本，永远与 git 同步，零漂移）。
- `~/WorkBuddy/Skill-Dev/info-extract`：工作空间，保留规划文档（`info-extract-*.md`）与开发记忆（`.workbuddy/memory`），**不存技能源码**。

> 决策：技能源码只在一处（本地仓库）维护，技能仓库用软链避免三份拷贝漂移。

## 2. 目录布局

```
scripts/
  router.py                # 主入口：类型识别 + 按需路由（D8）
  provider_registry.py     # Provider 注册表（D15）
  quality_scorer.py        # 质量评分（D15 自动升级依据）
  skill_bridge.py          # 协同能力自检（D9）
  modules/
    base.py                # SourceType / Segment / ExtractResult / IModule
    audio/                 # 阶段一（已实现）
      transcribe.py        # AudioModule 编排
      vad.py               # 音频加载(PyAV) + VAD 分块(D12·J)
      language.py          # 语言/任务轻提示(D12·K)
      output.py            # 双通道输出(D11) + SRT/TXT/JSON/MD
      providers/           # ITranscriptProvider + faster-whisper + whisper.cpp
    ocr/ vision/ doc_extract/ video_online/   # 占位桩（规划中）
  utils/
    io.py                  # 发现 + 类型识别
    hash_cache.py          # 哈希缓存(D12·L)
    tmp.py                 # 临时沙箱(D12·G)
```

## 3. 标准输出契约（D11）

每条结果 = `ExtractResult`：
- `source`：`ocr` / `vision` / `transcript`
- `text`：纯文本主体（喂 summarize 纯文本通道）
- `confidence`：平均置信度（音频=词级概率均值）
- `fields`：关键字段（检测语言 / 时长 / 模型 / 段数）
- `media_ref`：来源路径 / 时间戳 / 产出文件路径 / 状态
- `referenced_frame`：视频专属（D13，规划中）
- `provider_meta`：用了哪个 provider、是否上云（D15/§4.7 透明回显）

落盘双通道：`*.txt`（纯文本）、`*.srt`（字幕）、`*.json` + `*.md`（结构化，含 source/confidence/fields/media_ref/provider_meta）。批量时额外生成 `info-extract-transcript-report.{md,json}` 聚合报告（D12·H）。

## 4. Provider 可插拔（D15）

- 每个能力域一个统一接口（`ITranscriptProvider` 等），签名：输入(路径/ndarray + 语言/任务/约束) → 输出(Segment 列表 + info)。
- 来源分层：① 本地内置（faster-whisper/whisper.cpp）② 本地增强 ③ 云端 ④ 外部技能 ⑤ 连接器。
- 选择：默认本地优先；显式指定 > 自动；全不可用 → 首个 provider（available=False），调用方给降级提示，不静默失败。
- 涉及上云/外部调用 → 穿透交互确认门（⑧⑨）+ 上云前脱敏闸门（DESEN，§4.4）。

## 5. 关键实现决策

- **音频解码走 PyAV**：本机实测无系统 ffmpeg，PyAV 自带 ffmpeg 库，零系统依赖、离线、数据不出本机。
- **长音频分块不落盘**：faster-whisper 直接接受 float32 16k ndarray，故 VAD 分块在内存切片后直传，无需写临时 WAV（更省、更隐私）。
- **能力声明 vs 就绪**：SKILL.md 暴露 ocr/speech_transcription/video_transcript 关键词（D9 机器可发现）；但 `assets/capabilities.json` 用 `ready` 标志标注当前仅 `speech_transcription` 就绪，OCR/视频为规划中——命中规划中能力时模块给出清晰提示，不静默失败。
- **隐私闭环**：哈希缓存仅落本地私有 `.cache`；临时文件走 `TempSandbox`（默认 `.tmp`，处理后清理）；在线/加密视频场景 `keep=False` 强制不落盘（审阅 G）。

## 6. 后续阶段衔接

- 阶段二/五：视频 `ffmpeg` 抽音轨 → 复用 `audio` 模块；在线/加密走 `browser` 协同。
- 阶段三：OCR 接入 `rapidocr+onnxruntime`，`utils` 与 DESEN 共享栈；PDF 类型探测分流（审阅 E）。
- 阶段四：本地 VLM（档位自适应 D7），与视频帧共用视觉栈；图结构重建（D14）。
