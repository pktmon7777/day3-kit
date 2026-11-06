#!/usr/bin/env python3
"""gate_ac.md(게이트 판정 조건 정본)와 코드 주석의 규칙 ID 가 맞는지 본다.

  py scripts/check_gate_ac.py      → 맞으면 「OK」 · 종료 코드 0 / 어긋나면 목록 · 종료 코드 1

보는 것
  ① 문서 표의 ID 마다 「코드」 칸에 적힌 파일의 주석에 그 ID 가 있나
  ② 코드 주석의 ID 가 문서 표에 있나
  ③ 옛 문서 이름(게이트-규칙.md)을 가리키는 파일이 남았나
조건의 뜻(문장)이 코드와 같은지는 보지 못한다 — 사람(또는 Claude)이 판정 줄을 읽고 맞춘다.
훅 scripts/gate_ac_sync.py 가 gate_ac.md 를 고친 뒤 이 점검을 부른다.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "gate_ac.md")
CODE = ["scripts/gate.py", "scripts/review_pr.py", "scripts/ci_check.py", "kit.py", "evals/eval.py",
        ".github/workflows/pr-review.yml", ".github/workflows/harness-gate.yml", ".github/workflows/deploy.yml"]
OLD_NAME = "게이트-규칙.md"
ID = r"[GHD]\d+"


def doc_rows():
    """{ID: [코드 칸의 파일]}"""
    rows = {}
    for line in open(DOC, encoding="utf-8"):
        m = re.match(rf"\|\s*({ID})\s*\|(.*)\|\s*$", line)
        if m:
            code_cell = m.group(2).split("|")[-1]
            rows[m.group(1)] = re.findall(r"`([\w./-]+\.(?:py|yml))`", code_cell)
    return rows


def ids_in(text):
    ids = set()
    for a, lo, hi in re.findall(r"\b([GHD])(\d+)\s*~\s*[GHD]?(\d+)\b", text):   # 범위 「G1 ~ G8」
        ids |= {f"{a}{i}" for i in range(int(lo), int(hi) + 1)}
    return ids | set(re.findall(rf"\b({ID})\b", text))


def code_ids(path):
    """주석(# 뒤)과 gate_ac.md 를 말하는 줄에서 규칙 ID 를 모은다"""
    ids = set()
    for line in open(path, encoding="utf-8"):
        if "gate_ac.md" in line:
            ids |= ids_in(line)
        elif "#" in line:
            ids |= ids_in(line.split("#", 1)[1])
    return ids


def main():
    if not os.path.exists(DOC):
        print(f"[gate_ac] 문서가 없다: {DOC}")
        return 1
    rows, problems = doc_rows(), []
    found = {f: code_ids(os.path.join(ROOT, f)) for f in CODE if os.path.exists(os.path.join(ROOT, f))}
    for rid, files in sorted(rows.items()):
        for f in files:
            if f in found and rid not in found[f]:
                problems.append(f"① 문서 {rid} 의 코드 칸 {f} 에 「{rid}」 주석이 없다")
    for f, ids in found.items():
        for rid in sorted(ids - set(rows)):
            problems.append(f"② {f} 주석의 {rid} 가 gate_ac.md 표에 없다")
    for f in CODE + ["README.md"]:
        p = os.path.join(ROOT, f)
        if os.path.exists(p) and OLD_NAME in open(p, encoding="utf-8").read():
            problems.append(f"③ {f} 가 옛 이름 {OLD_NAME} 을 가리킨다 → gate_ac.md")
    if problems:
        print("[gate_ac] 어긋남 " + str(len(problems)) + "건")
        print("\n".join("  " + p for p in problems))
        return 1
    print(f"[gate_ac] OK · 규칙 {len(rows)}개 · 코드 {len(found)}개 파일")
    return 0


if __name__ == "__main__":
    sys.exit(main())
