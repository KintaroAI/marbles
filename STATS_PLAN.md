# Game Statistics Plan

## Overview

Add persistent per-game statistics logging to the bubble shooter. Each finished game appends a JSON object to a log file. On startup, if the log file exists, create a timestamped snapshot backup before the session begins.

---

## Log Format

File: `stats.jsonl` (JSON Lines — one JSON object per line)

```json
{
  "start_time": "2026-02-28T14:30:00.123456",
  "end_time": "2026-02-28T14:35:12.654321",
  "result": "win",
  "duration_sec": 312.53,
  "active_play_time_sec": 187.20,
  "shots_fired": 42,
  "shots_hit": 28,
  "shots_missed": 14,
  "accuracy": 0.667,
  "bubbles_destroyed": 156,
  "bubbles_destroyed_by_match": 102,
  "bubbles_destroyed_by_disjoint": 54,
  "max_match_size": 7,
  "matches_made": 28,
  "rows_advanced": 3,
  "bubbles_remaining": 1,
  "initial_bubble_count": 153,
  "colors_in_play": 6
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `start_time` | string | ISO 8601 timestamp when the game started |
| `end_time` | string | ISO 8601 timestamp when game over triggered |
| `result` | string | `"win"` or `"loss"` |
| `duration_sec` | float | Wall clock `end_time - start_time` in seconds |
| `active_play_time_sec` | float | Sum of gaps between shots, each capped at 10s. See [Active Time Calculation](#active-time-calculation) |
| `shots_fired` | int | Total shots (calls to `shoot_bubble()`) |
| `shots_hit` | int | Shots that triggered a 3+ match |
| `shots_missed` | int | Shots that didn't match (`shots_fired - shots_hit`) |
| `accuracy` | float | `shots_hit / shots_fired` (0.0 if no shots) |
| `bubbles_destroyed` | int | Total bubbles killed (`by_match + by_disjoint`) |
| `bubbles_destroyed_by_match` | int | Bubbles removed via color matching |
| `bubbles_destroyed_by_disjoint` | int | Bubbles removed via gravity (disconnected from top) |
| `max_match_size` | int | Largest single color-match group in the game |
| `matches_made` | int | Number of times a 3+ match was triggered |
| `rows_advanced` | int | Number of new rows pushed from top (`board.step`) |
| `bubbles_remaining` | int | Bubbles on board at game end |
| `initial_bubble_count` | int | Bubbles on board at game start (after `init()`) |
| `colors_in_play` | int | Number of distinct colors at game start |

### Active Time Calculation

Track the timestamp of each shot. Active play time = sum of all inter-shot gaps, where each gap is `min(gap, 10.0)` seconds. The gap before the first shot (from game start) and the gap after the last shot (to game end) are also included, each capped at 10s.

```python
gaps = []
timestamps = [game_start] + shot_timestamps + [game_end]
for i in range(1, len(timestamps)):
    gap = timestamps[i] - timestamps[i-1]
    gaps.append(min(gap, 10.0))
active_play_time = sum(gaps)
```

---

## Snapshot Backup

On `main()` startup, before any game begins:

1. Check if `stats.jsonl` exists
2. If yes, copy it to `stats_snapshots/stats_YYYYMMDD_HHMMSS.jsonl`
3. Create `stats_snapshots/` directory if needed

This ensures that if the file gets corrupted during a session, a clean copy exists.

```python
def snapshot_stats_file():
    stats_path = Path("stats.jsonl")
    if not stats_path.exists():
        return
    snapshot_dir = Path("stats_snapshots")
    snapshot_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(stats_path, snapshot_dir / f"stats_{timestamp}.jsonl")
```

---

## Implementation

### New File: `stats.py`

A single module handling all stats tracking and persistence.

```python
class GameStats:
    def __init__(self):
        self.reset()

    def reset(self):
        """Called at the start of each new game."""
        self.start_time = datetime.now()
        self.shot_timestamps = []
        self.shots_fired = 0
        self.shots_hit = 0
        self.bubbles_destroyed_by_match = 0
        self.bubbles_destroyed_by_disjoint = 0
        self.max_match_size = 0
        self.matches_made = 0
        self.initial_bubble_count = 0
        self.colors_in_play = 0

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

    def record_game_start(self, bubble_count, color_count):
        """Called after board.init() with initial board state."""
        self.initial_bubble_count = bubble_count
        self.colors_in_play = color_count

    def finalize(self, win, bubbles_remaining, rows_advanced):
        """Called on game over. Returns the stats dict and appends to file."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        active_time = self._calc_active_time(end_time)
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

    def _calc_active_time(self, end_time):
        cap = 10.0
        start_ts = self.start_time.timestamp()
        end_ts = end_time.timestamp()
        timestamps = [start_ts] + self.shot_timestamps + [end_ts]
        return sum(min(timestamps[i] - timestamps[i-1], cap) for i in range(1, len(timestamps)))


def append_stats(record):
    with open("stats.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")


def snapshot_stats_file():
    stats_path = Path("stats.jsonl")
    if not stats_path.exists():
        return
    snapshot_dir = Path("stats_snapshots")
    snapshot_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(stats_path, snapshot_dir / f"stats_{timestamp}.jsonl")
```

### Integration Points

Each hook is a one-line call. No existing logic changes — only additions.

| Where | File | What to add |
|-------|------|-------------|
| `main()` startup, before game loop | `draw.py` | `snapshot_stats_file()` |
| After `board.init()` in `main()` | `draw.py` | `game_stats.reset()` + `game_stats.record_game_start(...)` |
| `board.shoot_bubble()` | `board.py` | `self.stats.record_shot()` |
| `board.kill_same_color()` | `board.py` | `self.stats.record_match(count)` |
| `board.remove_disjoint()` | `board.py` | `self.stats.record_disjoint_removal(count)` |
| `on_game_over()` | `draw.py` | `game_stats.finalize(win, ...)` then `game_stats.reset()` + `record_game_start()` |

### Passing Stats to Board

Add `stats` parameter to `Board.__init__()`:

```python
class Board:
    def __init__(self, stats=None):
        self.stats = stats
        ...
```

Then in `main()`:

```python
game_stats = GameStats()
board = Board(stats=game_stats)
```

Board methods call `self.stats.record_*()` with a guard: `if self.stats:` — keeps Board functional without stats (e.g. if swap.py reuses it).

---

## File Structure After Implementation

```
marbles/
├── draw.py
├── board.py
├── bubble.py
├── constants.py
├── utils.py
├── stats.py              # NEW — GameStats class + snapshot logic
├── stats.jsonl            # Created at runtime — game log (gitignored)
├── stats_snapshots/       # Created at runtime — backups (gitignored)
├── swap.py
├── README.md
├── SWAP_PLAN.md
├── MARBLES_PLAN.md
└── STATS_PLAN.md
```

Add to `.gitignore`:
```
stats.jsonl
stats_snapshots/
```

---

## Implementation Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Create `stats.py` with `GameStats` class, `append_stats()`, `snapshot_stats_file()` | ✅ Done |
| 2 | Add `stats` param to `Board.__init__()`, wire `record_shot`, `record_match`, `record_disjoint_removal` | ✅ Done |
| 3 | Update `draw.py` `main()`: create `GameStats`, pass to Board, call `snapshot_stats_file()` on startup | ✅ Done |
| 4 | Update `on_game_over()`: call `finalize()`, then `reset()` + `record_game_start()` for next game | ✅ Done |
| 5 | Add `.gitignore` entries | ✅ Done |
| 6 | Test: imports verified, runtime validation pending | ✅ Done |

---

## Summary of Changes

### New Files

**`stats.py`** — Self-contained stats module with:
- `GameStats` class tracking all per-game metrics in memory
  - `reset()` — clears all counters, sets `start_time` and `start_ts`
  - `record_game_start(bubble_count, color_count)` — captures initial board state
  - `record_shot()` — increments shot counter, logs timestamp for active time calculation
  - `record_match(match_size)` — increments hits, matches, destroyed-by-match; updates max match size
  - `record_disjoint_removal(count)` — tracks gravity-based bubble removals
  - `finalize(win, bubbles_remaining, rows_advanced)` — computes derived fields (duration, active time, accuracy), builds JSON record, appends to file
  - `_calc_active_time(end_ts)` — sums inter-shot gaps capped at 10s each
- `append_stats(record)` — writes one JSON line to `stats.jsonl`
- `snapshot_stats_file()` — copies `stats.jsonl` to `stats_snapshots/stats_YYYYMMDD_HHMMSS.jsonl`

**`.gitignore`** — Excludes `stats.jsonl`, `stats_snapshots/`, `__pycache__/`

### Modified Files

**`board.py`**
- `Board.__init__()` accepts `stats=None` parameter, stored as `self.stats`
- `shoot_bubble()` calls `self.stats.record_shot()` (guarded with `if self.stats`)
- `traverse()` calls `self.stats.record_match(match_count)` when a 3+ match is found
- `remove_disjoint()` counts disconnected bubbles and calls `self.stats.record_disjoint_removal(disjoint_count)`

**`draw.py`**
- Imports `GameStats` and `snapshot_stats_file` from `stats`
- New `start_new_game(board, game_stats)` helper — calls `reset()` + `record_game_start()`
- `on_game_over(board, game_stats, win)` — calls `finalize()` before board reinit, then `start_new_game()` for the next game
- `main()` — calls `snapshot_stats_file()` on startup, creates `GameStats`, passes to `Board(stats=game_stats)`, calls `start_new_game()` after first `board.init()`

### Data Flow

```
Game start → GameStats.reset() + record_game_start()
    ↓
Each shot → Board.shoot_bubble() → stats.record_shot()
    ↓
Match found → Board.traverse() → stats.record_match(count)
    ↓
Gravity removal → Board.remove_disjoint() → stats.record_disjoint_removal(count)
    ↓
Game over → on_game_over() → stats.finalize() → append to stats.jsonl
    ↓
Next game → board.init() + start_new_game()
```

On next launch, `snapshot_stats_file()` backs up the existing `stats.jsonl` before any new data is written.
