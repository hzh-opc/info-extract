---
name: info-extract
description: "跨智能体、跨平台的信息抽取技能：本地优先抽取 OCR 文字 / 音频转录（语音转写、字幕）/ 视频文案 / 图片与视频画面解读。当前已实现音频转录（speech_transcription）与视频文案（video_transcript，ffmpeg 抽音轨复用 Whisper + D13 讲解段关联帧）；OCR（ocr）、画面解读为规划中能力，将在后续阶段接入。所有处理默认在本地完成、默认不上云；支持按类型自动路由与按需载入，可对接脱敏技能（DESEN）做上云前脱敏。触发词：提取文字 / 转录 / 转写 / 语音转文字 / 听写 / 字幕生成 / 视频文案 / 视频转文字 / 图片转文字 / 截图转文字。"
version: "0.1.0"
agent_created: true
tags: [ocr, speech_transcription, video_transcript, image_understanding, 信息抽取, 转录, 字幕, 本地优先, 隐私]
---

# info-extract · 信息抽取技能

> **定位**：跨智能体（WorkBuddy / Claude / Codex / OpenClaw 等）、跨平台（Windows / macOS / Linux）的本地优先信息抽取技能，覆盖 OCR、音频转录、视频提取、画面解读四大能力域。
> **核心原则**：本地优先 · 默认不上云 · 机器结果须经你确认（方案 §4 / 流程规范 §1）。
> **当前阶段**：阶段一 · 音频转录（已实现）+ 阶段二 · 视频文案（已实现：ffmpeg/PyAV 抽音轨复用 Whisper 转录 + D13 讲解段关联帧抽取）；OCR / 画面解读（阶段三~四）、在线/加密视频（阶段五）规划中。

## 一、能做什么（能力域）

| 能力域 | 状态 | 说明 |
|--------|------|------|
| ① 音频转录（speech_transcription） | ✅ 已实现（阶段一） | 本地 Whisper 转录+时间戳；长音频 VAD 分块；外语/方言轻提示；批量+聚合报告；双通道输出 |
| ② 图片 OCR（ocr） | 🔜 规划中（阶段三） | rapidocr + onnxruntime（PP-OCRv6），图像预处理+置信度门控上云、PDF 类型探测分流 |
| ③ 图片/视频画面解读（image_understanding） | 🔜 规划中（阶段四） | 本地 VLM（档位自适应 D7），与视频帧共用视觉栈 |
| ④ 视频文案（video_transcript） | ✅ 已实现（阶段二） | 本地 ffmpeg(PyAV) 抽音轨 → 复用 Whisper 转录；D13 讲解段关联帧抽取（标准库 PNG 写出，零新依赖）；在线/加密视频见阶段五 |

## 二、怎么用（对话式，无需参数）

把音频交给本技能即可，例如：
- 「帮我把这段录音转成文字，并标出时间」
- 「转录这个会议录音，这是日文采访」
- 「把这摞音频都转写一下」（批量，审阅 H）

底层引擎默认本地 Whisper（small）；噪声明/方言可说「用 medium 模型」升级。所有处理默认在本地、不上云。

## 三、命令行（高级/批量）

技能目录 `scripts/` 下主入口 `router.py`：

```bash
# 转录单个音频（自动识别类型）
python router.py 录音.mp3
# 批量目录 + 递归 + 指定输出目录
python router.py ./音频 --recursive --out ./结果
# 语言/任务轻提示 + 升级模型
python router.py 会议.m4a --lang 日文 --model medium
# 仅自检能力/provider 可用性
python router.py --check
# 机器可读输出
python router.py 录音.mp3 --json

# 视频文案提取（抽音轨 → 转录，阶段二）
python router.py 课程.mp4
# 仅文案、不抽讲解画面帧（D13）
python router.py 课程.mp4 --no-frames
# 视频同样支持语言/模型轻提示与批量
python router.py ./视频 --recursive --lang 日文
```

## 四、架构要点（按需载入 + 可插拔 Provider）

- **按需载入（D8）**：主入口仅做类型识别+路由，仅命中类型才加载对应模块，未命中不预载 Whisper/VLM 等重型依赖。
- **可插拔 Provider（D15）**：各能力域底层引擎为可替换 Provider（本地内置/本地增强/云端/外部技能/连接器），默认本地优先，涉及上云/外部调用须经你确认；产出 `provider_meta` 透明回显「用了谁、是否上云」。
- **双通道输出（D11）**：纯文本 `.txt` + 结构化 `.json`/`.md` + 字幕 `.srt`，下游 summarize/知识库/翻译可直接消费。
- **能力声明（D9）**：本 SKILL.md 已暴露 `ocr`/`speech_transcription`/`video_transcript` 关键词，供 `summarize` 的 skill_bridge 自动发现；当前 `speech_transcription` 与 `video_transcript` 已就绪，OCR 为规划中（命中后给出清晰提示，不静默失败）。
- **隐私闭环（§4）**：敏感预检贯穿到上云门前强制脱敏（已装 DESEN 则调用、未装则提示）；临时文件私有 tmp、处理后即清（审阅 G）。

## 五、安装与跨平台

参见 `AGENT_INSTALL.md`（Agent 安装指引）与 `install.py`/`install.sh`（一键建隔离 venv 并安装依赖）。
运行要求：标准 CPython ≥3.10 且 <3.14（锁定 3.13）；音频解码用 PyAV（自带 ffmpeg，无需系统安装 ffmpeg）。

详细设计、模块契约、Provider 接口见 `references/reference.md`；决策记录见 `CHANGELOG.md`。
