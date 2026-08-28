#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info-extract · 协同能力自检（D9 / 流程规范 §6）。

复用 summarize 的 skill_bridge 思路：按 capabilities 关键词泛匹配已安装技能的
SKILL.md（name/description/tags），判定各协同能力是否可用；命中即调、缺失即降级。
当前关注三类协同：
- desensitization（DESEN，上云脱敏闸门，§4.4）
- document_text（原生文本层抽取，分工 D10）
- browser（在线视频捕获，阶段五）

纯标准库、离线、缺失不报错。
"""

from __future__ import annotations

import os
import re
from typing import Dict, Optional

# 协同能力清单（关键词与 summarize capabilities.json 对齐，子集）
COOP_CAPS = {
    "desensitization": ["脱敏", "desensitiz", "敏感信息", "sensitive", "去标识"],
    "document_text": ["文档", "document", "office", "pdf", "word", "ppt", "wps"],
    "browser": ["browser", "浏览器", "网页", "web", "捕获"],
}

SKILL_ROOTS = [
    os.path.expanduser("~/.workbuddy/skills"),
    os.path.expanduser("~/.claude/skills"),
    os.path.expanduser("~/.codex/skills"),
    os.path.expanduser("~/.openclaw/skills"),
]


def _load_skill_text(skill_dir: str) -> str:
    md = os.path.join(skill_dir, "SKILL.md")
    if os.path.isfile(md):
        try:
            with open(md, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    return ""


def _match_capability(keywords) -> Optional[str]:
    """扫描各技能根目录，返回首个匹配该能力关键词的技能名（无则 None）。"""
    for root in SKILL_ROOTS:
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            skill_dir = os.path.join(root, name)
            if not os.path.isdir(skill_dir):
                continue
            text = _load_skill_text(skill_dir).lower()
            if not text:
                continue
            for kw in keywords:
                if kw.lower() in text:
                    return name
    return None


def self_check(caps: Optional[list] = None) -> Dict[str, Optional[str]]:
    """返回 {能力: 已安装技能名或 None}。"""
    caps = caps or list(COOP_CAPS.keys())
    return {cap: _match_capability(COOP_CAPS[cap]) for cap in caps}


def has_desensitization() -> bool:
    return self_check(["desensitization"])["desensitization"] is not None


if __name__ == "__main__":
    import json

    print(json.dumps(self_check(), ensure_ascii=False, indent=2))


__all__ = ["COOP_CAPS", "self_check", "has_desensitization"]
