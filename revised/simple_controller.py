#!/usr/bin/env python3
"""
🎮 Simple Turntable Controller
==============================
간단한 터테이블 컨트롤러 GUI

Author: AI Assistant
Date: 2025-01-08
"""
import sys
import os
import subprocess
import signal
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon


class ProcessThread(QThread):
    """백그라운드에서 CLI 프로세스를 실행하는 스레드"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.running = False
        
    def run(self):
        """CLI 모드 실행"""
        try:
            # CLI 모드 실행 명령어
            cmd = [
                "/opt/homebrew/Caskroom/miniconda/base/envs/garden/bin/python",
                "turntable_gui_.py",
                "--cli",
                "--duration", "6000",
                "--rpm", "2.5",
                "--transmission-interval", "30",
                "--roi-mode", "Circular",
                "--config", "config.json"
            ]
            
            self.output_signal.emit("🚀 CLI 모드 실행 중...")
            self.output_signal.emit(f"📝 명령어: {' '.join(cmd)}")
            
            # 프로세스 실행
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.running = True
            
            # 실시간 출력 읽기
            while self.running and self.process.poll() is None:
                output = self.process.stdout.readline()
                if output:
                    self.output_signal.emit(output.strip())
                else:
                    time.sleep(0.1)
            
            # 프로세스가 종료된 경우
            if self.process.poll() is not None:
                self.output_signal.emit("✅ CLI 모드가 정상적으로 종료되었습니다.")
            else:
                self.output_signal.emit("🛑 CLI 모드가 중단되었습니다.")
                
        except Exception as e:
            self.output_signal.emit(f"❌ 오류 발생: {e}")
        finally:
            self.running = False
            self.finished_signal.emit()
    
    def stop(self):
        """프로세스 중지"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.output_signal.emit("🛑 CLI 모드가 중지되었습니다.")
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.output_signal.emit("⚠️ 강제 종료되었습니다.")
            except Exception as e:
                self.output_signal.emit(f"❌ 종료 중 오류: {e}")


class SimpleController(QMainWindow):
    """간단한 터테이블 컨트롤러 GUI"""
    
    def __init__(self):
        super().__init__()
        self.process_thread = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🎮 Simple Turntable Controller")
        self.setGeometry(100, 100, 600, 400)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        layout = QVBoxLayout(central_widget)
        
        # 제목
        title_label = QLabel("🎵 Audible Garden Turntable Controller")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel("CLI 모드를 제어하는 간단한 컨트롤러입니다.")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # START 버튼
        self.start_button = QPushButton("🚀 START")
        self.start_button.setMinimumHeight(50)
        self.start_button.clicked.connect(self.start_cli)
        button_layout.addWidget(self.start_button)
        
        # STOP 버튼
        self.stop_button = QPushButton("🛑 STOP")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.clicked.connect(self.stop_cli)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # 상태 표시
        self.status_label = QLabel("대기 중...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 로그 출력 영역
        log_label = QLabel("📋 실행 로그:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 초기 상태 설정
        self.update_status("대기 중")
        
    def update_status(self, status):
        """상태 업데이트"""
        self.status_label.setText(f"상태: {status}")
        
    def log_message(self, message):
        """로그 메시지 추가"""
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        # 자동 스크롤
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def start_cli(self):
        """CLI 모드 시작"""
        if self.process_thread and self.process_thread.isRunning():
            self.log_message("⚠️ 이미 실행 중입니다.")
            return
            
        self.log_message("🎮 START 버튼이 눌렸습니다.")
        self.log_message("⏳ 3초 후 CLI 모드가 시작됩니다...")
        
        # 버튼 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_status("시작 대기 중")
        
        # 3초 대기 후 실행
        def delayed_start():
            time.sleep(3)
            self.log_message("🚀 CLI 모드 시작!")
            self.update_status("실행 중")
            
            # 프로세스 스레드 시작
            self.process_thread = ProcessThread()
            self.process_thread.output_signal.connect(self.log_message)
            self.process_thread.finished_signal.connect(self.on_process_finished)
            self.process_thread.start()
        
        # 백그라운드에서 대기
        wait_thread = threading.Thread(target=delayed_start)
        wait_thread.daemon = True
        wait_thread.start()
        
    def stop_cli(self):
        """CLI 모드 중지"""
        if not self.process_thread or not self.process_thread.isRunning():
            self.log_message("⚠️ 실행 중인 프로세스가 없습니다.")
            return
            
        self.log_message("🛑 STOP 버튼이 눌렸습니다.")
        self.log_message("⏳ 3초 후 CLI 모드가 중지됩니다...")
        
        # 3초 대기 후 중지
        def delayed_stop():
            time.sleep(3)
            self.log_message("🛑 CLI 모드 중지!")
            self.process_thread.stop()
        
        # 백그라운드에서 대기
        stop_thread = threading.Thread(target=delayed_stop)
        stop_thread.daemon = True
        stop_thread.start()
        
    def on_process_finished(self):
        """프로세스 종료 시 호출"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_status("대기 중")
        self.log_message("✅ 컨트롤러가 대기 상태로 돌아갔습니다.")
        
    def closeEvent(self, event):
        """창 닫기 시 처리"""
        if self.process_thread and self.process_thread.isRunning():
            self.log_message("🛑 컨트롤러 종료 중...")
            self.process_thread.stop()
            self.process_thread.wait(5000)  # 5초 대기
        event.accept()


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("Simple Turntable Controller")
    app.setApplicationVersion("1.0")
    
    # 컨트롤러 창 생성
    controller = SimpleController()
    controller.show()
    
    # 이벤트 루프 시작
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 