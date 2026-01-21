import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Constants
BUBBLE_SIZE = 40
BUBBLE_SPACE = 10
GRID_WIDTH = 17
GRID_HEIGHT = 15
INIT_HEIGHT = 9

SCREEN_WIDTH = (BUBBLE_SIZE + BUBBLE_SPACE // 2) * GRID_WIDTH - BUBBLE_SPACE // 2
SCREEN_HEIGHT = (BUBBLE_SIZE + BUBBLE_SPACE // 2) * GRID_HEIGHT - BUBBLE_SPACE // 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Setup the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bubbles")

# Load bubble images or use simple circles
def load_bubble_image(color):
    # Placeholder for loading a bubble image
    surface = pygame.Surface((BUBBLE_SIZE, BUBBLE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(surface, color, (BUBBLE_SIZE // 2, BUBBLE_SIZE // 2), BUBBLE_SIZE // 2)
    return surface

# Bubble colors
colors = [WHITE, (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

class Board:
    def __init__(self):
        self.next_bubble = None
        self.current_bubble = None
        # Group for all bubbles
        self.bubbles = pygame.sprite.Group()
        # Speed modifier
        self.speed = 1  # Default speed
        self.colors = colors


    def create_next_bubble(self):
        assert not self.next_bubble
        x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30
        color = random.choice(self.colors)
        self.next_bubble= Bubble(x, y, 0, 0, color)
        self.bubbles.add(self.next_bubble)

    def shoot_bubble(self):
        if not self.next_bubble:
            return
        x, y = self.next_bubble.x, self.next_bubble.y
        mouse_x, mouse_y = pygame.mouse.get_pos()
        angle = math.atan2(mouse_y - y, mouse_x - x)
        self.next_bubble.dx = math.cos(angle) * self.speed
        self.next_bubble.dy = math.sin(angle) * self.speed
        self.current_bubble = self.next_bubble
        self.next_bubble = None

    def update_colors(self):
        updated_colors = set()
        for bubble in self.bubbles:
            updated_colors.add(bubble.color)
        self.colors = list(updated_colors)

    def init(self):
        self.colors = colors
        if not self.next_bubble:
            self.create_next_bubble()
        for y in range(INIT_HEIGHT):
            for x in range(GRID_WIDTH):
                color = random.choice(self.colors)
                bubble = Bubble(
                    x * (BUBBLE_SIZE + BUBBLE_SPACE//2),
                    y * (BUBBLE_SIZE + BUBBLE_SPACE//2),
                    0,
                    0,
                    color)
                self.bubbles.add(bubble)

    def check_collisions(self):
        if not self.current_bubble:
            return
        bubble = self.current_bubble
        # Check for collision with other bubbles
        # The first False is for not killing the bubble being checked; the second is to use the collide_circle method
        collided_bubbles = pygame.sprite.spritecollide(bubble, self.bubbles, False, pygame.sprite.collide_circle)
        if len(collided_bubbles) > 1:  # It always finds itself, so more than 1 means it hit another bubble
            self.handle_collision(collided_bubbles)

    def handle_collision(self, collided_bubbles):
        # Simple collision handling: remove the bubble or add other logic
        for hit in collided_bubbles:
            if hit != self.current_bubble:  # Avoid killing the bubble itself
                if hit.color == self.current_bubble.color:
                    hit.kill()  # Remove the collided bubble

    def check_state(self):
        # Current bubble become part of the board or destroyed
        if self.current_bubble is None and self.next_bubble is None:
            # New game
            if len(self.bubbles) == 0:
                self.init()
            else:
                self.update_colors()
                self.create_next_bubble()



class Bubble(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy, color):
        super().__init__()
        self.color = color
        self.image = load_bubble_image(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.x = x
        self.y = y

    def update(self):
        self.x = 1.0*self.x + self.dx
        self.y = 1.0*self.y + self.dy
        self.rect.x = self.x
        self.rect.y = self.y
        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
            self.dx = -self.dx
        if self.rect.top <= 0:
            self.dy = -self.dy
        if self.rect.bottom >= SCREEN_HEIGHT + BUBBLE_SIZE:
            if self is board.current_bubble:
                board.current_bubble = None
            self.kill()  # This removes the Sprite from all Groups it belongs to





# Main game loop
running = True
board = Board()
board.init()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            board.shoot_bubble()

    # Update game state
    board.bubbles.update()

    board.check_collisions()

    board.check_state()

    # Draw everything
    screen.fill(BLACK)
    board.bubbles.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()

