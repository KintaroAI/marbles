# Bubble Shooter (`draw.py`) — Refactor & Bug Fix Plan

## Overview

Refactor `draw.py` to fix bugs, eliminate global coupling, and improve code structure — while keeping the game behavior identical.

---

## Phase 1: Bug Fixes

### 1.1 BFS duplicate-visit bug in `match_color_count()` and `kill_same_color()`

**Problem:** Both functions add cells to `seen` only when popped, not when enqueued. Two neighbors can both enqueue the same cell before it's visited, inflating the count (or adding a bubble to `removing_bubbles` twice).

**Fix:** Add cells to `seen` when they are appended to the queue, not when popped.

```python
# Before (buggy)
while cells:
    cell = cells.pop(0)
    seen.add(cell)          # too late — duplicates already in queue
    ...
    for next_cell in neigbour_cells(cell):
        if next_cell in seen:
            continue
        cells.append(next_cell)

# After (fixed)
seen.add(start_cell)
while cells:
    cell = cells.pop(0)
    ...
    for next_cell in neigbour_cells(cell):
        if next_cell in seen:
            continue
        seen.add(next_cell)   # mark on discovery
        cells.append(next_cell)
```

**Files:** `draw.py` — `match_color_count()` (line ~400) and `kill_same_color()` (line ~420)

### 1.2 Float vs int comparison in `snap()`

**Problem:** `occupied` set is built from `bubble.x, bubble.y` (floats after movement), but compared against `get_center()` results (ints). Floating-point drift after movement means lookups can miss, allowing overlaps.

**Fix:** Build the occupied set from grid cell coordinates `(bubble.cx, bubble.cy)` instead of pixel positions, and compare against cell coords.

```python
# Before
occupied = set()
for bubble in self.bubbles:
    occupied.add((bubble.x, bubble.y))
...
x, y = get_center(cx, cy)
if (x, y) in occupied:
    continue

# After
occupied = set()
for bubble in self.bubbles:
    occupied.add((bubble.cx, bubble.cy))
...
if (cx, cy) in occupied:
    continue
```

**Files:** `draw.py` — `snap()` (line ~339)

### 1.3 `check_state()` uses `if` chain instead of `elif`

**Problem:** A state change in one `if` block can immediately trigger the next block in the same frame, leading to double-processing.

**Fix:** Change subsequent `if` blocks to `elif` so only one state branch runs per frame.

**Files:** `draw.py` — `check_state()` (line ~485)

---

## Phase 2: Remove Dead Code & Cleanup

### 2.1 Delete `build_grid_old()`

Unused method. Remove entirely.

**Files:** `draw.py` — lines ~388-398

### 2.2 Remove unnecessary `1.0*` cast

```python
# Before
self.x = 1.0*self.x + self.dx

# After
self.x = self.x + self.dx
```

**Files:** `draw.py` — `Bubble.update()` (line ~558)

### 2.3 Fix typo: `neigbour_cells` → `neighbour_cells`

Rename both `neigbour_cells` and `simple_neigbour_cells` across the file.

**Files:** `draw.py` — all references

### 2.4 Add comment explaining `TRIES`

```python
# Number of shots before a new row advances, cycling through this list each step
TRIES = [5, 4, 3, 2, 1, 0]
```

---

## Phase 3: Decouple Globals

### 3.1 Remove global `board` reference from `Bubble`

**Problem:** `Bubble.update()` (line 574) calls `board.start_shimmer()` and `Bubble.set_cell_pos()` (line 594) calls `board.trigger_game_over()` — both reach into a module-level global.

**Fix:** Give `Bubble` a reference to its board via constructor parameter, stored as `self.board`.

```python
class Bubble(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy, color, cx, cy, board=None):
        ...
        self.board = board
```

Then replace `board.start_shimmer(...)` with `self.board.start_shimmer(...)` and `board.trigger_game_over(...)` with `self.board.trigger_game_over(...)`.

Update all `Bubble(...)` construction sites in `Board` to pass `self` as the board.

**Files:** `draw.py` — `Bubble.__init__()`, `Bubble.update()`, `Bubble.set_cell_pos()`, and all `Bubble(...)` calls in `Board`

### 3.2 Pass `board` into event handlers

Change `on_game_over()` and `on_state_change()` signatures (already take board — this is fine as-is, just verify the game loop passes it correctly).

---

## Phase 4: Structural Refactor — Split Into Modules

Split the single 700-line file into focused modules.

### Target structure

```
marbles/
├── draw.py              # Entry point — game loop only
├── bubble.py            # Bubble sprite class
├── board.py             # Board class (game logic + state machine)
├── constants.py         # All constants, colors, screen setup
├── utils.py             # get_center, get_distance, neighbour_cells, draw_multiline_text, color helpers
├── swap.py              # Swap game (unchanged)
├── README.md
├── SWAP_PLAN.md
└── MARBLES_PLAN.md
```

### 4.1 Extract `constants.py`

Move all constants, color definitions, and derived values:
- `BUBBLE_SIZE`, `BUBBLE_SPACE`, `GRID_WIDTH`, `GRID_HEIGHT`, etc.
- Color tuples: `BACKGROUND`, `PURPLE`, `BLUE`, `PINK`, `RED`, `GREEN`, `ORANGE`, `GREY`
- `PREVIEW_BUBBLE_X`, `PREVIEW_BUBBLE_Y`
- `TRIES`
- `colors` list
- `DEBUG` flag
- Custom event IDs: `GAME_OVER_EVENT`, `STATE_CHANGE_EVENT`, `TRAVERSE_EVENT`
- `SHOW_STATS`

**Do NOT** move pygame initialization or screen creation here — those stay in `draw.py`.

### 4.2 Extract `utils.py`

Move pure utility functions:
- `border_color()`
- `check_color_max()`
- `highlight_color()`
- `load_bubble_image()`
- `get_center()`
- `get_distance()`
- `neighbour_cells()` (renamed)
- `simple_neighbour_cells()` (renamed)
- `draw_multiline_text()`
- `probe()`

### 4.3 Extract `bubble.py`

Move `Bubble` class. Import from `constants` and `utils`.

### 4.4 Extract `board.py`

Move `Board` class. Import from `constants`, `utils`, and `bubble`.

### 4.5 Slim down `draw.py`

Keep only:
- Pygame initialization (`pygame.init()`, screen, clock)
- Game loop
- Event handling
- `on_game_over()`, `on_state_change()`
- Imports from the new modules

---

## Phase 5: Minor Improvements

### 5.1 Replace `probe()` with standard logging

`inspect.stack()` is expensive. Replace with Python's `logging` module at DEBUG level. This removes the `inspect` import entirely.

### 5.2 Wrap module-level code in `main()`

```python
def main():
    pygame.init()
    screen = pygame.display.set_mode(...)
    ...
    # game loop

if __name__ == '__main__':
    main()
```

This makes `draw.py` importable without side effects.

---

## Implementation Order

| Step | Phase | Description | Risk |
|------|-------|-------------|------|
| 1 | 1.1 | Fix BFS duplicate-visit bug | Low — localized change |
| 2 | 1.2 | Fix float/int snap comparison | Low — localized change |
| 3 | 1.3 | Fix `if` → `elif` in check_state | Low — behavior change, test carefully |
| 4 | 2.* | Dead code removal, typo fix, cleanup | Low — no behavior change |
| 5 | 3.* | Decouple global board from Bubble | Medium — touches many call sites |
| 6 | 4.* | Split into modules | Medium — file reorganization |
| 7 | 5.* | Logging, main() wrapper | Low — final polish |

Each step should be a separate commit, tested by running the game after each change.

---

*Ready for review. Once approved, we'll implement step by step.*
