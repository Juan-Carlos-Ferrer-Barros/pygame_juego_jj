import pygame
from ..settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT


class Decoration:
    """Static decorative sprite placed from level JSON."""
    def __init__(self, x, y, name, assets):
        self.name = name
        try:
            self.image = assets.get_item(name)
        except Exception:
            try:
                self.image = assets.get_tile(name, size=None)
            except Exception:
                self.image = None
        self.world_x = x * TILE_SIZE
        self.world_y = y * TILE_SIZE
        if self.image:
            self.rect = self.image.get_rect(midbottom=(self.world_x + TILE_SIZE // 2, y * TILE_SIZE))
        else:
            self.rect = pygame.Rect(self.world_x, self.world_y, TILE_SIZE, TILE_SIZE)

    def draw(self, screen, camera):
        if self.image is None:
            return
        r = self.rect.move(-camera.x, -camera.y)
        if r.right < 0 or r.left > SCREEN_WIDTH or r.bottom < 0 or r.top > SCREEN_HEIGHT:
            return
        screen.blit(self.image, r)
