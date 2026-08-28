#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info-extract · Provider 注册表（D15 可插拔架构核心）。

按能力域登记可替换 Provider，主入口只按类型取 provider，不感知具体实现：
- 默认：返回第一个「可用」的 Provider（列表顺序即优先级 → 本地内置①优先）。
- 显式指定：用户指定 provider 名称优先于自动判定。
- 全不可用：返回列表中第一个（available()=False），由调用方给出降级提示，不静默失败。
后续阶段（OCR / 视觉 / 文档抽取 / 在线视频）按 §0.6 来源分层接入本地增强/云端/技能/连接器。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from modules.base import InfoExtractError, SourceType

# 注意：为避免与 modules.audio.transcribe（其又 import 本模块）形成循环依赖，
# 这里不在此模块加载时 import modules.audio，而是在首次调用时惰性构建注册表。
_REGISTRY: Optional[Dict] = None


def _build_registry() -> Dict:
    from modules.audio.providers import PROVIDERS as AUDIO_PROVIDERS

    return {
        SourceType.TRANSCRIPT: AUDIO_PROVIDERS,
        # 以下在对应阶段落地后接入：
        # SourceType.OCR: [RapidOcrProvider, ...]
        # SourceType.VISION: [LocalVLMProvider, ...]
        # SourceType.DOC_EXTRACT: [...]
        # SourceType.VIDEO_ONLINE: [...]
    }


def _registry() -> Dict:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


def register(capability: str, provider_cls, priority: int = 99) -> None:
    """扩展接入新 Provider（阶段落地时调用）。priority 越小越优先。"""
    reg = _registry()
    lst: List = reg.setdefault(capability, [])
    lst.append(provider_cls)
    # 简单按类名排序维持稳定；真实优先级由调用方在类上声明
    if priority < 99:
        lst.sort(key=lambda c: 0 if c.name == provider_cls.name else 1)


def get_provider(capability: str, name: Optional[str] = None):
    """取 provider 实例。

    name=None → 默认第一个可用的（本地优先）；
    name 指定 → 精确匹配；无匹配返回 None（调用方降级）。
    """
    providers = _registry().get(capability, [])
    if not providers:
        return None
    if name:
        for p in providers:
            if p.name == name:
                return p()
        return None
    for p in providers:
        inst = p()
        if inst.available():
            return inst
    # 全不可用：返回首个，供调用方给降级提示
    return providers[0]()


def available_providers(capability: str) -> List[dict]:
    """列出某能力域所有已注册 provider 及其可用性（供 --check / 透明回显）。"""
    out = []
    for p in _registry().get(capability, []):
        inst = p()
        out.append({"name": inst.name, "available": inst.available(), "meta": inst.meta()})
    return out


__all__ = ["register", "get_provider", "available_providers"]
