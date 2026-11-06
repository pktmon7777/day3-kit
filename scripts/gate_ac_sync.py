#!/usr/bin/env python3
"""Claude Code 훅(PostToolUse · .claude/settings.json) — gate_ac.md 를 고치면 코드 반영을 Claude 에게 되돌려 준다.

gate_ac.md 가 아닌 파일이면 아무것도 하지 않는다(종료 코드 0).
gate_ac.md 이면 scripts/check_gate_ac.py 를 돌리고, 「판정 줄을 문서와 맞춰라」 와 점검 결과를
{"decision": "block", "reason": …} 로 내보낸다 — Claude 는 이것을 받아 이어서 코드를 고친다.
코드를 고칠 때는 이 훅이 다시 돌지 않는다(대상이 gate_ac.md 가 아니므로).
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
except ValueError:
    sys.exit(0)
path = (data.get("tool_input") or {}).get("file_path") or ""
if re.split(r"[\\/]", path)[-1].lower() != "gate_ac.md":   # Windows 경로(\)도
    sys.exit(0)

p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_gate_ac.py")], capture_output=True,
                   text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
reason = ("gate_ac.md(게이트 판정 조건 정본)가 바뀌었다. 바뀐 행의 조건이 코드의 판정과 같도록 고쳐라.\n"
          "- 리뷰 게이트: scripts/review_pr.py(PR) · scripts/gate.py(M1 gate)\n"
          "- 리뷰어 게이트: scripts/ci_check.py · kit.py 의 ci · evals/eval.py 통과선\n"
          "- 배포: .github/workflows/deploy.yml\n"
          "- 고친 판정 줄에는 「# 게이트 규칙 <ID> · gate_ac.md」 주석을 단다 · 문서에 없는 조건을 코드에 넣지 않는다\n"
          "- 다 고친 뒤 py scripts/check_gate_ac.py 가 OK 인지 본다\n"
          "ID 점검 결과:\n" + (p.stdout.strip() or p.stderr.strip()))
print(json.dumps({"decision": "block", "reason": reason}))
