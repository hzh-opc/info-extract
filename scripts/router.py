#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info-extract · 主入口（类型识别 + 按需路由，D8）。

设计（呼应方案 §0.5 / 流程规范 §1）：
- 仅做「接收 → 类型识别 → 路由」，命中类型才 import 对应模块（未命中不预载 Whisper/VLM 等重型依赖）。
- 默认本地优先、默认不上云（§4 红线）；涉及上云/外部调用由交互确认门（⑧⑨）控制，本 CLI 不自动上云。
- 输出经各模块落双通道（txt/srt/json/md，D11）；本入口负责汇总展示与批量聚合提示（D12·H）。

用法：
  python router.py 录音.mp3                       # 自动识别为音频 → 转录
  python router.py *.wav --lang 日文 --task transcribe
  python router.py 会议.m4a --model medium        # 升级模型（噪声明/方言）
  python router.py ./音频目录 --recursive --out ./结果
  python router.py --check                         # 查看能力/provider 可用性
  python router.py 课程.mp4                         # 抽音轨→转录（阶段二，复用 Whisper）
  python router.py 课程.mp4 --no-frames            # 仅文案，不抽讲解画面帧
  python router.py 图片.png                        # 当前阶段提示 OCR 规划中
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from modules.base import SourceType  # noqa: E402
from utils.io import classify, discover, is_url  # noqa: E402

MODULE_MAP = {
    SourceType.TRANSCRIPT: ("modules.audio", "AudioModule"),
    SourceType.OCR: ("modules.ocr", "OCRModule"),
    SourceType.VISION: ("modules.vision", "VisionModule"),
    SourceType.DOC_EXTRACT: ("modules.doc_extract", "DocExtractModule"),
    SourceType.VIDEO: ("modules.video", "VideoModule"),
    SourceType.VIDEO_ONLINE: ("modules.video_online", "VideoOnlineModule"),
}


def _detect_runtime_problem() -> str | None:
    """返回缺失的硬依赖名；都可用则返回 None。

    numpy/av 是阶段一音频管线的强制本地依赖（av 自带 ffmpeg 免系统依赖）。
    faster-whisper 为可选 provider，缺失时由 available() 优雅降级（显示 ⬜），不在此门禁。
    """
    for mod in ("numpy", "av"):
        try:
            __import__(mod)
        except ImportError:
            return mod
    return None


def _venv_python() -> Path | None:
    """找到与脚本同目录的隔离 venv 解释器（跨平台）。"""
    base = SCRIPT_DIR / ".venv"
    cand = base / "Scripts" / "python.exe" if sys.platform.startswith("win") else base / "bin" / "python"
    return cand if cand.is_file() else None


def ensure_runtime() -> None:
    """在导入任何重型依赖前，保证运行环境就绪。

    - 裸 python 缺 numpy/av 时：优先自动复用到同目录 .venv（仅一次，带 env 防递归标记）；
    - 否则给出明确 install 指引并干净退出（exit 2），避免抛出裸 ModuleNotFoundError traceback。
    """
    missing = _detect_runtime_problem()
    if missing is None:
        return

    # 尝试一次自动复用同目录 venv（防递归：已复刻进程不再二次复刻）
    if os.environ.get("INFO_EXTRACT_REEXEC") != "1":
        vp = _venv_python()
        if vp is not None:
            os.environ["INFO_EXTRACT_REEXEC"] = "1"
            try:
                os.execv(str(vp), [str(vp), str(Path(__file__).resolve()), *sys.argv[1:]])
            except OSError:
                pass  # 落到下面的友好提示

    print(
        "❌ 未检测到运行环境依赖（缺少 '" + (missing or "numpy/av") + "'）。\n"
        "info-extract 依赖隔离在 scripts/.venv 中，请先安装运行环境：\n"
        "  bash install.sh            # 或：python install.py\n"
        "随后可用 venv 解释器运行：\n"
        "  scripts/.venv/bin/python scripts/router.py --check\n"
        "（也可直接裸 python 运行，脚本会自动复用同目录 .venv；若 .venv 不存在则需先 install。）",
        file=sys.stderr,
    )
    sys.exit(2)


def load_module(source_type: str):
    mod_path, cls_name = MODULE_MAP[source_type]
    mod = importlib.import_module(mod_path)
    return getattr(mod, cls_name)()


def build_options(args) -> Dict:
    return {
        "lang": args.lang,
        "task": args.task,
        "model": args.model,
        "provider": args.provider,
        "out_dir": args.out,
        "use_cache": not args.no_cache,
        "long_threshold": args.long_threshold,
        "vad_threshold": args.vad_threshold,
        "extract_frames": not args.no_frames,
    }


def run_check() -> int:
    from provider_registry import available_providers  # noqa
    from skill_bridge import self_check  # noqa

    print("=== info-extract · 能力自检 ===")
    print("\n[本地 Provider 可用性]")
    for cap in [SourceType.TRANSCRIPT, SourceType.OCR, SourceType.VISION,
                SourceType.DOC_EXTRACT, SourceType.VIDEO, SourceType.VIDEO_ONLINE]:
        provs = available_providers(cap)
        if not provs:
            print(f"  - {cap}: (尚未接入)")
            continue
        for p in provs:
            mark = "✅" if p["available"] else "⬜"
            print(f"  - {cap} / {p['name']}: {mark} {p['meta'].get('cost','')}")
    print("\n[协同能力自检 D9]")
    for cap, skill in self_check().items():
        mark = "✅" if skill else "⬜"
        print(f"  - {cap}: {mark} {skill or '缺失（将降级）'}")
    print("\n原则：本地优先 · 默认不上云 · 机器结果须经你确认（§4）。")
    return 0


def main(argv: List[str] | None = None) -> int:
    ensure_runtime()  # 门禁：缺依赖自动复用 venv 或友好退出（见 ensure_runtime）
    parser = argparse.ArgumentParser(
        prog="info-extract",
        description="信息抽取技能主入口：音频转录（阶段一）与视频文案（阶段二）已实现；OCR/视觉/文档规划中。",
    )
    parser.add_argument("inputs", nargs="*", help="待处理文件/目录/glob")
    parser.add_argument("--type", choices=["auto", *MODULE_MAP.keys()], default="auto",
                        help="强制指定类型；默认 auto 按扩展名识别")
    parser.add_argument("--lang", help="语言/任务轻提示，如「日文采访」「翻译成英文」（D12·K）")
    parser.add_argument("--task", choices=["transcribe", "translate"], help="transcribe 原语转录 / translate 翻译")
    parser.add_argument("--model", default="small",
                        choices=["tiny", "base", "small", "medium", "large-v3", "turbo"],
                        help="Whisper 模型规模（默认 small）")
    parser.add_argument("--provider", default="auto",
                        help="转录 provider：auto / faster-whisper / whisper.cpp（D15）")
    parser.add_argument("--out", default=os.getcwd(), help="输出目录（默认当前目录）")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归目录")
    parser.add_argument("--no-cache", action="store_true", help="禁用哈希缓存（D12·L）")
    parser.add_argument("--no-frames", action="store_true",
                        help="禁用视频讲解段关联帧抽取（D13）；仅产出文案")
    parser.add_argument("--long-threshold", type=int, default=600,
                        help="超过该秒数启用 VAD 分块（默认 600，D12·J）")
    parser.add_argument("--vad-threshold", type=int, default=700,
                        help="VAD 最小静音毫秒（默认 700，D12·J）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果（供下游消费）")
    parser.add_argument("--check", action="store_true", help="仅自检能力/provider 可用性")
    parser.add_argument("--quiet", action="store_true", help="仅输出结果，不打印横幅")
    args = parser.parse_args(argv)

    if args.check:
        return run_check()

    if not args.inputs:
        parser.error("未提供输入；用 router.py --check 查看能力，或传入音频文件。")

    # 类型识别：拆分 URL 与本地文件（URL 归在线/加密视频，阶段五）
    url_inputs = [raw for raw in args.inputs if is_url(raw)]
    file_inputs = [raw for raw in args.inputs if not is_url(raw)]

    # 类型识别
    if args.type == "auto":
        found, unsupported = discover(file_inputs, recursive=args.recursive)
    else:
        # 强制类型：把所有存在的本地文件当作该类型
        found = []
        unsupported = []
        for raw in file_inputs:
            p = Path(raw).expanduser()
            if p.exists() and p.is_file():
                found.append((str(p.resolve()), args.type))
            else:
                unsupported.append(str(p))

    # URL 输入 → 在线/加密视频（阶段五；当前为占位提示，不静默失败）
    for u in url_inputs:
        found.append((u, SourceType.VIDEO_ONLINE))

    if not found and unsupported:
        print("⚠️ 无受支持的文件。以下格式当前未支持或对应能力规划中：")
        for u in unsupported:
            print(f"  - {u}")
        return 2

    # 按类型分组
    groups: Dict[str, List[str]] = {}
    for path, stype in found:
        groups.setdefault(stype, []).append(path)

    options = build_options(args)
    all_results = []

    if not args.quiet:
        print("info-extract · 本地优先 · 默认不上云（§4）")
        print(f"命中类型：{', '.join(groups.keys()) or '无'}")

    for stype, paths in groups.items():
        module = load_module(stype)
        if not module.ready:
            phase = module.run(paths, options)[0].media_ref.get("phase", "规划中")
            print(f"\n[{stype}] {phase}：当前阶段未实现，输入已识别但暂不处理：")
            for p in paths:
                print(f"  - {p}")
            continue
        results = module.run(paths, options)
        all_results.extend(results)

    # 汇总
    ok = [r for r in all_results if r.media_ref.get("status") == "ok"]
    cached = [r for r in all_results if r.media_ref.get("status") == "cached"]
    err = [r for r in all_results if r.media_ref.get("status") == "error"]

    if args.json:
        payload = {
            "total": len(all_results),
            "ok": len(ok), "cached": len(cached), "error": len(err),
            "results": [r.to_contract() | {"media_ref": _safe_media(r.media_ref)} for r in all_results],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not args.quiet:
            print(f"\n=== 处理汇总 ===\n成功 {len(ok)} ｜ 缓存命中 {len(cached)} ｜ 异常 {len(err)}")
            for r in all_results:
                mr = r.media_ref
                if mr.get("status") == "ok":
                    print(f"\n📄 {mr.get('path')}")
                    print(f"   语言={r.fields.get('detected_language')} 时长={r.fields.get('duration_sec')}s "
                          f"置信度={r.confidence} 引擎={r.provider_meta.get('provider')}")
                    outs = mr.get("outputs", {})
                    print(f"   产出：{', '.join(f'{k}→{v}' for k, v in outs.items())}")
                    if r.referenced_frame and r.referenced_frame.get("frames"):
                        n = len(r.referenced_frame["frames"])
                        print(f"   讲解画面帧(D13)：{n} 张（见输出目录 <stem>_frames/，默认落本地、不自动上云）")
                    if mr.get("report"):
                        print(f"   批量报告：{mr['report'].get('md')}")
                elif mr.get("status") == "cached":
                    print(f"\n♻️ {mr.get('path')}（缓存命中，已刷新产出）")
                else:
                    print(f"\n⚠️ {mr.get('path')}：{mr.get('error')}")
                    if mr.get("hint"):
                        print(f"   建议：{mr.get('hint')}")

    # 异常码
    return 1 if err else 0


def _safe_media(media_ref: dict) -> dict:
    """JSON 输出时去掉非序列化项（outputs 路径保留）。"""
    out = dict(media_ref)
    return out


if __name__ == "__main__":
    sys.exit(main())
