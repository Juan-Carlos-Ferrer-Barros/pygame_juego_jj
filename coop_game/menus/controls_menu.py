import pygame
from ..settings import SCREEN_WIDTH, SCREEN_HEIGHT
from .main_menu import GUI_BORDER, GUI_DARK, GUI_TEXT_LIGHT


def update_controls(game, events):
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                game.controls_mode = 2
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                game.controls_mode = 3
            elif event.key == pygame.K_2:
                game.controls_mode = 2
            elif event.key == pygame.K_3:
                game.controls_mode = 3
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                game.state = game._controls_from
                if game._controls_from == 'paused':
                    game.pause_index = 2
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                game.state = game._controls_from
                if game._controls_from == 'paused':
                    game.pause_index = 2
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            pw, ph = 800, 500
            px = (SCREEN_WIDTH - pw) // 2
            py = (SCREEN_HEIGHT - ph) // 2
            btn_w, btn_h, gap = 150, 32, 12
            bx = px + (pw - (btn_w * 2 + gap)) // 2
            by = py + 76
            btn2 = pygame.Rect(bx, by, btn_w, btn_h)
            btn3 = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)
            if btn2.collidepoint(mx, my):
                game.controls_mode = 2
            elif btn3.collidepoint(mx, my):
                game.controls_mode = 3


def draw_controls(game):
    s = game.game_surface
    if game._controls_from == 'paused' and game.world:
        game.world.draw(s)
    else:
        from .menu_bg import draw_menu_bg
        draw_menu_bg(game)

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    s.blit(overlay, (0, 0))

    pw, ph = 800, 500
    panel_surf = game.assets.scale_panel(pw, ph)
    px = (SCREEN_WIDTH - pw) // 2
    py = (SCREEN_HEIGHT - ph) // 2

    shadow = pygame.Surface((pw + 6, ph + 6), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 40))
    s.blit(shadow, (px - 3, py + 2))
    s.blit(panel_surf, (px, py))

    title = game.assets.font_big.render('Controles', True, GUI_DARK)
    s.blit(title, title.get_rect(center=(px + pw // 2, py + 40)))
    pygame.draw.line(s, GUI_BORDER, (px + 40, py + 65), (px + pw - 40, py + 65), 2)

    btn_w, btn_h, gap = 150, 32, 12
    bx = px + (pw - (btn_w * 2 + gap)) // 2
    by = py + 76
    btn2_rect = pygame.Rect(bx, by, btn_w, btn_h)
    btn3_rect = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)

    for rect, label, mode in ((btn2_rect, '2 Jugadores', 2), (btn3_rect, '3 Jugadores', 3)):
        active = game.controls_mode == mode
        fill = (255, 220, 150) if active else (235, 220, 200)
        pygame.draw.rect(s, fill, rect, border_radius=7)
        pygame.draw.rect(s, GUI_BORDER, rect, 2 if active else 1, border_radius=7)
        lab = game.assets.font_small.render(label, True, GUI_DARK)
        s.blit(lab, lab.get_rect(center=rect.center))

    all_players = {
        1:    ('Jugador 1', 'p1', 'A / D', 'W', 'S'),
        2:    ('Jugador 2', 'p2', '← / →', '↑', '↓'),
        '2b': ('Jugador 2', 'p2', 'J / L', 'I', 'K'),
        3:    ('Jugador 3', 'p3', '← / →', '↑', '↓'),
    }
    player_ids = [1, 2] if game.controls_mode == 2 else [1, '2b', 3]
    n_cols = len(player_ids)

    PAD_X = 44
    COL_GAP = 20
    col_w = (pw - PAD_X * 2 - COL_GAP * (n_cols - 1)) // n_cols
    content_top = by + btn_h + 18
    LINE_H = 28
    ICON_H = 26
    LABEL_COLOR = GUI_TEXT_LIGHT
    KEY_COLOR = GUI_DARK

    for col_i, pid in enumerate(player_ids):
        name, icon_key, move_k, jump_k, act_k = all_players[pid]
        cx = px + PAD_X + col_i * (col_w + COL_GAP)
        cy = content_top

        if col_i > 0:
            sep_x = cx - COL_GAP // 2
            pygame.draw.line(s, GUI_BORDER,
                             (sep_x, content_top - 4),
                             (sep_x, content_top + ICON_H + LINE_H * 3 + 28), 1)

        icon_surf = None
        if icon_key in game.assets.hud:
            icon = game.assets.hud[icon_key]
            iw, ih = icon.get_size()
            icon_surf = pygame.transform.smoothscale(icon, (int(iw * ICON_H / ih), ICON_H))
            s.blit(icon_surf, (cx, cy))

        icon_w = icon_surf.get_width() + 6 if icon_surf else 0
        name_s = game.assets.font.render(name, True, GUI_DARK)
        s.blit(name_s, (cx + icon_w, cy + 2))

        cy += ICON_H + 10
        pygame.draw.line(s, GUI_BORDER, (cx, cy), (cx + col_w, cy), 1)
        cy += 10

        for action_label, key_str in (
            ('Mover', move_k),
            ('Saltar', jump_k),
            ('Interactuar', act_k),
        ):
            label_s = game.assets.font_small.render(action_label, True, LABEL_COLOR)
            key_s = game.assets.font_small.render(key_str, True, KEY_COLOR)
            s.blit(label_s, (cx + 4, cy))
            s.blit(key_s, (cx + col_w - key_s.get_width() - 4, cy))
            cy += LINE_H

    gen_y = content_top + ICON_H + 10 + 10 + LINE_H * 3 + 24
    pygame.draw.line(s, GUI_BORDER, (px + 40, gen_y), (px + pw - 40, gen_y), 1)
    gen_y += 14

    for line in (
        'R = Reiniciar nivel',
        'ESC = Pausa  ·  F5 = Pantalla completa  ·  F3 = Mostrar FPS',
    ):
        surf = game.assets.font_small.render(line, True, GUI_TEXT_LIGHT)
        s.blit(surf, surf.get_rect(center=(px + pw // 2, gen_y)))
        gen_y += surf.get_height() + 8

    hint = game.assets.font_small.render('← → cambiar modo  ·  ESC / Enter para volver', True, GUI_TEXT_LIGHT)
    s.blit(hint, hint.get_rect(center=(px + pw // 2, py + ph - 24)))
