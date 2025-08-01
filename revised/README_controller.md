# 🎵 Turntable Controller

간단한 start/stop 버튼으로 터테이블 프로그램을 제어하는 GUI입니다.

## 📁 생성된 파일들

### 🎮 **GUI 컨트롤러 관련**
1. **`turntable_controller.py`** - 메인 GUI 컨트롤러
2. **`turntable_command_config.py`** - 명령어 설정 파일
3. **`run_controller.sh`** - GUI 컨트롤러 실행 (백그라운드)
4. **`run_controller_with_logs.sh`** - GUI 컨트롤러 실행 (로그 저장)
5. **`run_controller_terminal.sh`** - 터미널 출력 버전

### 🎥 **직접 실행 관련 (NEW!)**
6. **`run_turntable.sh`** - 메인 실행 스크립트 (모드 선택)
7. **`run_with_camera.sh`** - 카메라 화면과 함께 실행
8. **`run_without_camera.sh`** - 카메라 화면 없이 실행

### 📋 **로그 모니터링 관련**
9. **`monitor_logs.sh`** - 기본 로그 확인 유틸리티
10. **`monitor_both_logs.sh`** - 향상된 로그 모니터링
11. **`view_logs.sh`** - 로그 확인 유틸리티
12. **`README_controller.md`** - 사용법 설명서 (이 파일)

## 🚀 사용법

### 1. 환경 설정 (최초 1회)
```bash
# conda 환경 생성 (아직 안 했다면)
conda env create -f conda_garden.yml

# conda 환경 활성화
conda activate garden
```

### 2. 터테이블 실행 (추천 방법)

#### 🎯 **메인 실행 스크립트 (가장 간단!)**
```bash
./run_turntable.sh
```
- 메뉴에서 원하는 모드 선택
- 카메라 화면 표시 여부 선택 가능
- 가장 사용하기 쉬운 방법

#### 🎥 **카메라 화면과 함께 실행**
```bash
./run_with_camera.sh
```
- 터테이블 GUI 화면 + 카메라 화면 표시
- 시각적으로 회전 상태 확인 가능
- 더 많은 시스템 리소스 사용

#### 🎵 **카메라 화면 없이 실행**
```bash
./run_without_camera.sh
```
- 터미널에서만 로그 표시
- 시스템 리소스 절약
- 서버 환경에 적합

### 3. GUI 컨트롤러 실행 (고급 사용자용)

#### 🔍 방법 A: 로그 저장 버전
```bash
./run_controller_with_logs.sh
```

#### 🎯 방법 B: 백그라운드 실행
```bash
./run_controller.sh
```

### 3. 환경 문제 해결
만약 `python turntable_controller.py`로 실행 시 `ModuleNotFoundError: No module named 'PyQt5'` 오류가 발생한다면:

**원인**: pyenv와 conda 환경 충돌
**해결**: 위의 **간편 실행 스크립트** 또는 **직접 실행** 방법 사용

### 4. 프로그램 제어 (GUI 컨트롤러 사용 시)
- **🚀 START 버튼**: 클릭 시 3초 후 터테이블 프로그램 시작
- **🛑 STOP 버튼**: 클릭 시 3초 후 터테이블 프로그램 종료
- **📊 상태 표시**: 준비됨(초록), 실행중(파랑), 에러(빨강)

### 4. 로그 확인 방법

#### 🔥 **추천 방법: 향상된 로그 모니터링**
```bash
./monitor_both_logs.sh
```
- 메뉴에서 원하는 로그 선택 가능
- GUI 컨트롤러 로그 + 터테이블 프로세스 로그 모두 지원
- **"1. 터테이블 프로세스 로그 실시간 보기"** 선택 추천

#### 💡 **빠른 로그 확인 명령어**
```bash
# 터테이블 실행 로그 (가장 중요!)
tail -f turntable_process.log

# GUI 컨트롤러 로그
tail -f turntable_controller.log

# 최근 실행 결과 확인
tail -n 20 turntable_process.log
```

#### 📋 **기타 로그 확인 방법**
```bash
# 기본 로그 모니터링
./monitor_logs.sh

# 상세한 로그 유틸리티
./view_logs.sh
```

### 5. 명령어 수정
`turntable_command_config.py` 파일을 편집하여 실행 명령어를 변경할 수 있습니다:

```python
COMMAND_FLAGS = {
    "cli": True,           # CLI 모드 활성화
    "duration": 6000,      # 실행 시간 (초) 변경 가능
    "rpm": 2.5,           # 회전 속도 (RPM) 변경 가능
    "transmission_interval": 30,  # 전송 간격 변경 가능
    "roi_mode": "Circular",       # ROI 모드 (Circular/Rectangular)
    "record": False,              # 녹음 여부
    "exit_on_record_complete": False,  # 녹음 완료 시 자동 종료
    "config": "config.json"       # 설정 파일 경로
}
```

## ✨ 주요 기능

- **3초 지연**: 하드웨어와의 동기화를 위한 3초 지연 시간
- **시각적 피드백**: 상태 표시 및 카운트다운 디스플레이
- **안전한 종료**: 프로그램 종료 시 프로세스 안전 정리
- **명령어 표시**: 현재 설정된 명령어를 GUI에서 확인 가능

## 🎯 상태 표시

- **초록색 "준비됨"**: 대기 상태
- **주황색 "시작/종료 준비 중"**: 카운트다운 진행 중
- **파란색 "실행 중"**: 터테이블 프로그램 실행 중
- **빨간색**: 오류 발생

## ⚠️ 주의사항

- GUI를 닫으면 실행 중인 터테이블 프로세스도 함께 종료됩니다
- 명령어 수정 후 GUI를 다시 실행해야 변경사항이 적용됩니다
- `revised/turntable_gui_.py` 파일이 존재해야 정상 동작합니다
- **환경 문제가 있을 때는 `./run_controller.sh` 스크립트를 사용하세요** 