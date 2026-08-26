import pygame


class Switch:
    def __init__(self, rect, target, assets):
        self.rect = rect
        self.target = target
        self.on = False
        self.assets = assets
        self.cooldown = 0

    def try_toggle(self, players):
        if self.cooldown > 0:
            return False
        for p in players:
            if p.want_interact and p.rect.colliderect(self.rect.inflate(18, 8)):
                self.on = not self.on
                self.cooldown = 20
                return True
        return False

    def tick(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, screen, camera):
        img = self.assets.tiles['switch_right' if self.on else 'switch_left']
        r = img.get_rect(midbottom=self.rect.move(-camera.x, -camera.y).midbottom)
        screen.blit(img, r)
