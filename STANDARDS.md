# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/main
- 참조 커밋 SHA: `c3f2e254c0867f1825ca8f636c347582e06707db`
- 채택일: 2026-10-18
- profile: integration / ha (실제 HA fixture·통합 로딩 필수)
- 적용 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황표: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 조율 / 구현 / 독립 리뷰·검증 담당: root / ble_led_sign_impl / ble_led_sign_review
- 중앙 현황 갱신일: 2026-10-18
- 실제 기본 브랜치: master
- 테스트 경로: tests/components/ble_led_sign/
- 변경 전 지원 최소 HA / 선언 근거: 2025.1.0 (hacs.json "homeassistant": "2025.1.0")
- 적용 후 지원 최소 HA: 2025.1.0 (기존 지원 최소 보존)
- current HA 테스트 환경: Python 3.14.5 / Home Assistant 2026.10.2 / pytest-homeassistant-custom-component 0.13.373 (38 passed)
- 최소 HA 검증 환경: Python 3.13.14 / Home Assistant 2025.1.0 / pytest-homeassistant-custom-component 0.13.201 (38 passed)
- 최소 package 검증: imagespec==1.1.0
- PR: [PR #13](https://github.com/eigger/hass-ble-led-sign/pull/13)
- CI 검증: [Tests](https://github.com/eigger/hass-ble-led-sign/actions/runs/39113466684), [Validate](https://github.com/eigger/hass-ble-led-sign/actions/runs/39113466662)
- 예외: 없음

## 예외

| 규칙 ID | 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 | 해당 사항 없음 | - | - |
