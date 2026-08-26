import pygame


class Key:
    def __init__(self, rect, target, assets):
        self.rect = rect
        self.target = target
        self.collected = False
        self.image = assets.tiles['key']

    def update(self, players):
        if self.collected:
            return False
        for p in players:
            if p.rect.colliderect(self.rect):
                self.collected = True
                return True
        return False

    def draw(self, screen, camera):
        if self.collected:
            return
        r = self.image.get_rect(center=self.rect.move(-camera.x, -camera.y).center)
        screen.blit(self.image, r)
