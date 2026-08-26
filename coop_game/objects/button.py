import pygame


class Button:
    def __init__(self, rect, target, kind, min_weight, assets, red=False):
        self.rect = rect
        self.target = target
        self.kind = kind
        self.min_weight = min_weight
        self.is_pressed = False
        self.assets = assets
        self.red = red
        self._was_pressed = False

    def update(self, players, boxes):
        weight = 0
        for p in players:
            foot = pygame.Rect(p.rect.x + 4, p.rect.bottom - 6, p.rect.w - 8, 10)
            if foot.colliderect(self.rect):
                weight += 1
        for b in boxes:
            if b.rect.colliderect(self.rect):
                weight += 1 if not b.heavy else 2
        pressed_now = weight >= self.min_weight

        if self.kind == 'hold':
            self.is_pressed = pressed_now
        elif self.kind in ('latch', 'press_once'):
            if pressed_now:
                self.is_pressed = True
        elif self.kind == 'toggle':
            if pressed_now and not self._was_pressed:
                self.is_pressed = not self.is_pressed
        else:
            self.is_pressed = pressed_now
        self._was_pressed = pressed_now

    def draw(self, screen, camera):
        key = 'button_red_down' if self.red and self.is_pressed else 'button_red_up' if self.red else 'button_down' if self.is_pressed else 'button_up'
        img = self.assets.tiles[key]
        r = img.get_rect(midbottom=self.rect.move(-camera.x, -camera.y).midbottom)
        screen.blit(img, r)
