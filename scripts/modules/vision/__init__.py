#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画面内容识别与解读模块（阶段四，规划中）。

阶段四接入本地 VLM（档位自适应 D7），与视频帧共用视觉栈（方案 §3 阶段四）。
本占位模块确保 router 对画面解读请求给出清晰「规划中」提示（D9/D15）。
"""

from __future__ import annotations

from typing import Any, Dict, List

from modules.base import ExtractResult, IModule, SourceType

PHASE = "阶段四（规划中）"


class VisionModule(IModule):
    name = "vision"
    source_type = SourceType.VISION
    ready = False

    def run(self, inputs: List[str], options: Dict[str, Any]) -> List[ExtractResult]:
        return [
            ExtractResult(
                source=SourceType.VISION,
                text="",
                media_ref={"path": p, "status": "planned", "phase": PHASE},
            )
            for p in inputs
        ]


__all__ = ["VisionModule"]
