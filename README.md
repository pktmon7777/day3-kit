# Harness Eval 실습 키트 (3차수 3일차 M1~M3)

> 한 줄 목표: **AI 리뷰어(하네스)를 고치면 좋아졌는지 나빠졌는지, 감이 아니라 숫자로 판정한다.**

- 미션카드는 `MISSIONS.md`에 있습니다. 이 README는 키트 구조와 명령만 설명합니다.
- 명령은 `kit.py` 하나뿐입니다. Windows는 `py kit.py <명령>`, 그 밖의 환경은 `python3 kit.py <명령>`으로 실행합니다.
- GNU make, GitHub, 하네스 실행기(/harness · /run-phase)는 필요 없습니다. Python 3.10 이상과 Claude Code(`claude`)만 있으면 됩니다.
- `--mock`을 붙이면 LLM 없이 미리 만들어 둔 결과로 진행합니다. 흐름을 먼저 이해한 뒤 `--mock` 없이 실호출로 반복하세요.

## 구성

```
kit.py              명령 진입점
harness/            리뷰어 = 테스트 대상(SUT). 이 파일이 바뀌면 하네스 해시가 바뀜
  reviewer.md         역할 · 판단 기준 · 출력 JSON 규칙
  conventions.md      팀 코딩 컨벤션 C1~C3 (M1 에서 규칙을 더함)
evals/
  cases/E01~E06/      diff.patch + after.c + case.json(정답) — 결함 · 정상 섞임
  eval.py             채점기 (M2 에서 TODO 3개 완성)
  thresholds.json     통과 기준 (recall >= 0.75 · 오탐 <= 0.5/회 · 형식 오류 0)
src/compute.c       예제 원본 (함수 5개)
scripts/            키트 내부 (수정 불필요)
results/<해시>/     실호출 측정 결과. 같은 해시를 다시 재면 덮어씀
  <해시>-mock/        mock 측정 결과 (ci 는 인정하지 않음)
  <해시>-retry/       실호출 일부가 실패했을 때. 기존 results/<해시> 는 그대로 둠 → check --live 확인 후 다시 record
mocks/ solutions/ variants/   mock 결과 · 단계 정답 · 함정 규칙
```

## 명령

| 명령 | 하는 일 |
|---|---|
| `py kit.py check --live` | 환경 점검 + LLM 실호출 1회 확인 |
| `py kit.py review E01 [--mock]` | 케이스 1개 리뷰 → `out/E01.json` |
| `py kit.py gate E01 [--mock]` | 리뷰 + 머지 게이트(high 1건 이상이면 FAIL, 리뷰 실패도 FAIL) |
| `py kit.py record [--runs 3] [--mock]` | 6케이스 × runs회 측정 → `results/<해시>/` (실호출 1회 측정 = 18호출) · mock 은 `results/<해시>-mock/`. 실호출이 전부 실패하면 저장하지 않음 |
| `py kit.py eval [--mock] [--base <해시>]` | 채점. `--mock` 은 mock 결과, `--base` 를 주면 그 버전과 나란히 비교 |
| `py kit.py hash` | 현재 하네스 해시 |
| `py kit.py trap` / `reset-harness` | 함정 규칙 C4 넣기 / 하네스(conventions.md · reviewer.md) 원복 |
| `py kit.py stage 1·2·4` | 막혔을 때 정답 넣기: 1 = 정답셋, 2 = 채점기, 4 = CI workflow |
| `py kit.py ci` | CI 판정과 같음: 현재 해시의 **실호출** 측정 결과가 있는가 + 기준을 넘는가 (mock 은 불인정) |

실호출 모델은 기본 **sonnet**입니다. 바꾸려면 PowerShell 에서 `$env:REVIEW_MODEL="haiku"` 처럼 환경변수를 둡니다. 실호출이 끝나면 비용이 화면과 `results/<해시>/meta.json`에 남습니다.
