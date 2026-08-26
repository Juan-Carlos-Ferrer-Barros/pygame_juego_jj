from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSET_ROOT = BASE_DIR / 'assets' / 'Base pack'
PLAYER_DIR = ASSET_ROOT / 'Player'
TILE_DIR = ASSET_ROOT / 'Tiles'
ITEM_DIR = ASSET_ROOT / 'Items'
HUD_DIR = ASSET_ROOT / 'HUD'
GUI_DIR = BASE_DIR / 'assets' / 'GUI'
METEORITE_DIR = BASE_DIR / 'assets' / 'Meteorite'
SMOKE_DIR = BASE_DIR / 'assets' / 'Smoke'
BIRD_DIR = BASE_DIR / 'assets' / 'Bird'
AUDIO_DIR = BASE_DIR / 'assets' / 'Audio'
LEVEL_DIR = BASE_DIR / 'levels'
DATA_DIR = BASE_DIR / 'data'
SAVE_FILE = DATA_DIR / 'save.json'

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = 'Rope & Goal'

TILE_SIZE = 48
GRAVITY = 0.42
MOVE_SPEED = 4.5
JUMP_SPEED = 10.5
MAX_FALL_SPEED = 14
PLAYER_SCALE = 0.72
CAMERA_LERP = 0.09

BG_COLOR = (125, 190, 255)
TEXT_COLOR = (20, 24, 38)
PANEL_COLOR = (250, 250, 255)
PANEL_BORDER = (45, 55, 90)
ACCENT = (255, 212, 76)
LOCKED = (170, 170, 170)
GREEN = (95, 200, 110)
RED = (220, 90, 90)

DEFAULT_SAVE = {
    'player_count': 2,
    'unlocked_levels': [1],
    'completed_levels': [],
    'best_times': {},
}
