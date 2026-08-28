#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info-extract · 跨模块基础契约与接口。

本文件只依赖标准库，是各能力域模块共享的最小契约来源：
- SourceType：资料来源类型（ocr / vision / transcript / doc_extract / video_online）。
- Segment：带时间戳的片段（音频/视频文案的基本单位）。
- ExtractResult：标准输出契约对象（D11），下游 summarize / knowledge_base / translation 可直接消费。
- IModule：能力域模块统一接口（按需载入，D8）。

设计原则（呼应方案 §0.6 / §3.6 / 流程规范 §4.6）：
- 所有模块产出统一为 ExtractResult，落「双通道」（纯文本 .txt + 结构化 .json/.md）。
- provider_meta 透明回显「用了谁、是否上云」（D15 / 流程规范 §4.7）。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


class SourceType:
    """资料来源类型常量。"""

    OCR = "ocr"
    VISION = "vision"
    TRANSCRIPT = "transcript"
    DOC_EXTRACT = "doc_extract"
    VIDEO_ONLINE = "video_online"


@dataclass
class Segment:
    """带时间戳的片段（音频转录 / 视频文案的基本单位）。"""

    start: float  # 秒，相对整段素材
    end: float  # 秒
    text: str
    words: List[Dict[str, Any]] = field(default_factory=list)  # [{word,start,end,prob}]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractResult:
    """标准输出契约对象（方案 §3.6 / 流程规范 §4.6，D11）。

    双通道：
    - 纯文本通道：text（可直接喂 summarize）。
    - 结构化通道：to_contract() 的字段（source/confidence/fields/media_ref/...）。
    """

    source: str  # ocr / vision / transcript
    text: str  # 纯文本主体
    confidence: Optional[float] = None  # 平均置信度 / 不确定项清单
    fields: Dict[str, Any] = field(default_factory=dict)  # 抽取关键字段（语言/时长等）
    media_ref: Dict[str, Any] = field(default_factory=dict)  # 来源文件/时间戳/页码，便于溯源
    referenced_frame: Optional[Dict[str, Any]] = None  # 视频专属（D13）
    provider_meta: Dict[str, Any] = field(default_factory=dict)  # D15 透明回显
    segments: List[Segment] = field(default_factory=list)  # 带时间戳片段（供 srt/txt 通道）

    def to_contract(self) -> Dict[str, Any]:
        """序列化为结构化通道字典（供 JSON / MD 输出）。"""
        return {
            "source": self.source,
            "text": self.text,
            "confidence": self.confidence,
            "fields": self.fields,
            "media_ref": self.media_ref,
            "referenced_frame": self.referenced_frame,
            "provider_meta": self.provider_meta,
        }


class InfoExtractError(Exception):
    """info-extract 统一异常，便于 router 区分「本技能可处理的失败」与系统错误。"""

    def __init__(self, message: str, *, recoverable: bool = True, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.recoverable = recoverable  # True=用户可本地补充/换 provider 解决
        self.hint = hint  # 给用户的可执行建议


class IModule:
    """能力域模块统一接口（D8 按需载入）。

    主入口 router 仅做「类型识别 + 路由」，仅在命中某类型时才 import 对应模块、
    调用 run()。未命中类型不预载对应重型依赖（如 Whisper / VLM）。
    """

    name: str = ""
    source_type: str = ""
    # 是否已实现（阶段未到的能力域置 False，router 给出清晰提示而非静默失败，D9/D15）
    ready: bool = True

    def run(self, inputs: List[str], options: Dict[str, Any]) -> List[ExtractResult]:
        """处理一批同类型输入，返回 ExtractResult 列表。

        inputs：已校验存在的文件路径列表。
        options：来自 router 的全局选项（lang / task / model / provider / out_dir / ...）。
        """
        raise NotImplementedError


__all__ = [
    "SourceType",
    "Segment",
    "ExtractResult",
    "InfoExtractError",
    "IModule",
]
