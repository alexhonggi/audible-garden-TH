# 🎵 Audible Garden Turntable

## 개요
카메라를 통해 턴테이블의 회전을 감지하고 실시간으로 음악을 생성하는 프로젝트입니다.

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Conda 환경 생성
conda env create -f conda_garden.yml

# 환경 활성화
conda activate garden
```

### 2. 실행
```bash
# 메인 실행 스크립트
./run_turntable.sh
```

## 📁 프로젝트 구조

```
revised/
├── run_turntable.sh              # 🚀 메인 실행 스크립트
├── run_with_camera.sh            # 🎥 GUI 모드 실행
├── run_without_camera.sh         # 🎵 CLI 모드 실행
├── run_controller.sh             # 🎮 컨트롤러 모드 실행
├── run_controller_with_logs.sh   # 📊 로그 포함 컨트롤러
├── turntable_gui_.py            # 🖥️ 메인 GUI 애플리케이션
├── fixed_turntable.py           # 🔧 핵심 터테이블 로직
├── turntable_controller.py      # 🎮 컨트롤러 GUI
├── config.json                  # ⚙️ 설정 파일
├── conda_garden.yml             # 🐍 Conda 환경 설정
├── requirements.txt              # 📦 Python 패키지 요구사항
├── utils/                       # 🔧 유틸리티 모듈들
│   ├── camera_utils.py          # 📷 카메라 관련 유틸리티
│   ├── rotation_utils.py        # 🔄 회전 감지 유틸리티
│   ├── audio_utils_simple.py    # 🎵 오디오 처리 유틸리티
│   ├── osc_utils.py             # 📡 OSC 통신 유틸리티
│   └── record_detector.py       # 🎵 레코드 감지 유틸리티
└── data/                        # 💾 사용자 데이터 (보존)
```

## 🎯 주요 기능

### 1. 실시간 턴테이블 감지
- 카메라를 통한 회전 감지
- RPM 자동 계산
- 실시간 시각적 피드백

### 2. 레코드 감지
- 턴테이블에 레코드가 있는지 실시간 감지
- 레코드가 있을 때만 소리 생성
- 자동 소리 켜기/끄기

### 3. 실시간 음악 생성
- ROI 기반 음악 생성
- MIDI/OSC 통신
- 다양한 음계 지원

### 4. GUI 인터페이스
- 실시간 카메라 화면
- 설정 조정 가능
- 로그 모니터링

## 🎮 실행 모드

### 1. GUI 모드 (카메라 화면과 함께)
```bash
./run_turntable.sh
# 선택: 1
```

### 2. CLI 모드 (터미널만)
```bash
./run_turntable.sh
# 선택: 2
```

### 3. 컨트롤러 모드 (START/STOP 버튼)
```bash
./run_turntable.sh
# 선택: 3
```

## ⚙️ 설정

### config.json
```json
{
  "midi_generation": {
    "sampling_mode": "importance",
    "note_count_max": 5,
    "velocity_range": [32, 127],
    "velocity_threshold": 32
  },
  "scales": {
    "default_scale": "Piano",
    "definitions": {
      "Piano": "list(range(21, 109))",
      "CPentatonic": "[60, 62, 64, 67, 69]"
    }
  }
}
```

## 🔧 의존성

### Python 패키지
- PyQt5
- OpenCV
- NumPy
- python-osc
- pandas
- pillow

### 시스템 요구사항
- macOS (테스트됨)
- 카메라 (웹캠)
- Conda/Miniconda

## 🐛 문제 해결

### 카메라 문제
```bash
# 카메라 권한 확인
System Preferences → Security & Privacy → Camera
```

### Conda 환경 문제
```bash
# 환경 재생성
conda env remove -n garden
conda env create -f conda_garden.yml
```

### OSC 통신 문제
```bash
# 포트 확인
netstat -an | grep 5555
```

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

---

**💡 팁**: 처음 사용 시 GUI 모드로 시작하여 시각적으로 확인하는 것을 권장합니다! 