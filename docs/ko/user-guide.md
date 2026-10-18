# BLE LED 전광판 사용자 가이드

[English User Guide](../user-guide.md) · [한국어 README](../../README.ko.md) · [문제 해결](troubleshooting.md)

Home Assistant에서 블루투스 저전력(BLE) 매트릭스 LED 전광판을 통합 제어하는 가이드입니다.

## 아키텍처 및 지원 하드웨어

드라이버 기반 아키텍처를 채택하여 다양한 LED 전광판 제품군(`custom_components/ble_led_sign/drivers/`)을 통일된 엔티티와 액션 인터페이스로 제어할 수 있습니다.

### 지원 드라이버 제품군

| 드라이버 | 지원 제품군 | 블루투스 검색 조건 | 주요 기능 |
|----------|-------------|-------------------|-----------|
| `coolled` | CoolLED 1248, CoolLED S/X, CoolLED M/U/UX, CoolLED 536, iLed* | 기기 이름 접두사 또는 UUID `0xFFF0` | 전원, 밝기, 스크롤 속도, 스크롤 모드, 텍스트, 이미지, 애니메이션, JT 프로그램, 음악 이퀄라이저, 아이콘 |
| `ipixel_color` | `LED_BLE_*` (iPixel Color) | 이름 접두사 `LED_BLE*` 또는 UUID `0x00FA`, `0xAE00` | 전원, 밝기, 텍스트 속도, 상하반전, 지우기, 카운트다운, PNG/GIF 전송, 제어 프레임 |

### 색상 유형 (Color Types)

LED 전광판은 하드웨어에 따라 다음과 같은 색상 형식을 지원합니다:

| 유형 | 이름 | 지원 색상 |
|------|------|-----------|
| 0 | 단색 (Single) | `off`, `on`, `black`, `white` |
| 1 | 7색 (Seven) | 단색 + `red`, `yellow`, `green`, `cyan`, `blue`, `purple` |
| 2+ | 풀컬러 (Colorful) | 7색 + `orange`, `pink`, `#RRGGBB` (전광판 팔레트 근사값으로 자동 매핑) |

검색 후 Home Assistant 기기 정보 페이지에서 해상도(행 × 열), 펌웨어 버전, 색상 형식을 확인할 수 있습니다.

---

## 엔티티 구성

연결된 기기 드라이버가 지원하는 기능에 따라 필요한 엔티티가 자동 등록됩니다:

| 플랫폼 | 엔티티 | 설명 |
|--------|--------|------|
| `light` | 디스플레이 전원 | 전광판 전원 켜기/끄기 및 밝기 조절. CoolLED의 경우 스크롤 모드가 조명 효과(effect)로 제공됩니다. |
| `number` | 스크롤 속도 | 텍스트/애니메이션 스크롤 속도 조절 (0–255). |
| `number` | 카운트다운 (분) | 카운트다운 타이머 시간 설정 (iPixel Color). |
| `select` | 스크롤 모드 | CoolLED 애니메이션 모드 (`static`, `left`, `right`, `up`, `down`, `snowflake`, `picture`, `laser`). |
| `select` | 디스플레이 모드 | iPixel Color 표시 모드 (`normal`, `clock`, `stopwatch`, `scoreboard`). |
| `switch` | 화면 상하반전 | 전광판 화면을 180도 뒤집어 출력 (iPixel Color). |
| `button` | 화면 지우기 | 전광판에 저장된 내용 또는 슬롯 지우기 (iPixel Color). |
| `button` | 카운트다운 시작 | 디스플레이에 설정된 카운트다운 타이머 시작 (iPixel Color). |
| `text` | 스크롤 텍스트 | 변경 즉시 전광판으로 전송되는 텍스트 입력창. |
| `image` | 마지막 전송 화면 | 전광판에 성공적으로 전송된 마지막 렌더링 이미지. |
| `image` | 렌더링 미리보기 | `dry_run: true` 또는 마지막 렌더링으로 생성된 미리보기 이미지. |

---

## 설정 옵션

**설정 → 기기 및 서비스 → BLE LED Sign → 구성**에서 변경할 수 있습니다:

| 옵션 | 기본값 | 범위 | 설명 |
|------|--------|------|------|
| **디바이스 비밀번호** | `000000` | 6자리 | 비밀번호 인증이 필요한 CoolLED/iPixel 보호 모델용 비밀번호. |
| **재시도 횟수** | 3 | 1–10 | BLE 전송 실패 시 재시도 횟수. |
| **패킷 간격 (ms)** | 15 | 0–1000 | BLE 패킷 전송 간 딜레이(밀리초). 패킷 손실이 발생하는 경우 50–100ms로 상향 조정 권장. |

---

## `imagespec` 선언형 레이아웃 렌더링

`ble_led_sign.write` 액션은 [imagespec](https://github.com/eigger/imagespec) 라이브러리를 사용하여 YAML 형식으로 화면을 구성합니다.

- **해상도**: 서비스 호출 시 지정할 필요 없이 기기 프로필(예: 48 × 12)에 맞춰 캔버스 크기가 자동 설정됩니다.
- **색상 양자화**: 전광판 팔레트에 없는 색상은 가장 가까운 지원 색상으로 자동 변환됩니다.
- **화면 회전**: `rotate: 0`, `90`, `180`, `270`을 지원하며 고정된 전광판 크기 내에서 배경이 회전하는 캔버스 모드로 동작합니다.
- **글꼴**: 기본 내장된 픽셀 폰트 `Galmuri14.ttf`가 제공되며, `www/fonts/`에 추가 폰트를 둘 수 있습니다.
- **기록 차트**: `plot` 요소를 사용하면 Home Assistant **Recorder**에서 센서 기록 데이터를 가져와 그래프를 그립니다.
- **아이콘**: Home Assistant 날씨 아이콘(`weather-*`) 및 MDI 아이콘을 지원합니다.

---

## 서비스 예제

### `ble_led_sign.write`

레이아웃 요소를 렌더링하여 전광판에 비트맵으로 전송합니다.

```yaml
action: ble_led_sign.write
target:
  device_id: <기기 ID>
data:
  payload:
    - type: rectangle
      x_start: 0
      y_start: 0
      x_end: 47
      y_end: 11
      fill: black
    - type: text
      value: "21.5°C"
      x: 2
      y: 1
      size: 10
      color: cyan
    - type: icon
      x: 36
      y: 1
      value: "weather-partlycloudy"
      size: 10
      color: yellow
  rotate: 0
  background: black
  dry_run: false
```

### `ble_led_sign.send_text`

간단한 스크롤 텍스트를 전송합니다.

```yaml
action: ble_led_sign.send_text
target:
  device_id: <기기 ID>
data:
  text: "알림: 빨래가 완료되었습니다."
  color: "00FF00"
```

### `ble_led_sign.send_image`

로컬 이미지 파일을 전광판에 바로 전송합니다.

```yaml
action: ble_led_sign.send_image
target:
  device_id: <기기 ID>
data:
  image_path: "/config/www/images/logo.png"
  threshold: 128
```

### `ble_led_sign.send_animation`

애니메이션 GIF 파일을 전광판에 전송합니다.

```yaml
action: ble_led_sign.send_animation
target:
  device_id: <기기 ID>
data:
  image_path: "/config/www/animations/cat.gif"
  speed_ms: 100
```
