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
    
    def __init__(self, color, cx, cy):
        super().__init__()
        self.color = color
        self.cx = cx
        self.cy = cy
        self.x, self.y = get_center(cx, cy)
        self.target_x = self.x
        self.target_y = self.y
        self.image = load_block_image(color)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.selected = False
        self.swapping = False
    
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
    
    def update(self):
        """Update block state and handle animations"""
        # Smooth movement towards target
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
        
        self.rect.center = (int(self.x), int(self.y))
    
    def is_animating(self):
        """Check if block is currently animating"""
        return self.swapping
    
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
    
    def __init__(self):
        self.blocks = pygame.sprite.Group()
        self.grid = {}  # (cx, cy) -> Block
        self.selected_block = None
        self.state = Board.IDLE
        self.swapping_blocks = []  # Blocks currently being swapped
    
    def init(self):
        """Initialize the board with random blocks"""
        # Clear existing blocks
        for block in list(self.blocks):
            block.kill()
        self.grid = {}
        self.selected_block = None
        self.state = Board.IDLE
        self.swapping_blocks = []
        
        # Fill grid with random blocks
        for cy in range(GRID_HEIGHT):
            for cx in range(GRID_WIDTH):
                color = random.choice(colors)
                block = Block(color, cx, cy)
                self.blocks.add(block)
                self.grid[(cx, cy)] = block
    
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
            self.swapping_blocks = []
            self.state = Board.IDLE
    
    def draw(self, surface):
        """Draw all blocks and selection highlight"""
        self.blocks.draw(surface)
        # Draw selection highlight
        if self.selected_block:
            self.selected_block.draw_selected(surface)
    
    def update(self):
        """Update all blocks"""
        self.blocks.update()
        self.check_swap_complete()


# Create board
board = Board()
board.init()

# Main game loop
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                board.on_click(event.pos)
            elif event.button == pygame.BUTTON_RIGHT:
                board.on_right_click()
    
    clock.tick(fps)
    
    # Update
    board.update()
    
    # Draw
    screen.fill(BACKGROUND)
    board.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
