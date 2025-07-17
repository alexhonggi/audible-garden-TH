# Audible Garden - Turntable Project 수정 내역

## 2025-07-12

### 최종 작업: 전체 기능 검증 및 안정화

- **완료 (1/1): 버그 수정 및 최종 테스트**
  - 반복적으로 발생하던 `cv2.error`는 `roi_gray` 생성 및 전달 과정의 미묘한 로직 오류 때문임을 파악하고 최종 수정하여 완벽하게 해결했습니다.
  - `importance` 및 `random` 샘플링 모드 모두에서 안정적으로 작동하는 것을 최종 확인했습니다.
  - 디버깅을 위해 추가했던 임시 코드들을 모두 제거하여 코드를 정리했습니다.

---

### 작업 2: MIDI 생성 로직 재수정 및 고도화 (완료)

- **`config.json` 업데이트**: `sampling_mode` 및 `fixed_duration_seconds` 파라미터 추가.
- **`generate_midi_from_roi` 재설계**: '세로축=음높이', '밝기=세기', '밝기 반전', '두 가지 샘플링 모드' 기능 구현.

---

### 작업 1: 파라미터 관리 체계 개편 (완료)

- **`config.json` 파일 생성**: 핵심 파라미터를 외부 파일에서 관리하도록 변경.
- **MIDI 생성 로직 수정**: `config.json` 기반으로 동작하는 `generate_midi_from_roi` 함수 구현.
- **메인 로직 수정**: `turntable_gui.py`가 `config.json`을 읽어 동작하도록 수정. 

---

## 최종 실행 방법

이 프로그램은 **GUI(그래픽 사용자 인터페이스) 모드**와 **CLI(커맨드라인 인터페이스) 모드** 두 가지 방식으로 실행할 수 있습니다.

### 1. GUI 모드로 실행하기 (사용자 인터페이스 사용)

기존과 동일하게 그래픽 인터페이스를 통해 모든 기능을 제어합니다.

-   **실행 명령어:**
    ```bash
    # /revised 폴더로 이동 후
    python turntable_gui.py
    ```
-   **설명:**
    -   별도의 옵션 없이 실행하면 GUI 창이 나타납니다.
    -   마우스를 사용하여 ROI를 설정하고, 버튼으로 녹음/재생 등 모든 기능을 제어할 수 있습니다.

### 2. CLI 모드로 실행하기 (터미널에서 직접 실행)

GUI 없이 터미널에서 직접 프로그램을 실행하고 싶을 때 사용합니다. 모든 설정은 커맨드라인 옵션(인자)을 통해 지정해야 합니다.

-   **기본 실행 명령어:**
    ```bash
    # /revised 폴더로 이동 후
    python turntable_gui.py --cli
    ```

-   **주요 옵션:**
    -   `--cli`: (필수) CLI 모드로 실행합니다.
    -   `--duration <초>`: 프로그램을 실행할 총 시간을 초 단위로 지정합니다. (기본값: 60)
    -   `--rpm <숫자>`: 턴테이블의 분당 회전수(RPM)를 지정합니다. (기본값: 2.5)
    -   `--record`: 첫 번째 바퀴를 회전하는 동안의 연주를 악보 파일로 자동 저장합니다.
    -   `--exit-on-record-complete`: `--record` 옵션 사용 시, 악보 저장이 완료되면 프로그램을 자동으로 종료합니다.

-   **실행 예시:**
    ```bash
    # 30초 동안 실행하며 첫 바퀴를 녹음하고, 녹음이 끝나면 바로 종료
    python turntable_gui.py --cli --duration 30 --record --exit-on-record-complete
    ```

-   **추가 실행 예시:**
    -   **Rectangular 모드로 10분간 실행:**
        ```bash
        python turntable_gui.py --cli --roi-mode Rectangular --duration 600
        ```
    -   **빠른 속도(10 RPM)로 음 전송만 20초간 테스트:**
        ```bash
        python turntable_gui.py --cli --rpm 10 --duration 20
        ``` 