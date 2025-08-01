#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
터테이블 컨트롤러 GUI
start/stop 버튼으로 터테이블 프로그램을 제어합니다.
"""

import sys
import os
import subprocess
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# 명령어 설정 파일 임포트
from turntable_command_config import get_command, get_command_string

class CountdownThread(QThread):
    """카운트다운을 위한 별도 스레드"""
    countdown_update = pyqtSignal(int)
    countdown_finished = pyqtSignal()
    
    def __init__(self, seconds=3):
        super().__init__()
        self.seconds = seconds
        self.running = True
    
    def run(self):
        for i in range(self.seconds, 0, -1):
            if not self.running:
                return
            self.countdown_update.emit(i)
            time.sleep(1)
        
        if self.running:
            self.countdown_finished.emit()
    
    def stop(self):
        self.running = False

class TurntableController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.countdown_thread = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Turntable Controller")
        self.setGeometry(300, 300, 500, 400)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 제목
        title_label = QLabel("🎵 Audible Garden Turntable Controller")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 상태 표시
        self.status_label = QLabel("준비됨")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("QLabel { color: green; }")
        layout.addWidget(self.status_label)
        
        # 카운트다운 표시
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        countdown_font = QFont()
        countdown_font.setPointSize(24)
        countdown_font.setBold(True)
        self.countdown_label.setFont(countdown_font)
        self.countdown_label.setStyleSheet("QLabel { color: red; }")
        layout.addWidget(self.countdown_label)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # Start 버튼
        self.start_button = QPushButton("🚀 START")
        self.start_button.setMinimumHeight(60)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.start_button.clicked.connect(self.start_process)
        
        # Stop 버튼
        self.stop_button = QPushButton("🛑 STOP")
        self.stop_button.setMinimumHeight(60)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_button.clicked.connect(self.stop_process)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
        # 명령어 표시
        command_label = QLabel("실행될 명령어:")
        command_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(command_label)
        
        self.command_display = QTextEdit()
        self.command_display.setMaximumHeight(80)
        self.command_display.setPlainText(get_command_string())
        self.command_display.setReadOnly(True)
        self.command_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.command_display)
        
        # 설정 파일 수정 안내
        info_label = QLabel("💡 명령어를 수정하려면 'turntable_command_config.py' 파일을 편집하세요.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666666; font-size: 10px; }")
        layout.addWidget(info_label)
        
    def start_process(self):
        """프로세스 시작 (3초 후)"""
        if self.process and self.process.poll() is None:
            return  # 이미 실행 중
        
        self.start_button.setEnabled(False)
        self.status_label.setText("시작 준비 중...")
        self.status_label.setStyleSheet("QLabel { color: orange; }")
        
        # 3초 카운트다운 시작
        self.countdown_thread = CountdownThread(3)
        self.countdown_thread.countdown_update.connect(self.update_countdown)
        self.countdown_thread.countdown_finished.connect(self.execute_start)
        self.countdown_thread.start()
        
    def stop_process(self):
        """프로세스 중지 (3초 후)"""
        if not self.process or self.process.poll() is not None:
            return  # 실행 중이 아님
        
        self.stop_button.setEnabled(False)
        self.status_label.setText("종료 준비 중...")
        self.status_label.setStyleSheet("QLabel { color: orange; }")
        
        # 3초 카운트다운 시작
        self.countdown_thread = CountdownThread(3)
        self.countdown_thread.countdown_update.connect(self.update_countdown)
        self.countdown_thread.countdown_finished.connect(self.execute_stop)
        self.countdown_thread.start()
        
    def update_countdown(self, seconds):
        """카운트다운 업데이트"""
        self.countdown_label.setText(f"{seconds}")
        
    def execute_start(self):
        """실제 프로세스 시작 실행"""
        try:
            # 작업 디렉토리를 스크립트가 있는 곳으로 변경
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            command = get_command()
            print(f"실행할 명령어: {' '.join(command)}")
            print(f"작업 디렉토리: {script_dir}")
            
            # 파일 존재 여부 확인
            script_path = os.path.join(script_dir, command[1])  # command[1]은 스크립트 파일명
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"스크립트 파일을 찾을 수 없습니다: {script_path}")
            
            # 출력을 파일로 리다이렉트하여 프로세스가 제대로 실행되도록 함
            log_file = os.path.join(script_dir, "turntable_process.log")
            
            # 로그 파일을 열어두고 프로세스에 전달
            self.process_log_file = open(log_file, 'w')
            
            self.process = subprocess.Popen(
                command,
                cwd=script_dir,
                stdout=self.process_log_file,
                stderr=subprocess.STDOUT,  # stderr을 stdout으로 합침
                universal_newlines=True
            )
            
            # 프로세스가 즉시 종료되었는지 확인
            import time
            time.sleep(0.5)  # 잠시 대기
            if self.process.poll() is not None:
                # 프로세스가 종료됨 - 로그 파일에서 에러 확인
                try:
                    # 로그 파일 닫기
                    if hasattr(self, 'process_log_file') and self.process_log_file:
                        self.process_log_file.close()
                        self.process_log_file = None
                    
                    # 로그 파일에서 출력 읽기
                    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "turntable_process.log")
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            output = f.read()
                        print(f"=== 프로세스 출력 ===")
                        print(output)
                        print(f"==================")
                    
                    print(f"=== 프로세스 종료 디버그 정보 ===")
                    print(f"종료 코드: {self.process.returncode}")
                    print(f"===========================")
                    
                    if self.process.returncode != 0:
                        error_msg = f"프로세스 에러 (코드: {self.process.returncode})"
                    else:
                        error_msg = f"프로세스가 예상치 못하게 종료됨"
                    
                    # GUI에 에러 표시
                    self.status_label.setText(f"실행 실패: {error_msg}")
                    self.status_label.setStyleSheet("QLabel { color: red; }")
                    self.start_button.setEnabled(True)
                    self.countdown_label.setText("")
                    return
                    
                except Exception as e:
                    error_msg = f"프로세스 분석 실패: {str(e)}"
                    print(error_msg)
                
                raise RuntimeError(error_msg)
            
            self.countdown_label.setText("")
            self.status_label.setText("실행 중...")
            self.status_label.setStyleSheet("QLabel { color: blue; }")
            self.stop_button.setEnabled(True)
            
            print(f"프로세스 시작됨 (PID: {self.process.pid})")
            
            # 주기적으로 프로세스 상태 확인하는 타이머 시작
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self.check_process_status)
            self.monitor_timer.start(2000)  # 2초마다 확인
            
        except Exception as e:
            self.countdown_label.setText("")
            self.status_label.setText(f"시작 실패: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; }")
            self.start_button.setEnabled(True)
            print(f"프로세스 시작 실패: {e}")
            
    def execute_stop(self):
        """실제 프로세스 중지 실행"""
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                
                # 3초 대기 후 강제 종료
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                
                print(f"프로세스 종료됨 (PID: {self.process.pid})")
            
            self.countdown_label.setText("")
            self.status_label.setText("준비됨")
            self.status_label.setStyleSheet("QLabel { color: green; }")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.process = None
            
            # 타이머 중지
            if hasattr(self, 'monitor_timer'):
                self.monitor_timer.stop()
            
            # 로그 파일 정리
            if hasattr(self, 'process_log_file') and self.process_log_file:
                self.process_log_file.close()
                self.process_log_file = None
            
        except Exception as e:
            self.countdown_label.setText("")
            self.status_label.setText(f"종료 실패: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; }")
            self.stop_button.setEnabled(True)
            print(f"프로세스 종료 실패: {e}")
    
    def check_process_status(self):
        """프로세스 상태를 주기적으로 확인"""
        if self.process:
            if self.process.poll() is not None:
                # 프로세스가 종료됨
                print(f"프로세스가 종료됨 (PID: {self.process.pid})")
                
                # 로그 파일 정리
                try:
                    if hasattr(self, 'process_log_file') and self.process_log_file:
                        self.process_log_file.close()
                        self.process_log_file = None
                except:
                    pass
                
                # UI 상태 업데이트
                self.status_label.setText("프로세스 종료됨")
                self.status_label.setStyleSheet("QLabel { color: orange; }")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.process = None
                
                # 타이머 중지
                if hasattr(self, 'monitor_timer'):
                    self.monitor_timer.stop()
    
    def closeEvent(self, event):
        """창이 닫힐 때 프로세스 정리"""
        if self.countdown_thread and self.countdown_thread.isRunning():
            self.countdown_thread.stop()
            self.countdown_thread.wait()
        
        # 모니터링 타이머 중지
        if hasattr(self, 'monitor_timer'):
            self.monitor_timer.stop()
        
        # 로그 파일 정리
        if hasattr(self, 'process_log_file') and self.process_log_file:
            self.process_log_file.close()
            self.process_log_file = None
            
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except:
                pass
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # macOS에서 앱이 전면에 나타나도록 설정
    app.setQuitOnLastWindowClosed(True)
    
    controller = TurntableController()
    controller.show()
    controller.raise_()  # 창을 맨 앞으로
    controller.activateWindow()  # 창 활성화
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 