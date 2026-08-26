import pygame
import random as _random


class Meteorite:
    """A meteorite that falls from the sky and fades out on landing."""
    def __init__(self, x, y, frames, speed=2.0):
        self.x = float(x)
        self.y = float(y)
        self.frames = frames
        self.speed = speed
        self.anim_t = 0.0
        self.alive = True
        self.landed = False
        self.fade_alpha = 255
        self.scale = 0.8 + _random.random() * 0.4
        self.angle = _random.uniform(-15, 15)

    def update(self, dt, ground_y):
        self.anim_t += dt
        if not self.landed:
            self.y += self.speed * 60 * dt
            if self.y >= ground_y:
                self.y = ground_y
                self.landed = True
        else:
            self.fade_alpha -= 300 * dt
            if self.fade_alpha <= 0:
                self.alive = False

    def draw(self, screen, camera):
        if not self.frames or not self.alive:
            return
        idx = int(self.anim_t * 8) % len(self.frames)
        raw = self.frames[idx]
        w, h = raw.get_size()
        sw, sh = int(w * self.scale), int(h * self.scale)
        img = pygame.transform.smoothscale(raw, (sw, sh))
        if abs(self.angle) > 1:
            img = pygame.transform.rotate(img, self.angle)
        if self.landed:
            img.set_alpha(max(0, int(self.fade_alpha)))
        sx = int(self.x - camera.x) - img.get_width() // 2
        sy = int(self.y - camera.y) - img.get_height()
        screen.blit(img, (sx, sy))
