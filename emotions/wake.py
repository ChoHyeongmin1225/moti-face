import pygame
import math
from common_helpers import *
from . import neutral

class Emotion:
    def __init__(self):
        self.is_animating = True
        self.start_time = 0
        # Phase 1: Opening (0.75s)
        self.duration_phase1 = 750
        # Phase 2: Pause (1.0s)
        self.duration_pause = 1000
        # Phase 3: Opening (0.75s)
        self.duration_phase2 = 750
        # Total duration for the entire animation, including the pause
        self.total_duration = self.duration_phase1 + self.duration_pause + self.duration_phase2

    def reset(self):
        self.is_animating = True
        self.start_time = pygame.time.get_ticks()

    def draw(self, surface, common_data):
        left_eye, right_eye, offset, time = common_data['left_eye'], common_data['right_eye'], common_data['offset'], common_data['time']

        # Always draw the final eye state as the base layer
        neutral.Emotion().draw(surface, common_data)

        # --- Waking Up Animation Logic ---
        if self.is_animating:
            elapsed = time - self.start_time
            
            # --- Calculate the progress based on the current phase ---
            if elapsed < self.duration_phase1:
                # Phase 1: First half of opening
                progress = elapsed / self.duration_phase1 / 2
            elif elapsed < self.duration_phase1 + self.duration_pause:
                # Phase 2: Pause
                progress = 0.5
            else:
                # Phase 3: Second half of opening
                # Calculate progress for this phase from 0.5 to 1.0
                phase2_elapsed = elapsed - (self.duration_phase1 + self.duration_pause)
                progress = 0.5 + (phase2_elapsed / self.duration_phase2) / 2
                
            progress = min(progress, 1.0) # Ensure progress doesn't exceed 1.0
            
            # The eyelid's height starts at 100 and shrinks to 0 based on progress
            lid_height = 100 * (1 - progress)

            for eye_center in [left_eye, right_eye]:
                # Top eyelid
                top_lid_rect = (eye_center[0] - 100, eye_center[1] - 100, 200, lid_height+10)
                pygame.draw.rect(surface, (0, 0, 0), top_lid_rect)

                # Bottom eyelid
                bottom_lid_rect = (eye_center[0] - 100, eye_center[1] + 100 - lid_height, 200, lid_height+10)
                pygame.draw.rect(surface, (0, 0, 0), bottom_lid_rect)

            # Check if the overall animation is complete
            if elapsed >= self.total_duration:
                self.is_animating = False

        # If animation is finished, nothing is drawn on top of the eyes
        
        # Draw the mouth, which is not part of the eye animation
        pygame.draw.arc(surface, WHITE, (surface.get_width() // 2 - 40, surface.get_height() // 2 + 120, 80, 40), math.pi, 2 * math.pi, 5)