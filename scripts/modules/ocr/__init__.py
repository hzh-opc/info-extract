#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR 模块（阶段三，规划中）。

阶段一仅落地音频转录；OCR 将在阶段三接入 rapidocr + onnxruntime（PP-OCRv6），
含图像预处理链 + 置信度门控上云、PDF 类型探测分流、哈希缓存等（方案 §3 阶段三 / D12）。
本占位模块确保 router 对图片/文档输入给出清晰「规划中」提示，而非静默失败（D9/D15）。
"""

from __future__ import annotations

from typing import Any, Dict, List

from modules.base import ExtractResult, IModule, SourceType

PHASE = "阶段三（规划中）"


class OCRModule(IModule):
    name = "ocr"
    source_type = SourceType.OCR
    ready = False

    def run(self, inputs: List[str], options: Dict[str, Any]) -> List[ExtractResult]:
        return [
            ExtractResult(
                source=SourceType.OCR,
                text="",
                media_ref={"path": p, "status": "planned", "phase": PHASE},
            )
            for p in inputs
        ]


__all__ = ["OCRModule"]
