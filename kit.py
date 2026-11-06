#!/usr/bin/env python3
"""Harness Eval 실습 — 명령은 이 파일 하나 (Windows: py kit.py <명령> · 그 밖: python3 kit.py <명령>)

  check [--live]           환경 점검 (--live: LLM 실호출까지)
  review <CASE> [--mock]   케이스 1개 리뷰 -> out/<CASE>.json
  gate <CASE> [--mock]     리뷰 + 머지 게이트 판정
  record [--runs 3] [--mock]  전체 케이스 x runs회 측정 -> results/<해시>/ (mock 은 results/<해시>-mock/)
  eval [--mock] [--base <해시>]  채점 (--mock: mock 결과 · --base: 그 버전과 비교)
  hash                     현재 하네스 해시
  trap / reset-harness     함정 규칙 C4 넣기 / 하네스(규칙 파일 둘) 원복
  stage <1|2|4>            막혔을 때 그 단계 정답 넣기
  ci                       CI 와 같은 판정 (실호출 측정 결과 존재 + 기준 통과, mock 은 불인정)
  review-pr [--base <커밋>]  M5: PR 의 src/compute.c 변경을 리뷰 → PR 코멘트 (CI 에서)
"""
import argparse, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import common, review, record, check, gate, ci_check, review_pr  # noqa: E402


def results_dir(h, mock=False):
    return os.path.join(ROOT, "results", h + ("-mock" if mock else ""))


def run_eval(results, base=None, mock=False):
    cmd = [sys.executable, os.path.join(ROOT, "evals", "eval.py"), "--results", results]
    if base:
        b = results_dir(base.replace("-mock", ""), mock)
        if not os.path.isdir(b):
            print(f"비교할 결과가 없습니다: results/{os.path.basename(b)}  ({'mock' if mock else '실호출'} 측정을 먼저)")
            return 1
        cmd += ["--baseline", b]
    return subprocess.call(cmd, env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def main():
    ap = argparse.ArgumentParser(prog="kit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check"); p.add_argument("--live", action="store_true")
    for name in ("review", "gate"):
        p = sub.add_parser(name); p.add_argument("case"); p.add_argument("--mock", action="store_true")
    p = sub.add_parser("record"); p.add_argument("--runs", type=int, default=3); p.add_argument("--mock", action="store_true")
    p = sub.add_parser("eval"); p.add_argument("--base"); p.add_argument("--mock", action="store_true")
    sub.add_parser("hash"); sub.add_parser("trap"); sub.add_parser("reset-harness"); sub.add_parser("ci")
    p = sub.add_parser("stage"); p.add_argument("n", choices=["1", "2", "4"])
    p = sub.add_parser("review-pr"); p.add_argument("--base"); p.add_argument("--mock", action="store_true")
    a = ap.parse_args()

    if a.cmd == "check":
        return 0 if check.check(a.live) else 1
    if a.cmd in ("review", "gate"):
        res, mode = review.run_review(a.case, 1, a.mock)
        out = os.path.join(ROOT, "out", f"{a.case}.json")
        review.write(out, res)
        print(f"[review] {a.case} ({mode}) -> out/{a.case}.json")
        print(open(out, encoding="utf-8").read())
        if a.cmd == "gate":
            return 0 if gate.gate(out) else 1
        return 1 if mode == "error" else 0
    if a.cmd == "record":
        record.record(a.runs, a.mock); return 0
    if a.cmd == "eval":
        d = results_dir(common.harness_hash(), a.mock)
        if not os.path.isdir(d):
            print(f"결과가 없습니다: results/{os.path.basename(d)}  → py kit.py record{' --mock' if a.mock else ''} 먼저")
            return 1
        return run_eval(d, a.base, a.mock)
    if a.cmd == "hash":
        print(common.harness_hash()); return 0
    if a.cmd == "trap":
        conv = os.path.join(ROOT, "harness", "conventions.md")
        if "C4." in common.read(conv):
            print("이미 C4 가 들어 있음"); return 0
        with open(conv, "a", encoding="utf-8") as f:
            f.write(common.read(os.path.join(ROOT, "variants", "trap-rule.md")))
        print("C4 추가됨 -> hash", common.harness_hash()); return 0
    if a.cmd == "reset-harness":
        for f in ("conventions", "reviewer"):
            shutil.copy(os.path.join(ROOT, "variants", f"{f}.v1.md"), os.path.join(ROOT, "harness", f"{f}.md"))
        print("원복 -> hash", common.harness_hash()); return 0
    if a.cmd == "stage":
        shutil.copytree(os.path.join(ROOT, "solutions", f"stage{a.n}"), ROOT, dirs_exist_ok=True)
        print(f"stage{a.n} 정답 적용"); return 0
    if a.cmd == "review-pr":
        return 0 if review_pr.review_pr(a.base, a.mock) else 1
    if a.cmd == "ci":
        if not ci_check.ci_check():
            return 1
        pre = os.path.join(results_dir(common.harness_hash()), "verdict.txt")
        if os.path.exists(pre):  # M5 템플릿 — 정답 · 채점기를 빼고 빌드 때 미리 계산한 판정
            line = (open(pre, encoding="utf-8").read().strip().splitlines() or ["EVAL: 채점 실패"])[0]
            print(f"[ci] 미리 계산한 채점 판정 — {line}")
            return 0 if line.startswith("EVAL: PASS") else 1
        return run_eval(results_dir(common.harness_hash()))


if __name__ == "__main__":
    sys.exit(main())
