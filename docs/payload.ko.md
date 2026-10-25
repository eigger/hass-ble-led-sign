# Payload

[README](../README.ko.md) | [English](payload.md) | **한국어**

## 공통 payload 안내

그리기 요소와 공통 속성은 [imagespec payload 안내](https://github.com/eigger/imagespec/blob/main/docs/payload.ko.md)를 참고하세요.

## 이 통합에서 payload 사용

개발자 도구 → 작업 또는 자동화에서 `ble_led_sign.write`를 호출합니다. `target.entity_id` 또는 기기 ID로 전광판을 선택하고 `data.payload`에 그리기 요소 목록을 넣습니다. Home Assistant가 템플릿을 준비한 뒤 통합에서 설치된 imagespec으로 그립니다. 기존 기기별 설명은 [사용자 가이드](ko/user-guide.md)에 유지합니다.

## 최소 동작 예제

[사각형 작업](../examples/payload/minimal.yaml)은 48 × 12 단색 CoolLED 패널의 검은 배경에 흰 사각형을 그립니다. [템플릿 작업](../examples/payload/template.yaml)은 실제 HA 템플릿 처리로 `HA` 텍스트를 만듭니다. 두 파일은 완전한 작업 YAML이며 실행 전 실제 전광판의 light 엔티티를 선택하세요.

## 기기 출력 설정

렌더러는 감지된 기기의 열 수와 행 수를 사용합니다. 예제는 검정/off와 흰색/on을 지원하는 12행 48열 단색 CoolLED용입니다. 7색 및 RGB 기기는 팔레트가 다르며 실제 패널에 맞춰 드라이버가 인코딩합니다. `data.rotate`는 회전 각도이며 고정 패널 크기(`rotate_mode: canvas`)를 유지합니다. `data.background` 기본값은 black입니다. 기본 폰트는 내장 Galmuri14.ttf이고 내장 폰트 및 HA 설정 디렉터리의 `www/fonts`에서 폰트를 찾습니다. threshold와 invert는 imagespec 캔버스 이후 기기 비트맵 인코딩에 적용됩니다.

## 지원 기능과 제한

그리기 요소, 폰트와 recorder 이력은 통합의 실제 imagespec 컨텍스트를 사용합니다. 이력에는 실제 recorder와 기록된 엔티티가 필요합니다. HA가 작업 템플릿을 처리하며 통합은 지원하는 날씨 아이콘을 매핑합니다. 예제에는 네트워크, 이력, 사용자 폰트가 필요하지 않습니다. `dry_run: true`이면 BLE 전송 없이 미리보기를 생성합니다. payload 렌더링으로 기본 스크롤이나 애니메이션이 추가되지는 않으므로 해당 드라이버의 전용 작업을 사용하세요. 실제 크기와 색상은 기기별로 다르며 모든 모델 출력을 검증한 예제는 아닙니다.

## 문제 해결

[기존 문제 해결 문서](troubleshooting.ko.md)와 패널 크기, 사용 가능한 폰트, 선택한 엔티티를 확인하세요. 문제는 [Issues](https://github.com/eigger/hass-ble-led-sign/issues)에 제보하세요.
