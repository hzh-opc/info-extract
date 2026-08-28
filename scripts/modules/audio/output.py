#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info-extract · 音频转录输出契约（D11 双通道 + 时间戳）。

- 纯文本通道 .txt：可直接喂 summarize 做摘要。
- 结构化通道 .json：ExtractResult.to_contract()，供归档/知识库/翻译消费。
- 字幕通道 .srt：带时间戳，便于字幕/跳转。
- 可读通道 .md：带来源/置信度/字段/provider 标注，供用户核验（流程规范 §4.1）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from modules.base import ExtractResult, Segment
from utils.io import format_seconds


def _srt_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    s = ms // 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms % 1000:03d}"


def segments_to_srt(segments: List[Segment]) -> str:
    lines: List[str] = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_srt_ts(seg.start)} --> {_srt_ts(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def segments_to_txt(segments: List[Segment], with_ts: bool = True) -> str:
    out: List[str] = []
    for seg in segments:
        text = seg.text.strip()
        out.append(f"{format_seconds(seg.start)} {text}" if with_ts else text)
    return "\n".join(out)


def _to_md(result: ExtractResult) -> str:
    lines: List[str] = []
    lines.append(f"# 音频转录结果\n")
    lines.append(f"- **来源 (source)**：`{result.source}`")
    pm = result.provider_meta or {}
    lines.append(f"- **引擎 (provider)**：`{pm.get('provider', '?')}`（上云：{pm.get('cost', 'local')}）")
    if result.confidence is not None:
        lines.append(f"- **平均置信度 (confidence)**：{result.confidence:.3f}")
    if result.fields:
        lines.append("- **关键字段 (fields)**：")
        for k, v in result.fields.items():
            lines.append(f"  - {k}: {v}")
    if result.media_ref:
        lines.append("- **溯源 (media_ref)**：")
        for k, v in result.media_ref.items():
            lines.append(f"  - {k}: {v}")
    lines.append("")
    lines.append("## 带时间戳转录（请核对标★的关键信息）\n")
    lines.append(segments_to_txt(result.segments, with_ts=True))
    return "\n".join(lines) + "\n"


def write_outputs(
    result: ExtractResult,
    out_dir: str | Path,
    stem: str,
    formats: Tuple[str, ...] = ("txt", "srt", "json", "md"),
) -> Dict[str, str]:
    """把结果落到双通道（含字幕与可读 MD）。返回 {格式: 路径}。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, str] = {}

    if "txt" in formats:
        p = out_dir / f"{stem}.txt"
        p.write_text(segments_to_txt(result.segments, with_ts=True), encoding="utf-8")
        written["txt"] = str(p)
    if "srt" in formats:
        p = out_dir / f"{stem}.srt"
        p.write_text(segments_to_srt(result.segments), encoding="utf-8")
        written["srt"] = str(p)
    if "json" in formats:
        p = out_dir / f"{stem}.json"
        p.write_text(
            json.dumps(result.to_contract(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        written["json"] = str(p)
    if "md" in formats:
        p = out_dir / f"{stem}.md"
        p.write_text(_to_md(result), encoding="utf-8")
        written["md"] = str(p)
    return written


__all__ = [
    "segments_to_srt", "segments_to_txt", "_to_md", "write_outputs",
]
