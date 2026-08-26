from __future__ import annotations
import pygame
from ..settings import MOVE_SPEED, JUMP_SPEED, MAX_FALL_SPEED, GRAVITY, TILE_SIZE, GREEN


class Player:
    def __init__(self, idx, pos, controls, assets):
        self.idx = idx
        self.assets = assets.players[idx]
        self.rect = pygame.Rect(pos[0], pos[1], 34, 56)
        self.pos = pygame.Vector2(self.rect.topleft)
        self.spawn = self.rect.topleft
        self.controls = controls
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.want_interact = False
        self.goal_reached = False
        self.facing = 1
        self.anim_t = 0.0
        self.image = self.assets['idle']
        self.carrying_box = None
        self._prev_interact = False
        self._just_landed = False
        self._was_on_ground = False
        self._landed_on_solid = False
        self._carry_anim = 0.0

    def reset(self):
        self.rect.topleft = self.spawn
        self.pos = pygame.Vector2(self.rect.topleft)
        self.vel.xy = (0, 0)
        self.on_ground = False
        self.goal_reached = False
        self.anim_t = 0.0
        self.carrying_box = None
        self._prev_interact = False
        self._just_landed = False
        self._was_on_ground = False
        self._landed_on_solid = False
        self._carry_anim = 0.0

    def update_input(self, keys):
        move = 0
        if keys[self.controls['left']]:
            move -= 1
        if keys[self.controls['right']]:
            move += 1
        self.vel.x = move * MOVE_SPEED
        if move != 0:
            self.facing = 1 if move > 0 else -1
        if keys[self.controls['jump']] and self.on_ground:
            jump_power = JUMP_SPEED * 0.85 if self.carrying_box else JUMP_SPEED
            self.vel.y = -jump_power
            self.on_ground = False
        self.want_interact = keys[self.controls['interact']]

    def physics(self, solids, boxes, others, platforms, ramps=None):
        ramps = ramps or []
        prev_rect = self.rect.copy()
        was_on_ground_before = self.on_ground
        self.vel.y = min(MAX_FALL_SPEED, self.vel.y + GRAVITY)

        # Horizontal
        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        dx = self.rect.x - prev_rect.x

        for box in boxes:
            if self.rect.colliderect(box.rect):
                helpers = sum(1 for o in others if o is not self and o.rect.colliderect(box.rect.inflate(18, 6)))
                needed = 2 if box.heavy else 1
                can_push = box.try_push(dx, solids, platforms, boxes) if dx != 0 and (1 + helpers) >= needed else False
                if not can_push:
                    if dx > 0:
                        self.rect.right = box.rect.left
                    elif dx < 0:
                        self.rect.left = box.rect.right
                    self.pos.x = self.rect.x

        for ramp in ramps:
            r = ramp['rect']
            if self.rect.colliderect(r):
                direction = ramp['dir']
                if direction == '/':
                    progress = (self.rect.right - r.left) / TILE_SIZE
                else:
                    progress = (r.right - self.rect.left) / TILE_SIZE
                progress = max(0.0, min(1.0, progress))
                target_bottom = r.bottom - int(progress * TILE_SIZE)
                if self.rect.bottom > target_bottom:
                    self.rect.bottom = target_bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True

        for o in others:
            if o is self:
                continue
            if self.rect.colliderect(o.rect):
                if self.vel.x > 0:
                    self.rect.right = o.rect.left
                elif self.vel.x < 0:
                    self.rect.left = o.rect.right
                self.pos.x = self.rect.x

        collidables = solids + [p.top_rect for p in platforms] + [b.rect for b in boxes]
        for r in collidables:
            if self.rect.colliderect(r):
                is_ramp = any(ramp['rect'] == r for ramp in ramps)
                if is_ramp:
                    continue
                if self.vel.x > 0:
                    self.rect.right = r.left
                elif self.vel.x < 0:
                    self.rect.left = r.right
                self.pos.x = self.rect.x

        # Vertical
        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False
        self._landed_on_solid = False
        collidables = solids + [b.rect for b in boxes] + [p.top_rect for p in platforms]
        for r in collidables:
            if self.rect.colliderect(r):
                is_ramp = any(ramp['rect'] == r for ramp in ramps)
                if is_ramp:
                    continue
                if self.vel.y > 0 and prev_rect.bottom <= r.top + 6:
                    self.rect.bottom = r.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True
                    self._landed_on_solid = True
                elif self.vel.y < 0 and prev_rect.top >= r.bottom - 6:
                    self.rect.top = r.bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0

        for o in others:
            if o is self:
                continue
            if self.rect.colliderect(o.rect):
                if self.vel.y >= 0 and prev_rect.bottom <= o.rect.top + 6:
                    self.rect.bottom = o.rect.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True
                    # landing on player, NOT solid
                elif self.vel.y < 0 and prev_rect.top >= o.rect.bottom - 6:
                    self.rect.top = o.rect.bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0

        if not self.on_ground and self.vel.y >= 0:
            for r in collidables:
                is_ramp = any(rr['rect'] == r for rr in ramps)
                if is_ramp:
                    continue
                dy = r.top - self.rect.bottom
                if 0 <= dy <= 3 and self.rect.right > r.left and self.rect.left < r.right:
                    self.rect.bottom = r.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.on_ground = True
                    self._landed_on_solid = True
                    break

        # Detect landing event (was airborne, now on solid ground)
        self._just_landed = (not was_on_ground_before and self.on_ground and self._landed_on_solid)

    def resolve_collisions(self, solids, boxes, others, platforms, ramps=None):
        ramps = ramps or []
        collidables = list(solids) + [p.top_rect for p in platforms] + [b.rect for b in boxes]
        for o in others:
            if o is not self:
                collidables.append(o.rect)

        changed = True
        iterations = 0
        while changed and iterations < 6:
            changed = False
            iterations += 1
            for r in collidables:
                if self.rect.colliderect(r):
                    if any(rr['rect'] == r for rr in ramps):
                        continue
                    ox = min(self.rect.right, r.right) - max(self.rect.left, r.left)
                    oy = min(self.rect.bottom, r.bottom) - max(self.rect.top, r.top)
                    if ox <= 0 or oy <= 0:
                        continue
                    if ox < oy:
                        if self.rect.centerx < r.centerx:
                            self.rect.right = r.left
                        else:
                            self.rect.left = r.right
                        self.pos.x = self.rect.x
                        changed = True
                    else:
                        if self.rect.centery < r.centery:
                            self.rect.bottom = r.top
                            self.pos.y = self.rect.y
                            self.vel.y = 0
                            self.on_ground = True
                        else:
                            self.rect.top = r.bottom
                            self.pos.y = self.rect.y
                            self.vel.y = 0
                        changed = True

    def animate(self, dt):
        if not self.on_ground:
            img = self.assets['jump']
        elif abs(self.vel.x) > 0.1:
            walk = self.assets['walk']
            speed_factor = max(0.5, abs(self.vel.x) / MOVE_SPEED)
            cycle_speed = 6.0
            self.anim_t = (self.anim_t + dt * cycle_speed * speed_factor) % 1.0
            frame = int(self.anim_t * len(walk)) % len(walk)
            img = walk[frame]
        else:
            self.anim_t = 0.0
            img = self.assets['idle']
        self.image = pygame.transform.flip(img, self.facing < 0, False)

    def draw(self, screen, camera):
        img_rect = self.image.get_rect(midbottom=self.rect.move(-camera.x, -camera.y).midbottom)
        screen.blit(self.image, img_rect)
        if self.carrying_box:
            self._carry_anim = min(1.0, self._carry_anim + 0.12)
            box_img = self.carrying_box.image
            target = box_img.get_rect(midbottom=(img_rect.centerx, img_rect.top + 4))
            src_x = self.carrying_box.rect.centerx - camera.x - box_img.get_width() // 2
            src_y = self.carrying_box.rect.centery - camera.y - box_img.get_height() // 2
            t = self._carry_anim
            bx = int(src_x + (target.x - src_x) * t)
            by = int(src_y + (target.y - src_y) * t)
            screen.blit(box_img, (bx, by))
        if self.goal_reached:
            pygame.draw.circle(screen, GREEN, (img_rect.centerx, img_rect.top - 12), 8)
