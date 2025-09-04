# main.py (수정됨)

import pygame
import sys
import random
import math
import queue
import os

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
from dotenv import load_dotenv

load_dotenv(dotenv_path='./.env.local')

# Import the HotwordDetector class from hotword.py
from hotword import HotwordDetector
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

class RobotFaceApp:
    def __init__(self):
        pygame.init()

        # 모든 모니터의 해상도를 리스트로 가져옵니다.
        monitor_sizes = pygame.display.get_desktop_sizes()

        # 사용할 모니터의 인덱스를 지정합니다 (0은 메인, 1은 서브 등등).
        monitor_index = 1

        # 만약 모니터가 하나뿐이면, 메인 모니터를 사용하도록 합니다.
        if len(monitor_sizes) <= monitor_index:
            monitor_index = 0

        self.desktop_width, self.desktop_height = monitor_sizes[monitor_index]
        self.original_width, self.original_height = 800, 480

        # 화면 비율을 유지하기 위한 스케일링 비율을 계산합니다.
        self.scale_factor = min(self.desktop_width / self.original_width, self.desktop_height / self.original_height)

        # 새로운 스케일링된 크기를 계산합니다.
        self.scaled_width = int(self.original_width * self.scale_factor)

        # 원래 디자인 해상도로 그리기 위한 베이스 서피스를 생성합니다.
        self.scaled_height = int(self.original_height * self.scale_factor)

        # 전체 화면 모드로 주 화면을 생성하고, 선택한 모니터에 띄웁니다.
        self.screen = pygame.display.set_mode(
            (self.desktop_width, self.desktop_height), 
            0, 
            display=monitor_index
        )

        # 마우스 포커스를 창에 고정하여 클릭 시 창이 닫히는 현상을 방지합니다.
        #pygame.event.set_grab(True)

        self.base_surface = pygame.Surface((self.original_width, self.original_height))

        pygame.display.set_caption("로봇 얼굴 (감정 선택: H, E, T, S, A, B, N)")
        self.clock = pygame.time.Clock()
        self.emotion_timer_start_time = pygame.time.get_ticks()
        self.neutral_to_sleepy_duration = 20000 

        self.wake_timer_start_time = 0 
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

        # --- Hotword Detector Integration ---
        # 1. Create a queue for communication
        self.hotword_queue = queue.Queue()
        # 2. Instantiate and start the hotword detector thread
        self.hotword_detector = HotwordDetector(access_key=PICOVOICE_ACCESS_KEY, hotword_queue=self.hotword_queue)
        self.hotword_detector.start()
        print("Hotword detector thread started.")

    def change_emotion(self, new_emotion_key):
        # 감정을 변경하고 핫워드 감지기의 상태를 관리하는 헬퍼 메서드
        if self.current_emotion_key != new_emotion_key:
            self.current_emotion_key = new_emotion_key
            self.emotion_timer_start_time = pygame.time.get_ticks()

            if hasattr(self.emotions[self.current_emotion_key], 'reset'):
                self.emotions[self.current_emotion_key].reset()

            # 감정에 따른 핫워드 감지 로직
            if new_emotion_key == "SLEEPY":
                # SLEEPY 상태일 때만 핫워드 감지를 시작합니다.
                self.hotword_detector.start_detection()
                print("Now listening for hotword '안녕 모티'.")

            elif new_emotion_key == "WAKE":
                # WAKE 상태일 때는 핫워드 감지를 중지하고, 깨어 있는 시간 타이머를 시작합니다.
                self.hotword_detector.stop_detection()
                self.wake_timer_start_time = pygame.time.get_ticks()
                print("Hotword detection stopped.")

            else:
                # 다른 모든 감정 상태일 때 핫워드 감지를 중지합니다.
                self.hotword_detector.stop_detection()
                print("Not listening for hotword.")

    def handle_events(self):
        # 키보드 및 마우스 입력을 처리하는 메서드
        for event in pygame.event.get():
            # 프로그램 종료 또는 ESC 키 입력을 감지
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            
            # 키보드 입력에 따라 감정을 즉시 변경
            if event.type == pygame.KEYDOWN:
                # SLEEPY 모드일 때는 키보드 입력을 처리하지 않습니다.
                if self.current_emotion_key == "SLEEPY":
                    continue

                key_map = {
                    pygame.K_1: "NEUTRAL", pygame.K_2: "HAPPY", pygame.K_3: "EXCITED",
                    pygame.K_4: "TENDER", pygame.K_5: "SCARED", pygame.K_6: "ANGRY",
                    pygame.K_7: "SAD", pygame.K_8: "SURPRISED", pygame.K_9: "THINKING", 
                    pygame.K_0: "SLEEPY"
                }

                if event.key in key_map:
                    self.change_emotion(key_map[event.key])
            
            # 마우스 클릭 이벤트를 처리
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    self.is_mouse_down = True
                    self.mouse_down_time = pygame.time.get_ticks()

                    # NEUTRAL 상태에서만 터치 횟수를 계산합니다.
                    if self.current_emotion_key == "NEUTRAL" or self.current_emotion_key == "WAKE":
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

            # 눈동자 무작위 움직임과 깜빡임 이벤트를 처리
            if event.type == pygame.USEREVENT + 1:
                self.target_offset = self.get_random_target_offset()
            if event.type == pygame.USEREVENT + 2 and not self.is_blinking:
                self.is_blinking = True
                self.blink_progress = 0
        return True

    def update(self):
        # 게임의 논리 및 상태 변경을 처리하는 메서드
        # 핫워드 감지 큐를 확인하여 메시지가 있으면 WAKE 상태로 전환
        try:
            message = self.hotword_queue.get_nowait()
            if message == "hotword_detected":
                print("Hotword detected in main thread. Waking up!")
                # Change to WAKE emotion when hotword is detected
                self.change_emotion("WAKE")
        except queue.Empty:
            pass
        
        # 눈동자 움직임 로직
        dx = self.target_offset[0] - self.common_data['offset'][0]
        dy = self.target_offset[1] - self.common_data['offset'][1]
        dist = math.hypot(dx, dy)

        # 모든 감정 전환 로직
         # 1. SLEEPY 상태에서 마우스 홀드로 WAKE로 전환
        if self.current_emotion_key == "SLEEPY":
            if self.is_mouse_down and pygame.time.get_ticks() - self.mouse_down_time >= self.hold_duration:
                self.change_emotion("WAKE")

         # 2. WAKE 상태에서 3초 후 NEUTRAL로 전환
        elif self.current_emotion_key == "WAKE":
            if pygame.time.get_ticks() - self.wake_timer_start_time >= 3000:
                self.change_emotion("NEUTRAL")

         # 3. NEUTRAL 상태에서 3번의 터치로 ANGRY로 전환
        elif self.current_emotion_key == "NEUTRAL":
            if self.click_count >= 3:
                self.change_emotion("ANGRY")
                self.click_count = 0

            # NEUTRAL 상태에서 20초 후 SLEEPY로 전환
            elif pygame.time.get_ticks() - self.emotion_timer_start_time >= 20000:
                self.change_emotion("SLEEPY")

        # 4. 그 외 모든 감정 상태일 때의 동작 (ANGRY, SAD 등)
        else:
            if pygame.time.get_ticks() - self.emotion_timer_start_time >= 10000:
                self.change_emotion("NEUTRAL")

        # 눈동자 움직임과 깜빡임 상태를 업데이트
        if dist > self.move_speed:
            self.common_data['offset'][0] += (dx / dist) * self.move_speed
            self.common_data['offset'][1] += (dy / dist) * self.move_speed
        
        if self.is_blinking:
            self.blink_progress += self.normal_blink_speed
            if self.blink_progress >= 200:
                self.is_blinking = False
        
        self.common_data['time'] = pygame.time.get_ticks()

    def draw(self):
        # 화면 요소를 그리는 메서드
        # 주 화면을 검은색으로 채웁니다.
        # 모든 요소를 그릴 베이스 서피스를 검은색으로 채워 초기화합니다.
        self.screen.fill((0, 0, 0))
        self.base_surface.fill((0, 0, 0))
        
        # 현재 감정 키에 해당하는 감정 객체를 가져옵니다.
        # 베이스 서피스에 현재 감정의 얼굴을 그립니다.
        current_emotion = self.emotions[self.current_emotion_key]
        current_emotion.draw(self.base_surface, self.common_data)

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
        
        # 스케일링된 서피스를 주 화면에 복사합니다.
        self.screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()
        
    def get_random_target_offset(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, self.max_pupil_move_distance)
        return [math.cos(angle) * distance, math.sin(angle) * distance]

    def run(self):
        # 애플리케이션의 메인 루프
        running = True

        # 프로그램 시작 시 초기 감정 상태에 따라 핫워드 감지기를 설정합니다.
        # (예: NEUTRAL 상태에서 시작하므로 SLEEPY로 전환될 때까지는 비활성화됩니다)
        if self.current_emotion_key == "SLEEPY":
            self.change_emotion("SLEEPY")

        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        # 프로그램 종료 시 핫워드 감지 스레드를 안전하게 종료
        self.hotword_detector.stop()
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    app = RobotFaceApp()
    app.run()