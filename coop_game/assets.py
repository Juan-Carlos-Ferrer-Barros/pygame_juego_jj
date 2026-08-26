from __future__ import annotations
import pygame
from pathlib import Path
from .settings import PLAYER_DIR, TILE_DIR, ITEM_DIR, HUD_DIR, GUI_DIR, METEORITE_DIR, SMOKE_DIR, BIRD_DIR, TILE_SIZE, PLAYER_SCALE, SCREEN_WIDTH, SCREEN_HEIGHT


def load_image(path: Path):
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 180))
        pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 2)
        return surf


def load_sheet_map(path: Path):
    mapping = {}
    if not path.exists():
        return mapping
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' not in line:
                continue
            name, vals = [p.strip() for p in line.split('=', 1)]
            mapping[name] = tuple(int(v) for v in vals.split())
    return mapping


def extract(sheet, rect):
    x, y, w, h = rect
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.blit(sheet, (0, 0), pygame.Rect(x, y, w, h))
    return surf


CHICKEN_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'Chicken'


class Assets:
    def __init__(self):
        self.tile_cache = {}
        self.item_cache = {}
        self.players = {}
        self.chicken = {}
        self.font_big = pygame.font.SysFont('arial', 48, bold=True)
        self.font = pygame.font.SysFont('arial', 28)
        self.font_small = pygame.font.SysFont('arial', 20)
        self._load_players()
        self._load_common()
        self._load_background()
        self._load_chicken()
        self._load_gui()
        self._load_hud_sprites()
        self._load_meteorite()
        self._load_smoke()
        self._load_bird()

    def _scale(self, surf, factor=None, size=None):
        if size is not None:
            return pygame.transform.smoothscale(surf, size)
        w, h = surf.get_size()
        return pygame.transform.smoothscale(surf, (int(w * factor), int(h * factor)))

    def _load_players(self):
        for idx in (1, 2, 3):
            prefix = f'p{idx}'
            sheet = load_image(PLAYER_DIR / f'{prefix}_spritesheet.png')
            mapping = load_sheet_map(PLAYER_DIR / f'{prefix}_spritesheet.txt')
            walk_frames = []
            for i in range(1, 12):
                key = f'{prefix}_walk{i:02d}'
                if key in mapping:
                    walk_frames.append(self._scale(extract(sheet, mapping[key]), PLAYER_SCALE))
            stand = self._scale(load_image(PLAYER_DIR / f'{prefix}_stand.png'), PLAYER_SCALE)
            jump = self._scale(load_image(PLAYER_DIR / f'{prefix}_jump.png'), PLAYER_SCALE)
            duck = self._scale(load_image(PLAYER_DIR / f'{prefix}_duck.png'), PLAYER_SCALE)
            front = self._scale(load_image(PLAYER_DIR / f'{prefix}_front.png'), PLAYER_SCALE)
            self.players[idx] = {
                'walk': walk_frames or [stand],
                'idle': stand,
                'jump': jump,
                'duck': duck,
                'front': front,
            }

    def _load_common(self):
        self.tiles = {
            'ground': self.get_tile('grassMid' if (TILE_DIR / 'grassMid.png').exists() else 'grassHalfMid'),
            'platform': self.get_tile('grassHalfMid'),
            'wall': self.get_tile('stoneMid'),
            'crate': self.get_tile('boxItem'),
            'crate_heavy': self.get_tile('boxWarning'),
            'door_closed': self.get_tile('lock_blue'),
            'door_open': self.get_item('switchMid', size=(32, 32)),
            'goal': self.get_item('flagGreen2', size=(42, 70)),
            'button_up': self.get_item('buttonBlue', size=(46, 18)),
            'button_down': self.get_item('buttonBlue_pressed', size=(46, 14)),
            'button_red_up': self.get_item('buttonRed', size=(46, 18)),
            'button_red_down': self.get_item('buttonRed_pressed', size=(46, 14)),
            'switch_left': self.get_item('switchLeft', size=(40, 46)),
            'switch_right': self.get_item('switchRight', size=(40, 46)),
            'spring_up': self.get_item('springboardUp', size=(42, 28)),
            'spring_down': self.get_item('springboardDown', size=(42, 18)),
            'spikes': self.get_item('spikes', size=(48, 24)),
            'key': self.get_item('keyBlue', size=(44, 26)),
            'chain': self.get_item('chain', size=(18, 18)),
        }

    def get_tile(self, name, size=(TILE_SIZE, TILE_SIZE)):
        key = (name, size)
        if key in self.tile_cache:
            return self.tile_cache[key]
        path = TILE_DIR / f'{name}.png'
        surf = load_image(path)
        if size is not None:
            surf = self._scale(surf, size=size)
        self.tile_cache[key] = surf
        return surf

    def get_item(self, name, size=None):
        key = (name, size)
        if key in self.item_cache:
            return self.item_cache[key]
        path = ITEM_DIR / f'{name}.png'
        surf = load_image(path)
        if size:
            surf = self._scale(surf, size=size)
        self.item_cache[key] = surf
        return surf

    def _load_background(self):
        """Load cloud, hill, bush and plant sprites for parallax backgrounds."""
        self.bg = {}
        # Clouds
        for i in (1, 2, 3):
            self.bg[f'cloud{i}'] = self.get_item(f'cloud{i}')
        # Hills (from Tiles)
        for name in ('hill_large', 'hill_largeAlt', 'hill_small', 'hill_smallAlt'):
            self.bg[name] = self.get_tile(name, size=None)
        # Vegetation
        for name in ('bush', 'plant', 'plantPurple', 'rock', 'fence'):
            path = ITEM_DIR / f'{name}.png' if name != 'fence' else TILE_DIR / f'{name}.png'
            try:
                self.bg[name] = load_image(path)
            except Exception:
                pass
        # Extra decorations: mushrooms, cactus, snowhill, signs, torches
        for name in ('mushroomRed', 'mushroomBrown', 'cactus', 'snowhill', 'star'):
            path = ITEM_DIR / f'{name}.png'
            if path.exists():
                try:
                    self.bg[name] = load_image(path)
                except Exception:
                    pass
        for name in ('sign', 'signExit', 'signLeft', 'signRight', 'fence', 'fenceBroken',
                     'tochLit', 'tochLit2', 'torch'):
            path = TILE_DIR / f'{name}.png'
            if path.exists():
                try:
                    self.bg[name] = load_image(path)
                except Exception:
                    pass

    def _load_chicken(self):
        """Load chicken sprites for the cooperative chicken vehicle."""
        SCALE = 0.22  # 473x545 originals → ~104x120
        def _load_seq(folder, prefix, count):
            frames = []
            for i in range(count):
                path = CHICKEN_DIR / folder / f'{prefix}_{i:03d}.png'
                if path.exists():
                    img = load_image(path)
                    w, h = img.get_size()
                    img = pygame.transform.smoothscale(img, (int(w * SCALE), int(h * SCALE)))
                    frames.append(img)
            return frames

        self.chicken = {
            'idle': _load_seq('01-Idle/01-Idle', 'FA_CHICKEN_Idle', 12),
            'walk': _load_seq('03-Walk', 'FA_CHICKEN_Walk', 12),
            'run': _load_seq('04-Run', 'FA_CHICKEN_Run', 10),
            'jump_up': _load_seq('06-Jump/01-Jump_Up', 'FA_CHICKEN_Jump_UP', 5),
            'jump_fall': _load_seq('06-Jump/02-Jump_Fall', 'FA_CHICKEN_Jump_Fall', 5),
            'hurt': _load_seq('07-Hurt', 'FA_CHICKEN_Hurt', 5) if (CHICKEN_DIR / '07-Hurt').exists() else [],
        }
        # Fallback: if any list is empty, use a placeholder
        for k in list(self.chicken.keys()):
            if not self.chicken[k]:
                placeholder = pygame.Surface((104, 120), pygame.SRCALPHA)
                pygame.draw.ellipse(placeholder, (255, 220, 50), placeholder.get_rect())
                pygame.draw.circle(placeholder, (30, 30, 30), (48, 20), 5)
                self.chicken[k] = [placeholder]

        # Normalize all chicken frames to a uniform canvas so flipping/animation
        # doesn't cause visual teleportation due to uneven frame sizes or padding.
        all_frames = []
        for frames in self.chicken.values():
            all_frames.extend(frames)

        if all_frames:
            max_w = max(img.get_width() for img in all_frames)
            max_h = max(img.get_height() for img in all_frames)
            # Ensure minimum reasonable size
            max_w = max(max_w, 64)
            max_h = max(max_h, 64)

            processed = {}
            for k, frames in self.chicken.items():
                out_frames = []
                for img in frames:
                    # Crop to visible content to avoid carrying extra transparent margins
                    try:
                        bbox = img.get_bounding_rect()
                    except Exception:
                        bbox = img.get_rect()
                    if bbox.width == 0 or bbox.height == 0:
                        content = img.copy()
                    else:
                        content = img.subsurface(bbox).copy()
                    # Create uniform canvas and blit content centered horizontally,
                    # bottom-aligned so the feet line up across frames.
                    canvas = pygame.Surface((max_w, max_h), pygame.SRCALPHA)
                    x = (max_w - content.get_width()) // 2
                    y = max_h - content.get_height()
                    canvas.blit(content, (x, y))
                    out_frames.append(canvas)
                processed[k] = out_frames
            self.chicken = processed
            # Store frame size for consumers (e.g., ChickenVehicle)
            self.chicken_frame_size = (max_w, max_h)
        else:
            self.chicken_frame_size = (104, 120)

    def _load_gui(self):
        """Load GUI panel sprites for menus and HUD."""
        self.gui = {}
        # Panel background from Setting menu (right panel = empty)
        try:
            setting_img = load_image(GUI_DIR / 'Setting menu.png')
            w, h = setting_img.get_size()
            panel_w = w // 2
            self.gui['panel_raw'] = setting_img.subsurface(pygame.Rect(panel_w + 4, 2, panel_w - 6, h - 4)).copy()
        except Exception:
            self.gui['panel_raw'] = None
        # Dialog boxes
        for size_name, fname in [('dialog_big', 'Premade dialog box  big.png'),
                                   ('dialog_medium', 'Premade dialog box medium.png'),
                                   ('dialog_small', 'Premade dialog box small.png')]:
            path = GUI_DIR / 'Dialouge UI' / fname
            if path.exists():
                try:
                    self.gui[size_name] = load_image(path)
                except Exception:
                    pass
        # Play buttons
        try:
            play_img = load_image(GUI_DIR / 'UI Big Play Button.png')
            pw, ph = play_img.get_size()
            btn_w, btn_h = pw // 2, ph // 2
            self.gui['btn_normal'] = play_img.subsurface(pygame.Rect(0, btn_h, btn_w, btn_h)).copy()
            self.gui['btn_hover'] = play_img.subsurface(pygame.Rect(btn_w, btn_h, btn_w, btn_h)).copy()
        except Exception:
            pass

    def _load_hud_sprites(self):
        """Load HUD number sprites and player/status icons."""
        self.hud = {}
        for i in range(10):
            path = HUD_DIR / f'hud_{i}.png'
            if path.exists():
                self.hud[f'num_{i}'] = load_image(path)
        for i in (1, 2, 3):
            for suffix in ('', 'Alt'):
                path = HUD_DIR / f'hud_p{i}{suffix}.png'
                key = f'p{i}' if not suffix else f'p{i}_alt'
                if path.exists():
                    self.hud[key] = load_image(path)
        for name in ('heartFull', 'heartEmpty', 'heartHalf', 'coins', 'x',
                     'gem_blue', 'gem_green', 'gem_red', 'gem_yellow',
                     'keyBlue', 'keyBlue_disabled', 'keyGreen',
                     'keyRed', 'keyRed_disabled', 'keyYellow', 'keyYellow_disabled'):
            path = HUD_DIR / f'hud_{name}.png'
            if path.exists():
                self.hud[name] = load_image(path)

        # Prefer explicit icon files if present: use extracted icons or a provided lock.png
        try:
            icons_dir = GUI_DIR / 'Icons'
            extracted_dir = icons_dir / 'extracted'

            def _recolor_icon(surf, brown=(160, 135, 100), white_thresh=230):
                out = surf.copy()
                w, h = out.get_size()
                for yy in range(h):
                    for xx in range(w):
                        r, g, b, a = out.get_at((xx, yy))
                        if a == 0:
                            continue
                        if r >= white_thresh and g >= white_thresh and b >= white_thresh:
                            out.set_at((xx, yy), (255, 255, 255, a))
                        else:
                            out.set_at((xx, yy), (brown[0], brown[1], brown[2], a))
                return out

            # User-specified preferred icons
            check_file = extracted_dir / 'icon_2_9.png'
            unlocked_file = extracted_dir / 'icon_2_7.png'
            lock_file = icons_dir / 'lock.png'

            if check_file.exists() and unlocked_file.exists():
                try:
                    c_check = load_image(check_file)
                    c_x = load_image(unlocked_file)
                    # recolor check/unlocked to match HUD tint
                    self.hud['status_check'] = _recolor_icon(c_check)
                    self.hud['status_x'] = _recolor_icon(c_x)
                    # use provided lock.png if present, but resize/center it to
                    # match the check icon size so labels don't shift.
                    if lock_file.exists():
                        try:
                            lock_img = load_image(lock_file)
                            base = self.hud.get('status_check')
                            if base:
                                bw, bh = base.get_size()
                            else:
                                bw, bh = (16, 16)
                            lw, lh = lock_img.get_size()
                            if lw == 0 or lh == 0:
                                canvas = pygame.Surface((bw, bh), pygame.SRCALPHA)
                            else:
                                scale = min(bw / lw, bh / lh)
                                new_w = max(1, int(lw * scale))
                                new_h = max(1, int(lh * scale))
                                scaled_lock = pygame.transform.smoothscale(lock_img, (new_w, new_h))
                                canvas = pygame.Surface((bw, bh), pygame.SRCALPHA)
                                canvas.blit(scaled_lock, ((bw - new_w) // 2, (bh - new_h) // 2))
                            self.hud['status_locked'] = canvas
                        except Exception:
                            # fallback: load raw
                            self.hud['status_locked'] = load_image(lock_file)
                except Exception:
                    pass
            else:
                # Fallback: try the All Icons sheet and previous heuristics
                icons_path = icons_dir / 'All Icons.png'
                if icons_path.exists():
                    sheet = load_image(icons_path)

                    def _get_icon(r, c):
                        return extract(sheet, (c * 16, r * 16, 16, 16))

                    # Heuristically find a circled icon that contains a diagonal from TL->BR
                    best_locked = None
                    best_score = 0
                    cell_w = cell_h = 16
                    sw, sh = sheet.get_size()
                    cols = sw // cell_w
                    rows = sh // cell_h
                    for ry in range(rows):
                        for cx in range(cols):
                            icon = _get_icon(ry, cx)
                            center_x = cell_w // 2
                            center_y = cell_h // 2
                            ring_count = 0
                            diag_count = 0
                            for y in range(cell_h):
                                for x in range(cell_w):
                                    a = icon.get_at((x, y))[3]
                                    if a > 16:
                                        dx = x - center_x
                                        dy = y - center_y
                                        dist2 = dx * dx + dy * dy
                                        if 10 <= dist2 <= 100:
                                            ring_count += 1
                                        if x == y:
                                            diag_count += 1
                            score = ring_count * 3 + diag_count * 4
                            if score > best_score:
                                best_score = score
                                best_locked = (ry, cx)

                    # Fallback positions if heuristics fail
                    check_pos = (2, 3)
                    x_pos = (2, 4)
                    locked_pos = best_locked or (0, 12)

                    try:
                        c_check = _get_icon(*check_pos)
                        c_x = _get_icon(*x_pos)
                        c_locked = _get_icon(*locked_pos)
                        # recolor non-white pixels to light brown
                        self.hud['status_check'] = _recolor_icon(c_check)
                        self.hud['status_x'] = _recolor_icon(c_x)
                        self.hud['status_locked'] = _recolor_icon(c_locked)
                    except Exception:
                        pass
        except Exception:
            pass

    def _load_meteorite(self):
        """Load meteorite animation frames."""
        self.meteorite_frames = []
        for i in range(1, 9):
            path = METEORITE_DIR / f'Group 4 - 2_{i}.png'
            if path.exists():
                self.meteorite_frames.append(load_image(path))

    def _load_smoke(self):
        """Load smoke effect frames from the spritesheet (row 2 = effect #2)."""
        self.smoke_frames = []
        path = SMOKE_DIR / 'smoke_fx.png'
        if not path.exists():
            return
        sheet = load_image(path)
        cell_w, cell_h = 64, 64
        sw, sh = sheet.get_size()
        cols = sw // cell_w
        row = 1  # effect #2 (0-indexed row 1)
        for c in range(cols):
            frame = extract(sheet, (c * cell_w, row * cell_h, cell_w, cell_h))
            # Skip fully transparent frames
            if frame.get_bounding_rect().width > 0:
                self.smoke_frames.append(frame)

    def _load_bird(self):
        """Load bird flying sprite frames from Walk.png spritesheet."""
        self.bird_frames = []
        path = BIRD_DIR / 'Walk.png'
        if not path.exists():
            return
        sheet = load_image(path)
        sw, sh = sheet.get_size()
        frame_w = sh  # square frames (32x32)
        n = sw // frame_w
        for i in range(n):
            frame = extract(sheet, (i * frame_w, 0, frame_w, sh))
            if frame.get_bounding_rect().width > 0:
                self.bird_frames.append(frame)

    def scale_panel(self, w, h, corner=14):
        """Create a GUI-styled panel at the given size using 9-slice scaling."""
        src = self.gui.get('panel_raw')
        if src is None:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (222, 198, 166), surf.get_rect(), border_radius=16)
            pygame.draw.rect(surf, (148, 108, 68), surf.get_rect(), 3, border_radius=16)
            return surf
        sw, sh = src.get_size()
        c = min(corner, sw // 3, sh // 3)
        result = pygame.Surface((w, h), pygame.SRCALPHA)
        # Corners
        result.blit(src.subsurface(pygame.Rect(0, 0, c, c)), (0, 0))
        result.blit(src.subsurface(pygame.Rect(sw - c, 0, c, c)), (w - c, 0))
        result.blit(src.subsurface(pygame.Rect(0, sh - c, c, c)), (0, h - c))
        result.blit(src.subsurface(pygame.Rect(sw - c, sh - c, c, c)), (w - c, h - c))
        # Edges
        top = src.subsurface(pygame.Rect(c, 0, sw - 2 * c, c))
        result.blit(pygame.transform.smoothscale(top, (w - 2 * c, c)), (c, 0))
        bot = src.subsurface(pygame.Rect(c, sh - c, sw - 2 * c, c))
        result.blit(pygame.transform.smoothscale(bot, (w - 2 * c, c)), (c, h - c))
        left = src.subsurface(pygame.Rect(0, c, c, sh - 2 * c))
        result.blit(pygame.transform.smoothscale(left, (c, h - 2 * c)), (0, c))
        right = src.subsurface(pygame.Rect(sw - c, c, c, sh - 2 * c))
        result.blit(pygame.transform.smoothscale(right, (c, h - 2 * c)), (w - c, c))
        # Center fill
        center = src.subsurface(pygame.Rect(c, c, sw - 2 * c, sh - 2 * c))
        result.blit(pygame.transform.smoothscale(center, (w - 2 * c, h - 2 * c)), (c, c))
        return result
