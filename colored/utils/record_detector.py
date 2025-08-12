#!/usr/bin/env python3
"""
🎵 Record Detector - 턴테이블에 레코드가 있는지 감지
==================================================
카메라 영상에서 턴테이블에 레코드가 놓여있는지 감지하는 모듈

Author: AI Assistant
Date: 2025-01-08
"""
import cv2 as cv
import numpy as np
import time
from typing import Tuple, Optional, Dict, Any


class RecordDetector:
    """
    턴테이블에 레코드가 있는지 감지하는 클래스
    """
    
    def __init__(self, 
                 detection_method: str = "color_analysis",
                 roi_coords: Optional[Tuple] = None,
                 threshold: float = 0.1,  # 더 낮은 임계값으로 변경
                 baseline_frames: int = 30,
                 smoothing_factor: float = 0.8):
        """
        초기화
        
        Args:
            detection_method: 감지 방법 ("color_analysis", "template_matching", "edge_analysis")
            roi_coords: 감지할 ROI 좌표 (center_x, center_y, radius) 또는 (x, y, w, h)
            threshold: 레코드 감지 임계값
            baseline_frames: 기준 프레임 수집 개수
            smoothing_factor: 결과 스무딩 팩터 (0-1)
        """
        self.detection_method = detection_method
        self.roi_coords = roi_coords
        self.threshold = threshold
        self.baseline_frames = baseline_frames
        self.smoothing_factor = smoothing_factor
        
        # 상태 변수
        self.baseline_collected = False
        self.baseline_data = None
        self.record_present = False
        self.confidence = 0.0
        self.frame_count = 0
        self.smoothed_confidence = 0.0
        
        # 그레이스케일 평균 관련 변수 (전송 간격 동적 조정용)
        self.grayscale_averages = []
        self.calibrated_grayscale_avg = None
        self.dynamic_transmission_interval = None
        
        # 템플릿 매칭용 변수
        self.empty_template = None
        self.template_collected = False
        
        print(f"🎵 Record Detector 초기화 완료 - 방법: {detection_method}")
    
    def set_roi(self, roi_coords: Tuple):
        """ROI 좌표 설정"""
        self.roi_coords = roi_coords
        print(f"🎯 ROI 설정: {roi_coords}")
    
    def collect_baseline(self, frame: np.ndarray) -> bool:
        """
        빈 턴테이블 기준 데이터 수집
        
        Args:
            frame: 입력 프레임
            
        Returns:
            bool: 기준 수집 완료 여부
        """
        if self.baseline_collected:
            return True
            
        if self.frame_count < self.baseline_frames:
            # 기준 데이터 수집
            if self.detection_method == "color_analysis":
                self._collect_color_baseline(frame)
            elif self.detection_method == "template_matching":
                self._collect_template_baseline(frame)
            elif self.detection_method == "edge_analysis":
                self._collect_edge_baseline(frame)
            
            # 그레이스케일 평균 수집 (모든 방법에 대해 공통으로 수집)
            self._collect_grayscale_average(frame)
            
            self.frame_count += 1
            print(f"📊 기준 데이터 수집 중... ({self.frame_count}/{self.baseline_frames})")
            return False
        else:
            # 기준 수집 완료
            self.baseline_collected = True
            self._calculate_dynamic_transmission_interval()
            print("✅ 기준 데이터 수집 완료!")
            brightness_level = "어두움" if self.calibrated_grayscale_avg < 0.33 else ("보통" if self.calibrated_grayscale_avg < 0.67 else "밝음")
            print(f"📈 동적 전송 간격: {self.dynamic_transmission_interval}프레임 (그레이스케일: {self.calibrated_grayscale_avg:.3f} - {brightness_level})")
            return True
    
    def _collect_color_baseline(self, frame: np.ndarray):
        """색상 분석 기준 데이터 수집"""
        roi_data = self._extract_roi(frame)
        if roi_data is not None:
            # 색상 히스토그램 계산
            hist = cv.calcHist([roi_data], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv.normalize(hist, hist).flatten()
            
            if self.baseline_data is None:
                self.baseline_data = []
            self.baseline_data.append(hist)
    
    def _collect_template_baseline(self, frame: np.ndarray):
        """템플릿 매칭 기준 데이터 수집"""
        roi_data = self._extract_roi(frame)
        if roi_data is not None and not self.template_collected:
            # 첫 번째 프레임을 템플릿으로 저장
            self.empty_template = roi_data.copy()
            self.template_collected = True
    
    def _collect_edge_baseline(self, frame: np.ndarray):
        """엣지 분석 기준 데이터 수집"""
        roi_data = self._extract_roi(frame)
        if roi_data is not None:
            # 그레이스케일 변환
            gray = cv.cvtColor(roi_data, cv.COLOR_BGR2GRAY)
            # 엣지 감지
            edges = cv.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            if self.baseline_data is None:
                self.baseline_data = []
            self.baseline_data.append(edge_density)
    
    def _collect_grayscale_average(self, frame: np.ndarray):
        """ROI 영역의 그레이스케일 평균값 수집"""
        roi_data = self._extract_roi(frame)
        if roi_data is not None:
            # 그레이스케일 변환
            gray = cv.cvtColor(roi_data, cv.COLOR_BGR2GRAY)
            # 평균값 계산 (0~255)
            avg_grayscale = np.mean(gray)
            self.grayscale_averages.append(avg_grayscale)
    
    def _calculate_dynamic_transmission_interval(self):
        """수집된 그레이스케일 평균값을 바탕으로 동적 전송 간격 계산"""
        if not self.grayscale_averages:
            self.dynamic_transmission_interval = 60  # 기본값
            return
        
        # 수집된 그레이스케일 평균값들의 평균 계산
        avg_grayscale = np.mean(self.grayscale_averages)
        self.calibrated_grayscale_avg = avg_grayscale / 255.0  # 0~1로 정규화
        
        # 3개 구간으로 나누어 50, 60, 70 매핑
        # 0.0~0.33 (어두움) -> 70 (느린 전송)
        # 0.33~0.67 (보통) -> 60 (중간 전송)  
        # 0.67~1.0 (밝음) -> 50 (빠른 전송)
        if self.calibrated_grayscale_avg < 0.33:
            bin_index = 0  # 어두움
        elif self.calibrated_grayscale_avg < 0.67:
            bin_index = 1  # 보통
        else:
            bin_index = 2  # 밝음
        
        # 3개 구간을 50, 60, 70에 매핑 (어두울수록 느린 전송)
        transmission_intervals = [70, 60, 50]  # [어두움, 보통, 밝음]
        self.dynamic_transmission_interval = transmission_intervals[bin_index]
    
    def detect_record(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        레코드 감지
        
        Args:
            frame: 입력 프레임
            
        Returns:
            Tuple[bool, float]: (레코드 존재 여부, 신뢰도)
        """
        if not self.baseline_collected:
            # 기준 수집이 완료되지 않았으면 수집 계속
            self.collect_baseline(frame)
            return False, 0.0
        
        # 감지 방법에 따른 처리
        if self.detection_method == "color_analysis":
            confidence = self._detect_by_color(frame)
        elif self.detection_method == "template_matching":
            confidence = self._detect_by_template(frame)
        elif self.detection_method == "edge_analysis":
            confidence = self._detect_by_edge(frame)
        else:
            confidence = 0.0
        
        # 결과 스무딩
        self.smoothed_confidence = (
            self.smoothing_factor * self.smoothed_confidence + 
            (1 - self.smoothing_factor) * confidence
        )
        
        # 레코드 존재 여부 판단
        record_present = self.smoothed_confidence > self.threshold
        
        # 상태 업데이트
        self.record_present = record_present
        self.confidence = confidence
        
        return record_present, self.smoothed_confidence
    
    def _detect_by_color(self, frame: np.ndarray) -> float:
        """색상 분석으로 레코드 감지"""
        roi_data = self._extract_roi(frame)
        if roi_data is None:
            return 0.0
        
        # 현재 프레임의 히스토그램 계산
        current_hist = cv.calcHist([roi_data], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        current_hist = cv.normalize(current_hist, current_hist).flatten()
        
        # 기준 히스토그램과 비교
        baseline_hist = np.mean(self.baseline_data, axis=0)
        similarity = cv.compareHist(current_hist, baseline_hist, cv.HISTCMP_CORREL)
        
        # 유사도가 낮을수록 레코드가 있을 가능성이 높음
        # 더 민감하게 조정
        confidence = 1.0 - (similarity + 1.0) / 2.0
        # 신뢰도를 증폭 (더 민감하게)
        return min(confidence * 5.0, 1.0)
    
    def _detect_by_template(self, frame: np.ndarray) -> float:
        """템플릿 매칭으로 레코드 감지"""
        if self.empty_template is None:
            return 0.0
        
        roi_data = self._extract_roi(frame)
        if roi_data is None:
            return 0.0
        
        # 템플릿 매칭
        result = cv.matchTemplate(roi_data, self.empty_template, cv.TM_CCOEFF_NORMED)
        similarity = result[0, 0]
        
        # 유사도가 낮을수록 레코드가 있을 가능성이 높음
        return 1.0 - similarity
    
    def _detect_by_edge(self, frame: np.ndarray) -> float:
        """엣지 분석으로 레코드 감지"""
        roi_data = self._extract_roi(frame)
        if roi_data is None:
            return 0.0
        
        # 그레이스케일 변환
        gray = cv.cvtColor(roi_data, cv.COLOR_BGR2GRAY)
        # 엣지 감지
        edges = cv.Canny(gray, 50, 150)
        current_edge_density = np.sum(edges > 0) / edges.size
        
        # 기준 엣지 밀도와 비교
        baseline_edge_density = np.mean(self.baseline_data)
        edge_change = abs(current_edge_density - baseline_edge_density)
        
        # 엣지 변화가 클수록 레코드가 있을 가능성이 높음
        return min(edge_change * 10, 1.0)  # 스케일링
    
    def _extract_roi(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """ROI 영역 추출"""
        if self.roi_coords is None:
            return None
        
        if len(self.roi_coords) == 3:
            # 원형 ROI
            center_x, center_y, radius = self.roi_coords
            x1 = max(0, center_x - radius)
            y1 = max(0, center_y - radius)
            x2 = min(frame.shape[1], center_x + radius)
            y2 = min(frame.shape[0], center_y + radius)
            return frame[y1:y2, x1:x2]
        elif len(self.roi_coords) == 4:
            # 직사각형 ROI
            x, y, w, h = self.roi_coords
            return frame[y:y+h, x:x+w]
        else:
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 정보 반환"""
        return {
            'record_present': self.record_present,
            'confidence': self.confidence,
            'smoothed_confidence': self.smoothed_confidence,
            'baseline_collected': self.baseline_collected,
            'detection_method': self.detection_method,
            'threshold': self.threshold,
            'calibrated_grayscale_avg': self.calibrated_grayscale_avg,
            'dynamic_transmission_interval': self.dynamic_transmission_interval
        }
    
    def get_dynamic_transmission_interval(self) -> int:
        """동적으로 계산된 전송 간격 반환"""
        if self.dynamic_transmission_interval is not None:
            return self.dynamic_transmission_interval
        else:
            return 60  # 기본값
    
    def reset_baseline(self):
        """기준 데이터 재설정"""
        self.baseline_collected = False
        self.baseline_data = None
        self.empty_template = None
        self.template_collected = False
        self.frame_count = 0
        self.smoothed_confidence = 0.0
        self.grayscale_averages = []
        self.calibrated_grayscale_avg = None
        self.dynamic_transmission_interval = None
        print("🔄 기준 데이터 재설정 완료")


def create_record_detector(method: str = "color_analysis", **kwargs) -> RecordDetector:
    """
    레코드 감지기 생성 헬퍼 함수
    
    Args:
        method: 감지 방법
        **kwargs: 추가 설정
        
    Returns:
        RecordDetector: 레코드 감지기 인스턴스
    """
    return RecordDetector(detection_method=method, **kwargs) 