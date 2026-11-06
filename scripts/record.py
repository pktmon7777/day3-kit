#!/usr/bin/env python3
"""측정: 모든 케이스 × RUNS회 리뷰 → results/<해시>/run<k>/<case>.json (mock 은 results/<해시>-mock/)
실호출이 전부 실패하면 저장하지 않는다 (이전 측정을 덮어쓰지 않도록)."""
import datetime, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, review


def record(runs=3, mock=False):
    h = common.harness_hash()
    name = h + ("-mock" if mock else "")
    base = os.path.join(common.ROOT, "results", name)
    modes, cost, errors, got = set(), 0.0, 0, []
    for k in range(1, runs + 1):
        for c in common.list_cases():
            res, mode = review.run_review(c, k, mock)
            modes.add(mode)
            c_usd = (res.get("_meta") or {}).get("cost_usd") or 0
            cost += c_usd
            errors += mode == "error"
            got.append((os.path.join(base, f"run{k}", f"{c}.json"), res))
            note = f"  ERROR: {res['_error'][:80]}" if mode == "error" else ""
            print(f"[record] run{k} {c} ({mode}){note}")
    if errors == len(got):
        print(f"[record] 모두 실패 {errors}건 — 저장하지 않음 (py kit.py check --live 로 확인)")
        return None
    if errors and not mock and os.path.isdir(base):
        name = h + "-retry"
        print(f"[record] 오류 {errors}건 — 기존 측정 results/{h} 는 그대로 두고 이번 결과는 results/{name} 에 저장")
        base = os.path.join(common.ROOT, "results", name)
        got = [(p.replace(os.path.join("results", h), os.path.join("results", name), 1), r) for p, r in got]
    if os.path.isdir(base):
        shutil.rmtree(base)
    for path, res in got:
        review.write(path, res)
    meta = {"harness_hash": h, "runs": runs, "modes": sorted(modes), "errors": errors,
            "cost_usd_total": round(cost, 4), "harness_files": common.harness_files(),
            "recorded_at": datetime.datetime.now().isoformat(timespec="seconds")}
    review.write(os.path.join(base, "meta.json"), meta)
    print(f"[record] 완료 -> results/{name}  (하네스 해시 {h} · 오류 {errors}건"
          + (f" · 비용 ${cost:.4f}" if cost else "") + ")")
    return h
