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
from emotions.wake import Emotion as wake
from emotions import eyebrow
from emotions import cheeks

class RobotFaceApp:
    def __init__(self):
        pygame.init()
        self.desktop_width, self.desktop_height = pygame.display.get_desktop_sizes()[1]
        self.original_width, self.original_height = 800, 480

        # 화면 비율을 유지하기 위한 스케일링 비율을 계산합니다.
        self.scale_factor = min(self.desktop_width / self.original_width, self.desktop_height / self.original_height)

        # 새로운 스케일링된 크기를 계산합니다.
        self.scaled_width = int(self.original_width * self.scale_factor)

        # 원래 디자인 해상도로 그리기 위한 베이스 서피스를 생성합니다.
        self.scaled_height = int(self.original_height * self.scale_factor)

        # 스케일링된 크기로 주 화면을 생성합니다.
        self.screen = pygame.display.set_mode((self.scaled_width, self.scaled_height), pygame.FULLSCREEN)
        self.base_surface = pygame.Surface((self.original_width, self.original_height))

        pygame.display.set_caption("로봇 얼굴 (감정 선택: H, E, T, S, A, B, N)")
        self.clock = pygame.time.Clock()
        self.emotion_timer_start_time = pygame.time.get_ticks()
        self.neutral_to_sleepy_duration = 20000 

        # 마우스 누르기 상태를 추적하는 변수입니다.
        self.is_mouse_down = False
        self.mouse_down_time = 0

        # 2초(밀리초) 동안 누르고 있을 때를 위한 타이머입니다.
        self.hold_duration = 2000

        # 터치 횟수 및 타이머 변수
        self.click_count = 0
        self.click_timer = 0
        self.click_timeout = 3000 # 3초 안에 3번 터치해야 함


        self.common_data = {
            'left_eye': (self.original_width // 2 - 200, self.original_height // 2),
            'right_eye': (self.original_width // 2 + 200, self.original_height // 2),
            'offset': [0.0, 0.0],
            'time': 0,
            'scale_factor': self.scale_factor
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
            "TENDER": TenderEmotion(), "SCARED": ScaredEmotion(), "ANGRY": AngryEmotion(), 
            "SAD": SadEmotion(), "SURPRISED": SurprisedEmotion(), "THINKING": ThinkingEmotion(), 
            "SLEEPY": SleepyEmotion(), "WAKE": wake()
        }
        self.current_emotion_key = "NEUTRAL"


        # Initialize the eyebrow_drawers dictionary here (THIS WAS MISSING/INCORRECT)
        self.eyebrow_drawers = {
            "ANGRY": eyebrow.draw_angry_eyebrows,
            "SAD": eyebrow.draw_sad_eyebrows,
            "THINKING": eyebrow.draw_thinking_eyebrows,
        }

        self.cheek_drawers = {
            "HAPPY": cheeks.draw_happy_cheeks,
            "TENDER": cheeks.draw_tender_cheeks,
        }

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            
            if event.type == pygame.KEYDOWN:
                key_map = {
                    pygame.K_n: "NEUTRAL", pygame.K_h: "HAPPY", pygame.K_e: "EXCITED",
                    pygame.K_t: "TENDER", pygame.K_s: "SCARED", pygame.K_a: "ANGRY",
                    pygame.K_b: "SAD", pygame.K_u: "SURPRISED", pygame.K_i: "THINKING", 
                    pygame.K_z: "SLEEPY"
                }
                if event.key in key_map:
                    if self.current_emotion_key != key_map[event.key]:
                        self.current_emotion_key = key_map[event.key]
                        self.emotion_timer_start_time = pygame.time.get_ticks()
                    if hasattr(self.emotions[self.current_emotion_key], 'reset'):
                            self.emotions[self.current_emotion_key].reset()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    self.is_mouse_down = True
                    self.mouse_down_time = pygame.time.get_ticks()

                    # NEUTRAL 상태에서만 터치 횟수를 계산합니다.
                    if self.current_emotion_key == "NEUTRAL":
                        current_time = pygame.time.get_ticks()
                        # 1초 이상 간격이 벌어졌으면 카운트를 초기화합니다.
                        if current_time - self.click_timer > self.click_timeout:
                            self.click_count = 1
                        else:
                            self.click_count += 1
                        self.click_timer = current_time
                    else:
                        # NEUTRAL 상태가 아니면 카운트를 초기화합니다.
                        self.click_count = 0

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_mouse_down = False

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

        # 마우스가 눌려있을 때 SLEEPY에서 WAKE로 전환하는 로직이 가장 우선순위가 높습니다.
        if self.current_emotion_key == "SLEEPY" and self.is_mouse_down:
            if pygame.time.get_ticks() - self.mouse_down_time >= self.hold_duration:
                self.current_emotion_key = "WAKE"
                # 감정 전환 후 타이머를 리셋합니다.
                self.emotion_timer_start_time = pygame.time.get_ticks()
                if hasattr(self.emotions[self.current_emotion_key], 'reset'):
                    self.emotions[self.current_emotion_key].reset()

        # 현재 감정이 SLEEPY가 아닐 때만 아래 타이머 로직을 실행합니다.
        elif self.current_emotion_key != "SLEEPY":
            # NEUTRAL 상태에서 20초가 지나면 SLEEPY로 전환합니다.
            if self.current_emotion_key == "NEUTRAL":
                if pygame.time.get_ticks() - self.emotion_timer_start_time >= 20000:
                    self.current_emotion_key = "SLEEPY"
                    self.emotion_timer_start_time = pygame.time.get_ticks()
                    if hasattr(self.emotions[self.current_emotion_key], 'reset'):
                        self.emotions[self.current_emotion_key].reset()
            # SLEEPY나 NEUTRAL이 아닌 다른 감정에서 10초가 지나면 NEUTRAL로 전환합니다.
            else:
                if pygame.time.get_ticks() - self.emotion_timer_start_time >= 10000:
                    self.current_emotion_key = "NEUTRAL"
                    self.emotion_timer_start_time = pygame.time.get_ticks()
                    if hasattr(self.emotions[self.current_emotion_key], 'reset'):
                        self.emotions[self.current_emotion_key].reset()

        # 추가: NEUTRAL 상태에서 3번 이상 터치하면 ANGRY로 전환합니다.
        if self.current_emotion_key == "NEUTRAL" and self.click_count >= 3:
            self.current_emotion_key = "ANGRY"
            self.click_count = 0 # 터치 횟수 초기화
            if hasattr(self.emotions[self.current_emotion_key], 'reset'):
                self.emotions[self.current_emotion_key].reset()

        if dist > self.move_speed:
            self.common_data['offset'][0] += (dx / dist) * self.move_speed
            self.common_data['offset'][1] += (dy / dist) * self.move_speed
        
        if self.is_blinking:
            self.blink_progress += self.normal_blink_speed
            if self.blink_progress >= 200:
                self.is_blinking = False
        
        self.common_data['time'] = pygame.time.get_ticks()

    def draw(self):
        # 주 화면을 검은색으로 채웁니다.
        # 모든 요소를 그릴 베이스 서피스를 검은색으로 채워 초기화합니다.
        self.screen.fill((0, 0, 0))
        self.base_surface.fill((0, 0, 0))
        
        # 현재 감정 키에 해당하는 감정 객체를 가져옵니다.
        # 베이스 서피스에 현재 감정의 얼굴을 그립니다.
        current_emotion = self.emotions[self.current_emotion_key]
        current_emotion.draw(self.base_surface, self.common_data)

        # 감정이 'SLEEPY'이고 마우스가 2초 이상 눌렸을 경우, 'WAKE' 감정으로 전환하는 로직입니다.
        if self.current_emotion_key == "SLEEPY" and self.is_mouse_down:
            if pygame.time.get_ticks() - self.mouse_down_time >= self.hold_duration:
                self.current_emotion_key = "WAKE"
                if hasattr(self.emotions[self.current_emotion_key], 'reset'):
                    self.emotions[self.current_emotion_key].reset()

        # 깜빡이는 중이고 감정이 'SLEEPY'가 아닐 경우, 눈꺼풀을 그립니다.
        if self.is_blinking and self.current_emotion_key != "SLEEPY":
            progress = self.blink_progress if self.blink_progress <= 100 else 200 - self.blink_progress
            for eye_center in [self.common_data['left_eye'], self.common_data['right_eye']]:
                top_rect = (eye_center[0]-100, eye_center[1]-150, 200, progress+50)
                bottom_rect = (eye_center[0]-100, eye_center[1]+100-progress, 200, progress+50)
                pygame.draw.rect(self.base_surface, (0,0,0), top_rect)
                pygame.draw.rect(self.base_surface, (0,0,0), bottom_rect)

        # 현재 감정 키에 따라 눈썹을 그립니다.
        if self.current_emotion_key in self.eyebrow_drawers:
            self.eyebrow_drawers[self.current_emotion_key](self.base_surface, self.common_data)
        
        # 현재 감정 키에 따라 볼을 그립니다.
        if self.current_emotion_key in self.cheek_drawers:
            self.cheek_drawers[self.current_emotion_key](self.base_surface, self.common_data)
        
        # 베이스 서피스를 주 화면 크기에 맞게 스케일링합니다.
        # 스케일링된 서피스를 주 화면에 복사합니다.
        scaled_surface = pygame.transform.scale(self.base_surface, (self.scaled_width, self.scaled_height))
        self.screen.blit(scaled_surface, (0, 0))

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