# 게이트 규칙 — 판정 조건(ERROR · FAIL · REVIEW · PASS)

- 판정 조건의 정본은 이 문서다
- 코드는 판정하는 줄에 주석 `# 게이트 규칙 <ID> · gate_ac.md` 로 이 문서를 가리킨다
- 조건을 바꾸면 이 문서의 표와 그 코드 줄을 함께 고친다

## 1. 리뷰 게이트 — M1 `py kit.py gate` · M5 `pr-review`

판정 상태는 넷이다 · PASS 만 체크 초록(종료 코드 0) · 나머지는 체크 빨강(1)

| 상태 | 뜻 |
|---|---|
| PASS | 막을 지적이 없다 · 병합해도 된다 |
| FAIL | 이 PR 이 바꾼 줄에 high 지적이 있다 · 고친 뒤 다시 |
| REVIEW | 이 PR 이 바꾸지 않은 줄(범위 밖)에 지적이 있다 · 사람이 그 줄을 보고 병합을 정한다 |
| ERROR | 리뷰를 하지 못했다(도구 · 환경) · 결함이 있다는 뜻이 아니다 · PASS 도 아니다 |

| ID | 조건 | 판정 | 코드 |
|---|---|---|---|
| G1 | 리뷰가 실패했다(claude 오류 · 시간 초과 · 답이 JSON 이 아님 → 답안에 `_error`) | ERROR | `scripts/gate.py` · `scripts/review_pr.py` |
| G2 | 지적 가운데 severity `high` 가 1건 이상(PR 은 diff 안 줄만) | FAIL | `scripts/gate.py` · `scripts/review_pr.py` |
| G8 | (PR 만) G2 가 아니고 diff 밖 줄(이 PR 이 바꾸지 않은 줄)에 지적이 있다 · severity 는 묻지 않는다 | REVIEW | `scripts/review_pr.py` |
| G3 | G1 · G2 · G8 이 아니다 · diff 안 medium · low 는 코멘트에만 | PASS | `scripts/gate.py` · `scripts/review_pr.py` |
| G4 | (PR 만) 지금 하네스 해시의 실호출 측정 결과(`results/<해시>/meta.json`)가 없다 | 리뷰하지 않고 FAIL | `scripts/review_pr.py` `measured()` |
| G5 | (PR 만) 이 PR 에 리뷰 대상 파일(`TARGET` = `src/compute.c`) 변경이 없다 | 리뷰를 건너뛰고 PASS | `scripts/review_pr.py` |
| G6 | (PR 만) diff 안 지적을 그 줄에 인라인 코멘트로 달지 못했다 | 판정에 영향 없음(결과 코멘트에 한 줄) | `scripts/review_pr.py` `post_inline()` |
| G7 | (PR 만) diff 밖 지적은 결과 코멘트 「범위」 열에 「범위 밖」 으로 표시한다 | 표시(판정은 G8) | `scripts/review_pr.py` `comment_body()` |

- 우선순위: ERROR(G1) → FAIL(G2) → REVIEW(G8) → PASS(G3)
- category 는 판정에 쓰지 않는다
- 심각도(severity)는 규칙 글이 정한다
  - 팀 규칙(`harness/conventions.md`)은 규칙마다 severity 를 적는다
  - 판단 기준의 결함(0으로 나누기 · 배열 경계 · 반환값 미확인)은 severity 가 적혀 있지 않아 모델이 고른다
- PR 에서 보는 차례: G5 → G4 → 리뷰 → G1 · G2 · G8 · G3 → 인라인(G6) · 결과 코멘트(G7)
- M1 `py kit.py gate` 는 diff 가 없어 G4 ~ G8 이 없다 · ERROR(G1) · FAIL(G2 · 지적 전부) · PASS(G3) 셋

## 2. 리뷰어 게이트 — M5 `harness-gate`(`py kit.py ci`)

| ID | 조건 | 판정 | 코드 |
|---|---|---|---|
| H1 | 지금 하네스 해시의 실호출 측정 결과(`results/<해시>/meta.json`)가 없다 · mock(`<해시>-mock`)만 있다 | FAIL | `scripts/ci_check.py` |
| H2 | 그 측정 결과가 통과선을 넘지 못했다 | FAIL | `kit.py` `ci` · `evals/eval.py` |
| H3 | H1 · H2 가 아니다 | PASS | `kit.py` `ci` |

- 통과선은 `evals/thresholds.json`
  - `recall` ≥ `min_recall` · `fp_per_run` ≤ `max_fp_per_run` · `schema_errors` ≤ `max_schema_errors`
  - `pass^k` 는 참고 값이다(판정에 쓰지 않는다)
- 키트에 처음부터 든 강사 측정(`results/ac434c76`)은 미리 계산한 판정 `verdict.txt` 의 첫 줄로 H2 를 본다 · 내가 측정한 해시는 `evals/eval.py` 로 채점한다
- 같은 통과선이 M2 · M3 의 `py kit.py eval` 판정(`EVAL: PASS · FAIL`)이다

## 3. 배포 — M5 `deploy`(main 에 병합되면)

| ID | 조건 | 판정 | 코드 |
|---|---|---|---|
| D1 | 빌드 실패(gcc `-Wall -Werror`) | 배포하지 않는다 | `.github/workflows/deploy.yml` |
| D2 | 시험 실패(`tests/test_compute.c`) | 배포하지 않는다 | `.github/workflows/deploy.yml` |
| D3 | D1 · D2 가 아니다 | 아티팩트 `compute-<번호>` | `.github/workflows/deploy.yml` |

- `.github/` · `tests/` 는 M0 에서 키트를 내 GitHub 저장소로 push 하면 GitHub 이 읽는다

## 4. 바꿀 때

- 이 문서의 표 → 그 ID 주석이 붙은 코드 줄 → 바꾼 까닭 한 줄을 PR 에 쓴다
- 하네스(`harness/*.md`)는 해시에 들어가 바꾸면 H1 로 막힌다
- 이 문서 · 코드(`scripts/` · `kit.py`)는 해시에 들어가지 않고, 바꿔도 어느 게이트도 돌지 않는다
  - PR 리뷰에서 사람이 본다
- 통과선(`evals/thresholds.json`)을 바꾼 PR 은 `harness-gate` 가 돌지만 해시는 그대로라 H2 만 다시 본다
  - 강사 측정(`ac434c76`)은 미리 계산한 판정(`verdict.txt`)을 쓰므로 바뀐 통과선이 반영되지 않는다
- Claude Code 로 이 문서를 고치면 훅(`.claude/settings.json` → `scripts/gate_ac_sync.py`)이 「판정 줄을 문서와 맞춰라」 와 ID 점검 결과를 Claude 에게 돌려준다
  - Claude Code 는 저장소 맨 위에서 연다(훅 명령이 `py scripts/gate_ac_sync.py`)
- 손으로 고쳤으면 `py scripts/check_gate_ac.py` 로 ID 가 맞는지 본다(조건 문장의 뜻까지는 보지 못한다)
