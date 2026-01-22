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
    
    def __init__(self, color, cx, cy):
        super().__init__()
        self.color = color
        self.cx = cx
        self.cy = cy
        self.x, self.y = get_center(cx, cy)
        self.image = load_block_image(color)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.selected = False
    
    def set_cell_pos(self, cx, cy):
        """Update grid position"""
        self.cx = cx
        self.cy = cy
        self.x, self.y = get_center(cx, cy)
        self.rect.center = (self.x, self.y)
    
    def update(self):
        """Update block state"""
        self.rect.center = (self.x, self.y)
    
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
    
    def __init__(self):
        self.blocks = pygame.sprite.Group()
        self.grid = {}  # (cx, cy) -> Block
        self.selected_block = None
    
    def init(self):
        """Initialize the board with random blocks"""
        # Clear existing blocks
        for block in list(self.blocks):
            block.kill()
        self.grid = {}
        self.selected_block = None
        
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
    
    def draw(self, surface):
        """Draw all blocks and selection highlight"""
        self.blocks.draw(surface)
        # Draw selection highlight
        if self.selected_block:
            self.selected_block.draw_selected(surface)
    
    def update(self):
        """Update all blocks"""
        self.blocks.update()


# Create board
board = Board()
board.init()

# Main game loop
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    clock.tick(fps)
    
    # Update
    board.update()
    
    # Draw
    screen.fill(BACKGROUND)
    board.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
