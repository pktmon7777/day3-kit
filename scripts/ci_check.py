#!/usr/bin/env python3
"""CI 사전검사: 현재 하네스로 측정한 결과가 커밋돼 있는가?"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def ci_check():
    h = common.harness_hash()
    meta_path = os.path.join(common.ROOT, "results", h, "meta.json")
    if not os.path.exists(meta_path):
        if os.path.exists(os.path.join(common.ROOT, "results", h + "-mock")):
            print(f"::error::하네스(해시 {h})는 mock 결과만 있습니다. mock 은 측정 증거가 아닙니다 → 'py kit.py record'(실호출)")
        else:
            print(f"::error::하네스(해시 {h})가 바뀌었는데 측정 결과가 없습니다. 로컬에서 'py kit.py record' 후 results/{h} 를 커밋하세요.")
        return False
    meta = json.load(open(meta_path, encoding="utf-8"))
    print(f"[ci_check] OK - results/{h} (runs={meta['runs']}, modes={meta['modes']})")
    return True
