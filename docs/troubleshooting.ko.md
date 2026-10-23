# BLE LED 전광판 문제 해결

[English Troubleshooting](troubleshooting.md) · [한국어 README](../README.ko.md) · [사용자 가이드](ko/user-guide.md)

## 공통 문제 해결

[공통 Bluetooth 문제 해결](https://github.com/eigger/blesession/blob/main/docs/troubleshooting.ko.md)과 [프록시 설정 안내](https://github.com/eigger/blesession/blob/main/docs/bluetooth.ko.md)를 참고하세요.

## 기기별 확인 사항

- **안정적인 전원 공급**: LED 매트릭스 전광판은 순간 전류 소비가 큽니다. 패널 정격에 맞는 전원을 사용하세요. 고전류 패널은 5V 2A 이상의 별도 전원이 필요할 수 있습니다.
- **스마트폰 앱 연결 해제**: 이 제품군은 보통 한 제어기만 연결할 수 있으며 정확한 연결 수는 펌웨어에 따라 다릅니다. 스마트폰의 전용 앱(CoolLED1248, iPixel Color 등)이 켜져 있으면 Home Assistant에서 연결할 수 없습니다.
- **신호 거리 및 프록시 활용**: 서버 본체의 내장 블루투스 어댑터는 금속 케이스나 거리로 인해 신호가 약할 수 있습니다. `active: true`가 설정된 [ESPHome 블루투스 프록시](https://github.com/eigger/blesession/blob/main/docs/bluetooth.ko.md) 사용을 강력히 권장합니다.

## 증상과 조치

| 증상 | 실패 단계 | 확인 사항 | 조치 |
|---|---|---|---|
| 기기가 검색되지 않음 | unreachable | 전원, 광고 수신, 어댑터/프록시 상태 | 기기를 가까이 옮기고 전용 앱을 종료하세요. 수동 스캔으로도 GATT 연결이 가능하며 이 통합은 능동 스캔을 요구하지 않습니다. |
| 연결 실패 | connect | 다른 앱 연결, 프록시 연결 슬롯 | CoolLED1248/iPixel Color 앱을 종료하고 프록시 용량을 확인하세요. 재시도 횟수는 총 시도 수입니다. |
| 비밀번호 거부 | auth | 비밀번호를 요구하는 CoolLED 모델 | 올바른 6자리 비밀번호를 설정하세요(기본값 `000000`). 명시적인 인증 거부는 재시도하지 않습니다. |
| 이미지 깨짐/전송 실패 | transfer | 전원과 무선 경로 | 필요하면 패킷 간격을 50–100ms로 늘리세요. 이는 통합 옵션이며 프록시 스캔 설정과 별개입니다. |
| 패널 크기를 알 수 없음 | transfer / device_info | iPixel Color는 해상도를 광고하지 않음 | 조회 성공 후 크기가 반영됩니다. 시간 초과는 오류로 남기며 다음 광고 수신 때 다시 조회할 수 있습니다. |
| 명령 성공 후 화면이 바뀌지 않음 | transfer / finish | 일부 짧은 명령에는 완료 ACK가 없음 | 쓰기 성공은 전송 완료를 뜻하며 실제 화면을 읽어 확인한 결과는 아닙니다. |

## 진단 및 로그

작업마다 연결하고 완료 후 해제합니다. **BLE 연결** 진단은 실제 GATT 세션 중에만 켜지므로 대기 중 꺼짐은 정상입니다.

**마지막 통신**은 최신 보고서를 표시합니다. **마지막 오류 단계**, **마지막 실패**, **실패 횟수**는 이후 성공해도 최종 실패 기록을 유지합니다. 횟수는 재로드 시 초기화됩니다. 재시도 중 오류는 진단 다운로드의 별도 기록에 남으며 최종 실패 횟수에는 포함하지 않습니다. 취소도 실패로 집계하지 않습니다.

속성에는 `operation`, `success`, `failed_stage`, `failed_detail`, `error`, 단계별 시간과 수집 가능한 `via`, `via_type`, `rssi`, `paths`, `via_unconfirmed`가 포함됩니다. `via_unconfirmed: true`는 광고 수신 정보를 통한 경로 추정입니다. 보고서는 각 시도 종료 시 고정됩니다. 통합 진단 다운로드는 무선 장치 이름과 자유 형식 오류를 제거하지만 센서 속성에는 주소나 이름이 남을 수 있으므로 공유 전에 지우세요.

알림 등록/MTU 설정은 15초, 각 GATT 쓰기는 10초로 제한되고 응답 대기는 프로토콜별 제한을 유지합니다. 이미지/애니메이션 전체 시간 제한은 없습니다. 시도 사이에는 공통 잠금을 해제하며 연결 해제 정리는 blesession의 제한 시간을 사용합니다.

이미지 엔티티로 렌더링 내용을 확인할 수 있습니다:

- `image.<기기>_render_preview`: `ble_led_sign.write` 호출 시 `dry_run: true` 옵션을 주면 실제 BLE 전송 없이 생성된 미리보기 이미지를 확인할 수 있습니다. 레이아웃 테스트에 유용합니다.
- `image.<기기>_last_sent_display`: 전광판에 성공적으로 전송 완료된 마지막 비트맵 이미지를 표시합니다.

## 문제가 계속되는 경우

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

통합·blesession·ESPHome 버전, 패널/프록시 모델과 리비전, 연결 방식, 실패 시각·단계와 재현 절차도 포함하세요. 재현 구간만 로그로 수집하고 디버그 로깅은 다시 끄세요. 주소·비밀번호·토큰·개인 표시 내용을 제거하세요. 이번 변경으로 실물·프록시·Home Assistant UI를 검증하지는 않았습니다.
