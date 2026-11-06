#!/usr/bin/env python3
"""머지 게이트 (단순판): high 1건 이상 또는 리뷰 실패 -> FAIL"""
import json


def gate(path):
    r = json.load(open(path, encoding="utf-8"))
    if "_error" in r:                      # 리뷰어가 죽으면 통과시키지 않는다 (fail-safe)
        print(f"GATE: FAIL (리뷰 실패: {r['_error']})")
        return False
    high = [f for f in r.get("findings", []) if f.get("severity") == "high"]
    for f in high:
        print(f"  BLOCK {f['file']}:{f['line']} [{f['category']}] {f.get('message', '')}")
    print("GATE:", "FAIL" if high else "PASS")
    return not high
