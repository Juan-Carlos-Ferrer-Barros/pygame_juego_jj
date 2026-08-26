"""
Sprite Viewer - Visor automático de animaciones
Escanea la carpeta 'assets/' y detecta todas las animaciones automáticamente.
Corre: python chicken_sprite_viewer.py
O con carpeta específica: python chicken_sprite_viewer.py ruta/a/assets
"""

import pygame
import sys
import os
from pathlib import Path

# ─── Configuración visual ─────────────────────────────────────────────────────
WIDTH, HEIGHT      = 1100, 700
PANEL_W            = 260
BG_COLOR           = (28, 28, 36)
PANEL_COLOR        = (38, 38, 50)
PANEL_HOVER        = (50, 50, 68)
SELECTED_BG        = (60, 110, 230)
SELECTED_TXT       = (255, 255, 255)
TEXT_COLOR         = (215, 215, 225)
DIM_COLOR          = (130, 130, 150)
FRAME_BG           = (22, 22, 30)
FRAME_BORDER       = (80, 80, 100)
OK_COLOR           = (80, 210, 120)
ERR_COLOR          = (240, 80, 80)
WARN_COLOR         = (240, 180, 50)
THUMB_SELECTED     = (60, 110, 230)
THUMB_NORMAL       = (70, 70, 90)

SCROLL_SPEED       = 3
MIN_FRAMES_TO_SHOW = 1     # carpetas con al menos N PNGs se consideran animación


def scan_animations(root: Path) -> list[dict]:
    """
    Recorre root recursivamente.
    Cada subcarpeta que contenga ≥ MIN_FRAMES_TO_SHOW archivos .png
    se convierte en una animación. Los frames se ordenan alfabéticamente.
    """
    animations = []
    for dirpath, _dirs, files in os.walk(root):
        pngs = sorted(
            [f for f in files if f.lower().endswith('.png')],
            key=lambda n: n.lower()
        )
        if len(pngs) >= MIN_FRAMES_TO_SHOW:
            folder = Path(dirpath)
            rel = folder.relative_to(root)
            parts = rel.parts
            # Nombre legible: última parte del path (nombre de carpeta)
            short_name = folder.name
            # Etiqueta de grupo: carpeta padre relativa a root
            group = str(rel.parent) if len(parts) > 1 else ""
            animations.append({
                'name':       short_name,
                'group':      group,
                'rel_path':   str(rel),
                'full_path':  folder,
                'png_files':  [folder / f for f in pngs],
                'frames':     [],
                'loaded':     False,
            })
    animations.sort(key=lambda a: a['rel_path'].lower())
    return animations


def load_frames(anim: dict) -> None:
    """Carga los frames de una animación (lazy, solo cuando se selecciona)."""
    if anim['loaded']:
        return
    frames = []
    for path in anim['png_files']:
        try:
            img = pygame.image.load(str(path)).convert_alpha()
            w, h = img.get_size()
            frames.append({
                'image':  img,
                'path':   str(path),
                'name':   path.name,
                'size':   (w, h),
                'status': 'ok',
            })
        except Exception as e:
            frames.append({
                'image':  None,
                'path':   str(path),
                'name':   path.name,
                'size':   (0, 0),
                'status': f'error: {e}',
            })
    anim['frames'] = frames
    anim['loaded'] = True


def make_checkerboard(rect: pygame.Rect, size: int = 20) -> pygame.Surface:
    surf = pygame.Surface((rect.width, rect.height))
    for cy in range(0, rect.height, size):
        for cx in range(0, rect.width, size):
            col = (30, 30, 40) if ((cx // size + cy // size) % 2 == 0) else (42, 42, 54)
            pygame.draw.rect(surf, col, (cx, cy, size, size))
    return surf


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return '...' + text[-(max_chars - 3):]


def main():
    # ── Determinar carpeta raíz ───────────────────────────────────────────────
    if len(sys.argv) >= 2:
        root = Path(sys.argv[1])
    else:
        # Buscar 'assets' junto al script o en el directorio actual
        candidates = [
            Path(__file__).parent / 'assets',
            Path.cwd() / 'assets',
            Path(__file__).parent,
        ]
        root = next((p for p in candidates if p.is_dir()), Path.cwd())

    if not root.is_dir():
        print(f"[ERROR] No se encontró la carpeta: {root}")
        sys.exit(1)

    print(f"Escaneando: {root.resolve()}")

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption(f"Sprite Viewer — {root.resolve()}")

    font       = pygame.font.SysFont('consolas', 15)
    font_bold  = pygame.font.SysFont('consolas', 17, bold=True)
    font_small = pygame.font.SysFont('consolas', 12)
    font_title = pygame.font.SysFont('consolas', 20, bold=True)

    def txt(surface, text, pos, color=TEXT_COLOR, fnt=None, clip=None):
        fnt = fnt or font
        rendered = fnt.render(str(text), True, color)
        if clip:
            surface.set_clip(clip)
        surface.blit(rendered, pos)
        if clip:
            surface.set_clip(None)
        return rendered.get_width(), rendered.get_height()

    # ── Escanear animaciones ──────────────────────────────────────────────────
    print("Detectando animaciones...")
    animations = scan_animations(root)
    print(f"  → {len(animations)} carpetas con sprites encontradas")
    if not animations:
        print("No se encontraron imágenes PNG. Verifica la ruta.")
        sys.exit(1)

    # Estado del visor
    selected      = 0
    frame_idx     = 0
    playing       = False
    play_fps      = 10
    play_timer    = 0.0
    zoom          = 1.0
    show_original = True
    scroll_offset = 0   # scroll del panel izquierdo (en píxeles)
    thumb_scroll  = 0   # scroll horizontal de thumbnails
    hover_idx     = -1
    clock         = pygame.time.Clock()

    ITEM_H   = 38
    THUMB_SZ = 56
    THUMB_GAP = 4

    def select(idx: int):
        nonlocal selected, frame_idx, playing, scroll_offset
        selected  = max(0, min(idx, len(animations) - 1))
        frame_idx = 0
        playing   = False
        load_frames(animations[selected])
        # Scroll automático para mantener el item visible
        item_y = selected * ITEM_H - scroll_offset
        visible_h = HEIGHT - 100
        if item_y < 0:
            scroll_offset = selected * ITEM_H
        elif item_y + ITEM_H > visible_h:
            scroll_offset = selected * ITEM_H - visible_h + ITEM_H

    # Cargar primera animación
    select(0)

    running = True
    while running:
        dt  = clock.tick(60)
        W, H = screen.get_size()
        panel_w = PANEL_W

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEWHEEL:
                mx, _ = pygame.mouse.get_pos()
                if mx < panel_w:
                    max_scroll = max(0, len(animations) * ITEM_H - (H - 100))
                    scroll_offset = max(0, min(scroll_offset - event.y * SCROLL_SPEED * 8, max_scroll))
                else:
                    thumb_scroll = max(0, thumb_scroll - event.x * (THUMB_SZ + THUMB_GAP))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mx < panel_w:
                    list_y = my - 90 + scroll_offset
                    idx = list_y // ITEM_H
                    if 0 <= idx < len(animations):
                        select(idx)
                else:
                    anim = animations[selected]
                    if anim['frames']:
                        thumb_area_y = H - THUMB_SZ - 30
                        if my >= thumb_area_y:
                            avail_w = W - panel_w - 20
                            rel_x = mx - panel_w - 10 + thumb_scroll
                            clicked = rel_x // (THUMB_SZ + THUMB_GAP)
                            if 0 <= clicked < len(anim['frames']):
                                frame_idx = int(clicked)

            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    running = False
                elif key == pygame.K_UP:
                    select(selected - 1)
                elif key == pygame.K_DOWN:
                    select(selected + 1)
                elif key == pygame.K_LEFT:
                    anim = animations[selected]
                    if anim['frames']:
                        frame_idx = (frame_idx - 1) % len(anim['frames'])
                elif key == pygame.K_RIGHT:
                    anim = animations[selected]
                    if anim['frames']:
                        frame_idx = (frame_idx + 1) % len(anim['frames'])
                elif key == pygame.K_SPACE:
                    playing = not playing
                elif key == pygame.K_o:
                    show_original = not show_original
                elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    zoom = min(zoom + 0.25, 8.0)
                elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    zoom = max(zoom - 0.25, 0.25)
                elif key == pygame.K_r:
                    zoom = 1.0
                elif key == pygame.K_PAGEUP:
                    play_fps = min(play_fps + 2, 60)
                elif key == pygame.K_PAGEDOWN:
                    play_fps = max(play_fps - 2, 1)
                elif key == pygame.K_HOME:
                    frame_idx = 0
                elif key == pygame.K_END:
                    anim = animations[selected]
                    if anim['frames']:
                        frame_idx = len(anim['frames']) - 1

        # ── Auto-play ─────────────────────────────────────────────────────────
        if playing:
            play_timer += dt
            interval = 1000.0 / play_fps
            while play_timer >= interval:
                play_timer -= interval
                anim = animations[selected]
                if anim['frames']:
                    frame_idx = (frame_idx + 1) % len(anim['frames'])

        # ── Dibujar ───────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)

        # Panel izquierdo
        pygame.draw.rect(screen, PANEL_COLOR, (0, 0, panel_w, H))

        # Header panel
        pygame.draw.rect(screen, (30, 30, 42), (0, 0, panel_w, 88))
        txt(screen, "SPRITE VIEWER", (12, 10), SELECTED_BG, font_title)
        txt(screen, f"{root.name}/", (12, 36), DIM_COLOR, font_small)
        txt(screen, f"{len(animations)} animaciones", (12, 52), DIM_COLOR, font_small)
        txt(screen, "↑↓ navegar  Scroll rueda", (12, 68), DIM_COLOR, font_small)
        pygame.draw.line(screen, (55, 55, 75), (0, 88), (panel_w, 88))

        # Lista de animaciones (con scroll y agrupado)
        list_clip = pygame.Rect(0, 90, panel_w, H - 90)
        screen.set_clip(list_clip)
        mx_cur, my_cur = pygame.mouse.get_pos()
        prev_group = None

        for i, anim in enumerate(animations):
            item_top = 90 + i * ITEM_H - scroll_offset
            item_rect = pygame.Rect(4, item_top, panel_w - 8, ITEM_H - 2)

            if item_top + ITEM_H < 90 or item_top > H:
                continue

            # Separador de grupo
            if anim['group'] != prev_group and anim['group']:
                group_label = anim['group'].replace('\\', '/').replace('/', ' › ')
                if len(group_label) > 30:
                    group_label = '...' + group_label[-27:]
                grect = pygame.Rect(0, item_top - 2, panel_w, 1)
                pygame.draw.rect(screen, (55, 55, 75), grect)

            prev_group = anim['group']

            is_sel   = (i == selected)
            is_hover = item_rect.collidepoint(mx_cur, my_cur) and not is_sel

            if is_sel:
                pygame.draw.rect(screen, SELECTED_BG, item_rect, border_radius=5)
            elif is_hover:
                pygame.draw.rect(screen, PANEL_HOVER, item_rect, border_radius=5)

            name_color = SELECTED_TXT if is_sel else TEXT_COLOR
            dim_c      = (200, 200, 215) if is_sel else DIM_COLOR

            name_clip  = pygame.Rect(item_rect.x + 8, item_rect.y, panel_w - 80, ITEM_H)
            name_label = truncate(anim['name'], 22)
            txt(screen, name_label, (item_rect.x + 8, item_top + 5), name_color, font_bold, clip=name_clip)

            # Estado: cuántos PNGs tiene
            n = len(anim['png_files'])
            status_x = panel_w - 52
            if anim['loaded']:
                ok_n = sum(1 for f in anim['frames'] if f['status'] == 'ok')
                sc = OK_COLOR if ok_n == n else ERR_COLOR
                count_str = f"{ok_n}/{n}"
            else:
                sc = DIM_COLOR
                count_str = f"{n} png"
            txt(screen, count_str, (status_x, item_top + 12), sc, font_small)

        screen.set_clip(None)

        # Borde derecho del panel
        pygame.draw.line(screen, (55, 55, 75), (panel_w, 0), (panel_w, H))

        # ── Área de previsualización ───────────────────────────────────────────
        anim = animations[selected]
        px = panel_w + 10
        pw = W - panel_w - 20

        # Header info
        txt(screen, anim['name'], (px, 8), (120, 170, 255), font_title)
        path_label = truncate(anim['rel_path'].replace('\\', '/'), 80)
        txt(screen, path_label, (px, 36), DIM_COLOR, font_small)

        if anim['frames']:
            frame = anim['frames'][frame_idx]
            n_frames = len(anim['frames'])
            ok_frames = sum(1 for f in anim['frames'] if f['status'] == 'ok')

            # Fila de estado del frame actual
            st_color = OK_COLOR if frame['status'] == 'ok' else ERR_COLOR
            txt(screen, f"Frame {frame_idx + 1} / {n_frames}", (px, 56), TEXT_COLOR, font)
            txt(screen, f"  {frame['status']}", (px + 130, 56), st_color, font_small)
            if frame['status'] == 'ok':
                w0, h0 = frame['size']
                txt(screen, f"  {w0}×{h0}px", (px + 260, 56), DIM_COLOR, font_small)
            fname = truncate(frame['name'], 55)
            txt(screen, fname, (px, 74), DIM_COLOR, font_small)

            if ok_frames < n_frames:
                txt(screen, f"  ⚠ {n_frames - ok_frames} frames con errores", (px + 350, 74), WARN_COLOR, font_small)

            # ── Área de preview ────────────────────────────────────────────────
            thumb_area_h = THUMB_SZ + 30
            preview_top    = 98
            preview_bottom = H - thumb_area_h - 10
            preview_rect   = pygame.Rect(px, preview_top, pw, preview_bottom - preview_top)

            checker = make_checkerboard(preview_rect)
            screen.blit(checker, preview_rect.topleft)
            pygame.draw.rect(screen, FRAME_BORDER, preview_rect, 1, border_radius=4)

            if frame['status'] == 'ok':
                img = frame['image']
                w, h = img.get_size()
                disp_w = int(w * zoom)
                disp_h = int(h * zoom)

                # Ajuste automático si no cabe
                max_w = preview_rect.width - 4
                max_h = preview_rect.height - 4
                if not show_original and (disp_w > max_w or disp_h > max_h):
                    scale_fit = min(max_w / w, max_h / h)
                    disp_w = int(w * scale_fit * zoom)
                    disp_h = int(h * scale_fit * zoom)

                disp_img = pygame.transform.smoothscale(img, (max(1, disp_w), max(1, disp_h)))
                ix = preview_rect.centerx - disp_w // 2
                iy = preview_rect.centery - disp_h // 2
                screen.set_clip(preview_rect)
                screen.blit(disp_img, (ix, iy))
                screen.set_clip(None)
                pygame.draw.rect(screen, (90, 90, 115), (ix - 1, iy - 1, disp_w + 2, disp_h + 2), 1)

                zoom_label = f"zoom {zoom:.2f}x"
                txt(screen, zoom_label, (preview_rect.right - 85, preview_rect.bottom - 18), DIM_COLOR, font_small)
            else:
                err_msg = truncate(frame['status'], 60)
                txt(screen, f"[ERROR] {err_msg}",
                    (preview_rect.centerx - 150, preview_rect.centery - 10), ERR_COLOR, font)

            # ── Thumbnails ─────────────────────────────────────────────────────
            thumb_y = H - thumb_area_h - 2
            pygame.draw.rect(screen, (30, 30, 40), (px, thumb_y - 2, pw, thumb_area_h + 4))
            pygame.draw.line(screen, (55, 55, 75), (px, thumb_y - 2), (px + pw, thumb_y - 2))

            thumb_total_w = n_frames * (THUMB_SZ + THUMB_GAP)
            max_thumb_scroll = max(0, thumb_total_w - pw + 20)
            thumb_scroll = max(0, min(thumb_scroll, max_thumb_scroll))

            screen.set_clip(pygame.Rect(px, thumb_y, pw, THUMB_SZ + 20))
            for i, f in enumerate(anim['frames']):
                tx = px + i * (THUMB_SZ + THUMB_GAP) - thumb_scroll
                ty = thumb_y + 4
                tr = pygame.Rect(tx, ty, THUMB_SZ, THUMB_SZ)

                if tx + THUMB_SZ < px or tx > px + pw:
                    continue

                if f['status'] == 'ok':
                    thumb = pygame.transform.smoothscale(f['image'], (THUMB_SZ, THUMB_SZ))
                    screen.blit(thumb, (tx, ty))
                else:
                    pygame.draw.rect(screen, (60, 25, 25), tr, border_radius=3)
                    txt(screen, '?', (tx + THUMB_SZ // 2 - 5, ty + THUMB_SZ // 2 - 8), ERR_COLOR, font_bold)

                border_col = THUMB_SELECTED if i == frame_idx else THUMB_NORMAL
                bw = 3 if i == frame_idx else 1
                pygame.draw.rect(screen, border_col, tr, bw, border_radius=3)

                num = str(i)
                txt(screen, num, (tx + 2, ty + THUMB_SZ - 14), DIM_COLOR, font_small)

            screen.set_clip(None)

        else:
            txt(screen, "Sin frames", (px + 20, H // 2), DIM_COLOR, font_bold)

        # ── Barra de controles (abajo) ─────────────────────────────────────────
        bar_y = H - 22
        pygame.draw.rect(screen, (22, 22, 32), (0, bar_y, W, 22))
        play_lbl  = "[SPACE] Pause" if playing else "[SPACE] Play"
        fps_lbl   = f"FPS:{play_fps} [PgUp/Dn]"
        zoom_lbl  = f"Zoom +/-  R=reset"
        orig_lbl  = "[O] Modo: " + ("original" if show_original else "ajustado")
        ctrl_line = f"  ←→ frame  |  {play_lbl}  |  {fps_lbl}  |  {zoom_lbl}  |  {orig_lbl}  |  ESC salir"
        txt(screen, ctrl_line, (0, bar_y + 4), DIM_COLOR, font_small)

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
