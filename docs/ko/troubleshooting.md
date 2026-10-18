# BLE LED 전광판 문제 해결

[English Troubleshooting](../troubleshooting.md) · [한국어 README](../../README.ko.md) · [사용자 가이드](user-guide.md)

ESPHome 설정, 추천 하드웨어(XIAO W5500 Ethernet Adapter V1.2, M5Stack AtomS3U 등) 및 일반 블루투스 문제 해결은 중앙 [블루투스 프록시 가이드](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.ko.md#문제-해결)를 참고하세요.

## 1. 전광판 기기 점검

- **안정적인 전원 공급**: LED 매트릭스 전광판은 순간 전류 소비가 큽니다. PC USB 포트 대신 5V 2A 이상의 전용 USB 전원 어댑터를 사용하세요.
- **스마트폰 앱 연결 해제**: BLE 기기는 동시에 단 하나의 중앙 장치(Central)와만 연결될 수 있습니다. 스마트폰의 전용 앱(CoolLED1248, iPixel Color 등)이 켜져 있으면 Home Assistant에서 연결할 수 없습니다.
- **신호 거리 및 프록시 활용**: 서버 본체의 내장 블루투스 어댑터는 금속 케이스나 거리로 인해 신호가 약할 수 있습니다. `active: true`가 설정된 [ESPHome 블루투스 프록시](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.ko.md) 사용을 강력히 권장합니다.

## 2. 자주 발생하는 문제 및 해결 방법

| 증상 | 원인 및 권장 조치 |
|------|-------------------|
| **기기가 검색되지 않음** | 전광판 전원이 켜져 있고 정상적으로 BLE 신호를 송출하는지 확인하세요. 블루투스 프록시가 온라인 상태이고 기기 근처에 위치하는지 확인하세요. |
| **연결 실패 또는 타임아웃** | 1. 스마트폰 앱 연결이 완전히 종료되었는지 확인하세요.<br>2. ESP32 프록시의 최대 동시 연결 수(3개)가 다른 기기에 의해 고갈되지 않았는지 확인하세요.<br>3. 통합 **구성**에서 **재시도 횟수**를 `3`에서 `5`로 늘려보세요. |
| **전송 중 패킷 손실 또는 이미지 깨짐** | 대용량 매트릭스 데이터 전송 시 BLE 버퍼 오버플로우가 발생할 수 있습니다. 통합 **구성**에서 **패킷 간격 (ms)**을 `50`~`100`ms로 늘려보세요. |
| **비밀번호 인증 오류** | 일부 모델(CoolLEDS, CoolLEDX 등)은 6자리 비밀번호 인증을 요구합니다. 통합 **구성**에서 올바른 비밀번호를 입력하세요 (기본값: `000000`). |
| **해상도가 48×12 기본값으로 표시됨** | iPixel Color 등 일부 제품군은 광고 패킷에 크기 정보를 포함하지 않습니다. 기기 첫 연결 시 내부 메타데이터를 조회하여 업데이트하므로, 기기가 통신 범위 내에 있는지 확인하세요. |

## 3. 진단 엔티티 활용

Home Assistant 엔티티를 활용하여 전송 상태를 검증할 수 있습니다:

- `image.<기기>_render_preview`: `ble_led_sign.write` 호출 시 `dry_run: true` 옵션을 주면 실제 BLE 전송 없이 생성된 미리보기 이미지를 확인할 수 있습니다. 레이아웃 테스트에 유용합니다.
- `image.<기기>_last_sent_display`: 전광판에 성공적으로 전송 완료된 마지막 비트맵 이미지를 표시합니다.

## 4. 문제 제보 방법

[GitHub Issues](https://github.com/eigger/hass-ble-led-sign/issues)에 문제를 제보하실 때는:

1. `configuration.yaml`에서 디버그 로그를 활성화합니다:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.ble_led_sign: debug
   ```
2. 게시 전 로그에서 기기 MAC 주소나 민감한 텍스트 내용을 마스킹합니다.
3. 전광판 모델명, 검색 시 표시된 이름, 블루투스 어댑터 종류(USB 동글 또는 ESPHome 프록시 보드 모델), Home Assistant 버전을 함께 기재해 주세요.
