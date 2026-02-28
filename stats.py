import json
import shutil
import time
from datetime import datetime
from pathlib import Path

STATS_FILE = Path("stats.jsonl")
SNAPSHOT_DIR = Path("stats_snapshots")


def snapshot_stats_file():
    """Copy stats.jsonl to stats_snapshots/ with a timestamp, if it exists."""
    if not STATS_FILE.exists():
        return
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(STATS_FILE, SNAPSHOT_DIR / f"stats_{timestamp}.jsonl")


def append_stats(record):
    """Append a single JSON record as a line to the stats file."""
    with open(STATS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


class GameStats:
    ACTIVE_TIME_CAP = 10.0

    def __init__(self):
        self.reset()

    def reset(self):
        """Called at the start of each new game."""
        self.start_time = datetime.now()
        self.start_ts = time.time()
        self.shot_timestamps = []
        self.shots_fired = 0
        self.shots_hit = 0
        self.bubbles_destroyed_by_match = 0
        self.bubbles_destroyed_by_disjoint = 0
        self.max_match_size = 0
        self.matches_made = 0
        self.initial_bubble_count = 0
        self.colors_in_play = 0

    def record_game_start(self, bubble_count, color_count):
        """Called after board.init() with initial board state."""
        self.initial_bubble_count = bubble_count
        self.colors_in_play = color_count

    def record_shot(self):
        """Called when shoot_bubble() fires."""
        self.shots_fired += 1
        self.shot_timestamps.append(time.time())

    def record_match(self, match_size):
        """Called from kill_same_color() with the count of matched bubbles."""
        self.shots_hit += 1
        self.matches_made += 1
        self.bubbles_destroyed_by_match += match_size
        self.max_match_size = max(self.max_match_size, match_size)

    def record_disjoint_removal(self, count):
        """Called from remove_disjoint() with count of disconnected bubbles."""
        self.bubbles_destroyed_by_disjoint += count

    def finalize(self, win, bubbles_remaining, rows_advanced):
        """Called on game over. Builds the stats dict and appends to file."""
        end_time = datetime.now()
        end_ts = time.time()
        duration = (end_time - self.start_time).total_seconds()
        active_time = self._calc_active_time(end_ts)
        accuracy = self.shots_hit / self.shots_fired if self.shots_fired else 0.0

        record = {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "result": "win" if win else "loss",
            "duration_sec": round(duration, 2),
            "active_play_time_sec": round(active_time, 2),
            "shots_fired": self.shots_fired,
            "shots_hit": self.shots_hit,
            "shots_missed": self.shots_fired - self.shots_hit,
            "accuracy": round(accuracy, 3),
            "bubbles_destroyed": self.bubbles_destroyed_by_match + self.bubbles_destroyed_by_disjoint,
            "bubbles_destroyed_by_match": self.bubbles_destroyed_by_match,
            "bubbles_destroyed_by_disjoint": self.bubbles_destroyed_by_disjoint,
            "max_match_size": self.max_match_size,
            "matches_made": self.matches_made,
            "rows_advanced": rows_advanced,
            "bubbles_remaining": bubbles_remaining,
            "initial_bubble_count": self.initial_bubble_count,
            "colors_in_play": self.colors_in_play,
        }

        append_stats(record)
        return record

    def _calc_active_time(self, end_ts):
        cap = self.ACTIVE_TIME_CAP
        timestamps = [self.start_ts] + self.shot_timestamps + [end_ts]
        return sum(min(timestamps[i] - timestamps[i - 1], cap) for i in range(1, len(timestamps)))
