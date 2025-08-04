# 🎵 Audible Garden Turntable

## 📋 프로젝트 개요

카메라를 통해 터테이블의 회전을 감지하고, 레코드의 존재 여부에 따라 소리를 생성하는 인터랙티브 터테이블 시스템입니다.

## 🚀 주요 기능

### 🎯 레코드 감지 시스템
- **실시간 감지**: 카메라를 통해 레코드의 존재/부재를 실시간으로 감지
- **스마트 소리 제어**: 레코드가 있을 때만 소리 생성, 없을 때는 자동으로 소리 중지
- **기준 설정**: 30프레임 기준 데이터 수집으로 정확한 감지

### 🎵 음악 생성
- **MIDI 생성**: ROI(Region of Interest) 데이터를 MIDI 노트로 변환
- **OSC 통신**: 외부 오디오 시스템과 OSC 프로토콜로 통신
- **실시간 전송**: 회전에 따라 실시간으로 음악 데이터 전송

## 🛠️ 설치 및 설정

### 1. Conda 환경 설정
```bash
# Conda 환경 생성
conda env create -f conda_garden.yml

# 환경 활성화
conda activate garden
```

### 2. 의존성 확인
필요한 패키지들이 `conda_garden.yml`에 정의되어 있습니다:
- OpenCV (cv2)
- PyQt5
- NumPy
- Python-OSC

## 🎮 사용 방법

### 메인 실행 스크립트
```bash
./run_turntable.sh
```

### 실행 모드 선택

#### 1. 🎥 카메라 화면과 함께 실행 (GUI 모드)
- 터테이블과 카메라 화면이 모두 표시됩니다
- 시각적으로 회전 상태를 확인할 수 있습니다
- 레코드 감지 상태를 실시간으로 확인 가능

#### 2. 🎵 카메라 화면 없이 실행 (CLI 모드)
- 터미널에서만 로그가 표시됩니다
- 시스템 리소스를 적게 사용합니다
- 백그라운드 실행에 적합

#### 3. 🎮 Simple Controller로 실행
- 간단한 START/STOP 버튼만 있는 GUI
- 실시간 로그 표시가 가능합니다
- 직관적인 제어 인터페이스

### 직접 실행 옵션

#### GUI 모드 직접 실행
```bash
./run_with_camera.sh
```

#### CLI 모드 직접 실행
```bash
./run_without_camera.sh
```

#### Simple Controller 직접 실행
```bash
./run_simple_controller.sh
```

## 📁 프로젝트 구조

```
revised/
├── run_turntable.sh          # 메인 실행 스크립트
├── run_with_camera.sh        # GUI 모드 실행
├── run_without_camera.sh     # CLI 모드 실행
├── run_simple_controller.sh  # Simple Controller 실행
├── simple_controller.py      # Simple Controller GUI
├── turntable_gui_.py        # 메인 애플리케이션
├── config.json              # 설정 파일
├── conda_garden.yml         # Conda 환경 설정
├── utils/                   # 유틸리티 모듈
│   ├── camera_utils.py      # 카메라 관련
│   ├── audio_utils_simple.py # 오디오 처리
│   ├── osc_utils.py         # OSC 통신
│   ├── rotation_utils.py    # 회전 감지
│   └── record_detector.py   # 레코드 감지
└── data/                    # 데이터 저장소
```

## ⚙️ 설정

### config.json
주요 설정 항목:
- `scales`: 음계 설정
- `rpm`: 회전 속도 (기본값: 2.5)
- `duration`: 실행 시간 (초)
- `transmission_interval`: OSC 전송 간격

### 레코드 감지 설정
- **threshold**: 0.2 (감지 민감도)
- **baseline_frames**: 30 (기준 데이터 수집 프레임 수)
- **smoothing_factor**: 0.8 (신호 평활화)

## 🎯 레코드 감지 시스템

### 동작 원리
1. **기준 설정**: 레코드가 없는 상태에서 30프레임 수집
2. **실시간 감지**: 현재 프레임과 기준 데이터 비교
3. **신뢰도 계산**: 색상 히스토그램 분석으로 confidence 계산
4. **소리 제어**: confidence > threshold 시 소리 생성

### 감지 조건
- **레코드**: 흑백 또는 컬러 레코드
- **터테이블**: 검은색 바닥, 은색 중심부
- **조명**: 일정한 조명 조건에서 최적 성능

## 🔧 기술 스펙

### 카메라
- **해상도**: 1280x720
- **FPS**: 30
- **지원 카메라**: Logitech BRIO (기본)

### 오디오
- **프로토콜**: OSC (Open Sound Control)
- **포트**: 5555
- **데이터**: MIDI 노트, velocity, duration

### 성능
- **지연 시간**: < 100ms
- **CPU 사용률**: 낮음 (CLI 모드)
- **메모리 사용률**: 최적화됨

## 🐛 문제 해결

### 일반적인 문제들

#### 1. Conda 환경 오류
```bash
# Conda 초기화
conda init zsh
source ~/.zshrc

# 환경 재생성
conda env remove -n garden
conda env create -f conda_garden.yml
```

#### 2. 카메라 연결 실패
- 카메라가 연결되어 있는지 확인
- 다른 프로그램에서 카메라를 사용 중인지 확인
- 카메라 권한 설정 확인

#### 3. OSC 연결 실패
- 외부 오디오 시스템이 실행 중인지 확인
- 포트 5555가 사용 가능한지 확인

#### 4. 레코드 감지 문제
- 조명 조건 확인
- 카메라 각도 조정
- threshold 값 조정 (config.json)

## 📝 로그 확인

### 실시간 로그
```bash
# GUI 모드에서 실시간 로그 확인
tail -f turntable_controller.log
```

### 디버그 정보
- 레코드 감지 confidence 값
- OSC 전송 상태
- 카메라 프레임 정보

## 🎨 커스터마이징

### 새로운 음계 추가
`config.json`의 `scales` 섹션에 새로운 음계 정의:
```json
{
  "scales": {
    "CUSTOM_SCALE": ["C", "D", "E", "F", "G", "A", "B"]
  }
}
```

### 레코드 감지 민감도 조정
`utils/record_detector.py`에서 threshold 값 수정:
```python
threshold=0.2  # 기본값, 0.1-0.5 범위 권장
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해 주세요.

---

**💡 팁**: 처음 사용 시에는 GUI 모드(옵션 1)로 시작하여 시스템이 정상 작동하는지 확인하세요! 