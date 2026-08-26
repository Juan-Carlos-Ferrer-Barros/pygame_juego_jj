import math
import pygame
import random as _random
from ..settings import SCREEN_WIDTH, SCREEN_HEIGHT


class BirdDecor:
    """A decorative bird that flies across the screen."""
    def __init__(self, frames, world_w, world_h):
        self.frames = frames
        self.world_w = world_w
        self.facing = 1 if _random.random() > 0.5 else -1
        speed = _random.uniform(40, 80)
        self.vx = speed * self.facing
        self.vy = 0.0
        if self.facing > 0:
            self.x = -50.0
        else:
            self.x = float(world_w + 50)
        self.y = float(_random.randint(30, max(60, int(world_h * 0.35))))
        self.anim_t = _random.random() * 10.0
        self.alive = True
        self.wave_amp = _random.uniform(8, 20)
        self.wave_speed = _random.uniform(1.5, 3.0)
        self.base_y = self.y
        # Smaller birds (was 1.5-2.5, now 0.6-1.0)
        self.scale = _random.uniform(0.6, 1.0)

    def update(self, dt):
        self.anim_t += dt
        self.x += self.vx * dt
        self.y = self.base_y + math.sin(self.anim_t * self.wave_speed) * self.wave_amp
        if self.facing > 0 and self.x > self.world_w + 100:
            self.alive = False
        elif self.facing < 0 and self.x < -100:
            self.alive = False

    def draw(self, screen, camera):
        if not self.frames or not self.alive:
            return
        idx = int(self.anim_t * 8) % len(self.frames)
        raw = self.frames[idx]
        w, h = raw.get_size()
        sw, sh = int(w * self.scale), int(h * self.scale)
        img = pygame.transform.smoothscale(raw, (sw, sh))
        if self.facing < 0:
            img = pygame.transform.flip(img, True, False)
        sx = int(self.x - camera.x) - img.get_width() // 2
        sy = int(self.y - camera.y) - img.get_height() // 2
        if sx > SCREEN_WIDTH + 50 or sx < -80 or sy > SCREEN_HEIGHT + 50 or sy < -80:
            return
        screen.blit(img, (sx, sy))
