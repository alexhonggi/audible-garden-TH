#!/usr/bin/env python3
"""
🎮 Minimal Turntable Controller
===============================
정말 START/STOP 버튼만 있는 최소한의 컨트롤러

Author: AI Assistant
Date: 2025-01-08
"""
import sys
import os
import subprocess
import signal
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont


class ProcessThread(QThread):
    """백그라운드에서 CLI 프로세스를 실행하는 스레드"""
    finished_signal = pyqtSignal()
    ready_signal = pyqtSignal()  # 시스템 준비 완료 시그널
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.running = False
        
    def run(self):
        """CLI 모드 실행"""
        try:
            # CLI 모드 실행 명령어
            cmd = [
                sys.executable,
                "turntable_gui_.py",
                "--cli",
                "--duration", "6000",
                "--rpm", "2.5",
                "--transmission-interval", "30",
                "--roi-mode", "Circular",
                "--config", "config.json",
                "--osc-ports", "5555,5556,5557"
            ]
            
            # 프로세스 실행 (출력 모니터링)
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.running = True
            baseline_complete = False
            
            # 프로세스가 종료될 때까지 대기하면서 출력 모니터링
            while self.running and self.process.poll() is None:
                output = self.process.stdout.readline()
                if output:
                    output = output.strip()
                    # 기준 설정 완료 감지
                    if "✅ 기준 데이터 수집 완료!" in output and not baseline_complete:
                        baseline_complete = True
                        self.ready_signal.emit()
                else:
                    time.sleep(0.1)
            
        except Exception as e:
            pass  # 오류도 조용히 무시
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
            except:
                try:
                    self.process.kill()
                except:
                    pass


class MinimalController(QMainWindow):
    """최소한의 터테이블 컨트롤러 GUI - START/STOP 버튼만"""
    
    def __init__(self):
        super().__init__()
        self.process_thread = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화 - 버튼만"""
        self.setWindowTitle("Turntable Controller")
        self.setGeometry(100, 100, 300, 100)
        self.setFixedSize(300, 100)  # 크기 고정
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # START 버튼
        self.start_button = QPushButton("START")
        self.start_button.setMinimumHeight(60)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.start_button.clicked.connect(self.start_cli)
        layout.addWidget(self.start_button)
        
        # STOP 버튼
        self.stop_button = QPushButton("STOP")
        self.stop_button.setMinimumHeight(60)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_button.clicked.connect(self.stop_cli)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        # 상태 표시 라벨 (파란 불)
        self.status_label = QLabel("●")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
        
    def start_cli(self):
        """CLI 모드 시작"""
        if self.process_thread and self.process_thread.isRunning():
            return
            
        # 버튼 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # 대기 상태(stand-by) 표시: 오렌지 불
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FFA500;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        # 0.01초 대기 후 실행
        def delayed_start():
            time.sleep(0.01)
            
            # 프로세스 스레드 시작
            self.process_thread = ProcessThread()
            self.process_thread.finished_signal.connect(self.on_process_finished)
            self.process_thread.ready_signal.connect(self.on_system_ready)
            self.process_thread.start()
        
        # 백그라운드에서 대기
        wait_thread = threading.Thread(target=delayed_start)
        wait_thread.daemon = True
        wait_thread.start()
        
    def stop_cli(self):
        """CLI 모드 중지"""
        if not self.process_thread or not self.process_thread.isRunning():
            return
            
        # 0.01초 대기 후 중지
        def delayed_stop():
            time.sleep(0.01)
            self.process_thread.stop()
        
        # 백그라운드에서 대기
        stop_thread = threading.Thread(target=delayed_stop)
        stop_thread.daemon = True
        stop_thread.start()
        
    def on_process_finished(self):
        """프로세스 종료 시 호출"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        # 파란 불 끄기
        self.status_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
    def on_system_ready(self):
        """시스템 준비 완료 시 호출 (파란 불 켜기)"""
        self.status_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
    def closeEvent(self, event):
        """창 닫기 시 처리"""
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.stop()
            self.process_thread.wait(5000)  # 5초 대기
        event.accept()


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("Minimal Turntable Controller")
    app.setApplicationVersion("1.0")
    
    # 컨트롤러 창 생성
    controller = MinimalController()
    controller.show()
    
    # 이벤트 루프 시작
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 