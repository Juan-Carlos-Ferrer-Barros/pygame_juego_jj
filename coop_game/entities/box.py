from __future__ import annotations
import pygame
from ..settings import GRAVITY, MAX_FALL_SPEED


class Box:
    GROUND_FRICTION = 0.78
    AIR_DRAG = 0.996
    STATIC_THRESH = 0.07
    MAX_VEL_X = 9.0
    RESTITUTION = 0.20
    WALL_BOUNCE = 0.18
    PUSH_IMPULSE = 3.8
    PUSH_HEAVY = 2.0
    MAX_ANGLE = 18.0
    OMEGA_DAMP = 0.80
    SETTLE_RATE = 0.86

    def __init__(self, rect, heavy, assets):
        self.rect = rect.copy()
        self.spawn = rect.copy()
        self.heavy = heavy
        self.image = assets.tiles['crate_heavy' if heavy else 'crate']
        self.pos = pygame.Vector2(float(rect.x), float(rect.y))
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.angle = 0.0
        self.omega = 0.0

    def reset(self):
        self.rect = self.spawn.copy()
        self.pos = pygame.Vector2(float(self.rect.x), float(self.rect.y))
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.angle = 0.0
        self.omega = 0.0

    def try_push(self, dx, solids, platforms, boxes):
        trial = self.rect.move(dx, 0)
        blockers = solids + [p.top_rect for p in platforms] + [b.rect for b in boxes if b is not self]
        if any(trial.colliderect(r) for r in blockers):
            return False
        self.rect = trial
        self.pos.x = float(self.rect.x)
        impulse = self.PUSH_HEAVY if self.heavy else self.PUSH_IMPULSE
        direction = 1 if dx > 0 else -1
        self.vel_x = max(-self.MAX_VEL_X, min(self.MAX_VEL_X, self.vel_x + impulse * direction))
        self.omega += direction * 4.5
        return True

    def update(self, solids, platforms):
        collidables = solids + [p.top_rect for p in platforms]
        self.vel_y = min(MAX_FALL_SPEED, self.vel_y + GRAVITY)

        self.pos.y += self.vel_y
        self.rect.y = int(self.pos.y)
        self.on_ground = False
        landing_speed = 0.0

        for r in collidables:
            if self.rect.colliderect(r):
                if self.vel_y > 0:
                    landing_speed = self.vel_y
                    bounce = -self.vel_y * self.RESTITUTION
                    self.rect.bottom = r.top
                    self.pos.y = float(self.rect.y)
                    self.vel_y = bounce if abs(bounce) > 0.6 else 0.0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = r.bottom
                    self.pos.y = float(self.rect.y)
                    self.vel_y = 0.0

        self.vel_x *= self.GROUND_FRICTION if self.on_ground else self.AIR_DRAG
        if abs(self.vel_x) < self.STATIC_THRESH:
            self.vel_x = 0.0

        if self.vel_x != 0.0:
            self.pos.x += self.vel_x
            self.rect.x = int(self.pos.x)
            for r in collidables:
                if self.rect.colliderect(r):
                    if self.vel_x > 0:
                        self.rect.right = r.left
                        self.vel_x = -self.vel_x * self.WALL_BOUNCE
                    elif self.vel_x < 0:
                        self.rect.left = r.right
                        self.vel_x = -self.vel_x * self.WALL_BOUNCE
                    self.pos.x = float(self.rect.x)

        # Tilt physics
        if self.on_ground:
            if abs(self.vel_x) > 0.3:
                target_omega = self.vel_x * 0.85
                self.omega += (target_omega - self.omega) * 0.18
            else:
                self.omega *= 0.55
                self.angle *= self.SETTLE_RATE
                if abs(self.angle) < 0.4:
                    self.angle = 0.0
            if landing_speed > 3.5:
                self.omega += self.vel_x * 0.35
                self.omega *= 0.45
        else:
            self.omega *= 0.98

        self.omega *= self.OMEGA_DAMP
        self.omega = max(-5.0, min(5.0, self.omega))
        self.angle += self.omega
        self.angle = max(-self.MAX_ANGLE, min(self.MAX_ANGLE, self.angle))

    def draw(self, screen, camera):
        img = self.image
        if abs(self.angle) > 0.4:
            img = pygame.transform.rotate(self.image, -self.angle)
        r = img.get_rect(midbottom=self.rect.move(-camera.x, -camera.y).midbottom)
        screen.blit(img, r)
