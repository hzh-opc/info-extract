#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info-extract · 结果哈希缓存（D12·L）。

基于输入文件哈希 + 关键选项哈希缓存抽取结果，重跑同文件跳过，避免重复算力。
隐私：缓存仅落本地私有目录（默认 <skill>/scripts/.cache），绝不外传（呼应 §4 隐私闭环）。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"


def sha256_file(path: str, chunk_size: int = 1 << 20) -> str:
    """分块读取大文件计算 sha256，避免一次性读入内存（长音频/视频友好）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _options_hash(options: dict) -> str:
    """对影响结果的关键选项求稳定哈希（排除 out_dir 等路径类无关项）。"""
    relevant = {
        k: v for k, v in options.items()
        if k in ("lang", "task", "model", "provider", "vad_threshold", "min_silence_ms")
    }
    blob = json.dumps(relevant, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ResultCache:
    """本地结果缓存。key = sha256(文件) + 选项哈希；value = ExtractResult.to_contract()。"""

    def __init__(self, cache_dir: str | os.PathLike = DEFAULT_CACHE_DIR):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.cache_dir / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> dict:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_index(self) -> None:
        self._index_path.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def key(self, path: str, options: dict) -> str:
        return f"{sha256_file(path)}:{_options_hash(options)}"

    def get(self, path: str, options: dict) -> Optional[dict]:
        k = self.key(path, options)
        entry = self._index.get(k)
        if not entry:
            return None
        result_path = self.cache_dir / f"{k}.json"
        if not result_path.exists():
            # 索引与文件不一致，清理索引
            self._index.pop(k, None)
            return None
        try:
            return json.loads(result_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def put(self, path: str, options: dict, contract: dict) -> None:
        k = self.key(path, options)
        result_path = self.cache_dir / f"{k}.json"
        result_path.write_text(
            json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._index[k] = {
            "source": path,
            "options_hash": _options_hash(options),
            "result": str(result_path),
        }
        self._save_index()


__all__ = ["sha256_file", "ResultCache"]
