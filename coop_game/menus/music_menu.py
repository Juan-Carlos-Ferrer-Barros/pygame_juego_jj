import pygame
from ..settings import SCREEN_WIDTH, SCREEN_HEIGHT, GUI_DIR
from .main_menu import GUI_BORDER, GUI_DARK, GUI_TEXT_LIGHT

# ── Icon loading ────────────────────────────────────────────────
_icons_loaded = False
_icon_next = _icon_prev = _icon_vol = _icon_mute = None
_ICON_SIZE = 36


def _ensure_icons():
    global _icons_loaded, _icon_next, _icon_prev, _icon_vol, _icon_mute
    if _icons_loaded:
        return
    _icons_loaded = True
    more = GUI_DIR / 'Icons' / 'more'
    try:
        # Next icon (has a specific name)
        raw = None
        for candidate in ('Next - Speed Up 256 px.png', 'Next 256 px.png', 'Next.png'):
            p = more / candidate
            if p.exists():
                raw = pygame.image.load(str(p)).convert_alpha()
                break
        if raw:
            _icon_next = pygame.transform.smoothscale(raw, (_ICON_SIZE, _ICON_SIZE))
            _icon_prev = pygame.transform.flip(_icon_next, True, False)

        # Volume icon
        raw_v = None
        for candidate in ('Volume 256 px.png', 'Volume.png'):
            p = more / candidate
            if p.exists():
                raw_v = pygame.image.load(str(p)).convert_alpha()
                break
        if raw_v:
            _icon_vol = pygame.transform.smoothscale(raw_v, (_ICON_SIZE, _ICON_SIZE))

        # Mute icon: prefer 'Mute 2 256 px.png' (user provided), fallback to
        # older names if not present.
        raw_m = None
        for candidate in ('Mute 2 256 px.png', 'Mute 256 px.png', 'Mute.png'):
            p = more / candidate
            if p.exists():
                raw_m = pygame.image.load(str(p)).convert_alpha()
                break
        if raw_m:
            _icon_mute = pygame.transform.smoothscale(raw_m, (_ICON_SIZE, _ICON_SIZE))
    except Exception:
        pass


def _tint_icon(icon, color):
    """Return a copy of *icon* tinted to *color* (preserving alpha)."""
    if icon is None:
        return None
    # Create a solid color surface and multiply the icon into it using
    # BLEND_RGBA_MULT. This avoids using pygame.surfarray / NumPy.
    ic = icon.copy().convert_alpha()
    w, h = ic.get_size()
    color_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    color_surf.fill(color + (255,))
    # Multiply icon alpha into color: first preserve icon's alpha by
    # multiplying the color by the icon, then restore alpha channel.
    try:
        # BLEND_RGBA_MULT will multiply RGB and alpha channels.
        color_surf.blit(ic, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return color_surf
    except Exception:
        # Fallback: tint by drawing icon then a semi-transparent color overlay
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        out.blit(ic, (0, 0))
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill(color + (120,))
        out.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return out


# ── Update / Draw ───────────────────────────────────────────────

def update_music_menu(game, events):
    """Handle input for the music menu.
    menu_index: 0=prev track, 1=mute, 2=next track, 3=volver"""
    opts = 4
    audio = game.audio
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                game.menu_index = (game.menu_index + 1) % opts
                audio.play_menu_sfx()
            elif event.key in (pygame.K_UP, pygame.K_w):
                game.menu_index = (game.menu_index - 1) % opts
                audio.play_menu_sfx()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if game.menu_index == 0:
                    audio.prev_track()
                elif game.menu_index == 1:
                    audio.toggle_mute()
                elif game.menu_index == 2:
                    audio.next_track()
                elif game.menu_index == 3:
                    _back(game)
                audio.play_menu_sfx()
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                _back(game)
            # Volume with +/- keys
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                audio.set_volume(min(1.0, audio.volume + 0.05))
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                audio.set_volume(max(0.0, audio.volume - 0.05))


def _back(game):
    """Return to the previous state."""
    prev = getattr(game, '_music_menu_from', 'main_menu')
    game.state = prev
    if prev == 'paused':
        game.pause_index = getattr(game, '_music_pause_idx', 3)
    else:
        game.menu_index = 0


def draw_music_menu(game):
    _ensure_icons()

    # Background: if coming from pause, show the game behind an overlay
    from_pause = getattr(game, '_music_menu_from', 'main_menu') == 'paused'
    if from_pause and game.world:
        game.world.draw(game.game_surface)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        game.game_surface.blit(overlay, (0, 0))
    else:
        from .menu_bg import draw_menu_bg
        draw_menu_bg(game)

    s = game.game_surface
    audio = game.audio
    pw, ph = 540, 360
    panel_surf = game.assets.scale_panel(pw, ph)
    px = (SCREEN_WIDTH - pw) // 2
    py = (SCREEN_HEIGHT - ph) // 2 + 10

    shadow = pygame.Surface((pw + 8, ph + 8), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 40))
    s.blit(shadow, (px - 4, py + 2))
    s.blit(panel_surf, (px, py))

    # Title
    title_s = game.assets.font_big.render('Música', True, GUI_DARK)
    s.blit(title_s, title_s.get_rect(center=(SCREEN_WIDTH // 2, py + 44)))

    line_y = py + 72
    pygame.draw.line(s, GUI_BORDER, (px + 40, line_y), (px + pw - 40, line_y), 2)

    # Now-playing track name
    track_name = audio.current_track_name()
    now_s = game.assets.font_small.render(f'Reproduciendo: {track_name}', True, GUI_DARK)
    s.blit(now_s, now_s.get_rect(center=(SCREEN_WIDTH // 2, py + 94)))

    # ── Volume bar ──────────────────────────────────────────────
    vol_pct = int(audio.volume * 100)
    muted_tag = '  [MUTE]' if audio.muted else ''
    vol_txt = f'Volumen: {vol_pct}%{muted_tag}'
    vol_s = game.assets.font_small.render(vol_txt, True, GUI_DARK)
    s.blit(vol_s, vol_s.get_rect(center=(SCREEN_WIDTH // 2, py + 118)))

    bar_w, bar_h = 300, 12
    bar_x = (SCREEN_WIDTH - bar_w) // 2
    bar_y = py + 134
    pygame.draw.rect(s, (200, 180, 150), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    fill_w = int(bar_w * audio.volume)
    if fill_w > 0:
        color = (180, 160, 130) if audio.muted else (120, 200, 120)
        pygame.draw.rect(s, color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
    pygame.draw.rect(s, GUI_BORDER, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)

    # ── Icon buttons row: [Prev] [Mute/Vol] [Next] ─────────────
    icon_y = py + 170
    gap = 72
    cx = SCREEN_WIDTH // 2
    positions = [cx - gap, cx, cx + gap]  # prev=0, mute=1, next=2
    icons = [_icon_prev, _icon_mute if audio.muted else _icon_vol, _icon_next]

    for i, (ix, icon) in enumerate(zip(positions, icons)):
        is_sel = (game.menu_index == i)
        # Selection highlight circle
        if is_sel:
            pygame.draw.circle(s, (255, 220, 160, 160), (ix, icon_y + _ICON_SIZE // 2), _ICON_SIZE // 2 + 10)
            pygame.draw.circle(s, GUI_BORDER, (ix, icon_y + _ICON_SIZE // 2), _ICON_SIZE // 2 + 10, 2)
        if icon:
            tint_color = GUI_DARK if is_sel else GUI_TEXT_LIGHT
            tinted = _tint_icon(icon, tint_color)
            r = tinted.get_rect(center=(ix, icon_y + _ICON_SIZE // 2))
            s.blit(tinted, r)

    # Labels under icons
    labels = ['Anterior', 'Silenciar' if not audio.muted else 'Activar', 'Siguiente']
    for i, (ix, lbl) in enumerate(zip(positions, labels)):
        is_sel = (game.menu_index == i)
        color = GUI_DARK if is_sel else GUI_TEXT_LIGHT
        lbl_s = game.assets.font_small.render(lbl, True, color)
        s.blit(lbl_s, lbl_s.get_rect(center=(ix, icon_y + _ICON_SIZE + 16)))

    # ── Volver button ───────────────────────────────────────────
    volver_y = icon_y + _ICON_SIZE + 52
    is_sel = (game.menu_index == 3)
    color = GUI_DARK if is_sel else GUI_TEXT_LIGHT
    if is_sel:
        bw = 200
        bar_sel = pygame.Rect(0, 0, bw, 34)
        bar_sel.center = (SCREEN_WIDTH // 2, volver_y)
        highlight = pygame.Surface((bar_sel.w, bar_sel.h), pygame.SRCALPHA)
        highlight.fill((255, 220, 160, 60))
        pygame.draw.rect(highlight, GUI_BORDER, highlight.get_rect(), 2, border_radius=10)
        s.blit(highlight, bar_sel.topleft)
    volver_s = game.assets.font.render('Volver', True, color)
    s.blit(volver_s, volver_s.get_rect(center=(SCREEN_WIDTH // 2, volver_y)))

    # ── Hint bar ────────────────────────────────────────────────
    hint = game.assets.font_small.render(
        '+/- volumen  ·  Enter selecciona  ·  ESC vuelve', True, GUI_TEXT_LIGHT)
    s.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, py + ph - 20)))
