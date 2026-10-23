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
- current HA 테스트 환경: 로컬 Python 3.14.5 / 원격 CI Python 3.14.8 / Home Assistant 2026.10.2 / pytest-homeassistant-custom-component 0.13.373 (41 passed)
- 최소 HA 검증 환경: 로컬 Python 3.13.14 / 원격 CI Python 3.13.16 / Home Assistant 2025.1.0 / pytest-homeassistant-custom-component 0.13.201 (41 passed)
- 최소 package 검증: imagespec==1.1.0 (Core 기본 의존성인 pillow, requests를 manifest에서 제외하고 imagespec만 선언)
- PR: [PR #13](https://github.com/eigger/hass-ble-led-sign/pull/13)
- CI 검증: [Tests](https://github.com/eigger/hass-ble-led-sign/actions/runs/39115741996), [Validate](https://github.com/eigger/hass-ble-led-sign/actions/runs/39115742010)
- 예외: 없음

## 예외

| 규칙 ID | 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 | 해당 사항 없음 | - | - |

- Reviewed release standards SHA: `fd4162c0b93fbe8e109f99c787773ae09ba157e1`


## 2026-10-23 ZIP release and Downloads update

Base commit: `44d51e0332362bce84c3520ebc9b685074f74f47`. HACS remains Custom. `hacs.json` now selects `ble_led_sign.zip`; publishing the next release builds and attaches that integration ZIP through the pinned central action. Analytics Usage is replaced by Downloads. The archive contains tracked integration files at its root. No existing release/tag/assets are modified.

Implementation and review: root; generated release caller reuses the independently reviewed central ZIP contract. Support minimum, manifest, code, dependencies, README body and prior adoption exceptions are preserved. Verification evidence is recorded in ADOPTION_CHECKLIST.md; this scoped update does not establish full standards compliance.


## 2026-10-23 blesession and diagnostics

Scoped implementation reference: hass-repo-standards `3897aaa8564e8e22582d72843534c92e87f83478`, hass-niimbot `0af28aafa29914cc61a9a117a3d29d006a18348b`, blesession public API 0.9.0 (source `4078a4025f6e07140c0aaffd92168a712f90b127`). This entry records the BLE change only; it does not assert a new complete standards adoption or update the existing CI pins.

- Both CoolLED and iPixel Color use `ble_session`, queued `Notifications`, guarded writes, `run_attempts`, and frozen `SessionReports`. Services and entities share the domain lock per attempt; route lookup happens after acquiring it on every attempt.
- Five diagnostic entities: active BLE connection, last operation, last error stage, last failure timestamp, failure count. Report attributes retain failure details/timings and available radio facts. Final failures survive recovery; intermediate retry failures and cancellations do not increment the final failure count. Counts are in-memory and reset on reload.
- Integration diagnostics download excludes config/password/content and redacts radio identities and free-text errors. Raw entity attributes still require redaction before sharing.
- Explicit password rejection stops retries. Silent authentication, dropped connections and hung writes fail visibly. Setup/MTU negotiation is limited to 15 seconds, individual GATT writes to 10 seconds; existing protocol response limits remain and bulk transfers have no overall deadline. Unload cancels queued/running sessions and waits for connection cleanup.
- Active iPixel dimension queries no longer cache default dimensions after silence, and keep their device object across advertisements while a query runs.
- English/Korean DOC-07 troubleshooting updated; the prior Korean URL is retained as a forwarding document. Support minimum stays HA 2025.1.0; runtime manifest adds `blesession>=0.9.0`; CI minimum-package and updater selections include it.

Verification (real HA fixtures, mocked external BLE boundary): Python 3.14.7 / HA 2026.10.2 / pytest HA plugin 0.13.373: **55 passed**; Python 3.13.15 / HA 2025.1.0 / plugin 0.13.201: **55 passed**. Both install blesession 0.9.0 and imagespec 1.1.0; both `uv pip check` pass. Ruff lint/format, `git diff --check`, and the central DOC-07 checker pass. New regression coverage includes recovery/error retention, unreachable devices, rejected/silent authentication, dropped notification waits, bounded writes, cancellation/unload cleanup, report fallback/redaction, route lookup under lock and iPixel metadata preservation. No physical panel, proxy hardware, live HA UI or remote CI was tested in this change.
