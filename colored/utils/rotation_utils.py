import cv2 as cv
import numpy as np
from collections import deque

class RotationDetector:
    """
    🌀 ORB 특징점 매칭을 이용한 실제 회전 속도(RPM) 감지 클래스
    """
    def __init__(self, fps, buffer_size=30):
        """
        초기화

        Args:
            fps (float): 카메라의 초당 프레임 수
            buffer_size (int): RPM 계산 시 사용할 프레임 버퍼 크기 (평균화 효과)
        """
        self.fps = fps
        self.orb = cv.ORB_create(nfeatures=1000)
        self.matcher = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
        
        self.reference_kp = None
        self.reference_des = None
        
        self.last_angle = 0.0
        self.rpm = 0.0
        
        # RPM 값의 부드러운 평균을 내기 위한 deque
        self.rpm_buffer = deque(maxlen=buffer_size)

    def set_reference_frame(self, frame):
        """
        회전 비교의 기준이 될 첫 프레임을 설정합니다.
        
        Args:
            frame: 기준 프레임 (컬러 이미지)
        """
        if frame is None:
            print("⚠️ 기준 프레임이 없어 회전 감지를 시작할 수 없습니다.")
            return

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        # 중앙 영역에만 마스크를 적용하여 특징점 검출 (성능 및 정확도 향상)
        h, w = gray.shape
        mask = np.zeros_like(gray)
        cv.circle(mask, (w // 2, h // 2), min(w, h) // 3, 255, -1)
        
        self.reference_kp, self.reference_des = self.orb.detectAndCompute(gray, mask)
        self.last_angle = 0.0
        self.rpm_buffer.clear()
        
        if self.reference_des is not None:
            print(f"✅ 회전 감지 기준 프레임 설정 완료 ({len(self.reference_kp)}개 특징점).")
        else:
            print("⚠️ 기준 프레임에서 특징점을 찾지 못했습니다.")

    def calculate_rpm(self, current_frame):
        """
        현재 프레임과 기준 프레임을 비교하여 RPM을 계산합니다.

        Args:
            current_frame: 현재 프레임 (컬러 이미지)

        Returns:
            float: 계산된 현재 RPM 값
        """
        if self.reference_des is None or current_frame is None:
            return 0.0

        gray = cv.cvtColor(current_frame, cv.COLOR_BGR2GRAY)
        current_kp, current_des = self.orb.detectAndCompute(gray, None)

        if current_des is None or len(current_des) < 10:
            return self.rpm # 이전 RPM 값 반환

        # 특징점 매칭
        matches = self.matcher.match(self.reference_des, current_des)
        matches = sorted(matches, key=lambda x: x.distance)
        good_matches = matches[:25] # 상위 25개 매칭 사용

        if len(good_matches) < 10: # 안정적인 변환 행렬을 위해 최소 10개 필요
            return self.rpm

        # 매칭된 점들의 좌표 추출
        ref_pts = np.float32([self.reference_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        cur_pts = np.float32([current_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # 아핀 변환 행렬 추정 (회전 + 이동)
        M, _ = cv.estimateAffinePartial2D(ref_pts, cur_pts)
        
        if M is None:
            return self.rpm

        # 변환 행렬에서 회전 각도 추출
        # M = [[cos(theta), -sin(theta), tx], [sin(theta), cos(theta), ty]]
        angle = np.degrees(np.arctan2(M[1, 0], M[0, 0]))
        
        # 각도 변화량 계산 (360도 경계 처리)
        angle_diff = angle - self.last_angle
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360
            
        self.last_angle = angle

        # 초당 각속도 (degrees per second)
        angular_velocity_dps = angle_diff * self.fps
        
        # RPM으로 변환: (deg/sec * 60 sec/min) / 360 deg/rev
        current_rpm = abs(angular_velocity_dps / 6.0)

        # 버퍼에 추가하여 부드러운 평균 RPM 계산
        self.rpm_buffer.append(current_rpm)
        self.rpm = np.mean(self.rpm_buffer)

        return self.rpm 