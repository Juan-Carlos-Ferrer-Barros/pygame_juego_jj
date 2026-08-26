from .settings import SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_LERP

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, targets, world_w, world_h):
        if not targets:
            return
        cx = sum(t.rect.centerx for t in targets) / len(targets)
        cy = sum(t.rect.centery for t in targets) / len(targets)
        tx = cx - SCREEN_WIDTH / 2
        ty = cy - SCREEN_HEIGHT / 2
        tx = max(0, min(tx, max(0, world_w - SCREEN_WIDTH)))
        ty = max(0, min(ty, max(0, world_h - SCREEN_HEIGHT)))
        self.x += (tx - self.x) * CAMERA_LERP
        self.y += (ty - self.y) * CAMERA_LERP

    def apply_rect(self, rect):
        return rect.move(-int(self.x), -int(self.y))
