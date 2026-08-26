import json
from copy import deepcopy
from .settings import SAVE_FILE, DEFAULT_SAVE, DATA_DIR

class SaveSystem:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self.load()

    def load(self):
        if not SAVE_FILE.exists():
            self._write(DEFAULT_SAVE)
            return deepcopy(DEFAULT_SAVE)
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            data = deepcopy(DEFAULT_SAVE)
            data.update(raw)
            return data
        except Exception:
            self._write(DEFAULT_SAVE)
            return deepcopy(DEFAULT_SAVE)

    def _write(self, data):
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def save(self):
        self._write(self.data)

    def get_player_count(self):
        return int(self.data.get('player_count', 2))

    def set_player_count(self, count):
        self.data['player_count'] = count
        self.save()

    def is_unlocked(self, level_id):
        return level_id in self.data.get('unlocked_levels', [1])

    def is_completed(self, level_id):
        return level_id in self.data.get('completed_levels', [])

    def complete_level(self, level_id, elapsed, total_levels):
        completed = set(self.data.get('completed_levels', []))
        completed.add(level_id)
        self.data['completed_levels'] = sorted(completed)

        unlocked = set(self.data.get('unlocked_levels', [1]))
        unlocked.add(level_id)
        if level_id < total_levels:
            unlocked.add(level_id + 1)
        self.data['unlocked_levels'] = sorted(unlocked)

        best_times = self.data.setdefault('best_times', {})
        k = str(level_id)
        if k not in best_times or elapsed < best_times[k]:
            best_times[k] = round(elapsed, 2)
        self.save()

    def reset_progress(self):
        """Reset the save data to defaults and persist immediately."""
        self.data = deepcopy(DEFAULT_SAVE)
        self._write(self.data)
