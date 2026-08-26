from __future__ import annotations
import math
import random as _random
import pygame
from dataclasses import dataclass
from .settings import (
    TILE_SIZE, GRAVITY, MOVE_SPEED, JUMP_SPEED, MAX_FALL_SPEED,
    SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, PANEL_COLOR, PANEL_BORDER,
    TEXT_COLOR, ACCENT, GREEN, RED,
)
from .camera import Camera
from .rope_system import *

# Entity / object / effect imports from subpackages
from .entities import Player, Box, ChickenVehicle
from .objects import (
    Button, Switch, Door, Goal, Hazard, Spring, Key,
    Decoration, MovingPlatform,
)
from .effects import TetrisBlock, TETRIS_SHAPES, TETRIS_COLORS, Meteorite, SmokeParticle, BirdDecor


def rect_from_grid(x, y, w=1, h=1):
    return pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, w * TILE_SIZE, h * TILE_SIZE)


BIOME_PREFIX = {
    'green': 'grass',
    'snow': 'snow',
    'stone': 'castle',
}
BIOME_FILL = {
    'green': 'grassCenter',
    'snow': 'snowCenter',
    'stone': 'castleCenter',
}


@dataclass
class Tile:
    rect: pygame.Rect
    kind: str


class LevelWorld:
    def __init__(self, level_data, player_count, assets, audio=None):
        self.data = level_data
        self.assets = assets
        self.audio = audio
        self.id = level_data['id']
        self.name = level_data['name']
        self.player_count = player_count
        self.camera = Camera()
        self.elapsed = 0
        self.complete = False
        self.failed = False
        self.grid = level_data['grid']
        self.h = len(self.grid)
        self.w = max(len(row) for row in self.grid)
        self.world_w = self.w * TILE_SIZE
        self.world_h = self.h * TILE_SIZE
        self.solids = []
        self.decor = []
        self.hazards = []
        self.buttons = []
        self.switches = []
        self.doors = []
        self.boxes = []
        self.springs = []
        self.keys = []
        self.platforms = []
        self.goal = None
        self.spawns = [(100, 100)] * 3
        self.triggers = {}
        self.biome = level_data.get('biome', 'green')
        self._build_world()
        # Add extra subsurface rows below the defined grid so the level doesn't look floating.
        # Use a small fixed margin (4 rows) so larger/smaller grids still look right.
        extra_depth = 4
        self.subsurface_cells = getattr(self, 'subsurface_cells', [])
        for x in range(self.w):
            for y in range(self.h, self.h + extra_depth):
                self.subsurface_cells.append((x, y))
        # World bounds = grid size + subsurface (NOT hardcoded to SCREEN_HEIGHT)
        self.world_w = self.w * TILE_SIZE
        self.world_h = (self.h + extra_depth) * TILE_SIZE
        self.players = self._make_players()
        rope_cfg = level_data.get('rope', {'enabled': False, 'max_dist': 160})
        self.rope = RopeSystem(rope_cfg.get('enabled', False), rope_cfg.get('max_dist', 200))

        # ── New features ────────────────────────────────────────────
        # Darkness mode
        darkness_cfg = level_data.get('darkness')
        self.darkness = bool(darkness_cfg)
        self.darkness_radius = darkness_cfg.get('radius', 120) if darkness_cfg else 120
        self._darkness_surface = None  # lazy-init in draw

        # Inverted controls
        self.inverted_controls = bool(level_data.get('inverted_controls', False))
        if self.inverted_controls:
            for p in self.players:
                orig = p.controls.copy()
                p.controls = {
                    'left': orig['right'],
                    'right': orig['left'],
                    'jump': orig['interact'],
                    'interact': orig['jump'],
                }

        # Chicken vehicle mode
        chicken_cfg = level_data.get('chicken')
        self.chicken = None
        if chicken_cfg:
            cx = chicken_cfg.get('x', 5)
            cy = chicken_cfg.get('y', 8)
            frame_h = getattr(self.assets, 'chicken_frame_size', (ChickenVehicle.WIDTH, ChickenVehicle.HEIGHT))[1]
            spawn_y = cy * TILE_SIZE - frame_h
            self.chicken = ChickenVehicle((cx * TILE_SIZE, spawn_y), self.assets)

        # Tetris mode
        tetris_cfg = level_data.get('tetris')
        self.tetris_mode = bool(tetris_cfg)
        self.tetris_blocks = []
        self.tetris_timer = 0.0
        self.tetris_interval = tetris_cfg.get('interval', 2.5) if tetris_cfg else 2.5
        self.tetris_speed = tetris_cfg.get('speed', 0.8) if tetris_cfg else 0.8
        self.tetris_cols = self.w  # spawn across the level width

        # Meteorite rain
        meteor_cfg = level_data.get('meteorites')
        self.meteor_mode = bool(meteor_cfg)
        self.meteorites = []
        self.meteor_timer = 0.0
        self.meteor_interval = meteor_cfg.get('interval', 2.0) if meteor_cfg else 2.0
        self.meteor_speed = meteor_cfg.get('speed', 2.0) if meteor_cfg else 2.0

        # Smoke puff effects
        self.smoke_particles = []

        # Decorative birds
        self.birds = []
        self.bird_timer = 0.0
        self.bird_interval = 12.0  # seconds between new bird spawns

        # Footstep sound timer
        self._footstep_timer = 0.0
        self._footstep_interval = 0.32  # seconds between footstep sounds

        # Door state tracking for open/close SFX
        self._prev_door_states: dict[str, bool] = {}

    def _make_players(self):
        controls_2 = [
            {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'interact': pygame.K_s},
            {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'interact': pygame.K_DOWN},
        ]
        controls_3 = [
            {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'interact': pygame.K_s},
            {'left': pygame.K_j, 'right': pygame.K_l, 'jump': pygame.K_i, 'interact': pygame.K_k},
            {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'interact': pygame.K_DOWN},
        ]
        controls = controls_2 if self.player_count == 2 else controls_3
        players = []
        for i in range(self.player_count):
            players.append(Player(i + 1, self.spawns[i], controls[i], self.assets))
        return players

    def _build_world(self):
        # Determine subsurface rows: for each column, find the topmost solid '#' or ramp row,
        # then fill everything below it (that is empty) with grassCenter subsurface decor.
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                rect = rect_from_grid(x, y)
                if ch in '#X':
                    self.solids.append(rect)
                elif ch in '/\\':
                    # Ramp cells: handled by slope physics, NOT added to solids
                    # (solids would cause horizontal blocking instead of smooth climbing)
                    self.ramps = getattr(self, 'ramps', [])
                    self.ramps.append({'x': x, 'y': y, 'dir': ch, 'rect': rect})
                elif ch == 'G':
                    self.goal = Goal(rect_from_grid(x, y - 1, 1, 2), self.assets)
                elif ch == '^':
                    self.hazards.append(Hazard(rect_from_grid(x, y, 1, 1), self.assets))
                elif ch == 'B':
                    self.boxes.append(Box(rect.inflate(-8, -8).move(4, 4), False, self.assets))
                elif ch == 'H':
                    self.boxes.append(Box(rect.inflate(-8, -8).move(4, 4), True, self.assets))
                elif ch in '123':
                    idx = int(ch) - 1
                    while len(self.spawns) <= idx:
                        self.spawns.append((0, 0))
                    self.spawns[idx] = (rect.x + 7, rect.y - 10)

        if not hasattr(self, 'ramps'):
            self.ramps = []

        # Auto-fill subsurface: for each column, below the topmost solid/ramp row fill with grassCenter decor
        for x in range(self.w):
            top_solid_y = None
            for y in range(self.h):
                row = self.grid[y]
                ch = row[x] if x < len(row) else '.'
                if ch in '#X/\\':
                    top_solid_y = y
                    break
            if top_solid_y is not None:
                top_row = self.grid[top_solid_y]
                top_ch = top_row[x] if x < len(top_row) else '.'
                # don't auto-fill under ramps or thin/half platforms/cliffs
                if top_ch in '/\\':
                    continue
                key = self._tile_key_for(x, top_solid_y)
                mid_key = self._bt('Mid')
                center_key = self._bt('Center')
                if key not in (mid_key, center_key):
                    continue
                for y in range(top_solid_y + 1, self.h):
                    row = self.grid[y]
                    ch = row[x] if x < len(row) else '.'
                    if ch == '.':
                        self.subsurface_cells = getattr(self, 'subsurface_cells', [])
                        self.subsurface_cells.append((x, y))

        if not hasattr(self, 'subsurface_cells'):
            self.subsurface_cells = []
        for button in self.data.get('buttons', []):
            rect = rect_from_grid(button['x'], button['y'], button.get('w', 1), 1)
            self.buttons.append(Button(rect, button['target'], button.get('kind', 'hold'), button.get('min_weight', 1), self.assets, red=button.get('red', False)))
        for switch in self.data.get('switches', []):
            rect = rect_from_grid(switch['x'], switch['y'], 1, 1)
            self.switches.append(Switch(rect, switch['target'], self.assets))
        for door in self.data.get('doors', []):
            rect = rect_from_grid(door['x'], door['y'], door.get('w', 1), door.get('h', 2))
            self.doors.append(Door(rect, door['id'], self.assets))
        for spring in self.data.get('springs', []):
            rect = rect_from_grid(spring['x'], spring['y'], 1, 1)
            self.springs.append(Spring(rect, spring.get('power', 14), self.assets))
        for key in self.data.get('keys', []):
            rect = rect_from_grid(key['x'], key['y'], 1, 1).inflate(-4, -14)
            self.keys.append(Key(rect, key['target'], self.assets))
        for platform in self.data.get('platforms', []):
            rect = rect_from_grid(platform['x'], platform['y'], platform['w'], platform.get('h', 1))
            self.platforms.append(MovingPlatform(rect, platform['id'], platform.get('axis', 'y'), platform.get('distance', 96), platform.get('speed', 1.5), platform.get('active', False), self.assets))
        # Level decorations
        self.decorations = []
        for dec in self.data.get('decorations', []):
            self.decorations.append(Decoration(dec['x'], dec['y'], dec['name'], self.assets))

    def reset(self):
        for p in self.players:
            p.reset()
        for b in self.boxes:
            b.reset()
        for k in self.keys:
            k.collected = False
        if self.chicken:
            self.chicken.reset()
        self.tetris_blocks = []
        self.tetris_timer = 0.0
        self.meteorites = []
        self.meteor_timer = 0.0
        self.smoke_particles = []
        self.elapsed = 0
        self.complete = False
        self.failed = False

    def get_active_solids(self):
        solids = list(self.solids)
        for d in self.doors:
            if not d.open:
                solids.append(d.rect)
        return solids

    def _apply_triggers(self):
        states = {}
        for d in self.doors:
            states[d.id] = False
        plat_state = {p.id: p.active for p in self.platforms}

        for b in self.buttons:
            if b.is_pressed:
                states[b.target] = True
                if b.target in plat_state:
                    plat_state[b.target] = True
        for s in self.switches:
            if s.on:
                states[s.target] = True
                if s.target in plat_state:
                    plat_state[s.target] = True
        for k in self.keys:
            if k.collected:
                states[k.target] = True
                if k.target in plat_state:
                    plat_state[k.target] = True

        for d in self.doors:
            was_open = self._prev_door_states.get(d.id, False)
            now_open = states.get(d.id, False)
            d.open = now_open
            if self.audio and was_open != now_open:
                if now_open:
                    self.audio.play_dooropen()
                else:
                    self.audio.play_doorclose()
            self._prev_door_states[d.id] = now_open
        for p in self.platforms:
            p.active = plat_state.get(p.id, p.active)

    def update(self, dt, keys):
        self.elapsed += dt

        # ── Chicken vehicle mode ────────────────────────────────
        if self.chicken:
            self.chicken.update_input(keys, self.players)
            solids = self.get_active_solids()
            self.chicken.physics(solids, self.platforms)
            self.chicken.snap_players(self.players)
            self.chicken.animate(dt)
            # Check hazards for the chicken
            if any(self.chicken.rect.colliderect(h.damage_rect) for h in self.hazards):
                self.failed = True
            if self.chicken.rect.top > self.world_h + 80:
                self.failed = True
            # Goal check: chicken touching goal counts for all players
            if self.goal and self.chicken.rect.colliderect(self.goal.rect):
                for p in self.players:
                    p.goal_reached = True
            else:
                for p in self.players:
                    p.goal_reached = False
            self.complete = all(p.goal_reached for p in self.players)
            self.camera.update([self.chicken], self.world_w, self.world_h)
            return

        # ── Normal mode ─────────────────────────────────────────
        for p in self.players:
            p.update_input(keys)

        # ── Box carrying logic ──────────────────────────────────
        carried_set = set()
        for p in self.players:
            if p.carrying_box:
                carried_set.add(id(p.carrying_box))
        free_boxes = [b for b in self.boxes if id(b) not in carried_set]

        for p in self.players:
            interact_edge = p.want_interact and not p._prev_interact
            p._prev_interact = p.want_interact
            if p.carrying_box:
                # Keep carried box above player's head
                p.carrying_box.rect.midbottom = (p.rect.centerx, p.rect.top - 2)
                p.carrying_box.pos.x = float(p.carrying_box.rect.x)
                p.carrying_box.pos.y = float(p.carrying_box.rect.y)
                p.carrying_box.vel_x = 0
                p.carrying_box.vel_y = 0
                if interact_edge:
                    box = p.carrying_box
                    p.carrying_box = None
                    p._carry_anim = 0.0
                    # Place box directly in front of the player on the ground
                    drop_x = p.rect.centerx + p.facing * (p.rect.width // 2 + box.rect.width // 2 + 2)
                    box.rect.midbottom = (drop_x, p.rect.bottom)
                    box.pos.x = float(box.rect.x)
                    box.pos.y = float(box.rect.y)
                    box.vel_x = p.facing * 2.0
                    box.vel_y = -1.0
                    if self.audio:
                        self.audio.play_box()
                    carried_set.discard(id(box))
                    free_boxes.append(box)
            else:
                if interact_edge and p.on_ground:
                    grab_rect = p.rect.inflate(20, 10)
                    for box in free_boxes:
                        if box.rect.colliderect(grab_rect):
                            p.carrying_box = box
                            p._carry_anim = 0.0
                            carried_set.add(id(box))
                            free_boxes.remove(box)
                            break

        for sw in self.switches:
            if sw.try_toggle(self.players):
                if self.audio:
                    self.audio.play_lever()
            sw.tick()

        for b in self.buttons:
            b.update(self.players, self.boxes)
        for k in self.keys:
            k.update(self.players)
        self._apply_triggers()

        solids = self.get_active_solids()
        # Include landed tetris blocks as solids
        tetris_solids = []
        for tb in self.tetris_blocks:
            if not tb.falling:
                tetris_solids.extend(tb.rects)
        all_solids = solids + tetris_solids

        for platform in self.platforms:
            platform.update()
        for box in free_boxes:
            box.update(all_solids, self.platforms)

        for p in self.players:
            platform_push = False
            for plat in self.platforms:
                foot = pygame.Rect(p.rect.x + 4, p.rect.bottom - 2, p.rect.w - 8, 6)
                if foot.colliderect(plat.top_rect):
                    p.rect.x += int(plat.delta.x)
                    p.rect.y += int(plat.delta.y)
                    if hasattr(p, 'pos'):
                        p.pos.x = p.rect.x
                        p.pos.y = p.rect.y
                    platform_push = True
            p.physics(all_solids, free_boxes, self.players, self.platforms, self.ramps)
            if platform_push:
                p.on_ground = True

        for spring in self.springs:
            if spring.update(self.players):
                if self.audio:
                    self.audio.play_trampoline()

        self.rope.apply(self.players, all_solids)

        for p in self.players:
            if hasattr(p, 'resolve_collisions'):
                p.resolve_collisions(all_solids, self.boxes, self.players, self.platforms, self.ramps)

        # ── Tetris mode update ──────────────────────────────────
        if self.tetris_mode:
            self.tetris_timer += dt
            if self.tetris_timer >= self.tetris_interval:
                self.tetris_timer = 0.0
                self._spawn_tetris_block()
            for tb in self.tetris_blocks:
                tb.update(dt, all_solids + tetris_solids)
            # Crush detection: only kill if a falling block lands on a player from above
            for tb in self.tetris_blocks:
                if tb.falling:
                    for r in tb.rects:
                        for p in self.players:
                            if p.rect.colliderect(r):
                                # Only crush if block is moving down onto the player's top half
                                if r.bottom > p.rect.top and r.top < p.rect.centery:
                                    self.failed = True

        for p in self.players:
            if p.rect.top > self.world_h + 80:
                self.failed = True
            if any(p.rect.colliderect(h.damage_rect) for h in self.hazards):
                self.failed = True
            if self.goal and p.rect.colliderect(self.goal.rect):
                p.goal_reached = True
            else:
                p.goal_reached = False
            # Spawn smoke puff when player lands on solid ground
            if getattr(p, '_just_landed', False) and self.assets.smoke_frames:
                self.smoke_particles.append(SmokeParticle(
                    p.rect.centerx, p.rect.bottom + 4, self.assets.smoke_frames))
                p._just_landed = False
            p.animate(dt)

        # ── Footstep sounds ─────────────────────────────────────
        if self.audio:
            self._footstep_timer -= dt
            if self._footstep_timer <= 0:
                # Check if any player is walking on ground
                walking = any(p.on_ground and abs(p.vel.x) > 0.5 for p in self.players)
                if walking:
                    self.audio.play_footstep(self.biome)
                    self._footstep_timer = self._footstep_interval
                else:
                    self._footstep_timer = 0.0

        # ── Meteorite rain ──────────────────────────────────────
        if self.meteor_mode:
            self.meteor_timer += dt
            if self.meteor_timer >= self.meteor_interval:
                self.meteor_timer = 0.0
                mx = _random.randint(0, self.world_w)
                my = -60.0
                # Find ground level at that x
                col = mx // TILE_SIZE
                ground_y = self.world_h
                for y_idx in range(self.h):
                    row = self.grid[y_idx] if y_idx < len(self.grid) else ''
                    ch = row[col] if col < len(row) else '.'
                    if ch in '#X':
                        ground_y = y_idx * TILE_SIZE
                        break
                self.meteorites.append(Meteorite(mx, my, self.assets.meteorite_frames, self.meteor_speed))
            for m in self.meteorites:
                # Find ground for this meteorite
                col = max(0, min(int(m.x) // TILE_SIZE, self.w - 1))
                ground_y = self.world_h
                for y_idx in range(self.h):
                    row = self.grid[y_idx] if y_idx < len(self.grid) else ''
                    ch = row[col] if col < len(row) else '.'
                    if ch in '#X':
                        ground_y = y_idx * TILE_SIZE
                        break
                m.update(dt, ground_y)
            self.meteorites = [m for m in self.meteorites if m.alive]

        # ── Smoke particles ─────────────────────────────────────
        for sp in self.smoke_particles:
            sp.update(dt)
        self.smoke_particles = [sp for sp in self.smoke_particles if sp.alive]

        # ── Decorative birds ────────────────────────────────────
        self.bird_timer += dt
        if self.bird_timer >= self.bird_interval and self.assets.bird_frames:
            self.bird_timer = 0.0
            self.birds.append(BirdDecor(self.assets.bird_frames, self.world_w, self.world_h))
        for bird in self.birds:
            bird.update(dt)
        self.birds = [b for b in self.birds if b.alive]

        self.complete = all(p.goal_reached for p in self.players)
        self.camera.update(self.players, self.world_w, self.world_h)

    def _spawn_tetris_block(self):
        """Spawn a random tetris piece at the top of the level."""
        shape = _random.choice(list(TETRIS_SHAPES.keys()))
        # Random x within level bounds (leave margin for piece width)
        max_x = max(1, self.w - 4)
        x = _random.randint(1, max_x)
        tb = TetrisBlock(shape, x, -2)
        tb.fall_speed = self.tetris_speed
        self.tetris_blocks.append(tb)

    def _cell_solid(self, x, y):
        if y < 0 or y >= self.h or x < 0:
            return False
        row = self.grid[y]
        if x >= len(row):
            return False
        return row[x] in '#X\\'

    def _bt(self, suffix):
        """Return biome-prefixed tile name, e.g. 'Mid' → 'snowMid' for snow biome."""
        prefix = BIOME_PREFIX.get(self.biome, 'grass')
        return f'{prefix}{suffix}'

    def _tile_sprite_for(self, x, y):
        """Determine the correct tile sprite for a solid cell, biome-aware."""
        left = self._cell_solid(x - 1, y)
        right = self._cell_solid(x + 1, y)
        up = self._cell_solid(x, y - 1)
        down = self._cell_solid(x, y + 1)

        if not up:
            if not down:
                if not left and not right:
                    return self.assets.get_tile(self._bt('HalfMid'))
                if not left:
                    return self.assets.get_tile(self._bt('HalfLeft'))
                if not right:
                    return self.assets.get_tile(self._bt('HalfRight'))
                if left and not right:
                    return self.assets.get_tile(self._bt('CliffRight'))
                if right and not left:
                    return self.assets.get_tile(self._bt('CliffLeft'))
                return self.assets.get_tile(self._bt('HalfMid'))
            else:
                return self.assets.get_tile(self._bt('Mid'))
        else:
            return self.assets.get_tile(self._bt('Center'))

    def _tile_key_for(self, x, y):
        """Like _tile_sprite_for but return the asset key string."""
        left = self._cell_solid(x - 1, y)
        right = self._cell_solid(x + 1, y)
        up = self._cell_solid(x, y - 1)
        down = self._cell_solid(x, y + 1)

        if not up:
            if not down:
                if not left and not right:
                    return self._bt('HalfMid')
                if not left:
                    return self._bt('HalfLeft')
                if not right:
                    return self._bt('HalfRight')
                if left and not right:
                    return self._bt('CliffRight')
                if right and not left:
                    return self._bt('CliffLeft')
                return self._bt('HalfMid')
            else:
                return self._bt('Mid')
        else:
            return self._bt('Center')

    def _ramp_sprite_for(self, x, y, direction):
        """Return the correct biome-aware hill sprite for a ramp cell."""
        if direction == '/':
            right = self._cell_solid(x + 1, y)
            if right:
                return self.assets.get_tile(self._bt('HillLeft2'))
            return self.assets.get_tile(self._bt('HillLeft'))
        else:
            left = self._cell_solid(x - 1, y)
            if left:
                return self.assets.get_tile(self._bt('HillRight2'))
            return self.assets.get_tile(self._bt('HillRight'))

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self._draw_background(screen)
        cam = self.camera

        # Draw auto-filled subsurface dirt first, behind everything (biome-aware)
        fill_tile = BIOME_FILL.get(self.biome, 'grassCenter')
        sub_img = self.assets.get_tile(fill_tile)
        for (sx, sy) in self.subsurface_cells:
            world_rect = rect_from_grid(sx, sy)
            rect = cam.apply_rect(world_rect)
            if rect.right < 0 or rect.left > SCREEN_WIDTH or rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                continue
            screen.blit(sub_img, rect)

        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                world_rect = rect_from_grid(x, y)
                rect = cam.apply_rect(world_rect)
                if rect.right < 0 or rect.left > SCREEN_WIDTH or rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                    continue
                if ch in '#X':
                    img = self._tile_sprite_for(x, y)
                    screen.blit(img, rect)
                elif ch in '/\\':
                    img = self._ramp_sprite_for(x, y, ch)
                    screen.blit(img, rect)
                elif ch == '-':
                    img = self.assets.get_tile('bridge', size=(TILE_SIZE, TILE_SIZE//2))
                    screen.blit(img, (rect.x, rect.y + TILE_SIZE//2))

        for plat in self.platforms:
            plat.draw(screen, cam)
        # Draw level decorations behind interactive objects
        for dec in self.decorations:
            dec.draw(screen, cam)
        for d in self.doors:
            d.draw(screen, cam)
        for h in self.hazards:
            h.draw(screen, cam)
        for b in self.buttons:
            b.draw(screen, cam)
        for s in self.switches:
            s.draw(screen, cam)
        for k in self.keys:
            k.draw(screen, cam)
        for sp in self.springs:
            sp.draw(screen, cam)
        if self.goal:
            self.goal.draw(screen, cam)
        for box in self.boxes:
            # Skip drawing carried boxes (Player.draw handles them)
            if any(p.carrying_box is box for p in self.players):
                continue
            box.draw(screen, cam)
        # Draw decorative birds behind players
        for bird in self.birds:
            bird.draw(screen, cam)
        self.rope.draw(screen, cam, self.players)
        # Draw chicken behind players if in chicken mode
        if self.chicken:
            self.chicken.draw(screen, cam)
            # Don't draw individual player sprites in chicken mode
        else:
            for p in self.players:
                p.draw(screen, cam)
        # Draw tetris blocks
        for tb in self.tetris_blocks:
            tb.draw(screen, cam)
        # Draw meteorites
        for m in self.meteorites:
            m.draw(screen, cam)
        # Draw smoke particles
        for sp in self.smoke_particles:
            sp.draw(screen, cam)
        # Darkness overlay
        if self.darkness:
            self._draw_darkness(screen)
        self._draw_hud(screen)

    def _draw_background(self, screen):
        cam = self.camera
        bg = self.assets.bg
        t = self.elapsed

        # --- Layer 1: far clouds (slow parallax, animated drift) ---
        cloud_keys = ['cloud1', 'cloud2', 'cloud3']
        cloud_positions = [
            (120, 60, 12), (450, 90, 8), (800, 50, 15), (1100, 100, 10), (1500, 70, 13),
            (300, 110, 7), (680, 40, 11), (1000, 85, 9), (1300, 55, 14),
            (200, 130, 6), (900, 30, 16), (1600, 80, 10),
        ]
        for i, (bx, by, speed) in enumerate(cloud_positions):
            key = cloud_keys[i % len(cloud_keys)]
            if key not in bg:
                continue
            img = bg[key]
            drift = t * speed * 0.5
            px = int((bx + drift - cam.x * 0.08) % (SCREEN_WIDTH + 400)) - 200
            py = int(by - cam.y * 0.04)
            screen.blit(img, (px, py))

        # --- Layer 2: far hills (medium parallax) ---
        hill_pairs = [
            ('hill_large', 0), ('hill_smallAlt', 350), ('hill_largeAlt', 750),
            ('hill_small', 1100), ('hill_large', 1500),
        ]
        for name, bx in hill_pairs:
            if name not in bg:
                continue
            img = bg[name]
            px = int(bx - cam.x * 0.2) % (SCREEN_WIDTH + 500) - 250
            py = SCREEN_HEIGHT - img.get_height() - 20 - int(cam.y * 0.15)
            screen.blit(img, (px, py))

        # --- Layer 3: near vegetation & details (faster parallax, biome-aware) ---
        if self.biome == 'snow':
            veg_items = [
                ('snowhill', 80), ('rock', 320), ('fence', 550), ('snowhill', 800),
                ('rock', 1050), ('fenceBroken', 1280), ('snowhill', 1550),
            ]
        elif self.biome == 'stone':
            veg_items = [
                ('torch', 80), ('rock', 320), ('sign', 550), ('tochLit', 800),
                ('rock', 1050), ('fence', 1280), ('torch', 1550),
            ]
        else:
            veg_items = [
                ('bush', 80), ('mushroomRed', 220), ('plant', 380), ('fence', 550),
                ('rock', 700), ('mushroomBrown', 850), ('plantPurple', 1050),
                ('bush', 1280), ('plant', 1450), ('mushroomRed', 1600),
            ]
        for name, bx in veg_items:
            if name not in bg:
                continue
            img = bg[name]
            px = int(bx - cam.x * 0.35) % (SCREEN_WIDTH + 400) - 200
            py = SCREEN_HEIGHT - img.get_height() - 5 - int(cam.y * 0.25)
            screen.blit(img, (px, py))

    def _draw_hud(self, screen):
        # ── GUI-styled HUD panel ──
        panel_w, panel_h = 400, 80
        panel_surf = self.assets.scale_panel(panel_w, panel_h)
        screen.blit(panel_surf, (12, 12))

        # Level number using HUD digit sprites
        hud = self.assets.hud
        level_str = str(self.id)
        dx = 24
        for ch in level_str:
            num_key = f'num_{ch}'
            if num_key in hud:
                digit = hud[num_key]
                dh = digit.get_height()
                screen.blit(digit, (dx, 16 + (panel_h - dh) // 2 - 4))
                dx += digit.get_width() + 2
        dx += 8

        # Level name
        name_s = self.assets.font_small.render(self.name, True, (80, 55, 30))
        screen.blit(name_s, (dx, 28))

        # Timer
        time_s = self.assets.font_small.render(f'{self.elapsed:05.1f}s', True, (80, 55, 30))
        screen.blit(time_s, (dx, 52))

        # Player status icons
        ix = panel_w - 20
        for i in range(len(self.players) - 1, -1, -1):
            p = self.players[i]
            icon_key = f'p{i + 1}' if not p.goal_reached else f'p{i + 1}_alt'
            if icon_key not in hud:
                icon_key = f'p{i + 1}'
            if icon_key in hud:
                icon = hud[icon_key]
                iw, ih = icon.get_size()
                scaled_icon = pygame.transform.smoothscale(icon, (int(iw * 0.7), int(ih * 0.7)))
                sw, sh = scaled_icon.get_size()
                screen.blit(scaled_icon, (ix - sw, 16 + (panel_h - sh) // 2 - 4))
                if p.goal_reached:
                    pygame.draw.circle(screen, GREEN, (ix - sw // 2, 16 + panel_h // 2 + sh // 2 - 2), 5)
                ix -= sw + 6

        # Bottom hints
        hints = self.assets.font_small.render('ESC pausa  ·  R reinicia', True, (140, 120, 90))
        screen.blit(hints, (16, panel_h + 18))

        # Chicken mode HUD hint
        if self.chicken:
            n = len(self.players)
            if n == 2:
                hint = 'P1: ←→ mueve  |  P2: ↑ salta'
            else:
                hint = 'P1: ← izquierda  |  P2: → derecha  |  P3: ↑ salta'
            hint_s = self.assets.font_small.render(hint, True, ACCENT)
            screen.blit(hint_s, (SCREEN_WIDTH // 2 - hint_s.get_width() // 2, SCREEN_HEIGHT - 36))
        # Inverted controls HUD hint
        if self.inverted_controls:
            warn = self.assets.font_small.render('¡CONTROLES INVERTIDOS!', True, RED)
            screen.blit(warn, (SCREEN_WIDTH // 2 - warn.get_width() // 2, SCREEN_HEIGHT - 36))

    def _draw_darkness(self, screen):
        """Draw total darkness with smooth radial light around each player.
        Uses a light map so overlapping player lights merge naturally."""
        cam = self.camera
        radius = self.darkness_radius

        # Build a radial gradient light brush (cached)
        if self._darkness_surface is None or self._darkness_surface.get_width() != radius * 2:
            size = radius * 2
            light_brush = pygame.Surface((size, size), pygame.SRCALPHA)
            for r in range(radius, 0, -1):
                t = r / radius
                alpha = int(255 * (1.0 - t * t))
                pygame.draw.circle(light_brush, (255, 255, 255, alpha), (radius, radius), r)
            self._darkness_surface = light_brush

        # Create a light map (black = dark, white = lit)
        light_map = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        light_map.fill((0, 0, 0))
        brush = self._darkness_surface
        for p in self.players:
            cx = int(p.rect.centerx - cam.x - radius)
            cy = int(p.rect.centery - cam.y - radius)
            light_map.blit(brush, (cx, cy), special_flags=pygame.BLEND_ADD)

        # Create fully opaque dark surface and subtract light from it
        dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 255))
        # Use surfarray to subtract light_map brightness from dark alpha
        try:
            import numpy as np
            d_alpha = pygame.surfarray.pixels_alpha(dark)
            l_arr = pygame.surfarray.pixels3d(light_map)
            brightness = l_arr[:, :, 0]  # R channel (all channels same in grayscale)
            result = np.clip(d_alpha.astype(np.int16) - brightness.astype(np.int16), 0, 255).astype(np.uint8)
            d_alpha[:] = result
            del d_alpha, l_arr
        except Exception:
            # Fallback: simple circle punch-through
            for p in self.players:
                cx = int(p.rect.centerx - cam.x)
                cy = int(p.rect.centery - cam.y)
                pygame.draw.circle(dark, (0, 0, 0, 0), (cx, cy), radius // 2)
        screen.blit(dark, (0, 0))

    def draw_overlay(self, screen, title, subtitle_lines):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        screen.blit(overlay, (0, 0))
        pw = 560
        base_ph = 280
        # Compute panel height based on number of subtitle lines so pause/complete
        # menus can grow downward to fit options. Anchor top so it expands down.
        per_line_h = 48
        panel_h = max(base_ph, 140 + len(subtitle_lines) * per_line_h)
        panel_surf = self.assets.scale_panel(pw, panel_h)
        px = (SCREEN_WIDTH - pw) // 2
        # Anchor to original top position so extra space grows downward
        py = (SCREEN_HEIGHT - base_ph) // 2
        # Shadow
        shadow = pygame.Surface((pw + 6, panel_h + 6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 40))
        screen.blit(shadow, (px - 3, py + 2))
        screen.blit(panel_surf, (px, py))
        t = self.assets.font_big.render(title, True, (80, 55, 30))
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, py + 54)))
        y = py + 110
        for line, color in subtitle_lines:
            surf = self.assets.font.render(line, True, color)
            screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))
            y += 38
