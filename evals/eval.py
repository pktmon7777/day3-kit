#!/usr/bin/env python3
"""Harness Eval Grader — results/<hash>/run*/<case>.json 을 정답(case.json)과 비교해 점수를 계산한다.
사용: python3 evals/eval.py --results results/<hash> [--baseline results/<hash2>]
"""
import argparse, glob, json, os, sys
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import common

LINE_TOL = 3   # 라인번호 허용 오차


# ── ① 오라클: 기대 지적 1건과 실제 지적 1건이 '같은 것'인가 ─────────────────
def is_match(exp, got, file):
    # TODO(S2-①): file 같고, category 같고, line 차이가 LINE_TOL 이내면 True
    raise NotImplementedError("is_match")


# ── ② 케이스 1회 채점: TP / FN / FP ─────────────────────────────────────────
def match(case, output):
    # TODO(S2-②): case["expected"] 각각에 대해 output["findings"] 에서 is_match 되는 것을 찾는다
    #   찾으면 tp+1 (그 finding은 목록에서 제거), 못 찾으면 fn+1
    #   끝나고 남은 findings 개수 = fp
    raise NotImplementedError("match")


# ── ③ 실행 결과 전체 채점 ──────────────────────────────────────────────────
def grade(results_dir):
    cases = {c: json.load(open(os.path.join(common.CASES_DIR, c, "case.json"), encoding="utf-8"))
             for c in common.list_cases()}
    todo = [c for c, v in cases.items() if not isinstance(v["expected"], list)]
    if todo:
        sys.exit(f"정답 미작성 케이스: {todo} → evals/cases/<id>/case.json 의 expected 를 채우세요")
    runs = sorted(glob.glob(os.path.join(results_dir, "run*")))
    if not runs:
        sys.exit(f"결과 없음: {results_dir} → py kit.py record 먼저")
    table = {}   # case → [cell per run]
    for r in runs:
        for c, case in cases.items():
            out = json.load(open(os.path.join(r, f"{c}.json"), encoding="utf-8"))
            err = common.validate(out)
            if err:
                cell = {"schema": err, "tp": 0, "fn": len(case["expected"]), "fp": 0}
            else:
                tp, fn, fp = match(case, out)
                cell = {"tp": tp, "fn": fn, "fp": fp}
            table.setdefault(c, []).append(cell)
    return cases, table, len(runs)


# ── ④ 지표 ────────────────────────────────────────────────────────────────
def summarize(table, k):
    # TODO(S2-④): 아래 키를 계산해 dict로 반환
    #   recall        = 전체 tp / (tp + fn), 소수 셋째 자리로 반올림 round(…, 3). tp + fn 이 0 이면 1.0
    #   fp_per_run    = 전체 fp / k, 소수 둘째 자리로 반올림 round(…, 2)
    #   schema_errors = "schema" 키가 있는 cell 수
    #   pass_k        = "통과케이스수/전체케이스수" (k회 모두 fn=0, fp=0, schema 없음)
    #   pass_k_rate   = 통과케이스수 / 전체케이스수, round(…, 3)
    raise NotImplementedError("summarize")


def cell_str(x):
    if "schema" in x:
        return "SCHEMA!"
    s = []
    if x["fn"]:
        s.append(f"MISS{x['fn']}")
    if x["fp"]:
        s.append(f"FP{x['fp']}")
    return " ".join(s) or "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--baseline")
    ap.add_argument("--thresholds", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "thresholds.json"))
    a = ap.parse_args()
    cases, table, k = grade(a.results)
    m = summarize(table, k)

    print(f"\n## Harness Eval — {os.path.basename(a.results.rstrip('/'))} (k={k})\n")
    print("| case | 설명 | " + " | ".join(f"run{i+1}" for i in range(k)) + " | pass^k |")
    print("|---|---|" + "---|" * (k + 1))
    for c, row in table.items():
        ok = all(cell_str(x) == "OK" for x in row)
        print(f"| {c} | {cases[c].get('desc', '')} | " + " | ".join(cell_str(x) for x in row) + f" | {'OK' if ok else '-'} |")

    base = None
    if a.baseline:
        _, bt, bk = grade(a.baseline)
        base = summarize(bt, bk)
    th = json.load(open(a.thresholds, encoding="utf-8"))
    rules = [("recall", ">=", th["min_recall"]), ("fp_per_run", "<=", th["max_fp_per_run"]),
             ("schema_errors", "<=", th["max_schema_errors"])]
    print("\n| 지표 | 값 | " + ("baseline | Δ | " if base else "") + "기준 | 판정 |")
    print("|---|---|" + ("---|---|" if base else "") + "---|---|")
    failed = []
    for key, op, lim in rules:
        v = m[key]
        ok = v >= lim if op == ">=" else v <= lim
        if not ok:
            failed.append(key)
        extra = f"{base[key]} | {round(v - base[key], 3):+} | " if base else ""
        print(f"| {key} | {v} | {extra}{op} {lim} | {'PASS' if ok else 'FAIL'} |")
    print(f"| pass^k | {m['pass_k']} | " + (f"{base['pass_k']} | | " if base else "") + "참고 | |")

    with open(os.path.join(a.results, "score.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    meta_p = os.path.join(a.results, "meta.json")
    if os.path.exists(meta_p):
        m_ = json.load(open(meta_p, encoding="utf-8"))
        print(f"\n측정: modes={m_.get('modes')} · 오류 {m_.get('errors', 0)}건" + (f" · 비용 ${m_['cost_usd_total']}" if m_.get("cost_usd_total") else ""))
    print(f"\nEVAL: {'FAIL ' + str(failed) if failed else 'PASS'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
