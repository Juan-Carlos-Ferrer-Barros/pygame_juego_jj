import pygame
from ..settings import SCREEN_WIDTH

# GUI color palette (matches game.py)
GUI_BG = (222, 198, 166)
GUI_BORDER = (148, 108, 68)
GUI_DARK = (100, 70, 40)
GUI_TEXT = (80, 55, 30)
GUI_TEXT_LIGHT = (160, 135, 100)


def draw_panel(game, title, options, selected, width=640, height=None):
    """Draw a centered GUI-styled panel with 9-slice background.
    Returns the panel rect."""
    s = game.game_surface
    if height is None:
        height = 160 + len(options) * 56
    panel_w, panel_h = width, height
    panel_surf = game.assets.scale_panel(panel_w, panel_h)
    px = (SCREEN_WIDTH - panel_w) // 2
    from ..settings import SCREEN_HEIGHT
    py = (SCREEN_HEIGHT - panel_h) // 2 + 10

    shadow = pygame.Surface((panel_w + 8, panel_h + 8), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 40))
    s.blit(shadow, (px - 4, py + 2))
    s.blit(panel_surf, (px, py))

    title_s = game.assets.font_big.render(title, True, GUI_DARK)
    s.blit(title_s, title_s.get_rect(center=(SCREEN_WIDTH // 2, py + 58)))

    line_y = py + 85
    pygame.draw.line(s, GUI_BORDER, (px + 40, line_y), (px + panel_w - 40, line_y), 2)

    y = py + 110
    for i, line in enumerate(options):
        is_sel = (i == selected)
        color = GUI_DARK if is_sel else GUI_TEXT_LIGHT

        if is_sel:
            bar_w = min(panel_w - 60, 440)
            bar = pygame.Rect(0, 0, bar_w, 42)
            bar.center = (SCREEN_WIDTH // 2, y)
            highlight = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
            highlight.fill((255, 220, 160, 60))
            pygame.draw.rect(highlight, GUI_BORDER, highlight.get_rect(), 2, border_radius=10)
            s.blit(highlight, bar.topleft)
            arrow = game.assets.font.render('»', True, GUI_DARK)
            s.blit(arrow, (bar.left + 10, y - 18))

        surf = game.assets.font.render(line, True, color)
        s.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))
        y += 56

    hint = game.assets.font_small.render(
        'Enter selecciona  ·  ESC vuelve  ·  F5 pantalla completa', True, GUI_TEXT_LIGHT)
    s.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, py + panel_h - 28)))

    return pygame.Rect(px, py, panel_w, panel_h)


def draw_main_menu(game):
    from .menu_bg import draw_menu_bg
    draw_menu_bg(game)
    options = [
        'Jugar',
        f'Jugadores: {game.player_count}',
        'Controles',
        'Música',
        'Reiniciar progreso',
        'Salir',
    ]
    draw_panel(game, 'Ñoqui-Ñoqui', options, game.menu_index)
