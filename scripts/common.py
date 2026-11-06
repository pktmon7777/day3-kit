"""공통 유틸: 경로, 하네스 해시, 프롬프트 조립, JSON 추출·검증 (표준 라이브러리만 사용)"""
import hashlib, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS_DIR = os.path.join(ROOT, "harness")
CASES_DIR = os.path.join(ROOT, "evals", "cases")
CATEGORIES = {"div-by-zero", "buffer-overflow", "unchecked-return",
              "magic-number", "global-variable", "other"}
SEVERITIES = {"high", "medium", "low"}


def harness_files():
    return sorted(f for f in os.listdir(HARNESS_DIR) if f.endswith(".md"))


def harness_hash():
    """하네스 = 테스트 대상(SUT). 내용이 바뀌면 해시가 바뀐다 → 재측정 필요."""
    h = hashlib.sha256()
    for f in harness_files():
        h.update(f.encode())
        with open(os.path.join(HARNESS_DIR, f), "rb") as fp:
            # Windows(CRLF) 체크아웃과 CI(LF)에서 같은 해시가 나오도록 줄바꿈 정규화
            h.update(fp.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:8]


def list_cases():
    return sorted(d for d in os.listdir(CASES_DIR)
                  if os.path.isdir(os.path.join(CASES_DIR, d)))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build_prompt(case_id):
    cdir = os.path.join(CASES_DIR, case_id)
    after = read(os.path.join(cdir, "after.c")).splitlines()
    numbered = "\n".join(f"{i:>3}| {line}" for i, line in enumerate(after, 1))
    parts = [read(os.path.join(HARNESS_DIR, f)) for f in harness_files()]
    parts.append("## 변경 후 파일: src/compute.c (라인번호| 코드)\n" + numbered)
    parts.append("## diff\n" + read(os.path.join(cdir, "diff.patch")))
    return "\n\n".join(parts)


def extract_json(text):
    """LLM 출력에서 첫 '{' ~ 마지막 '}' 구간을 JSON으로 파싱. 실패 시 None."""
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        return json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        return None


def validate(output):
    """스키마 검증. 문제 없으면 None, 있으면 에러 메시지."""
    if not isinstance(output, dict):
        return "JSON 객체가 아님"
    if "_error" in output:
        return output["_error"]
    fs = output.get("findings")
    if not isinstance(fs, list):
        return "findings 배열 없음"
    for i, f in enumerate(fs):
        for k in ("file", "line", "category", "severity"):
            if k not in f:
                return f"findings[{i}].{k} 누락"
        if f["category"] not in CATEGORIES:
            return f"findings[{i}].category 허용값 아님: {f['category']}"
        if f["severity"] not in SEVERITIES:
            return f"findings[{i}].severity 허용값 아님: {f['severity']}"
        if not isinstance(f["line"], int):
            return f"findings[{i}].line 정수 아님"
    return None
