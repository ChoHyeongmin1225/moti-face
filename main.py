# main.py (수정됨)

import pygame
import sys
import random
import math

# 각 감정 모듈에서 Emotion 클래스를 불러옵니다.
from emotions.neutral import Emotion as NeutralEmotion
from emotions.happy import Emotion as HappyEmotion
from emotions.excited import Emotion as ExcitedEmotion
from emotions.tender import Emotion as TenderEmotion
from emotions.scared import Emotion as ScaredEmotion
from emotions.angry import Emotion as AngryEmotion
from emotions.sad import Emotion as SadEmotion
from emotions.surprised import Emotion as SurprisedEmotion
from emotions.thinking import Emotion as ThinkingEmotion
from emotions.sleepy import Emotion as SleepyEmotion

class RobotFaceApp:
    def __init__(self):
        pygame.init()
        self.screen_width, self.screen_height = 800, 480
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("로봇 얼굴 (감정 선택: H, E, T, S, A, B, N)")
        self.clock = pygame.time.Clock()

        self.common_data = {
            'left_eye': (self.screen_width // 2 - 200, self.screen_height // 2),
            'right_eye': (self.screen_width // 2 + 200, self.screen_height // 2),
            'offset': [0.0, 0.0],
            'time': 0
        }
        
        self.target_offset = [0.0, 0.0]
        self.move_speed = 1.5
        self.max_pupil_move_distance = 20
        self.is_blinking = False
        self.blink_progress = 0
        self.normal_blink_speed = 15

        pygame.time.set_timer(pygame.USEREVENT + 1, random.randint(2000, 5000))
        pygame.time.set_timer(pygame.USEREVENT + 2, random.randint(2000, 5000))
        
        # 각 클래스의 인스턴스를 생성합니다.
        self.emotions = {
            "NEUTRAL": NeutralEmotion(), "HAPPY": HappyEmotion(), "EXCITED": ExcitedEmotion(),
            "TENDER": TenderEmotion(), "SCARED": ScaredEmotion(), "ANGRY": AngryEmotion(), "SAD": SadEmotion(), "SURPRISED": SurprisedEmotion(), "THINKING": ThinkingEmotion(), "SLEEPY": SleepyEmotion()
        }
        self.current_emotion_key = "NEUTRAL"

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            if event.type == pygame.KEYDOWN:
                key_map = {
                    pygame.K_n: "NEUTRAL", pygame.K_h: "HAPPY", pygame.K_e: "EXCITED",
                    pygame.K_t: "TENDER", pygame.K_s: "SCARED", pygame.K_a: "ANGRY", pygame.K_b: "SAD", pygame.K_u: "SURPRISED", pygame.K_i: "THINKING", pygame.K_z: "SLEEPY"
                }
                if event.key in key_map:
                    self.current_emotion_key = key_map[event.key]
            
            if event.type == pygame.USEREVENT + 1:
                self.target_offset = self.get_random_target_offset()
            if event.type == pygame.USEREVENT + 2 and not self.is_blinking:
                self.is_blinking = True
                self.blink_progress = 0
        return True

    def update(self):
        dx = self.target_offset[0] - self.common_data['offset'][0]
        dy = self.target_offset[1] - self.common_data['offset'][1]
        dist = math.hypot(dx, dy)
        if dist > self.move_speed:
            self.common_data['offset'][0] += (dx / dist) * self.move_speed
            self.common_data['offset'][1] += (dy / dist) * self.move_speed
        
        if self.is_blinking:
            self.blink_progress += self.normal_blink_speed
            if self.blink_progress >= 200:
                self.is_blinking = False
        
        self.common_data['time'] = pygame.time.get_ticks()

    def draw(self):
        self.screen.fill((0,0,0))
        
        current_emotion = self.emotions[self.current_emotion_key]
        current_emotion.draw(self.screen, self.common_data)
        
        if self.is_blinking:
            progress = self.blink_progress if self.blink_progress <= 100 else 200 - self.blink_progress
            for eye_center in [self.common_data['left_eye'], self.common_data['right_eye']]:
                top_rect = (eye_center[0]-100, eye_center[1]-100, 200, progress)
                bottom_rect = (eye_center[0]-100, eye_center[1]+100-progress, 200, progress)
                pygame.draw.rect(self.screen, (0,0,0), top_rect)
                pygame.draw.rect(self.screen, (0,0,0), bottom_rect)

        pygame.display.flip()
        
    def get_random_target_offset(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, self.max_pupil_move_distance)
        return [math.cos(angle) * distance, math.sin(angle) * distance]

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    app = RobotFaceApp()
    app.run()