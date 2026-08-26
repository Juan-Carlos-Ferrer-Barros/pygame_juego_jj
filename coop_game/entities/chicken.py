from __future__ import annotations
import pygame
from ..settings import MOVE_SPEED, JUMP_SPEED, MAX_FALL_SPEED, GRAVITY


class ChickenVehicle:
    WIDTH, HEIGHT = 104, 120

    def __init__(self, pos, assets):
        frame_w, frame_h = getattr(assets, 'chicken_frame_size', (self.WIDTH, self.HEIGHT))
        self.WIDTH = frame_w
        self.HEIGHT = frame_h
        self.rect = pygame.Rect(pos[0], pos[1], self.WIDTH - 50, self.HEIGHT)
        self.pos = pygame.Vector2(self.rect.topleft)
        self.spawn = (pos[0], pos[1])
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.facing = 1
        self.anim_t = 0.0
        self.anim_frame = 0
        self.sprites = assets.chicken
        self.image = self.sprites.get('idle', [None])[0] or pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)

    def reset(self):
        self.rect.topleft = self.spawn
        self.pos = pygame.Vector2(self.rect.topleft)
        self.vel.xy = (0, 0)
        self.on_ground = False
        self.anim_t = 0.0

    def update_input(self, keys, players):
        move = 0
        jump = False
        n = len(players)
        if n == 2:
            c0 = players[0].controls
            if keys[c0['left']]:
                move -= 1
            if keys[c0['right']]:
                move += 1
            c1 = players[1].controls
            if keys[c1['jump']]:
                jump = True
        elif n >= 3:
            c0 = players[0].controls
            if keys[c0['left']]:
                move -= 1
            c1 = players[1].controls
            if keys[c1['right']]:
                move += 1
            c2 = players[2].controls
            if keys[c2['jump']]:
                jump = True
        self.vel.x = move * MOVE_SPEED
        if move != 0:
            self.facing = 1 if move > 0 else -1
        if jump and self.on_ground:
            self.vel.y = -JUMP_SPEED
            self.on_ground = False

    def physics(self, solids, platforms):
        prev_rect = self.rect.copy()
        self.vel.y = min(MAX_FALL_SPEED, self.vel.y + GRAVITY)
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        collidables = solids + [p.top_rect for p in platforms]
        for r in collidables:
            if self.rect.colliderect(r):
                if self.vel.x > 0:
                    self.rect.right = r.left
                elif self.vel.x < 0:
                    self.rect.left = r.right
                self.pos.x = self.rect.x
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False
        for r in collidables:
            if self.rect.colliderect(r):
                if self.vel.y > 0 and prev_rect.bottom <= r.top + 6:
                    self.rect.bottom = r.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0 and prev_rect.top >= r.bottom - 6:
                    self.rect.top = r.bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0
        if not self.on_ground and self.vel.y >= 0:
            for r in collidables:
                dy = r.top - self.rect.bottom
                if 0 <= dy <= 3 and self.rect.right > r.left and self.rect.left < r.right:
                    self.rect.bottom = r.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True
                    break

    def snap_players(self, players):
        n = len(players)
        spacing = max(20, self.WIDTH // (n + 1))
        for i, p in enumerate(players):
            px = self.rect.x + spacing * (i + 1) - p.rect.width // 2
            py = self.rect.top - p.rect.height + 4
            p.rect.topleft = (px, py)
            p.pos.x = p.rect.x
            p.pos.y = p.rect.y
            p.on_ground = True
            p.vel.xy = (0, 0)

    def animate(self, dt):
        if not self.on_ground:
            frames = self.sprites['jump_up'] if self.vel.y < 0 else self.sprites['jump_fall']
        elif abs(self.vel.x) > 0.1:
            frames = self.sprites['walk']
        else:
            frames = self.sprites['idle']
        if not hasattr(self, '_current_frames') or self._current_frames is not frames:
            self._current_frames = frames
            self.anim_t = 0.0
        self.anim_t += dt
        frame = int(self.anim_t / 0.1) % max(1, len(frames))
        img = frames[frame]
        self.image = pygame.transform.flip(img, self.facing > 0, False)

    def draw(self, screen, camera):
        r = self.rect.move(-camera.x, -camera.y)
        img_rect = self.image.get_rect(midbottom=r.midbottom)
        screen.blit(self.image, img_rect)
