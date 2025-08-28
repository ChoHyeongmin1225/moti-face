# emotions/tender.py
import pygame, math
from common_helpers import *

class Emotion:
    def draw(self, surface, common_data):
        left_eye, right_eye, offset, time = common_data['left_eye'], common_data['right_eye'], common_data['offset'], common_data['time']
        pupil_radius = 50 + math.sin(time * 0.002) * 5
        mouth_rect = (surface.get_width()//2-40, surface.get_height()//2+130, 80, 40)
        pygame.draw.arc(surface, WHITE, mouth_rect, math.pi, 2*math.pi, 6)
        cheek = pygame.Surface((100,50), pygame.SRCALPHA)
        alpha = 100 + math.sin(time * 0.002) * 50
        pygame.draw.ellipse(cheek, PINK+(int(alpha),), (0,0,100,50))
        surface.blit(cheek, (left_eye[0]-150, left_eye[1]+20))
        surface.blit(cheek, (right_eye[0]+50, right_eye[1]+20))
        draw_base_eye(surface, left_eye, offset, pupil_radius, SKY_BLUE_START, SKY_BLUE_END)
        draw_base_eye(surface, right_eye, offset, pupil_radius, SKY_BLUE_START, SKY_BLUE_END)