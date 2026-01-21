import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BUBBLE_SIZE = 40

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

class Bubble(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy, color):
        super().__init__()
        self.image = load_bubble_image(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
            self.dx = -self.dx
        if self.rect.top <= 0:
            self.dy = -self.dy

# Group for all bubbles
bubbles = pygame.sprite.Group()

def shoot_bubble():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30
    angle = math.atan2(mouse_y - y, mouse_x - x)
    dx = math.cos(angle) * 10
    dy = math.sin(angle) * -10
    color = random.choice(colors)
    bubble = Bubble(x, y, int(dx), int(dy), color)
    bubbles.add(bubble)

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            shoot_bubble()

    # Update game state
    bubbles.update()

    # Draw everything
    screen.fill(BLACK)
    bubbles.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()

