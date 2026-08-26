import pygame


class Door:
    def __init__(self, rect, door_id, assets):
        self.rect = rect
        self.id = door_id
        self.open = False
        self.assets = assets

    def draw(self, screen, camera):
        img = self.assets.tiles['door_closed']
        r = img.get_rect(midbottom=self.rect.move(-camera.x, -camera.y).midbottom)
        if self.open:
            ghost = img.copy()
            ghost.set_alpha(70)
            screen.blit(ghost, r)
        else:
            screen.blit(img, r)
