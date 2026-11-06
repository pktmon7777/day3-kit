# 팀 코딩 컨벤션
C1. 매직넘버 금지 — 0, 1, -1 이외의 숫자 리터럴은 #define 상수를 쓴다. (category=magic-number, severity=low)
C2. 반환값 확인 — malloc/calloc/fopen 결과는 NULL 체크 필수. (category=unchecked-return, severity=high)
C3. 전역 변수 금지 — const가 아닌 전역 변수를 선언하지 않는다. (category=global-variable, severity=medium)
