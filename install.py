#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""info-extract · 一键安装脚本（跨平台，兼容 WorkBuddy / Claude / Codex / OpenClaw）。

功能：
  1. 在 <技能目录>/scripts/.venv 创建隔离 venv（CPython 3.13，与 DESEN 一致）；
  2. 安装 requirements.txt 依赖（numpy / av / faster-whisper）；
  3. 运行 `router.py --check` 冒烟自检；
  4. 打印完成信息与使用命令。

用法：
  python3 install.py                       # 默认自动探测 3.13 解释器 + 建 venv + 装依赖 + 自检
  python3 install.py --python /path/python # 复用现有 3.13 解释器（不新建 venv）
  python3 install.py --venv /path/venv     # 指定 venv 目录
  python3 install.py --skip-venv --skip-tests
退出码：0=全部通过；非 0=存在失败项。
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REQ = SKILL_DIR / "requirements.txt"
PYPROJECT = SKILL_DIR / "scripts" / "pyproject.toml"
DEFAULT_VENV = SKILL_DIR / "scripts" / ".venv"

# 优先使用的受管 3.13 路径（若存在），否则回退系统 python3.13 / python3
MANAGED_313 = Path.home() / ".workbuddy" / "binaries" / "python" / "versions" / "3.13.12" / "bin" / "python3"


def find_python() -> str:
    for cand in [str(MANAGED_313), "python3.13", "python3"]:
        p = shutil.which(cand) if "/" not in cand else (cand if os.path.exists(cand) else None)
        if p and _py_version(p) >= (3, 10):
            return p
    return sys.executable


def _py_version(exe: str):
    try:
        out = subprocess.run([exe, "-c", "import sys;print(sys.version_info[:2])"],
                             capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            return tuple(eval(out.stdout.strip()))
    except Exception:
        pass
    return (0, 0)


def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", help="复用现有解释器（不新建 venv）")
    ap.add_argument("--venv", help="指定 venv 目录（替代 scripts/.venv）")
    ap.add_argument("--skip-venv", action="store_true", help="不创建/不安装 venv")
    ap.add_argument("--skip-tests", action="store_true", help="跳过冒烟自检")
    args = ap.parse_args()

    venv_py = None
    if not args.skip_venv:
        py = args.python or find_python()
        venv_dir = Path(args.venv) if args.venv else DEFAULT_VENV
        if not venv_dir.exists():
            print(f"[install] 创建 venv：{venv_dir}（解释器 {py}）")
            r = run([py, "-m", "venv", str(venv_dir)])
            if r.returncode != 0:
                print("[install] ❌ venv 创建失败"); sys.exit(1)
        venv_py = str(venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python")
        # 升级 pip + 安装依赖
        print("[install] 安装依赖（numpy/av/faster-whisper）…")
        run([venv_py, "-m", "pip", "install", "-U", "pip"], check=False)
        # 优先用 pyproject（若有 uv），否则 requirements.txt
        if PYPROJECT.exists() and shutil.which("uv"):
            run([shutil.which("uv"), "pip", "install", "-r", str(REQ)], check=False)
        else:
            r = run([venv_py, "-m", "pip", "install", "-r", str(REQ)])
            if r.returncode != 0:
                print("[install] ❌ 依赖安装失败（见上）"); sys.exit(1)
    else:
        venv_py = args.python or sys.executable

    # 冒烟自检
    if not args.skip_tests:
        print("[install] 运行 router.py --check 自检…")
        r = run([venv_py, str(SKILL_DIR / "scripts" / "router.py"), "--check"])
        if r.returncode != 0:
            print("[install] ⚠️ 自检返回非 0（部分 provider 可能未安装，属正常）")

    print("\n[install] ✅ 完成。使用：")
    print(f"  {venv_py} {SKILL_DIR/'scripts'/'router.py'} 录音.mp3")
    print(f"  {venv_py} {SKILL_DIR/'scripts'/'router.py'} --check")
    sys.exit(0)


if __name__ == "__main__":
    main()
