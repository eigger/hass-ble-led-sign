# 공통 규칙 적용 체크리스트

이 문서는 `hass-ble-led-sign` 저장소에 `hass-repo-standards`를 적용하고 검증한 결과를 기록한 체크리스트입니다.

## 검토 대상

| 항목 | 값 |
|---|---|
| 통합 리포 / 실제 기본 브랜치 | eigger/hass-ble-led-sign / master |
| domain / 구현 경로 | ble_led_sign / custom_components/ble_led_sign/ |
| 검토 대상 통합 커밋 / 채택 PR | PR #13 (`adopt-shared-standards`) |
| 검토한 표준 전체 커밋 SHA | c3f2e254c0867f1825ca8f636c347582e06707db |
| 검토일 / 조율 담당 | 2026-10-18 / root |
| 구현 서브 에이전트 / 독립 리뷰·검증 서브 에이전트 | ble_led_sign_impl / ble_led_sign_review |
| 중앙 현황표 반영일 / 기록 | 2026-10-18 |
| 변경 전 지원 최소 HA / 근거 파일(hacs.json·manifest·README) | 2025.1.0 / hacs.json ("homeassistant": "2025.1.0") |
| 유지·변경할 지원 최소 / 변경 시 실제 비호환 근거·명시적 승인 | 2025.1.0 보존 (OptionsFlowWithReload -> OptionsFlow 하위호환성 수정 완료) |
| current 테스트 HA / 호환 Python·플러그인 | 로컬 Python 3.14.5 / 원격 CI Python 3.14.8 / Home Assistant 2026.10.2 / pytest-homeassistant-custom-component 0.13.373 |
| 최소 테스트 HA / 호환 Python·플러그인 | 로컬 Python 3.13.14 / 원격 CI Python 3.13.16 / Home Assistant 2025.1.0 / pytest-homeassistant-custom-component 0.13.201 |
| profile / 테스트 경로 | integration / ha, tests/components/ble_led_sign/ |
| 이전 검토 기록 | 최초 검토 |
| 채택 판정 | PASS |

상태: `PASS` = 근거로 확인, `EXCEPTION` = 기록된 예외, `N/A` = 해당 없음.

## 채택·구조·사용자 데이터

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| GOV-01, GOV-02 | `STANDARDS.md`에 표준 SHA·profile·실제 기본 브랜치·예외 기록, workflow/action은 검토 SHA로 고정 | PASS | STANDARDS.md 생성 완료 (SHA `c3f2e254c0867f1825ca8f636c347582e06707db`, profile `integration / ha`, 기본 브랜치 `master`). 워크플로우 호출 SHA 고정. |
| GOV-03 | 새 표준 채택 변경의 영향·이관 방법과 명시적 채택 PR 확인. 규칙 자체를 변경하면 공통 CHANGELOG 기록 | PASS | adopt-shared-standards 브랜치에서 변경 분리 및 점검표 작성. |
| GOV-04 | 중앙 표에 작업 시작·단계 변경·종료 상태, 담당·적용 내용·검증/리뷰 근거·남은 작업 갱신, 타 리포 기록 보존 | PASS | adoption-status.md 형식에 맞춰 기록 완료. |
| GOV-05 | 구현과 독립 리뷰·검증을 별도 서브 에이전트에게 위임, 지적 수정·재검증 및 결과 취합 | PASS | root 조율 하에 ble_led_sign_impl 구현 및 ble_led_sign_review 검증 수행. Opus 독립 리뷰 지적 사항 반영 완료. |
| HA-01, HA-13 | `custom_components/<domain>/`와 domain 일치, 필요한 모듈·공개 API·생명주기는 Core 대응 구조 | PASS | `custom_components/ble_led_sign` 도메인 일치. Coordinator, ConfigEntry 생명주기 및 entity 구조 준수. |
| HA-02 | manifest 필드·정렬·동작 선언 확인, 공식 품질 등급 자가 표기 없음 | PASS | `manifest.json` Bluetooth matcher, requirements, version, iot_class 정상. Core 의존성인 `pillow`, `requests`를 manifest에서 제외하고 `imagespec[datamatrix]>=1.1.0`만 선언하여 표준 준수. |
| HA-03 (권장) | 공통 상수·설정·갱신·플랫폼 역할 및 프로토콜 경계에 맞게 모듈 구성 | PASS | `const.py`, `coordinator.py`, `config_flow.py`, `drivers/` 모듈화 유지. |
| HA-04, HA-08 | UI 설정·중복·안정적 식별 및 기능별 options/reauth/reconfigure, entity 의미·registry 영향 확인 | PASS | Bluetooth 자동 검색 및 User config flow, 중복 방지(`async_set_unique_id`), OptionsFlow 정상 동작 및 update listener 등록. |
| HA-01, HA-04, HA-08, REL-01, REL-03 | domain·unique ID·entry schema·상태/통계 계약 변경 시 migration 테스트와 사용자 조치 안내 | PASS | unique_id 및 config entry 데이터 스키마 변경 없음. 기존 사용자 호환 유지. |
| HA-05, HA-06 | setup 실패 구분, unload/reload·부분 실패의 task/listener/연결 정리, async·timeout·취소 처리 | PASS | 플랫폼 setup 실패 시 rollback 정리 로직 추가, unload 시 리스너 및 서비스 등록 해제, timeout 처리 확인. |
| HA-07 | 중복 polling·property I/O 방지, push 보존, unavailable/unknown·실패 후 복구 | PASS | Bluetooth push 콜백 기반 상태 수신, 불필요한 property I/O 없음. |
| HA-11, HA-12 | 번역·action/schema 일치, 로그/diagnostics/fixture 비식별화와 제공 시 redaction 테스트 | PASS | `strings.json`, `translations/en.json`, `translations/ko.json` 키 동기화 및 유효성 검증 완료. 로그 MAC 주소 비식별화 가이드 제공. |

## 실제 HA 테스트·호환성·의존성

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| TEST-08 | `tests/components/<domain>/`에 구현과 대응하는 테스트·domain fixture 배치, discovery·CI 경로 일치 | PASS | `tests/components/ble_led_sign/` 아래 13개 테스트 모듈(`test_*.py`, 총 41개 테스트) 배치. pyproject.toml testpaths 설정. |
| TEST-02, TEST-03, DEP-07 | 실제 HA·호환 플러그인과 `hass`/`enable_custom_integrations` fixture 사용, HA core stub/복사본/`--no-deps`로 대체하지 않음 | PASS | `pytest-homeassistant-custom-component` 사용, Core 모의 stub 완전 제거, 실제 HA 컴포넌트 로딩. |
| TEST-09 | 실제 loader·config entry manager로 setup/플랫폼 로딩, HA 상태·registry·service/action으로 결과 검증 | PASS | 실제 `hass.config_entries.async_setup`, `async_forward_entry_setups` 및 `hass.services.async_call`로 검증. entity_id 타깃 해석 검증 완료. |
| TEST-01, TEST-06, TEST-07 | 구현 기능별 성공·실패·중복·migration·unload·복구 회귀 검증, 외부 통신 경계만 mock, skip 사유 | PASS | Bluetooth discovery, in-progress flow, config flow, entities, drivers, services, dry_run, validation error 회귀 검증. BleakTransport GATT 통신 경계만 mock. |
| TEST-04, HACS-01 | 변경 전 지원 최소·current·각 Python/플러그인 분리, 선언한 정확한 최소 검증, 상향 시 비호환 근거·명시적 승인 확인 | PASS | Current(로컬 3.14.5 / 원격 3.14.8 / HA 2026.10.2) 및 Min(로컬 3.13.14 / 원격 3.13.16 / HA 2025.1.0) 환경에서 41개 테스트 모두 100% 통과. |
| TEST-05, HA-10, DEP-02, DEP-05 | imagespec·blesession 등 최소/현재 라이브러리 별도 환경, 실제 HA 테스트·정확한 설치값·API 경계 검증 | PASS | `imagespec[datamatrix]>=1.1.0` 연동 및 렌더러 테스트 검증 완료. |
| DEP-01, DEP-06 | Python runtime은 manifest requirements, HA domain은 dependencies/after_dependencies, 테스트·린트 requirements는 별도 | PASS | `manifest.json`, `requirements_test.txt`, `requirements_test_min.txt`, `requirements_lint.txt` 분리. Core 내장 패키지(pillow, requests)는 manifest requirements에서 제외. |
| DEP-07, CI-06 | 실제 사용하는 HA 구성요소의 requirements·필수 재귀 의존성·선택 로딩 경로 설치, resolver·`pip check` 통과 | PASS | `.venv` 및 `.venv-min`에서 `uv pip check` 충돌 없음 확인 완료. |
| DEP-02, DEP-03, DEP-08 | 의존성 추가/변경의 버전·extras·marker·선언 위치·지원 플랫폼·라이선스 검토, 실제 HA 테스트와 문서 갱신 | PASS | 추가 의존성 검토 완료 (Apache-2.0 / MIT / LGPL 호환). |

### 검증 환경 상세

| 검증 축 / 상태 | 통합 커밋 | Python / HA / 플러그인 실제 버전 | 대상 패키지 실제 버전·extras·marker | 명령·테스트 결과·pip check / CI run·job | skip·제외·미검증 범위 |
|---|---|---|---|---|---|
| 현재 환경 / PASS | [PR #13](https://github.com/eigger/hass-ble-led-sign/pull/13) | 로컬 Python 3.14.5, 원격 CI Python 3.14.8 / HA 2026.10.2 / pytest-homeassistant-custom-component 0.13.373 | imagespec 1.1.0 | 원격 Tests(39115741996) pass, 로컬 pytest 41 passed | 없음 (0 skipped) |
| 정확한 최소 HA / PASS | [PR #13](https://github.com/eigger/hass-ble-led-sign/pull/13) | 로컬 Python 3.13.14, 원격 CI Python 3.13.16 / HA 2025.1.0 / pytest-homeassistant-custom-component 0.13.201 | imagespec 1.1.0 | 원격 Tests(39115741996) pass, 로컬 pytest 41 passed | 없음 (0 skipped) |
| 정확한 최소 라이브러리 / PASS | [PR #13](https://github.com/eigger/hass-ble-led-sign/pull/13) | Python 3.14 / 3.13 | imagespec 1.1.0 | 원격 Tests(39115741996) minimum-packages pass | 없음 (0 skipped) |
| 원격 Validate / PASS | [PR #13](https://github.com/eigger/hass-ble-led-sign/pull/13) | Ubuntu latest | HACS 9 checks, Hassfest valid 0 invalid | 원격 Validate(39115742010) 성공 | 없음 |

## HACS·CI·의존성 업데이트

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| HACS-01, HACS-02 | 루트 README/LICENSE/hacs.json, 검증한 최소 HA, 실제 배포 구조와 필요한 옵션 일치 | PASS | `README.md`, `LICENSE`, `hacs.json` (`"homeassistant": "2025.1.0"`) 일치. 배포 구조 `custom_components/ble_led_sign` 정상. |
| HACS-03, HACS-05 | Default 여부는 목록 근거로 확인, 로컬 brand/icon.png 또는 원격 brands 근거와 HACS/Hassfest 실제 실행, ignore는 이유·해제 조건 기록 | PASS | HACS Custom 유지 (`.hass-standards.json` "hacs": "custom"). |
| HACS-06 (권장) | description·topics·issue 경로·brands 및 사용하는 HACS 필드 지원 확인 | PASS | 저장소 description, topics, issues, discussions 활성화 확인. |
| CI-01, CI-02 | Validate/Python Tests 공통화, 확장 job 유지, PR·실제 기본 브랜치 push·dispatch 및 필요한 schedule | PASS | `.github/workflows/tests.yml`, `validate.yml`, `update_dependencies.yml` 표준 호출 구성. 이벤트: PR, push(master), workflow_dispatch, schedule. |
| CI-03, CI-05, CI-08 | 최소 권한·checkout 자격증명 비보존·timeout·concurrency, full SHA·갱신 관리, 비신뢰 입력·secrets 경계 | PASS | `permissions: contents: read`, `persist-credentials: false`, full SHA(`c3f2e254c0867f1825ca8f636c347582e06707db`) 고정. 공용 workflow 내 lint 10m, test 20m timeout 적용. |
| CI-04, CI-07, CI-12 | 실패를 숨기지 않는 실제 `ha` 필수 테스트, 버전별 환경·cache·Ruff 설정과 required checks 이름 확인 | PASS | `test-profile: ha`, ruff 0.17.1 린트/포맷 설정. |
| DEP-03, DEP-04, CI-09 | updater의 선택 package·연산자/extras/marker 보존, 안정 버전·major 정책, 실제 기본 브랜치·단일 bot branch·PR만 제안 | PASS | `.github/workflows/update_dependencies.yml` 공통 워크플로우 호출 설정. |
| CI-09, CI-10, DEP-08 | 변경 tree의 새 하한·실제 HA 검증 후 PR 동기화, 실패 시 중단·변경 없음 시 기존 PR 정리, 후속 required checks 충족 방식 확인 | PASS | validation-command로 `tests/components/ble_led_sign` 지정. |

## README·Bluetooth·유지보수

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| DOC-01, DOC-02, DOC-06 | 영어 README.md·한국어 README.ko.md·상호 링크·기존 내용 보존, 간결한 제목/소개/핵심지원/최소요구/빠른설치·설정/짧은예제/중요제한/문서목록, 상세옵션·긴YAML·참조·개발/실HA테스트·의존성/검증범위를 docs·examples 등으로 보존·분리하고 유효한 링크 제공, 실제 활성 Issues·Discussions 또는 대체 지원 경로·실제 LICENSE 링크 | PASS | 간결한 `README.md` 및 `README.ko.md` 작성 및 상호 링크. 상세 내용은 `docs/user-guide.md`, `docs/ko/user-guide.md`, `docs/troubleshooting.md`, `docs/ko/troubleshooting.md`, `docs/development.md`로 분리 보존. |
| DOC-03, DOC-04, DOC-05 | 제목 아래 관리 블록, flat-square·순서·실제 조건별 배지, CI 실제 기본 브랜치, 필수 동적 Usage·Analytics 참여 설치 의미·미집계/조회 실패와 0 설치 구분·이전 안내 보존 | PASS | `sync_badges.py` 관리 블록 적용 및 `--check` 무오류 확인. Usage 동적 배지 포함. |
| HA-09, HA-10 | BLE 사용 시 HA Bluetooth API·라이브러리 공개 경계, 지원한 proxy 경로·재연결·취소·서비스 변경 검증 | PASS | `homeassistant.components.bluetooth` 공개 API (`async_ble_device_from_address`, `async_last_service_info` 등) 준수. |
| DOC-07 | blesession/proxy 통합 README의 핵심조건·영어 기본/한국어 대응 사용자 설정 링크(작성·구현 가이드로 대체 금지), 공통 Bluetooth 설정·추천기기·active 스캔/GATT 차이, 통합별 troubleshooting 또는 공통 링크+모델고유조건·실제진단·민감정보 제거 제보 안내 | PASS | `docs/troubleshooting.md` 및 `docs/ko/troubleshooting.md`에 프록시 설정, `active: true`, 전원 공급, 패킷 간격 조절, 모바일 앱 연결 해제 안내 및 공통 프록시 가이드 링크 제공. |
| DOC-07, HA-12 | 기기별 깨우기·인증·타 앱 연결·전송 제약, 실제 검증 경로와 미검증 범위, 공개 문제 로그 비식별화 | PASS | 전송 제약(BLE 단일 접속 제한, 패킷 손실 대처) 및 이슈 제보 시 민감정보(MAC 주소 등) 제거 가이드 문서화. |
| HACS-04, REL-01, REL-02, REL-03, CI-11 | 통합 릴리스 시 같은 검증 commit/tag·manifest 버전·산출물·권한, 사용자 영향·지원 변경·제한 안내 | PASS | 릴리스 절차 및 manifest 버전 동기화 원칙 확인. |
| REL-04 | 이전/중단 시 README 상단 경로·유지보수 상태·재등록 여부, 자동 이전으로 오인하지 않는 안내 | N/A | 이전 또는 지원 중단 계획 없음. |
| REL-05 (권장) | 의존성/HA API 변경과 기능 변경 분리, 표준 변경은 명시적 채택 PR로 반영 | PASS | `adopt-shared-standards` 전용 브랜치에서 표준 채택 작업 분리 수행. |

## 예외와 남은 작업

예외 원본은 `STANDARDS.md`입니다.

| 규칙 ID | 예외 위치 / 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 | 해당 사항 없음 | - | - |


## 2026-10-23 HACS ZIP and Downloads (scoped)

- Target base: `44d51e0332362bce84c3520ebc9b685074f74f47`; reviewed release central: `fd4162c0b93fbe8e109f99c787773ae09ba157e1`.
- Scope: HACS-04/CI-11 release ZIP and DOC-03/05 Downloads replacing Analytics Usage. No release is created during this update.
- Validation: pending badge/release contract checks, actionlint, actual local ZIP build and remote PR CI. Full adoption, device and real release upload are not asserted by this partial change.
