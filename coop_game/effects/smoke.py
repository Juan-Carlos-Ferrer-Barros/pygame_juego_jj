import pygame


class SmokeParticle:
    """A small smoke puff effect that plays once and disappears."""
    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.frames = frames
        self.t = 0.0
        self.alive = True
        self.speed = 12.0

    def update(self, dt):
        self.t += dt * self.speed
        if int(self.t) >= len(self.frames):
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive or not self.frames:
            return
        idx = min(int(self.t), len(self.frames) - 1)
        img = self.frames[idx]
        sx = int(self.x - camera.x) - img.get_width() // 2
        sy = int(self.y - camera.y) - img.get_height() // 2
        screen.blit(img, (sx, sy))
