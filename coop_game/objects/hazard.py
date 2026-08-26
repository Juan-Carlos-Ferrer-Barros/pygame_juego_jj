import pygame
from ..settings import TILE_SIZE


class Hazard:
    def __init__(self, rect, assets):
        self.rect = rect
        self.image = assets.tiles['spikes']
        dmg_h = max(8, TILE_SIZE // 4)
        self.damage_rect = pygame.Rect(self.rect.x, self.rect.bottom - dmg_h, self.rect.w, dmg_h)

    def draw(self, screen, camera):
        for x in range(self.rect.left, self.rect.right, 48):
            r = self.image.get_rect(midbottom=(x + 24 - camera.x, self.rect.bottom - camera.y))
            screen.blit(self.image, r)
