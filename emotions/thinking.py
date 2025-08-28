# emotions/thinking.py (애니메이션 제거 및 고정)

import pygame
import math
from common_helpers import *

class Emotion:
    def draw(self, surface, common_data):
        left_eye, right_eye, offset, time = common_data['left_eye'], common_data['right_eye'], common_data['offset'], common_data['time']

        # [수정] 애니메이션 효과를 제거하고 고정된 값으로 변경
        RIGHT_SIDE_RAISE = 8  # 오른쪽을 얼마나 올릴지 정하는 값
        
        # --- 눈썹 (비대칭 형태로 고정) ---
        eyebrow_thickness = 10
        
        # 왼쪽 눈썹 (평평함)
        left_brow_y = left_eye[1] - 90
        pygame.draw.line(surface, WHITE,
                         (left_eye[0] - 50, left_brow_y),
                         (left_eye[0] + 50, left_brow_y),
                         eyebrow_thickness)

        # 오른쪽 눈썹 (아치형으로 살짝 올라감)
        right_brow_y = right_eye[1] - 90 - RIGHT_SIDE_RAISE
        right_brow_rect = pygame.Rect(right_eye[0] - 50, right_brow_y - 30, 100, 60)
        pygame.draw.arc(surface, WHITE, right_brow_rect, math.radians(20), math.radians(160), eyebrow_thickness)


        # --- 입 모양 ('-' 모양, 중앙 고정) ---
        mouth_center_x = surface.get_width() // 2
        mouth_y = surface.get_height() // 2 + 130
        mouth_width = 80
        
        pygame.draw.line(surface, WHITE,
                         (mouth_center_x - mouth_width // 2, mouth_y),
                         (mouth_center_x + mouth_width // 2, mouth_y),
                         8)

        # --- 눈 그리기 (오른쪽 눈만 살짝 올림) ---
        pupil_radius = 35
        
        # 왼쪽 눈
        draw_base_eye(surface, left_eye, offset, pupil_radius, START_BLUE, END_BLUE)
        # 오른쪽 눈 (y좌표를 수정하여 살짝 올림)
        draw_base_eye(surface, (right_eye[0], right_eye[1] - RIGHT_SIDE_RAISE), offset, pupil_radius, START_BLUE, END_BLUE)