from __future__ import annotations
import sys
import math
import pygame
from .settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, PANEL_COLOR, PANEL_BORDER, TEXT_COLOR, ACCENT, GREEN, LOCKED, RED, BG_COLOR
from .assets import Assets
from .save_system import SaveSystem
from .level_loader import LevelLoader
from .world import LevelWorld
from .audio import AudioManager
from .menus.menu_bg import draw_menu_bg
from .menus.main_menu import draw_main_menu, draw_panel
from .menus.level_select import draw_level_select
from .menus.controls_menu import draw_controls, update_controls
from .menus.music_menu import draw_music_menu, update_music_menu

# GUI color palette
GUI_BG = (222, 198, 166)
GUI_BORDER = (148, 108, 68)
GUI_DARK = (100, 70, 40)
GUI_TEXT = (80, 55, 30)
GUI_TEXT_LIGHT = (160, 135, 100)


class Game:
    def __init__(self):
        pygame.init()
        self.logical_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.fullscreen = False
        self.screen = pygame.display.set_mode(self.logical_size)
        self.game_surface = self.screen  # in windowed mode, draw directly
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.audio = AudioManager()
        self.save = SaveSystem()
        self.loader = LevelLoader()
        self.running = True
        self.state = 'main_menu'
        self.menu_index = 0
        self.player_count = self.save.get_player_count()
        self.current_level_id = 1
        self.world = None
        self.pause_index = 0
        self.overlay_index = 0
        self.show_fps = False
        self._menu_anim_t = 0.0
        self._controls_from = 'paused'
        # Which controls layout to show (2 or 3 players)
        self.controls_mode = self.player_count if self.player_count in (2, 3) else 2

    # ── Fullscreen ──────────────────────────────────────────────────
    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            self.game_surface = pygame.Surface(self.logical_size)
        else:
            self.screen = pygame.display.set_mode(self.logical_size)
            self.game_surface = self.screen
        pygame.display.set_caption(TITLE)

    def _present(self):
        """Blit the logical game surface onto the actual screen, letterboxed."""
        if self.fullscreen:
            sw, sh = self.screen.get_size()
            lw, lh = self.logical_size
            scale = min(sw / lw, sh / lh)
            tw, th = int(lw * scale), int(lh * scale)
            ox, oy = (sw - tw) // 2, (sh - th) // 2
            if ox > 0 or oy > 0:
                self.screen.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(self.game_surface, (tw, th))
            self.screen.blit(scaled, (ox, oy))

    # ── Main loop ───────────────────────────────────────────────────
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._menu_anim_t += dt
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    # Global shortcut: Ctrl+M toggles mute
                    if event.key == pygame.K_m and (event.mod & pygame.KMOD_CTRL):
                        if self.audio:
                            self.audio.toggle_mute()
                    
                    if event.key == pygame.K_F5:
                        self._toggle_fullscreen()
                    if event.key == pygame.K_F3:
                        self.show_fps = not self.show_fps
            if self.state == 'main_menu':
                self.update_main_menu(events)
                draw_main_menu(self)
            elif self.state == 'player_menu':
                self.update_player_menu(events)
                self.draw_player_menu()
            elif self.state == 'level_select':
                self.update_level_select(events)
                draw_level_select(self)
            elif self.state == 'playing':
                self.update_playing(events, dt)
                self.draw_playing()
            elif self.state == 'paused':
                self.update_paused(events)
                self.draw_playing(paused=True)
            elif self.state == 'level_complete':
                self.update_level_complete(events)
                self.draw_playing(completed=True)
            elif self.state == 'controls':
                update_controls(self, events)
                draw_controls(self)
            elif self.state == 'music_menu':
                update_music_menu(self, events)
                draw_music_menu(self)
            if self.show_fps:
                self._draw_fps()
            self._present()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _draw_fps(self):
        fps = int(self.clock.get_fps())
        surf = self.assets.font_small.render(f'FPS: {fps}', True, (255, 255, 80))
        bg = pygame.Surface((surf.get_width() + 10, surf.get_height() + 6), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        self.game_surface.blit(bg, (SCREEN_WIDTH - surf.get_width() - 14, 2))
        self.game_surface.blit(surf, (SCREEN_WIDTH - surf.get_width() - 9, 5))

    # ── Level start ─────────────────────────────────────────────────
    def start_level(self, level_id):
        self.current_level_id = level_id
        level_data = self.loader.get(level_id)
        required = level_data.get('required_players')
        if required and self.player_count < required:
            self.player_count = required
            self.save.set_player_count(required)
        self.world = LevelWorld(level_data, self.player_count, self.assets, self.audio)
        self.audio.switch_to_ingame_music()
        self.state = 'playing'

    # ── Input helpers ───────────────────────────────────────────────
    def handle_basic_menu(self, events, size):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_index = (self.menu_index + 1) % size
                    self.audio.play_menu_sfx()
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.menu_index = (self.menu_index - 1) % size
                    self.audio.play_menu_sfx()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return 'select'
                elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return 'back'
        return None

    # ── State updates ───────────────────────────────────────────────
    def update_main_menu(self, events):
        options = 6
        action = self.handle_basic_menu(events, options)
        if action == 'select':
            self.audio.play_enter()
            if self.menu_index == 0:
                self.state = 'level_select'
                self.menu_index = 0
            elif self.menu_index == 1:
                self.state = 'player_menu'
                self.menu_index = 0
            elif self.menu_index == 2:
                self._controls_from = 'main_menu'
                self.state = 'controls'
            elif self.menu_index == 3:
                self._music_menu_from = 'main_menu'
                self.state = 'music_menu'
                self.menu_index = 0
            elif self.menu_index == 4:
                # Reset progress
                self.save.reset_progress()
                self.player_count = self.save.get_player_count()
                self.menu_index = 0
            elif self.menu_index == 5:
                self.running = False

    def update_player_menu(self, events):
        action = self.handle_basic_menu(events, 2)
        if action == 'select':
            self.audio.play_enter()
            self.player_count = 2 if self.menu_index == 0 else 3
            self.save.set_player_count(self.player_count)
            self.state = 'main_menu'
            self.menu_index = 0
        elif action == 'back':
            self.audio.play_esc()
            self.state = 'main_menu'
            self.menu_index = 0

    def update_level_select(self, events):
        total = len(self.loader.levels)

        # Custom navigation: skip locked levels when moving up/down.
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    # find next unlocked
                    start = self.menu_index
                    found = None
                    idx = (start + 1) % total
                    while idx != start:
                        if self.save.is_unlocked(self.loader.levels[idx]['id']):
                            found = idx
                            break
                        idx = (idx + 1) % total
                    if found is not None:
                        self.menu_index = found
                elif event.key in (pygame.K_UP, pygame.K_w):
                    start = self.menu_index
                    found = None
                    idx = (start - 1) % total
                    while idx != start:
                        if self.save.is_unlocked(self.loader.levels[idx]['id']):
                            found = idx
                            break
                        idx = (idx - 1) % total
                    if found is not None:
                        self.menu_index = found
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    level = self.loader.levels[self.menu_index]
                    if self.save.is_unlocked(level['id']):
                        self.audio.play_enter()
                        self.start_level(level['id'])
                elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.audio.play_esc()
                    self.state = 'main_menu'
                    self.menu_index = 0

    def update_playing(self, events, dt):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.audio.play_esc()
                    self.audio.pause_music()
                    self.state = 'paused'
                    self.pause_index = 0
                    return
                if event.key == pygame.K_r:
                    self.start_level(self.current_level_id)
                    return
        keys = pygame.key.get_pressed()
        self.world.update(dt, keys)
        if self.world.failed:
            self.start_level(self.current_level_id)
            return
        if self.world.complete:
            self.audio.play_level_complete()
            self.save.complete_level(self.current_level_id, self.world.elapsed, len(self.loader.levels))
            self.state = 'level_complete'
            self.overlay_index = 0

    def update_paused(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_index = (self.pause_index + 1) % 5
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.pause_index = (self.pause_index - 1) % 5
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.audio.play_enter()
                    if self.pause_index == 0:
                        self.state = 'playing'
                        self.audio.unpause_music()
                    elif self.pause_index == 1:
                        self.start_level(self.current_level_id)
                    elif self.pause_index == 2:
                        self._controls_from = 'paused'
                        self.state = 'controls'
                    elif self.pause_index == 3:
                        game = self
                        game._music_menu_from = 'paused'
                        game._music_pause_idx = 3
                        game.state = 'music_menu'
                        game.menu_index = 0
                    else:
                        self.audio.switch_to_menu_music()
                        self.state = 'main_menu'
                        self.menu_index = 0
                elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.audio.play_esc()
                    self.state = 'playing'
                    self.audio.unpause_music()

    def _is_last_level(self):
        return self.current_level_id >= len(self.loader.levels)

    def update_level_complete(self, events):
        is_last = self._is_last_level()
        options = 2 if is_last else 3
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.overlay_index = (self.overlay_index + 1) % options
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.overlay_index = (self.overlay_index - 1) % options
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.audio.play_enter()
                    if is_last:
                        # Last level: 0=Repetir, 1=Volver al menu
                        if self.overlay_index == 0:
                            self.start_level(self.current_level_id)
                        else:
                            self.audio.switch_to_menu_music()
                            self.state = 'main_menu'
                            self.menu_index = 0
                    else:
                        if self.overlay_index == 0:
                            self.start_level(self.current_level_id + 1)
                        elif self.overlay_index == 1:
                            self.start_level(self.current_level_id)
                        else:
                            self.audio.switch_to_menu_music()
                            self.state = 'level_select'
                            self.menu_index = self.current_level_id - 1

    # ── Menu draws ──────────────────────────────────────────────────
    def draw_player_menu(self):
        draw_menu_bg(self)
        options = ['2 jugadores', '3 jugadores']
        draw_panel(self, 'Cantidad de jugadores', options, self.menu_index)

    def draw_playing(self, paused=False, completed=False):
        self.world.draw(self.game_surface)
        if paused:
            opts = ['Continuar', 'Reiniciar nivel', 'Controles', 'Música', 'Volver al menu']
            lines = []
            for i, opt in enumerate(opts):
                color = GUI_DARK if i == self.pause_index else GUI_TEXT_LIGHT
                lines.append((opt, color))
            self.world.draw_overlay(self.game_surface, 'Pausa', lines)
        elif completed:
            is_last = self._is_last_level()
            if is_last:
                opts = ['Repetir', 'Volver al menu']
            else:
                opts = ['Siguiente nivel', 'Repetir', 'Volver a seleccion']
            lines = [(f'Tiempo: {self.world.elapsed:05.1f}s', GREEN)]
            for i, opt in enumerate(opts):
                color = GUI_DARK if i == self.overlay_index else GUI_TEXT_LIGHT
                lines.append((opt, color))
            title = '¡Juego completado!' if is_last else 'Nivel completado'
            self.world.draw_overlay(self.game_surface, title, lines)

    # Controls and music menus are handled by the menus/ package
