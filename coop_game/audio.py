from __future__ import annotations
import os
import random
import pygame
from .settings import AUDIO_DIR

_EXTS = ('.mp3', '.ogg', '.wav')


def _scan_tracks(directory):
    """Return sorted list of Path objects for audio files inside *directory*."""
    tracks = []
    if directory.exists():
        for f in sorted(directory.iterdir()):
            if f.suffix.lower() in _EXTS:
                tracks.append(f)
    return tracks


def _load_sound(path):
    """Safely load a Sound; returns None on failure."""
    try:
        return pygame.mixer.Sound(str(path))
    except Exception:
        return None


class AudioManager:
    """Manages background music (menu / in-game) and sound effects."""

    def __init__(self):
        self.volume = 0.5
        self.muted = False

        # ── Music pools ─────────────────────────────────────────
        self.menu_tracks = _scan_tracks(AUDIO_DIR / 'music' / 'menu')
        self.ingame_tracks = _scan_tracks(AUDIO_DIR / 'music' / 'ingame')
        self.menu_index = 0
        self.ingame_index = 0
        # "menu" or "ingame"
        self._active_pool = 'menu'
        # Position (in seconds) where we paused so we can resume
        self._paused_pos: float = 0.0
        self._paused_pool: str | None = None

        # ── SFX: menu ───────────────────────────────────────────
        self.menu_sfx: list[pygame.mixer.Sound] = []
        sfx_dir = AUDIO_DIR / 'sfx' / 'menu' / 'select'
        if sfx_dir.exists():
            for f in sorted(sfx_dir.iterdir()):
                snd = _load_sound(f)
                if snd:
                    self.menu_sfx.append(snd)

        self.sfx_enter = _load_sound(AUDIO_DIR / 'sfx' / 'menu' / 'enter.mp3')
        self.sfx_esc = _load_sound(AUDIO_DIR / 'sfx' / 'menu' / 'esc.mp3')

        # ── SFX: objects ────────────────────────────────────────
        obj = AUDIO_DIR / 'sfx' / 'objects'
        self.sfx_box = _load_sound(obj / 'box.mp3')
        self.sfx_dooropen = _load_sound(obj / 'dooropen0.mp3')
        self.sfx_doorclose = _load_sound(obj / 'doorclose0.mp3')
        self.sfx_lever = _load_sound(obj / 'lever.mp3')
        self.sfx_trampoline = _load_sound(obj / 'trampoline.mp3')

        # ── SFX: level complete ─────────────────────────────────
        self.sfx_level_complete = _load_sound(AUDIO_DIR / 'sfx' / 'level_complete.mp3')

        # ── SFX: footsteps (biome → list of Sound) ─────────────
        self.footstep_sounds: dict[str, list[pygame.mixer.Sound]] = {}
        fs_dir = AUDIO_DIR / 'sfx' / 'footsteps'
        # Map biome names to filename prefixes
        _biome_fs = {
            'green': ['Grass', 'Forest'],
            'snow': ['Snow'],
            'stone': ['Gravel', 'Concrete'],
        }
        if fs_dir.exists():
            for biome, prefixes in _biome_fs.items():
                sounds = []
                for f in sorted(fs_dir.iterdir()):
                    if f.suffix.lower() in _EXTS:
                        if any(f.stem.startswith(p) for p in prefixes):
                            snd = _load_sound(f)
                            if snd:
                                sounds.append(snd)
                if sounds:
                    self.footstep_sounds[biome] = sounds

        # ── Apply initial volume & start menu music ─────────────
        self._apply_volume()
        if self.menu_tracks:
            self._play_track(self.menu_tracks, self.menu_index)

    # ── Volume ──────────────────────────────────────────────────
    def _effective_volume(self):
        return 0.0 if self.muted else self.volume

    def _apply_volume(self):
        pygame.mixer.music.set_volume(self._effective_volume())

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))
        self._apply_volume()

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volume()

    # ── Track helpers ───────────────────────────────────────────
    @property
    def _pool(self):
        return self.menu_tracks if self._active_pool == 'menu' else self.ingame_tracks

    @property
    def _pool_index(self):
        return self.menu_index if self._active_pool == 'menu' else self.ingame_index

    @_pool_index.setter
    def _pool_index(self, val):
        if self._active_pool == 'menu':
            self.menu_index = val
        else:
            self.ingame_index = val

    def _play_track(self, pool, idx):
        if not pool:
            return
        try:
            pygame.mixer.music.load(str(pool[idx]))
            pygame.mixer.music.play(-1)
            self._apply_volume()
        except Exception:
            pass

    def current_track_name(self) -> str:
        pool = self._pool
        if not pool:
            return '(sin música)'
        name = pool[self._pool_index].stem
        if len(name) > 40:
            name = name[:37] + '...'
        return name

    def next_track(self):
        pool = self._pool
        if not pool:
            return
        self._pool_index = (self._pool_index + 1) % len(pool)
        self._play_track(pool, self._pool_index)

    def prev_track(self):
        pool = self._pool
        if not pool:
            return
        self._pool_index = (self._pool_index - 1) % len(pool)
        self._play_track(pool, self._pool_index)

    # ── Pool switching (menu ↔ ingame) ──────────────────────────
    def switch_to_menu_music(self):
        """Stop current music and start menu music from the beginning."""
        pygame.mixer.music.stop()
        self._active_pool = 'menu'
        if self.menu_tracks:
            self._play_track(self.menu_tracks, self.menu_index)

    def switch_to_ingame_music(self):
        """Stop current music and start in-game music from the beginning."""
        pygame.mixer.music.stop()
        self._active_pool = 'ingame'
        if self.ingame_tracks:
            self._play_track(self.ingame_tracks, self.ingame_index)

    def pause_music(self):
        pygame.mixer.music.pause()

    def unpause_music(self):
        pygame.mixer.music.unpause()
        self._apply_volume()

    # ── SFX helpers ─────────────────────────────────────────────
    def _play_sfx(self, snd: pygame.mixer.Sound | None, vol_mult: float = 1.0):
        if snd is None:
            return
        snd.set_volume(self._effective_volume() * vol_mult)
        snd.play()

    def play_menu_sfx(self):
        if self.menu_sfx:
            self._play_sfx(random.choice(self.menu_sfx))

    def play_enter(self):
        self._play_sfx(self.sfx_enter)

    def play_esc(self):
        self._play_sfx(self.sfx_esc)

    def play_box(self):
        self._play_sfx(self.sfx_box)

    def play_dooropen(self):
        self._play_sfx(self.sfx_dooropen)

    def play_doorclose(self):
        self._play_sfx(self.sfx_doorclose)

    def play_lever(self):
        self._play_sfx(self.sfx_lever)

    def play_trampoline(self):
        self._play_sfx(self.sfx_trampoline)

    def play_level_complete(self):
        # Play level complete quieter so it doesn't blast the player
        self._play_sfx(self.sfx_level_complete, 0.5)

    def play_footstep(self, biome: str):
        sounds = self.footstep_sounds.get(biome)
        if sounds:
            # Make snow footsteps louder per request, keep others softer
            if biome == 'snow':
                vol = 0.85
            else:
                vol = 0.35
            self._play_sfx(random.choice(sounds), vol)
