#!/usr/bin/env python3
"""M5 — PR 의 C 변경을 리뷰어에 넘기고, 결과를 PR 코멘트로 단다 (GitHub Actions self-hosted 러너에서).

CI 가 넘겨 주는 환경변수: BASE_SHA(비교 기준) · PR_NUMBER · REPO(owner/name) · GH_TOKEN(github.token)
로컬에서 시험: py kit.py review-pr --base main   (코멘트는 달지 않고 화면에만)
판정은 M1 게이트와 같다: high 1건 이상 또는 리뷰 실패 → FAIL(종료 코드 1).
"""
import json, os, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, review

TARGET = "src/compute.c"


def git(*args):
    return subprocess.run(["git", "-C", common.ROOT, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def build_pr_prompt(diff):
    after = common.read(os.path.join(common.ROOT, *TARGET.split("/"))).splitlines()
    numbered = "\n".join(f"{i:>3}| {line}" for i, line in enumerate(after, 1))
    parts = [common.read(os.path.join(common.HARNESS_DIR, f)) for f in common.harness_files()]
    parts.append(f"## 변경 후 파일: {TARGET} (라인번호| 코드)\n" + numbered)
    parts.append("## diff\n" + diff)
    return "\n\n".join(parts)


def measured():
    h = common.harness_hash()
    return h, os.path.exists(os.path.join(common.ROOT, "results", h, "meta.json"))


def eval_verdict(h):
    """측정 결과의 채점 판정 한 줄 (코멘트용). results/<h>/verdict.txt 가 있으면 그 줄(M5 템플릿 —
    정답 · 채점기를 빼고 빌드 때 미리 계산), 없으면 kit 의 evals/eval.py 로 채점한다."""
    pre = os.path.join(common.ROOT, "results", h, "verdict.txt")
    if os.path.exists(pre):
        line = open(pre, encoding="utf-8").read().strip().splitlines()
        return line[0] if line else "EVAL: 채점 실패"
    p = subprocess.run([sys.executable, os.path.join(common.ROOT, "evals", "eval.py"), "--results",
                        os.path.join(common.ROOT, "results", h)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    last = [l for l in p.stdout.splitlines() if l.startswith("EVAL:")]
    return last[-1] if last else "EVAL: 채점 실패"


def comment_body(h, is_measured, res, verdict):
    lines = [f"### AI 리뷰어 — {verdict}", "",
             f"하네스 해시 `{h}` · " + (f"측정된 버전 (`results/{h}` · {eval_verdict(h)})" if is_measured
                                        else "**측정되지 않은 리뷰어** — 리뷰하지 않고 FAIL. `py kit.py record` 로 재고 결과를 커밋한다"), ""]
    if not is_measured:
        return "\n".join(lines)
    if "_error" in res:
        lines += [f"리뷰 실패: {res['_error'][:300]}", "", "리뷰가 실패하면 통과시키지 않는다."]
    elif res.get("findings"):
        lines += ["| severity | 위치 | category | 지적 |", "|---|---|---|---|"]
        for f in res["findings"]:
            lines.append(f"| {f.get('severity')} | {f.get('file')}:{f.get('line')} | {f.get('category')} | {str(f.get('message', '')).replace('|', '/')} |")
    else:
        lines.append("지적 없음")
    return "\n".join(lines)


def post_comment(body):
    repo, pr, token = os.environ.get("REPO"), os.environ.get("PR_NUMBER"), os.environ.get("GH_TOKEN")
    if not (repo and pr and token):
        print("[review-pr] REPO · PR_NUMBER · GH_TOKEN 이 없어 코멘트는 생략 (로컬 실행)")
        return
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues/{pr}/comments",
                                 data=json.dumps({"body": body}).encode("utf-8"), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"[review-pr] PR #{pr} 에 코멘트 ({r.status})")
    except Exception as e:  # 코멘트 실패는 판정에 넣지 않는다 — 판정은 아래 종료 코드
        print(f"[review-pr] 코멘트 실패 (판정과 무관): {e}")


def review_pr(base=None, mock=False):
    base = base or os.environ.get("BASE_SHA") or "main"
    d = git("diff", f"{base}...HEAD", "--", TARGET)
    if d.returncode != 0:
        print(f"[review-pr] git diff 실패: {d.stderr.strip()[:200]} — checkout 에 fetch-depth: 0 이 있는지 확인")
        return False
    if not d.stdout.strip():
        print(f"[review-pr] 이 PR 에는 {TARGET} 변경이 없음 — 리뷰 생략 (PASS)")
        return True
    h, is_measured = measured()
    if not is_measured:  # 측정된 하네스 버전만 파이프라인에 — 측정 안 된 리뷰어는 리뷰하지 않고 막는다
        print(f"[review-pr] 하네스 {h} 의 측정 결과(results/{h})가 없음 — 측정되지 않은 리뷰어는 쓰지 않는다")
        print("GATE: FAIL")
        post_comment(comment_body(h, False, {}, "FAIL"))
        return False
    if mock:
        res, mode = {"findings": []}, "mock"
    else:
        res, mode = review.call_reviewer(build_pr_prompt(d.stdout))
    review.write(os.path.join(common.ROOT, "out", "pr-review.json"), res)
    high = [f for f in res.get("findings", []) if f.get("severity") == "high"]
    ok = "_error" not in res and not high
    verdict = "PASS" if ok else "FAIL"
    print(f"[review-pr] {TARGET} · 하네스 {h} ({'측정됨' if is_measured else '측정 안 됨'}) · {mode}")
    for f in res.get("findings", []):
        print(f"  {f.get('severity','?').upper():6} {f.get('file')}:{f.get('line')} [{f.get('category')}] {f.get('message','')}")
    print("GATE:", verdict)
    post_comment(comment_body(h, is_measured, res, verdict))
    return ok
