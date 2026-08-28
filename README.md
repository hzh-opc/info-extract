# info-extract · 信息抽取技能

跨智能体（WorkBuddy / Claude / Codex / OpenClaw）、跨平台（Windows / macOS / Linux）的**本地优先**信息抽取技能，覆盖 OCR、音频转录、视频提取、画面解读四大能力域。

> **核心原则**：本地优先 · 默认不上云 · 机器结果须经你确认。

## 仓库结构（三处仓库）

| 仓库 | 路径 | 职责 |
|------|------|------|
| 技能仓库 | `~/.workbuddy/skills/info-extract`（软链到本地仓库） | 部署 / 干净副本 |
| 本地仓库 | `~/Repositories/info-extract`（本目录，git 源） | 开发副本 / GitHub 唯一提交副本 |
| 工作空间 | `~/WorkBuddy/Skill-Dev/info-extract` | 开发记忆 + 隐私隔离（规划文档/日志） |

## 能力域与阶段

| 阶段 | 能力域 | 状态 |
|------|--------|------|
| 一 | 音频转录（speech_transcription） | ✅ 已实现 |
| 二 | 视频文案提取（video_transcript） | 🔜 规划中 |
| 三 | OCR（ocr） | 🔜 规划中 |
| 四 | 画面解读（image_understanding） | 🔜 规划中 |
| 五 | 受限场景（在线/加密视频） | 🔜 规划中 |

## 快速开始

```bash
# 1) 安装（建隔离 venv + 依赖）
python install.py            # 或 ./install.sh

# 2) 转录音频
python scripts/router.py 录音.mp3
python scripts/router.py ./音频目录 --recursive --out ./结果
```

详见 `SKILL.md`、`AGENT_INSTALL.md`、`CHANGELOG.md`、`references/reference.md`。
