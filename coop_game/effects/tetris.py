import pygame
from ..settings import TILE_SIZE

TETRIS_SHAPES = {
    'I': [(0, 0), (1, 0), (2, 0), (3, 0)],
    'O': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'T': [(0, 0), (1, 0), (2, 0), (1, 1)],
    'L': [(0, 0), (0, 1), (0, 2), (1, 2)],
    'J': [(1, 0), (1, 1), (1, 2), (0, 2)],
    'S': [(1, 0), (2, 0), (0, 1), (1, 1)],
    'Z': [(0, 0), (1, 0), (1, 1), (2, 1)],
}

TETRIS_COLORS = {
    'I': (0, 220, 220),
    'O': (220, 220, 0),
    'T': (160, 0, 220),
    'L': (220, 140, 0),
    'J': (0, 0, 220),
    'S': (0, 220, 0),
    'Z': (220, 0, 0),
}


class TetrisBlock:
    """A falling tetris piece that becomes solid when it lands."""
    CELL = TILE_SIZE

    def __init__(self, shape_name, x, y):
        self.shape_name = shape_name
        self.cells = [(cx + x, cy + y) for cx, cy in TETRIS_SHAPES[shape_name]]
        self.color = TETRIS_COLORS[shape_name]
        self.dark_color = tuple(max(0, c - 50) for c in self.color)
        self.falling = True
        self.fall_timer = 0.0
        self.fall_speed = 0.8
        self.rects = self._make_rects()

    def _make_rects(self):
        return [pygame.Rect(cx * self.CELL, cy * self.CELL, self.CELL, self.CELL)
                for cx, cy in self.cells]

    def update(self, dt, solids):
        if not self.falling:
            return
        self.fall_timer += dt
        if self.fall_timer >= self.fall_speed:
            self.fall_timer = 0.0
            new_cells = [(cx, cy + 1) for cx, cy in self.cells]
            new_rects = [pygame.Rect(cx * self.CELL, cy * self.CELL, self.CELL, self.CELL)
                         for cx, cy in new_cells]
            blocked = False
            for nr in new_rects:
                for s in solids:
                    if nr.colliderect(s):
                        blocked = True
                        break
                if blocked:
                    break
            if blocked:
                self.falling = False
            else:
                self.cells = new_cells
                self.rects = new_rects

    def draw(self, screen, camera):
        for r in self.rects:
            sr = r.move(-camera.x, -camera.y)
            pygame.draw.rect(screen, self.color, sr, border_radius=4)
            pygame.draw.rect(screen, self.dark_color, sr, 2, border_radius=4)
            highlight = pygame.Rect(sr.x + 4, sr.y + 4, sr.w // 3, sr.h // 3)
            h_surf = pygame.Surface((highlight.w, highlight.h), pygame.SRCALPHA)
            h_surf.fill((255, 255, 255, 60))
            screen.blit(h_surf, highlight)
