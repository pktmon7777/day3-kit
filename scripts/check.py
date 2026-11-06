#!/usr/bin/env python3
"""환경 점검: 실습 전 세팅 시간에 함께 실행 (클린 Windows PC 기준).
   py kit.py check          설치 상태만 (LLM 호출 없음)
   py kit.py check --live   + 로그인 · 모델(기본 sonnet) 실호출 1회
"""
import json, os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, review


def _version(exe):
    try:
        p = subprocess.run([exe, "--version"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        return (p.stdout or p.stderr).strip().splitlines()[0]
    except Exception:
        return ""


def check(live=False):
    ok = True

    def item(name, cond, fix, required=True):
        nonlocal ok
        mark = "OK" if cond else ("NG" if required else "--")
        print(f"  [{mark}] {name}" + ("" if cond else f"  -> {fix}"))
        if required:
            ok &= bool(cond)

    print("[check]")
    item(f"python >= 3.10 (지금 {sys.version.split()[0]})", sys.version_info >= (3, 10),
          "python.org 설치 프로그램에서 'Add python.exe to PATH' 체크 후 재설치")
    item(f"작업 폴더 경로가 영문 ({common.ROOT})", common.ROOT.isascii(),
          r"C:\lab 처럼 영문 경로로 폴더를 옮긴 뒤 다시 실행 (한글 경로는 도구별로 오동작 사례가 있음)",
          required=False)
    git = shutil.which("git")
    item("git (선택: Claude Code의 Bash 도구용)" + (f" {_version(git)}" if git else ""), bool(git),
          "Git for Windows 설치 권장. 없으면 Claude Code가 PowerShell로 대신 실행", required=False)
    exe = review.claude_path()
    item("claude 명령" + (f" {_version(exe)} ({exe})" if exe else ""), bool(exe),
          "PowerShell: irm https://claude.ai/install.ps1 | iex  → 새 창을 열고 다시 실행")
    print(f"  [..] 리뷰 모델: {review.MODEL}  (바꾸려면 PowerShell 에서 $env:REVIEW_MODEL='haiku')")

    if live:
        if not exe:
            item("로그인 · 실호출", False, "claude 설치 후 다시")
        else:
            try:
                p = subprocess.run([exe, "-p", "Reply with one JSON object only.", "--output-format", "json",
                                    "--model", review.MODEL, "--tools", ""],
                                   input='Return exactly this JSON: {"ok": true}', capture_output=True,
                                   cwd=tempfile.gettempdir(),
                                   text=True, encoding="utf-8", errors="replace", timeout=120)
                good, cost = False, ""
                try:
                    outer = json.loads(p.stdout)
                    good = (not outer.get("is_error")) and "ok" in str(outer.get("result", ""))
                    cost = f" (${outer.get('total_cost_usd') or 0:.4f})"
                except Exception:
                    good = '"ok"' in p.stdout
                item(f"로그인 · 실호출 [{review.MODEL}]" + cost, good,
                      "claude 를 한 번 실행해 브라우저 로그인 후 다시: "
                      + (p.stderr.strip()[:200] or p.stdout.strip()[:200]))
            except subprocess.TimeoutExpired:
                item("로그인 · 실호출", False, "120초 타임아웃 — 네트워크/로그인 확인")
    elif exe:
        print("  [..] 로그인 확인은 py kit.py check --live")
    print("[check]", "READY" if ok else "FIX NEEDED")
    return ok
