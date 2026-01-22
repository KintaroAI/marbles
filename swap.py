import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
BLOCK_SIZE = 50
BLOCK_SPACE = 4
GRID_WIDTH = 17
GRID_HEIGHT = 17
SCREEN_WIDTH = GRID_WIDTH * (BLOCK_SIZE + BLOCK_SPACE) + BLOCK_SPACE
SCREEN_HEIGHT = GRID_HEIGHT * (BLOCK_SIZE + BLOCK_SPACE) + BLOCK_SPACE + 100  # extra for score

# Colors (from draw.py)
BACKGROUND = (160, 192, 255)
PURPLE = (101, 35, 148)
BLUE = (1, 154, 255)
PINK = (249, 115, 223)
RED = (255, 20, 20)
GREEN = (101, 255, 1)
ORANGE = (254, 183, 42)

colors = [PINK, RED, PURPLE, BLUE, GREEN, ORANGE]

# Setup the display
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.HWSURFACE | pygame.DOUBLEBUF
)
pygame.display.set_caption("Swap")
clock = pygame.time.Clock()
fps = 60


def border_color(color):
    """Darken color for block border"""
    return tuple([int(0.7 * x) for x in color])


def check_color_max(c):
    if c > 255:
        return 255
    return int(c)


def highlight_color(color):
    """Lighten color for highlight effect"""
    return tuple([check_color_max(1.3 * x) for x in color])


def load_block_image(color):
    """Create a block/bubble sprite"""
    surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    border_width = 4
    pygame.draw.circle(surface, border_color(color), (BLOCK_SIZE // 2, BLOCK_SIZE // 2), BLOCK_SIZE // 2)
    pygame.draw.circle(surface, color, (BLOCK_SIZE // 2, BLOCK_SIZE // 2), BLOCK_SIZE // 2 - border_width)
    pygame.draw.circle(surface, highlight_color(color), (BLOCK_SIZE // 2, BLOCK_SIZE // 2), BLOCK_SIZE // 5)
    return surface


def get_center(cx, cy):
    """Get pixel coordinates for grid cell (cx, cy)"""
    x = cx * (BLOCK_SIZE + BLOCK_SPACE) + BLOCK_SIZE // 2 + BLOCK_SPACE
    y = cy * (BLOCK_SIZE + BLOCK_SPACE) + BLOCK_SIZE // 2 + BLOCK_SPACE
    return x, y


def get_cell_from_pos(pos):
    """Get grid cell (cx, cy) from pixel position"""
    px, py = pos
    cx = (px - BLOCK_SPACE) // (BLOCK_SIZE + BLOCK_SPACE)
    cy = (py - BLOCK_SPACE) // (BLOCK_SIZE + BLOCK_SPACE)
    if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT:
        return cx, cy
    return None


class Block(pygame.sprite.Sprite):
    """A single colored block on the grid"""
    SWAP_SPEED = 8  # pixels per frame
    FALL_SPEED = 12  # pixels per frame for falling
    REMOVE_SPEED = 3  # shrink speed per frame
    SHIMMER_MAX = 80
    SHIMMER_STEP = 4
    
    def __init__(self, color, cx, cy):
        super().__init__()
        self.color = color
        self.cx = cx
        self.cy = cy
        self.x, self.y = get_center(cx, cy)
        self.target_x = self.x
        self.target_y = self.y
        self.base_image = load_block_image(color)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.selected = False
        self.swapping = False
        self.falling = False
        self.removing = False
        self.scale = 1.0  # For shrink animation
        self.shimmer = 0
        self.shimmer_direction = 0
        self.hovered = False
    
    def set_cell_pos(self, cx, cy):
        """Update grid position"""
        self.cx = cx
        self.cy = cy
        self.x, self.y = get_center(cx, cy)
        self.target_x = self.x
        self.target_y = self.y
        self.rect.center = (self.x, self.y)
    
    def animate_to(self, target_x, target_y):
        """Start smooth animation to target position"""
        self.target_x = target_x
        self.target_y = target_y
        self.swapping = True
    
    def update(self, mouse_pos=None):
        """Update block state and handle animations"""
        # Smooth movement towards target (swapping)
        if self.swapping:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if distance < Block.SWAP_SPEED:
                # Arrived at target
                self.x = self.target_x
                self.y = self.target_y
                self.swapping = False
            else:
                # Move towards target
                self.x += dx / distance * Block.SWAP_SPEED
                self.y += dy / distance * Block.SWAP_SPEED
        
        # Falling animation
        if self.falling:
            dy = self.target_y - self.y
            
            if abs(dy) < Block.FALL_SPEED:
                # Arrived at target
                self.y = self.target_y
                self.falling = False
            else:
                # Fall down
                self.y += Block.FALL_SPEED if dy > 0 else -Block.FALL_SPEED
        
        # Shrink animation for removal
        if self.removing:
            self.scale -= 0.08
            if self.scale <= 0:
                self.scale = 0
                self.removing = False
                self.kill()
            else:
                # Scale down the image
                new_size = int(BLOCK_SIZE * self.scale)
                if new_size > 0:
                    self.image = pygame.transform.scale(self.base_image, (new_size, new_size))
                    self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        
        # Shimmer effect
        if self.shimmer_direction != 0:
            self.shimmer += self.shimmer_direction
            if self.shimmer >= Block.SHIMMER_MAX:
                self.shimmer = Block.SHIMMER_MAX
                self.shimmer_direction = -Block.SHIMMER_STEP
            elif self.shimmer <= 0:
                self.shimmer = 0
                self.shimmer_direction = 0
        
        # Check hover
        if mouse_pos and not self.removing:
            was_hovered = self.hovered
            self.hovered = self.rect.collidepoint(mouse_pos)
            if self.hovered and not was_hovered and self.shimmer_direction == 0:
                self.shimmer_direction = Block.SHIMMER_STEP
        
        # Apply shimmer alpha
        if not self.removing and self.shimmer > 0:
            self.image = self.base_image.copy()
            self.image.set_alpha(255 - self.shimmer)
        
        self.rect.center = (int(self.x), int(self.y))
    
    def start_removal(self):
        """Start the removal animation"""
        self.removing = True
    
    def start_falling(self, target_y):
        """Start falling animation to target y position"""
        self.target_y = target_y
        self.falling = True
    
    def is_animating(self):
        """Check if block is currently animating"""
        return self.swapping or self.falling or self.removing
    
    def draw_selected(self, surface):
        """Draw selection highlight around block"""
        if self.selected:
            pygame.draw.circle(
                surface, 
                (255, 255, 255), 
                (int(self.x), int(self.y)), 
                BLOCK_SIZE // 2 + 3, 
                3
            )


class Board:
    """Game board managing the grid of blocks"""
    
    # States
    IDLE = 'IDLE'
    SWAPPING = 'SWAPPING'
    CHECKING = 'CHECKING'
    REMOVING = 'REMOVING'
    FALLING = 'FALLING'
    
    def __init__(self):
        self.blocks = pygame.sprite.Group()
        self.grid = {}  # (cx, cy) -> Block
        self.selected_block = None
        self.state = Board.IDLE
        self.swapping_blocks = []  # Blocks currently being swapped
        self.removing_blocks = []  # Blocks being removed
        self.falling_blocks = []   # Blocks currently falling
        self.last_swapped = []  # Track last swapped blocks for invalid swap reversal
        self.score = 0
        self.combo = 0  # Chain combo multiplier
    
    def init(self):
        """Initialize the board with random blocks"""
        # Clear existing blocks
        for block in list(self.blocks):
            block.kill()
        self.grid = {}
        self.selected_block = None
        self.state = Board.IDLE
        self.swapping_blocks = []
        self.removing_blocks = []
        self.falling_blocks = []
        self.last_swapped = []
        self.score = 0
        self.combo = 0
        
        # Fill grid with random blocks, avoiding initial matches
        for cy in range(GRID_HEIGHT):
            for cx in range(GRID_WIDTH):
                color = self.get_safe_color(cx, cy)
                block = Block(color, cx, cy)
                self.blocks.add(block)
                self.grid[(cx, cy)] = block
    
    def get_safe_color(self, cx, cy):
        """Get a color that won't create a match at (cx, cy)"""
        forbidden = set()
        
        # Check horizontal - if two blocks to the left have same color, forbid it
        if cx >= 2:
            left1 = self.grid.get((cx - 1, cy))
            left2 = self.grid.get((cx - 2, cy))
            if left1 and left2 and left1.color == left2.color:
                forbidden.add(left1.color)
        
        # Check vertical - if two blocks above have same color, forbid it
        if cy >= 2:
            up1 = self.grid.get((cx, cy - 1))
            up2 = self.grid.get((cx, cy - 2))
            if up1 and up2 and up1.color == up2.color:
                forbidden.add(up1.color)
        
        # Choose from allowed colors
        allowed = [c for c in colors if c not in forbidden]
        if not allowed:
            allowed = colors  # Fallback if all forbidden (shouldn't happen)
        return random.choice(allowed)
    
    def get_block_at(self, cx, cy):
        """Get block at grid position"""
        return self.grid.get((cx, cy))
    
    def is_adjacent(self, block1, block2):
        """Check if two blocks are adjacent (horizontally or vertically)"""
        dx = abs(block1.cx - block2.cx)
        dy = abs(block1.cy - block2.cy)
        # Adjacent means exactly one cell apart in one direction only
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)
    
    def swap(self, block1, block2):
        """Initiate swap animation between two blocks"""
        if self.state != Board.IDLE:
            return
        
        self.state = Board.SWAPPING
        self.swapping_blocks = [block1, block2]
        
        # Animate blocks to each other's positions
        block1.animate_to(block2.x, block2.y)
        block2.animate_to(block1.x, block1.y)
        
        # Swap grid positions
        block1.cx, block2.cx = block2.cx, block1.cx
        block1.cy, block2.cy = block2.cy, block1.cy
        self.grid[(block1.cx, block1.cy)] = block1
        self.grid[(block2.cx, block2.cy)] = block2
        
        # Clear selection
        if self.selected_block:
            self.selected_block.selected = False
            self.selected_block = None
    
    def on_click(self, pos):
        """Handle click at pixel position"""
        if self.state != Board.IDLE:
            return
        
        cell = get_cell_from_pos(pos)
        if cell is None:
            # Clicked outside grid - deselect
            if self.selected_block:
                self.selected_block.selected = False
                self.selected_block = None
            return
        
        cx, cy = cell
        clicked_block = self.get_block_at(cx, cy)
        
        if clicked_block is None:
            return
        
        if self.selected_block is None:
            # First selection
            self.selected_block = clicked_block
            clicked_block.selected = True
        elif clicked_block == self.selected_block:
            # Clicked same block - deselect
            self.selected_block.selected = False
            self.selected_block = None
        elif self.is_adjacent(self.selected_block, clicked_block):
            # Swap adjacent blocks
            self.selected_block.selected = False
            self.swap(self.selected_block, clicked_block)
        else:
            # Select new block
            self.selected_block.selected = False
            self.selected_block = clicked_block
            clicked_block.selected = True
    
    def on_right_click(self):
        """Handle right click - cancel selection"""
        if self.selected_block:
            self.selected_block.selected = False
            self.selected_block = None
    
    def check_swap_complete(self):
        """Check if swap animation is complete"""
        if self.state != Board.SWAPPING:
            return
        
        # Check if all swapping blocks have finished animating
        all_done = all(not block.is_animating() for block in self.swapping_blocks)
        
        if all_done:
            # Update target positions to match grid
            for block in self.swapping_blocks:
                block.target_x, block.target_y = get_center(block.cx, block.cy)
            self.last_swapped = self.swapping_blocks[:]
            self.swapping_blocks = []
            self.state = Board.CHECKING
    
    def find_matches(self):
        """Find all matching blocks (3+ in a row horizontally or vertically)"""
        matches = set()
        
        # Check horizontal matches
        for cy in range(GRID_HEIGHT):
            run_start = 0
            run_color = None
            for cx in range(GRID_WIDTH + 1):
                block = self.grid.get((cx, cy))
                current_color = block.color if block else None
                
                if current_color == run_color and current_color is not None:
                    # Continue the run
                    pass
                else:
                    # End of run - check if it's a match (3+)
                    run_length = cx - run_start
                    if run_length >= 3 and run_color is not None:
                        for x in range(run_start, cx):
                            matches.add((x, cy))
                    # Start new run
                    run_start = cx
                    run_color = current_color
        
        # Check vertical matches
        for cx in range(GRID_WIDTH):
            run_start = 0
            run_color = None
            for cy in range(GRID_HEIGHT + 1):
                block = self.grid.get((cx, cy))
                current_color = block.color if block else None
                
                if current_color == run_color and current_color is not None:
                    # Continue the run
                    pass
                else:
                    # End of run - check if it's a match (3+)
                    run_length = cy - run_start
                    if run_length >= 3 and run_color is not None:
                        for y in range(run_start, cy):
                            matches.add((cx, y))
                    # Start new run
                    run_start = cy
                    run_color = current_color
        
        return matches
    
    def remove_matches(self, matches):
        """Start removal animation for matched blocks"""
        self.removing_blocks = []
        for cx, cy in matches:
            block = self.grid.get((cx, cy))
            if block:
                block.start_removal()
                self.removing_blocks.append(block)
                self.grid[(cx, cy)] = None
        
        # Update score with combo multiplier
        self.combo += 1
        points = len(matches) * 10 * self.combo
        self.score += points
        
        self.state = Board.REMOVING
    
    def check_removing_complete(self):
        """Check if all removal animations are complete"""
        if self.state != Board.REMOVING:
            return
        
        # Check if all removing blocks have finished animating
        all_done = all(not block.is_animating() for block in self.removing_blocks)
        
        if all_done:
            self.removing_blocks = []
            self.state = Board.FALLING
    
    def apply_gravity_and_refill(self):
        """
        Make blocks fall down to fill empty spaces, one step at a time.
        - Start from bottom row, check for empty cells
        - If empty, pull block from cell above
        - If top cell is empty, spawn new random block
        - Repeat until no empty cells
        """
        self.falling_blocks = []
        
        # Process each column
        for cx in range(GRID_WIDTH):
            # Start from bottom row, go up
            for cy in range(GRID_HEIGHT - 1, -1, -1):
                if self.grid.get((cx, cy)) is None:
                    # Empty cell - try to pull block from above
                    if cy > 0:
                        # Look for a block above
                        above_block = self.grid.get((cx, cy - 1))
                        if above_block:
                            # Pull block down
                            self.grid[(cx, cy - 1)] = None
                            self.grid[(cx, cy)] = above_block
                            above_block.cy = cy
                            target_x, target_y = get_center(cx, cy)
                            above_block.target_x = target_x
                            above_block.start_falling(target_y)
                            self.falling_blocks.append(above_block)
                    
                    # If this is the top row (cy == 0) and it's empty, spawn new block
                    if cy == 0 and self.grid.get((cx, 0)) is None:
                        color = random.choice(colors)
                        # Create block above the grid
                        block = Block(color, cx, -1)
                        start_x, start_y = get_center(cx, -1)
                        block.x = start_x
                        block.y = start_y
                        # Set target to top row
                        block.cx = cx
                        block.cy = 0
                        target_x, target_y = get_center(cx, 0)
                        block.target_x = target_x
                        block.start_falling(target_y)
                        
                        self.blocks.add(block)
                        self.grid[(cx, 0)] = block
                        self.falling_blocks.append(block)
    
    def has_empty_cells(self):
        """Check if there are any empty cells in the grid"""
        for cy in range(GRID_HEIGHT):
            for cx in range(GRID_WIDTH):
                if self.grid.get((cx, cy)) is None:
                    return True
        return False
    
    def check_falling_complete(self):
        """Check if all falling animations are complete"""
        if self.state != Board.FALLING:
            return
        
        # If no blocks are falling, nothing to check
        if not self.falling_blocks:
            return
        
        # Check if all falling blocks have finished animating
        all_done = all(not block.is_animating() for block in self.falling_blocks)
        
        if all_done:
            self.falling_blocks = []
            # Check if there are still empty cells - if so, continue falling
            if self.has_empty_cells():
                self.apply_gravity_and_refill()
            else:
                # All filled, check for new matches (cascades)
                self.state = Board.CHECKING
    
    def swap_back(self):
        """Swap back the last swapped blocks (invalid move)"""
        if len(self.last_swapped) == 2:
            block1, block2 = self.last_swapped
            self.state = Board.SWAPPING
            self.swapping_blocks = [block1, block2]
            
            # Animate blocks back to original positions
            block1.animate_to(block2.x, block2.y)
            block2.animate_to(block1.x, block1.y)
            
            # Swap grid positions back
            block1.cx, block2.cx = block2.cx, block1.cx
            block1.cy, block2.cy = block2.cy, block1.cy
            self.grid[(block1.cx, block1.cy)] = block1
            self.grid[(block2.cx, block2.cy)] = block2
            
            self.last_swapped = []
    
    def check_state(self):
        """Main state machine logic"""
        if self.state == Board.CHECKING:
            matches = self.find_matches()
            if matches:
                self.remove_matches(matches)
                self.last_swapped = []  # Valid move, clear swap history
            else:
                # No matches - swap back if this was a player swap
                if self.last_swapped:
                    self.swap_back()
                else:
                    # Reset combo when chain ends
                    self.combo = 0
                    self.state = Board.IDLE
        
        elif self.state == Board.FALLING:
            # Only start gravity if no blocks are currently falling
            if not self.falling_blocks:
                self.apply_gravity_and_refill()
                if not self.falling_blocks:
                    # No blocks moved, check for cascades
                    self.state = Board.CHECKING
    
    def draw(self, surface):
        """Draw all blocks and selection highlight"""
        self.blocks.draw(surface)
        # Draw selection highlight
        if self.selected_block:
            self.selected_block.draw_selected(surface)
    
    def update(self, mouse_pos=None):
        """Update all blocks"""
        for block in self.blocks:
            block.update(mouse_pos)
        self.check_swap_complete()
        self.check_removing_complete()
        self.check_falling_complete()
        self.check_state()


# Fonts
score_font = pygame.font.Font(None, 48)
combo_font = pygame.font.Font(None, 36)

# Create board
board = Board()
board.init()

# Main game loop
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                board.on_click(event.pos)
            elif event.button == pygame.BUTTON_RIGHT:
                board.on_right_click()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Reset game
                board.init()
    
    clock.tick(fps)
    
    # Update
    board.update(mouse_pos)
    
    # Draw
    screen.fill(BACKGROUND)
    board.draw(screen)
    
    # Draw score
    score_y = GRID_HEIGHT * (BLOCK_SIZE + BLOCK_SPACE) + BLOCK_SPACE + 20
    score_text = score_font.render(f"Score: {board.score}", True, (50, 50, 100))
    screen.blit(score_text, (20, score_y))
    
    # Draw combo indicator
    if board.combo > 1:
        combo_text = combo_font.render(f"Combo x{board.combo}!", True, (200, 50, 50))
        screen.blit(combo_text, (20, score_y + 40))
    
    # Draw state (for debugging, can be removed)
    # state_text = combo_font.render(f"State: {board.state}", True, (100, 100, 100))
    # screen.blit(state_text, (SCREEN_WIDTH - 200, score_y))
    
    pygame.display.flip()

pygame.quit()
sys.exit()
