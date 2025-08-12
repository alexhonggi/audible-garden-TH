# 🔧 Refactoring Plan - Turntable Project

## 🎯 목표
`./run_turntable.sh` 실행과 관련된 핵심 파일들만 남기고 불필요한 파일들을 정리

## 📋 파일 분석

### ✅ **필수 파일들 (Core Files)**

#### 1. 메인 실행 파일들
```
revised/
├── run_turntable.sh              # 🚀 메인 실행 스크립트
├── run_with_camera.sh            # 🎥 GUI 모드 실행
├── run_without_camera.sh         # 🎵 CLI 모드 실행
├── run_controller.sh             # 🎮 컨트롤러 모드 실행
└── run_controller_with_logs.sh   # 📊 로그 포함 컨트롤러
```

#### 2. 핵심 Python 모듈들
```
revised/
├── turntable_gui_.py            # 🖥️ 메인 GUI 애플리케이션
├── fixed_turntable.py           # 🔧 핵심 터테이블 로직
├── turntable_controller.py      # 🎮 컨트롤러 GUI
└── config.json                  # ⚙️ 설정 파일
```

#### 3. Utils 모듈들
```
revised/utils/
├── camera_utils.py              # 📷 카메라 관련 유틸리티
├── rotation_utils.py            # 🔄 회전 감지 유틸리티
├── audio_utils_simple.py        # 🎵 오디오 처리 유틸리티
├── osc_utils.py                 # 📡 OSC 통신 유틸리티
└── record_detector.py           # 🎵 레코드 감지 유틸리티
```

#### 4. 환경 설정 파일들
```
revised/
├── conda_garden.yml             # 🐍 Conda 환경 설정
└── requirements.txt              # 📦 Python 패키지 요구사항
```

### ❌ **제거 가능한 파일들 (Removable Files)**

#### 1. 테스트 파일들 (개발용)
```
revised/
├── test_record_detection.py     # 🧪 레코드 감지 테스트
├── test_sound_control.py        # 🔇 소리 제어 테스트
├── test_first_run_fix.py        # 🔧 첫 실행 문제 테스트
├── test_conda_setup.sh          # 🐍 Conda 설정 테스트
└── test_commands.txt            # 📝 테스트 명령어 모음
```

#### 2. 문서 파일들 (개발용)
```
revised/
├── USAGE_GUIDE.md              # 📖 사용 가이드
├── RECORD_DETECTION_README.md   # 📖 레코드 감지 문서
├── README.md                    # 📖 프로젝트 문서
├── README_controller.md         # 📖 컨트롤러 문서
├── GUI_MANUAL.md               # 📖 GUI 매뉴얼
├── GUI_MANUAL_EN.md            # 📖 GUI 매뉴얼 (영어)
├── changes.txt                  # 📝 변경 사항
└── memo.md                      # 📝 메모
```

#### 3. 로그 및 임시 파일들
```
revised/
├── turntable_controller.log     # 📊 로그 파일
├── turntable_process.log        # 📊 프로세스 로그
├── view_logs.sh                 # 👁️ 로그 보기 스크립트
├── monitor_logs.sh              # 📊 로그 모니터링
└── monitor_both_logs.sh         # 📊 통합 로그 모니터링
```

#### 4. 레거시 파일들
```
revised/
├── turntable_gui.py             # 🗑️ 이전 버전 GUI
├── turntable_command_config.py  # 🗑️ 명령어 설정 (사용 안함)
└── memo.txt                     # 🗑️ 중복 메모 파일
```

#### 5. 루트 디렉토리 파일들 (불필요)
```
/
├── turntable_gui_with_edge_detection.py  # 🗑️ 이전 버전
├── edge_detection.py                     # 🗑️ 엣지 감지 (사용 안함)
├── final_turntable.py                    # 🗑️ 이전 버전
├── legacy_final_turntable.py             # 🗑️ 레거시 버전
├── live_camera_edge_detection.py         # 🗑️ 엣지 감지 테스트
├── camera_spec_checker.py                # 🗑️ 카메라 체크 (사용 안함)
├── core_audio_processing.py              # 🗑️ 이전 오디오 처리
├── corrected_audio_processing.py         # 🗑️ 이전 오디오 처리
├── patch_audiolazy.sh                    # 🗑️ 패치 스크립트 (사용 안함)
├── receiveStoneMIDI.amxd                 # 🗑️ Max/MSP 파일
├── cadenza.mp3                          # 🗑️ 테스트 오디오 파일
├── cadenza.mp3.asd                      # 🗑️ 오디오 메타데이터
├── Info.plist                           # 🗑️ 시스템 파일
├── history.txt                           # 🗑️ 히스토리
├── history1.txt                          # 🗑️ 히스토리
├── ideal_run_options.txt                 # 🗑️ 실행 옵션
└── turntable_score_*.json               # 🗑️ 테스트 점수 파일들
```

### 🔄 **조건부 파일들 (Conditional Files)**

#### 1. 데이터 디렉토리
```
revised/data/                    # 💾 사용자 데이터 (보존)
```

#### 2. 캐시 파일들
```
revised/
├── __pycache__/                 # 🗂️ Python 캐시 (자동 생성)
└── utils/__pycache__/           # 🗂️ Utils 캐시 (자동 생성)
```

## 🚀 실행 계획

### 1단계: 백업 생성
```bash
# 현재 상태 백업
git add .
git commit -m "Backup before refactoring"
```

### 2단계: 불필요한 파일 제거
```bash
# 테스트 파일들 제거
rm revised/test_*.py
rm revised/test_*.sh
rm revised/test_commands.txt

# 문서 파일들 제거 (선택적)
rm revised/*.md
rm revised/changes.txt
rm revised/memo.txt

# 로그 파일들 제거
rm revised/*.log
rm revised/view_logs.sh
rm revised/monitor_*.sh

# 레거시 파일들 제거
rm revised/turntable_gui.py
rm revised/turntable_command_config.py

# 루트 디렉토리 불필요 파일들 제거
rm *.py
rm *.sh
rm *.json
rm *.txt
rm *.amxd
rm *.mp3
rm *.asd
rm *.plist
```

### 3단계: 핵심 파일들만 남기기
```
revised/
├── run_turntable.sh
├── run_with_camera.sh
├── run_without_camera.sh
├── run_controller.sh
├── run_controller_with_logs.sh
├── turntable_gui_.py
├── fixed_turntable.py
├── turntable_controller.py
├── config.json
├── conda_garden.yml
├── requirements.txt
├── utils/
│   ├── camera_utils.py
│   ├── rotation_utils.py
│   ├── audio_utils_simple.py
│   ├── osc_utils.py
│   └── record_detector.py
└── data/ (보존)
```

### 4단계: 테스트 및 커밋
```bash
# 기능 테스트
./run_turntable.sh

# 변경사항 커밋
git add .
git commit -m "Refactoring: Remove unnecessary files, keep only core turntable functionality"
```

## 📊 예상 결과

### 제거될 파일 수
- **테스트 파일들**: 5개
- **문서 파일들**: 8개
- **로그 파일들**: 5개
- **레거시 파일들**: 3개
- **루트 디렉토리 파일들**: 15개
- **총 제거 파일**: 36개

### 남을 파일 수
- **핵심 실행 파일들**: 5개
- **Python 모듈들**: 4개
- **Utils 모듈들**: 5개
- **설정 파일들**: 2개
- **총 핵심 파일**: 16개

### 용량 절약
- **현재**: ~50MB
- **리팩토링 후**: ~10MB
- **절약**: ~80% 용량 감소

## ✅ 검증 체크리스트

- [ ] `./run_turntable.sh` 정상 실행
- [ ] GUI 모드 정상 작동
- [ ] CLI 모드 정상 작동
- [ ] 컨트롤러 모드 정상 작동
- [ ] 레코드 감지 기능 정상
- [ ] 소리 제어 기능 정상
- [ ] 카메라 기능 정상
- [ ] 설정 파일 로드 정상

---

**💡 참고**: 이 계획은 `./run_turntable.sh` 기능에 집중합니다. 다른 기능이 필요하다면 해당 파일들을 보존할 수 있습니다. 