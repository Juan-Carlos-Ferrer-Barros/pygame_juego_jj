import pygame
from ..settings import SCREEN_WIDTH, SCREEN_HEIGHT, LOCKED, GREEN
from .main_menu import GUI_BORDER, GUI_DARK, GUI_TEXT_LIGHT


def draw_level_select(game):
    from .menu_bg import draw_menu_bg
    draw_menu_bg(game)
    s = game.game_surface
    total = len(game.loader.levels)
    row_h = 42
    visible_rows = 8
    panel_h = 160 + visible_rows * row_h + 30
    panel_w = 880
    panel_surf = game.assets.scale_panel(panel_w, panel_h)
    px = (SCREEN_WIDTH - panel_w) // 2
    py = (SCREEN_HEIGHT - panel_h) // 2 + 20

    shadow = pygame.Surface((panel_w + 8, panel_h + 8), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 40))
    s.blit(shadow, (px - 4, py + 2))
    s.blit(panel_surf, (px, py))

    title = game.assets.font_big.render('Seleccionar nivel', True, GUI_DARK)
    s.blit(title, title.get_rect(center=(px + panel_w // 2, py + 54)))
    pygame.draw.line(s, GUI_BORDER, (px + 40, py + 85), (px + panel_w - 40, py + 85), 2)

    scroll_offset = max(0, min(game.menu_index - visible_rows // 2, total - visible_rows))
    scroll_offset = max(0, scroll_offset)

    list_top = py + 110
    clip_rect = pygame.Rect(px, list_top - 8, panel_w, visible_rows * row_h + 8)
    old_clip = s.get_clip()
    s.set_clip(clip_rect)

    y = list_top
    hud = game.assets.hud
    for draw_i in range(scroll_offset, min(scroll_offset + visible_rows, total)):
        level = game.loader.levels[draw_i]
        lid = level['id']
        unlocked = game.save.is_unlocked(lid)
        completed = game.save.is_completed(lid)
        is_sel = (draw_i == game.menu_index)
        color = GUI_DARK if is_sel else GUI_TEXT_LIGHT
        if not unlocked:
            color = LOCKED

        if is_sel and unlocked:
            bar = pygame.Rect(px + 30, y - 4, panel_w - 60, 38)
            bar_surf = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
            bar_surf.fill((255, 220, 160, 50))
            pygame.draw.rect(bar_surf, GUI_BORDER, bar_surf.get_rect(), 2, border_radius=8)
            s.blit(bar_surf, bar.topleft)
            arrow = game.assets.font.render('»', True, GUI_DARK)
            s.blit(arrow, (px + 34, y - 2))

        # Level number digits
        level_str = str(lid)
        digit_surfs = []
        for ch in level_str:
            num_key = f'num_{ch}'
            if num_key in hud:
                digit = hud[num_key]
                dh = digit.get_height()
                dw = digit.get_width()
                scaled = pygame.transform.smoothscale(digit, (int(dw * 0.5), int(dh * 0.5)))
                digit_surfs.append(scaled)

        base_x = px + 56
        cur_x = base_x + 30
        for ds in reversed(digit_surfs):
            wds = ds.get_width()
            s.blit(ds, (cur_x, y + 6))
            cur_x -= (wds + 1)

        req = level.get('required_players')
        suffix = f'   [{req}P]' if req else ''

        icon = None
        if completed:
            icon = hud.get('status_check')
        elif unlocked:
            icon = hud.get('status_x')
        else:
            icon = hud.get('status_locked')

        label = f'{level["name"]}{suffix}'
        surf = game.assets.font.render(label, True, color)

        if icon is not None:
            iw, ih = icon.get_size()
            target_h = min(28, ih)
            if ih != target_h:
                icon_surf = pygame.transform.smoothscale(icon, (int(iw * (target_h / ih)), int(target_h)))
            else:
                icon_surf = icon
            icon_x = px + 120
            icon_y = y + (row_h - icon_surf.get_height()) // 2 - 2
            s.blit(icon_surf, (icon_x, icon_y))
            s.blit(surf, (icon_x + icon_surf.get_width() + 8, y))
        else:
            status = '✓' if completed else ('○' if unlocked else '🔒')
            label2 = f'{status}  {label}'
            surf2 = game.assets.font.render(label2, True, color)
            s.blit(surf2, (px + 80, y))

        if completed:
            best = game.save.data.get('best_times', {}).get(str(lid))
            if best:
                time_s = game.assets.font_small.render(f'{best:.1f}s', True, GREEN)
                s.blit(time_s, (px + panel_w - 120, y + 6))
        y += row_h

    s.set_clip(old_clip)

    if scroll_offset > 0:
        arrow_up = game.assets.font_small.render('▲ más niveles', True, GUI_TEXT_LIGHT)
        s.blit(arrow_up, arrow_up.get_rect(center=(px + panel_w // 2, list_top - 8)))
    if scroll_offset + visible_rows < total:
        arrow_dn = game.assets.font_small.render('▼ más niveles', True, GUI_TEXT_LIGHT)
        s.blit(arrow_dn, arrow_dn.get_rect(center=(px + panel_w // 2, list_top + visible_rows * row_h + 6)))

    hint = game.assets.font_small.render('Enter selecciona  ·  ESC vuelve', True, GUI_TEXT_LIGHT)
    s.blit(hint, hint.get_rect(center=(px + panel_w // 2, py + panel_h - 25)))
