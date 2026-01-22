# Swap Game Implementation Plan

## Overview

Create a new match-3 puzzle game (`swap.py`) where players swap adjacent blocks to create matches of 3+ same-colored blocks in a row or column. Matched blocks are destroyed and blocks above fall down to fill the gaps.

## Game Mechanics

### Core Rules

1. **Grid**: Fixed rectangular grid (17x17) filled with colored blocks
2. **Swapping**: Click two adjacent blocks (horizontal or vertical) to swap them
3. **Matching**: If a swap creates 3+ same-colored blocks in a row or column, they are destroyed
4. **Invalid swap**: If a swap doesn't create any match, blocks swap back to original positions
5. **Gravity**: After matches are removed, blocks above fall down to fill empty spaces
6. **Refill**: New random blocks spawn at the top to fill remaining empty spaces
7. **Chain reactions**: Falling blocks may create new matches (cascades)

### User Interaction

| Action | Control |
|--------|---------|
| Select first block | Left-click on block |
| Swap with adjacent | Left-click on adjacent block |
| Cancel selection | Click elsewhere / Right-click |

---

## Reuse from `draw.py`

### Colors (copy as-is)
```python
BACKGROUND = (160, 192, 255)
PURPLE = (101, 35, 148)
BLUE = (1, 154, 255)
PINK = (249, 115, 223)
RED = (255, 20, 20)
GREEN = (101, 255, 1)
ORANGE = (254, 183, 42)

colors = [PINK, RED, PURPLE, BLUE, GREEN, ORANGE]
```

### Visual helpers (adapt)
- `border_color()` - darken color for block border
- `highlight_color()` - lighten color for highlight effect
- `load_bubble_image()` → rename to `load_block_image()` - draw block sprite

### Utility functions (adapt)
- `get_center(cx, cy)` - simplified for rectangular grid (no row offset)
- `get_distance()` - for animations
- `draw_multiline_text()` - for score display

---

## New Components

### 1. Constants

```python
BLOCK_SIZE = 50
BLOCK_SPACE = 4
GRID_WIDTH = 17
GRID_HEIGHT = 17
SCREEN_WIDTH = GRID_WIDTH * (BLOCK_SIZE + BLOCK_SPACE) + BLOCK_SPACE
SCREEN_HEIGHT = GRID_HEIGHT * (BLOCK_SIZE + BLOCK_SPACE) + BLOCK_SPACE + 100  # extra for score
```

### 2. Block Class (replaces Bubble)

```python
class Block(pygame.sprite.Sprite):
    def __init__(self, color, cx, cy):
        # Grid position (cx, cy)
        # Pixel position (x, y) - for animation
        # Target position - for smooth falling animation
        # Selected state - highlight when clicked
        # Falling state - animate gravity
```

**Key methods:**
- `update()` - handle animations (falling, swapping)
- `set_cell_pos(cx, cy)` - update grid position
- `animate_to(target_x, target_y)` - smooth movement
- `draw_selected()` - highlight outline when selected

### 3. Board Class (simplified state machine)

**States:**
```python
IDLE = 'IDLE'           # Waiting for player input
SWAPPING = 'SWAPPING'   # Animating swap
CHECKING = 'CHECKING'   # Looking for matches
REMOVING = 'REMOVING'   # Animating block removal
FALLING = 'FALLING'     # Blocks falling down
REFILLING = 'REFILLING' # New blocks spawning
```

**State flow:**
```
IDLE → (player swaps) → SWAPPING → CHECKING
                                      ↓
                              [no match] → swap back → IDLE
                              [match found] → REMOVING → FALLING → REFILLING
                                                                      ↓
                                                              → CHECKING (cascade)
                                                              → IDLE (no more matches)
```

**Key methods:**
- `init()` - fill grid with random blocks (ensure no initial matches)
- `get_block_at(cx, cy)` - get block from grid
- `swap(block1, block2)` - initiate swap animation
- `find_matches()` - scan rows and columns for 3+ matches
- `remove_matches()` - destroy matched blocks
- `apply_gravity()` - drop blocks to fill gaps
- `refill()` - spawn new blocks at top
- `is_adjacent(block1, block2)` - check if blocks are neighbors

### 4. Selection Logic

```python
selected_block = None

def on_click(pos):
    clicked_block = get_block_at_pixel(pos)
    if selected_block is None:
        selected_block = clicked_block
    elif is_adjacent(selected_block, clicked_block):
        swap(selected_block, clicked_block)
        selected_block = None
    else:
        selected_block = clicked_block  # new selection
```

### 5. Match Detection Algorithm

```python
def find_matches():
    matches = set()
    
    # Check horizontal matches
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH - 2):
            if grid[row][col] == grid[row][col+1] == grid[row][col+2]:
                # Extend match as far as possible
                matches.add((row, col), (row, col+1), (row, col+2), ...)
    
    # Check vertical matches
    for col in range(GRID_WIDTH):
        for row in range(GRID_HEIGHT - 2):
            if grid[row][col] == grid[row+1][col] == grid[row+2][col]:
                matches.add(...)
    
    return matches
```

### 6. Gravity System

```python
def apply_gravity():
    for col in range(GRID_WIDTH):
        # Get all non-empty blocks in column
        blocks_in_col = [grid[row][col] for row in range(GRID_HEIGHT) if grid[row][col]]
        
        # Place them at bottom, fill rest with None
        for row in range(GRID_HEIGHT):
            bottom_index = GRID_HEIGHT - 1 - row
            if row < len(blocks_in_col):
                grid[bottom_index] = blocks_in_col[-(row+1)]
            else:
                grid[bottom_index] = None
```

---

## Implementation Steps

### Phase 1: Basic Setup ✅
- [x] Create `swap.py` with pygame initialization
- [x] Copy colors and visual helper functions from `draw.py`
- [x] Implement `Block` class with basic rendering
- [x] Create grid and display blocks

### Phase 2: Selection & Swapping
- [x] Implement click detection to select blocks
- [x] Highlight selected block
- [x] Implement adjacent check
- [x] Animate swap between two blocks

### Phase 3: Match Detection
- [ ] Implement horizontal match detection
- [ ] Implement vertical match detection
- [ ] Animate block removal (fade out / shrink - reuse it from draw.py)

### Phase 4: Gravity & Refill
- [ ] Implement gravity (blocks fall down)
- [ ] Animate falling blocks
- [ ] Spawn new blocks at top
- [ ] Animate new blocks falling in

### Phase 5: Game Loop & Polish
- [ ] Implement cascade detection (chain reactions)
- [ ] Add invalid swap animation (swap back)
- [ ] Add score counter
- [ ] Ensure no initial matches on board setup
- [ ] Add shimmer/hover effects (reuse from bubbles)

---

## File Structure

```
marbles/
├── draw.py       # Original bubble shooter
├── swap.py       # New match-3 swap game
├── README.md
└── SWAP_PLAN.md  # This plan
```

---

## Optional Enhancements (Future)

- [ ] Score multipliers for chains
- [ ] Special blocks (bomb, row clear, color clear)
- [ ] Timer mode
- [ ] Move limit mode
- [ ] Sound effects
- [ ] Particle effects on match

---

## Questions to Resolve

1. Should swapping animate smoothly or be instant?
   - **Recommendation**: Smooth animation (looks better)

2. What happens if board has no valid moves?
   - **Recommendation**: Shuffle board or game over

3. Should we use square blocks or keep circular style?
   - **Recommendation**: Keep circular (reuse bubble visuals)

---

*Ready for review. Once approved, we'll implement phase by phase.*
