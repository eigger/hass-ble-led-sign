<!-- hass-standards:header:start -->
# BLE LED Sign for Home Assistant

CoolLED, iLed, iPixel Color Bluetooth 매트릭스 LED 전광판의 스크롤 텍스트·상태 메시지·그래픽·동적 레이아웃을 자동화하는 Home Assistant 커스텀 통합입니다.

[English](README.md) | **한국어**

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-ble-led-sign?style=flat)](https://github.com/eigger/hass-ble-led-sign/releases)
[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5?style=flat)](#설치)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.1.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/tests.yml?branch=master&style=flat&label=Tests)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/validate.yml?branch=master&style=flat&label=Validate)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-ble-led-sign?style=flat)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/eigger/hass-ble-led-sign/latest/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/eigger/hass-ble-led-sign/releases)
<!-- hass-standards:badges:end -->
<!-- hass-standards:header:end -->

![LED Sign](custom_components/ble_led_sign/brand/logo.png)

## 지원 기기

| 기기 제품군 | 드라이버 | 블루투스 검색 조건 | 주요 특징 |
|-------------|----------|-------------------|-----------|
| **CoolLED / iLed** | `coolled` | `CoolLED*`, `iLed*`, UUID `0xFFF0` | 매트릭스 제어, 7색/풀 RGB, 내장 애니메이션, 속도 및 밝기 조절 |
| **iPixel Color** | `ipixel_color` | `LED_BLE*`, UUID `0x00FA`, `0xAE00` | 실시간 텍스트, 이미지, 애니메이션, 시계/점수판 제어 프레임 |

## 요구사항

- **Home Assistant:** 2025.1.0 이상.
- **Bluetooth:** 로컬 Bluetooth 어댑터 또는 `active: true`로 설정한 ESPHome Bluetooth 프록시.
- **기기:** [지원 기기](#지원-기기)에 나열된 전광판.

## 설치

<!-- hass-standards:installation:start -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eigger&repository=hass-ble-led-sign)
<!-- hass-standards:installation:end -->

1. 위 배지를 클릭해 마켓플레이스에서 저장소를 엽니다.
2. 저장소를 직접 추가하려면 **설정 → 마켓플레이스 → 링크에서 추가**에서 <https://github.com/eigger/hass-ble-led-sign>을 입력합니다. 안내가 표시되면 GitHub 계정을 연결합니다.
3. **설치**를 선택합니다. 재시작 안내가 표시되면 Home Assistant를 재시작합니다. 설치가 끝나면 [설정](#설정)으로 이동합니다.

## 설정

1. **설정 → 기기 및 서비스**에서 **통합 추가 → BLE LED Sign**을 선택하거나 자동으로 발견된 항목을 설정합니다.
2. 목록에서 전광판을 선택합니다.

[기기 암호, 재시도 횟수, 패킷 간격](docs/ko/user-guide.md#설정-옵션)은 **구성**에서 언제든지 변경할 수 있습니다.

## 빠른 시작

`ble_led_sign.write` 액션을 사용하여 전광판에 날씨 아이콘과 텍스트를 출력할 수 있습니다:

```yaml
action: ble_led_sign.write
target:
  entity_id: light.ble_led_sign_display_power  # 또는 device_id: <기기_ID>
data:
  payload:
    - type: text
      value: "Hello HA"
      x: 2
      y: 1
      size: 10
      color: cyan
    - type: icon
      value: "weather-sunny"
      x: 36
      y: 1
      size: 10
      color: yellow
```

## 중요 제한사항

- **한 번에 한 기기만 연결됩니다.** Home Assistant에서 연결하기 전에 CoolLED1248, iPixel Color 등 제조사 앱을 종료하거나 연결을 해제하세요.
- **패킷 손실.** BLE MTU 제한과 전파 간섭 때문에 큰 이미지나 애니메이션의 전송이 실패할 수 있습니다. 실패하면 **재시도 횟수**나 **패킷 간격**을 늘려보세요.

### 제거

마켓플레이스에서 저장소를 열고 **⋮ → 제거**를 선택합니다. 안내에 따라 기존 설정을 삭제하고, 재시작 안내가 표시되면 Home Assistant를 재시작합니다.

## 문서

- [사용자 가이드](docs/ko/user-guide.md) — 기기별 사양, 지원 색상, 엔티티, 액션, 애니메이션, `imagespec` 레이아웃.
- [문제 해결](docs/troubleshooting.ko.md): 연결 문제 진단, 프록시 설정 점검 및 진단 엔티티 활용법.
- [개발 및 테스트](docs/development.md): 개발 환경 구성, 테스트 실행 및 저장소 표준 안내.
- [블루투스 프록시 가이드](https://github.com/eigger/blesession/blob/main/docs/bluetooth.ko.md): 권장 ESPHome 프록시 하드웨어 및 설정 방법.
- [Payload 작업 예제](docs/payload.ko.md): 실행 가능한 레이아웃과 기기 출력 설정.

<!-- hass-standards:support:start -->
## 지원

- [Issues](https://github.com/eigger/hass-ble-led-sign/issues): 버그를 신고하거나 기능을 요청하세요.
- [Discussions](https://github.com/eigger/hass-ble-led-sign/discussions): 질문하고 사용 경험을 공유하세요.
<!-- hass-standards:support:end -->

<!-- hass-standards:related-projects:start -->
<!-- hass-standards:related-projects:end -->

<!-- hass-standards:license:start -->
## 라이선스

[MIT License](LICENSE) 라이선스로 배포됩니다.
<!-- hass-standards:license:end -->
