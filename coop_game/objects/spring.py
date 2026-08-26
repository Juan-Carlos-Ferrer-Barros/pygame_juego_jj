import pygame
from ..settings import TILE_SIZE


class Spring:
    def __init__(self, rect, power, assets):
        self.rect = rect
        self.power = power
        self.assets = assets
        self.cooldown = 0
        self.trigger_h = max(6, TILE_SIZE // 6)
        self.trigger_rect = pygame.Rect(self.rect.x, self.rect.bottom - self.trigger_h,
                                        self.rect.w, self.trigger_h)

    def update(self, players):
        triggered = False
        for p in players:
            foot = pygame.Rect(p.rect.x + 5, p.rect.bottom - 4, p.rect.w - 10, 8)
            if foot.colliderect(self.trigger_rect) and p.vel.y >= 0:
                p.rect.bottom = max(p.rect.bottom, self.rect.top + self.trigger_h // 2)
                if hasattr(p, 'pos'):
                    p.pos.y = p.rect.y
                p.vel.y = -self.power
                triggered = True
        self.cooldown = 5 if triggered else max(0, self.cooldown - 1)
        return triggered

    def draw(self, screen, camera):
        img = self.assets.tiles['spring_down' if self.cooldown else 'spring_up']
        r = img.get_rect(midbottom=self.rect.move(-camera.x, -camera.y).midbottom)
        screen.blit(img, r)
