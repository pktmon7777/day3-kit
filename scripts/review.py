#!/usr/bin/env python3
"""리뷰어 1회 실행: 케이스 1개 → 리뷰 JSON 1개

실호출: claude -p 에 프롬프트를 stdin 으로 넘긴다 (Windows 명령줄 따옴표 문제를 피하려고).
        --output-format json 으로 받아 결과 글에서 JSON 을 꺼내고, 비용 · 시간을 _meta 에 남긴다.
        모델 기본값은 sonnet. 바꾸려면 REVIEW_MODEL 환경변수 (PowerShell 예: $env:REVIEW_MODEL="haiku").
mock  : --mock 또는 REVIEW_MOCK=1 → mocks/<v1|trap>/run<N>/<case>.json 복사 (LLM 없이)
"""
import json, os, shutil, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

TIMEOUT = int(os.environ.get("REVIEW_TIMEOUT", "300"))
INSTRUCTION = "Read the review task from stdin. Reply with one JSON object only."
MODEL = os.environ.get("REVIEW_MODEL", "sonnet")  # 3차수 기본 모델


def mock_variant():
    # 하네스에 함정 규칙(C4)이 들어 있으면 trap mock, 아니면 v1 mock
    conv = common.read(os.path.join(common.HARNESS_DIR, "conventions.md"))
    return "trap" if "C4." in conv else "v1"


def claude_path():
    return shutil.which(os.environ.get("CLAUDE_BIN", "claude"))


def run_review(case_id, run_no=1, mock=False):
    if mock or os.environ.get("REVIEW_MOCK") == "1":
        src = os.path.join(common.ROOT, "mocks", mock_variant(), f"run{run_no}", f"{case_id}.json")
        return json.loads(common.read(src)), "mock:" + mock_variant()
    return call_reviewer(common.build_prompt(case_id))


def call_reviewer(prompt):
    """리뷰어 1회 실호출 — 케이스(run_review)와 PR diff(review_pr) 가 같이 쓴다."""
    exe = claude_path()
    if not exe:
        return {"_error": "claude 명령을 찾을 수 없음 — py kit.py check 로 확인 (LLM 없이 하려면 --mock)"}, "error"
    # 도구 없이(--tools "") · 키트 밖 임시 폴더에서 실행: 리뷰어가 정답(evals/cases, solutions)을 열어 볼 수 없게 한다
    cmd = [exe, "-p", INSTRUCTION, "--output-format", "json", "--model", MODEL, "--tools", ""]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, input=prompt, capture_output=True, cwd=tempfile.gettempdir(),
                           text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"_error": f"타임아웃 {TIMEOUT}s"}, "error"
    meta = {"seconds": round(time.time() - t0, 1)}
    if not p.stdout.strip():
        why = (p.stderr or "").strip()[-300:] or "출력 없음"
        return {"_error": f"claude 종료 코드 {p.returncode} · 빈 응답: {why} — py kit.py check --live 로 확인",
                "_meta": meta}, "error"
    text = p.stdout
    try:  # --output-format json 바깥 껍질: {"result": "...", "total_cost_usd": ...}
        outer = json.loads(p.stdout)
        text = outer.get("result", "") if isinstance(outer, dict) else p.stdout
        if isinstance(outer, dict):
            meta["cost_usd"] = outer.get("total_cost_usd")
            if outer.get("is_error"):
                return {"_error": "claude 오류: " + str(outer.get("result"))[:300], "_meta": meta}, "error"
    except json.JSONDecodeError:
        pass
    out = common.extract_json(text)
    if out is None:
        return {"_error": "JSON 파싱 실패", "raw": text[-2000:], "stderr": p.stderr[-500:], "_meta": meta}, "error"
    out["_meta"] = meta
    return out, "live:" + MODEL


def write(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
