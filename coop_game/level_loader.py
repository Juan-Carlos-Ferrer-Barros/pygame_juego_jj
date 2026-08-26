import json
from .settings import LEVEL_DIR

class LevelLoader:
    def __init__(self):
        self.levels = []
        self.by_id = {}
        for path in sorted(LEVEL_DIR.glob('level_*.json')):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.levels.append(data)
            self.by_id[data['id']] = data

    def get(self, level_id):
        return self.by_id[level_id]
