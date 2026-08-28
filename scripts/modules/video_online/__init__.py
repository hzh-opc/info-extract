#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频文案提取 / 在线·加密视频模块（阶段二/五，规划中）。

阶段二：ffmpeg 抽音轨 → 复用音频转录；阶段五：受限场景（yt-dlp / 浏览器捕获）。
本占位模块确保 router 对视频输入给出清晰「规划中」提示（D9/D15）。
"""

from __future__ import annotations

from typing import Any, Dict, List

from modules.base import ExtractResult, IModule, SourceType

PHASE = "阶段二/五（规划中）"


class VideoOnlineModule(IModule):
    name = "video_online"
    source_type = SourceType.VIDEO_ONLINE
    ready = False

    def run(self, inputs: List[str], options: Dict[str, Any]) -> List[ExtractResult]:
        return [
            ExtractResult(
                source=SourceType.VIDEO_ONLINE,
                text="",
                media_ref={"path": p, "status": "planned", "phase": PHASE},
            )
            for p in inputs
        ]


__all__ = ["VideoOnlineModule"]
