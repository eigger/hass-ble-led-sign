# BLE LED Sign

<!-- hass-standards:badges:start -->
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square)](#설치)
[![Release](https://img.shields.io/github/v/release/eigger/hass-ble-led-sign?style=flat-square)](https://github.com/eigger/hass-ble-led-sign/releases)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.1.0-41BDF5?style=flat-square)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/tests.yml?branch=master&style=flat-square&label=Tests)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/validate.yml?branch=master&style=flat-square&label=Validate)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-ble-led-sign?style=flat-square)](LICENSE)
[![Analytics reporting installs](https://img.shields.io/badge/dynamic/json?style=flat-square&color=41BDF5&label=Usage&query=%24.ble_led_sign.total&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json)](https://analytics.home-assistant.io/)
<!-- hass-standards:badges:end -->

[English](README.md) | **한국어**

BLE LED Sign은 블루투스 저전력(BLE) 매트릭스 LED 전광판(CoolLED, iLed, iPixel Color 등)을 제어하기 위한 Home Assistant 통합구성요소입니다. 제조사 전용 스마트폰 앱 대신 Home Assistant에서 직접 스크롤 텍스트, 상태 메시지, 그래픽 및 동적 레이아웃을 자동화할 수 있습니다.

## 지원 기기

드라이버 기반 아키텍처를 통해 다양한 하드웨어 제품군을 지원합니다:

| 기기 제품군 | 드라이버 | 블루투스 검색 조건 | 주요 특징 |
|-------------|----------|-------------------|-----------|
| **CoolLED / iLed** | `coolled` | `CoolLED*`, `iLed*`, UUID `0xFFF0` | 매트릭스 제어, 7색/풀 RGB, 내장 애니메이션, 속도 및 밝기 조절 |
| **iPixel Color** | `ipixel_color` | `LED_BLE*`, UUID `0x00FA`, `0xAE00` | 실시간 텍스트, 이미지, 애니메이션, 시계/점수판 제어 프레임 |

상세 하드웨어 사양 및 색상 지원 방식은 [사용자 가이드](docs/ko/user-guide.md)를 참고하세요.

## 요구사항

- **Home Assistant**: `2025.1.0` 이상.
- **블루투스**: 로컬 블루투스 어댑터 또는 `active: true`로 설정된 [ESPHome 블루투스 프록시](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.ko.md).

## 설치

### HACS를 통한 설치 (권장)

1. Home Assistant에서 HACS 메뉴로 이동한 후 **통합구성요소**를 선택합니다.
2. 우측 상단 메뉴에서 **사용자 지정 저장소**를 클릭합니다.
3. 저장소 URL `https://github.com/eigger/hass-ble-led-sign`을 입력하고 범주로 **통합구성요소**를 선택하여 추가합니다.
4. **BLE LED Sign**을 검색하여 **다운로드**한 후 Home Assistant를 다시 시작합니다.

### 수동 설치

1. 본 저장소의 `custom_components/ble_led_sign` 폴더를 Home Assistant의 `<config_dir>/custom_components/` 디렉터리에 복사합니다.
2. Home Assistant를 다시 시작합니다.

통합구성요소를 삭제하려면 `custom_components/ble_led_sign` 폴더를 삭제하고 Home Assistant를 다시 시작하세요.

## 설정

1. Home Assistant의 **설정 → 기기 및 서비스**로 이동합니다.
2. **통합구성요소 추가**를 클릭하고 **BLE LED Sign**을 검색합니다 (기기가 이미 감지된 경우 알림에서 구성을 누를 수도 있습니다).
3. 검색된 전광판 기기를 선택하여 추가를 완료합니다.
4. 기기 암호, 재시도 횟수, 패킷 간격 등의 옵션은 언제든지 **구성** 메뉴에서 변경할 수 있습니다. 자세한 내용은 [설정 옵션](docs/ko/user-guide.md#설정-옵션)을 참고하세요.

## 빠른 시작

`ble_led_sign.write` 액션을 사용하여 전광판에 날씨 아이콘과 텍스트를 출력할 수 있습니다:

```yaml
action: ble_led_sign.write
target:
  device_id: <기기_ID>
data:
  payload:
    - icon:
        name: weather-sunny
        color: yellow
    - text:
        content: " 안녕하세요 Home Assistant!"
        color: cyan
```

다양한 애니메이션, 이미지 렌더링 문법 및 예제는 [사용자 가이드](docs/ko/user-guide.md)를 참고하세요.

## 중요 제한사항

- **동시 연결 제한**: BLE 전광판은 한 번에 하나의 중앙 기기(Central)와만 연결할 수 있습니다. 스마트폰의 제조사 앱(CoolLED1248, iPixel Color 등)이 실행 중이면 Home Assistant에서 연결할 수 없으므로 앱을 완전히 종료해야 합니다.
- **패킷 전송 간격**: BLE 대역폭 한계로 인해 신호 간섭이 있는 환경에서는 대용량 데이터 전송 시 패킷 손실이 발생할 수 있습니다. 전송이 불안정한 경우 통합 구성 옵션에서 **재시도 횟수**나 **패킷 간격**을 늘려주세요.
- 연결 문제 해결 및 진단 방법은 [문제 해결 문서](docs/ko/troubleshooting.md)를 확인하세요.

## 문서

- [사용자 가이드](docs/ko/user-guide.md): 제품군별 상세 사양, 엔티티 목록, 서비스 참조 및 `imagespec` 선언형 레이아웃 가이드.
- [문제 해결](docs/ko/troubleshooting.md): 연결 문제 진단, 프록시 설정 점검 및 진단 엔티티 활용법.
- [개발 및 테스트](docs/development.md): 개발 환경 구성, 테스트 실행 및 저장소 표준 안내.
- [블루투스 프록시 가이드](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.ko.md): 권장 ESPHome 프록시 하드웨어 및 설정 방법.

## 지원

- 버그 제보나 문제 발생 시 [GitHub Issues](https://github.com/eigger/hass-ble-led-sign/issues)를 이용해 주세요.
- 사용 질문이나 기능 제안은 [GitHub Discussions](https://github.com/eigger/hass-ble-led-sign/discussions)를 이용해 주세요.

## 라이선스

이 프로젝트는 [MIT License](LICENSE)에 따라 제공됩니다.
