import math
import pygame


class Goal:
    def __init__(self, rect, assets):
        self.rect = rect
        self.assets = assets
        self.t = 0.0

    def draw(self, screen, camera):
        self.t += 0.016
        r = self.rect.move(-camera.x, -camera.y)
        pole_x = r.centerx
        pygame.draw.line(screen, (90, 65, 40), (pole_x, r.top + 4), (pole_x, r.bottom), 4)
        pygame.draw.line(screen, (130, 100, 60), (pole_x + 1, r.top + 4), (pole_x + 1, r.bottom), 2)
        pygame.draw.circle(screen, (255, 215, 0), (pole_x, r.top + 4), 5)
        pygame.draw.circle(screen, (255, 240, 100), (pole_x - 1, r.top + 3), 2)
        wave = int(math.sin(self.t * 4) * 3)
        flag_points = [
            (pole_x + 2, r.top + 10),
            (pole_x + 28 + wave, r.top + 18 + wave // 2),
            (pole_x + 26 + wave, r.top + 30 - wave // 2),
            (pole_x + 2, r.top + 34),
        ]
        pygame.draw.polygon(screen, (50, 180, 80), flag_points)
        pygame.draw.polygon(screen, (30, 140, 60), flag_points, 2)
        star_x = pole_x + 14 + wave // 2
        star_y = r.top + 22
        pygame.draw.circle(screen, (255, 255, 200), (star_x, star_y), 4)
        pygame.draw.circle(screen, (255, 240, 100), (star_x, star_y), 2)
        base_rect = pygame.Rect(r.centerx - 16, r.bottom - 8, 32, 8)
        glow_alpha = int(140 + 60 * math.sin(self.t * 3))
        glow = pygame.Surface((32, 8), pygame.SRCALPHA)
        glow.fill((100, 255, 120, min(255, glow_alpha)))
        screen.blit(glow, base_rect)
