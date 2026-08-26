import pygame
from ..settings import SCREEN_WIDTH, SCREEN_HEIGHT


def draw_menu_bg(game):
    """Animated sky + sprite-based parallax background for menus."""
    s = game.game_surface
    assets = game.assets
    t = game._menu_anim_t

    # Gradient sky
    for y in range(0, SCREEN_HEIGHT, 2):
        frac = y / SCREEN_HEIGHT
        r = int(90 + 65 * frac)
        g = int(170 + 60 * frac)
        b = int(255 - 30 * frac)
        pygame.draw.line(s, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        if y + 1 < SCREEN_HEIGHT:
            pygame.draw.line(s, (r, g, b), (0, y + 1), (SCREEN_WIDTH, y + 1))

    # Sun with glow
    sun_x, sun_y = SCREEN_WIDTH - 160, 95
    for rad in range(80, 30, -6):
        alpha = max(10, 50 - rad)
        glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 240, 100, alpha), (rad, rad), rad)
        s.blit(glow, (sun_x - rad, sun_y - rad))
    pygame.draw.circle(s, (255, 240, 110), (sun_x, sun_y), 38)

    # Clouds with actual sprites
    bg = assets.bg
    cloud_data = [
        ('cloud1', 0.12, 65), ('cloud2', 0.08, 100), ('cloud3', 0.15, 45),
        ('cloud1', 0.10, 130), ('cloud2', 0.07, 80),
    ]
    for i, (ck, speed, cy) in enumerate(cloud_data):
        if ck not in bg:
            continue
        img = bg[ck]
        x = ((i * 280 + t * speed * 60) % (SCREEN_WIDTH + 300)) - 150
        s.blit(img, (int(x), cy))

    # Hills
    for name, bx, off_y in [('hill_large', 100, 0), ('hill_smallAlt', 500, 10),
                             ('hill_largeAlt', 850, 5), ('hill_small', 1150, 15)]:
        if name not in bg:
            continue
        img = bg[name]
        s.blit(img, (bx, SCREEN_HEIGHT - 120 - img.get_height() + off_y))

    # Ground with grass tiles
    grass_img = assets.get_tile('grassMid')
    dirt_img = assets.get_tile('grassCenter')
    gw = grass_img.get_width()
    ground_y = SCREEN_HEIGHT - 120
    for x in range(0, SCREEN_WIDTH, gw):
        s.blit(grass_img, (x, ground_y))
        for dy in range(gw, 121, gw):
            s.blit(dirt_img, (x, ground_y + dy))

    # Vegetation decor on ground
    for name, bx in [('bush', 90), ('mushroomRed', 280), ('plant', 420),
                      ('fence', 600), ('mushroomBrown', 780), ('plantPurple', 950),
                      ('rock', 1100), ('mushroomRed', 1220)]:
        if name not in bg:
            continue
        img = bg[name]
        s.blit(img, (bx, ground_y - img.get_height() + 5))

    # Animated player character standing on ground
    p1 = assets.players[1]
    walk = p1['walk']
    frame = int(t * 4) % len(walk)
    char_img = walk[frame]
    char_rect = char_img.get_rect(midbottom=(220, ground_y + 2))
    s.blit(char_img, char_rect)
