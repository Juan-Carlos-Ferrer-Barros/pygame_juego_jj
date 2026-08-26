import pygame
from ..settings import TILE_SIZE


class MovingPlatform:
    def __init__(self, rect, platform_id, axis, distance, speed, active, assets):
        self.base = pygame.Vector2(rect.topleft)
        self.rect = rect
        self.top_rect = pygame.Rect(rect.x, rect.y, rect.w, 10)
        self.id = platform_id
        self.axis = axis
        self.distance = distance
        self.speed = speed
        self.active = active
        self.offset = 0
        self.direction = 1
        self.image = assets.get_tile('bridge', size=(rect.w, rect.h))
        self.delta = pygame.Vector2(0, 0)

    def update(self):
        prev = pygame.Vector2(self.rect.topleft)
        if self.active:
            self.offset += self.speed * self.direction
            if abs(self.offset) >= self.distance:
                self.offset = max(-self.distance, min(self.offset, self.distance))
                self.direction *= -1
        if self.axis == 'y':
            self.rect.y = int(self.base.y + self.offset)
        else:
            self.rect.x = int(self.base.x + self.offset)
        self.top_rect.topleft = self.rect.topleft
        self.delta = pygame.Vector2(self.rect.x - prev.x, self.rect.y - prev.y)

    def draw(self, screen, camera):
        pygame.draw.rect(screen, (135, 90, 45), camera.apply_rect(self.rect), border_radius=3)
        pygame.draw.rect(screen, (185, 140, 80), camera.apply_rect(self.rect.inflate(0, -10)), border_radius=3)
