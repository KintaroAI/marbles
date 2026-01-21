import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Constants
BUBBLE_SIZE = 60
BUBBLE_SPACE = 10
GRID_WIDTH = 17
GRID_HEIGHT = 15
INIT_HEIGHT = 9

SCREEN_WIDTH = (BUBBLE_SIZE + BUBBLE_SPACE // 2) * GRID_WIDTH + BUBBLE_SIZE // 2 + BUBBLE_SPACE // 2
SCREEN_HEIGHT = (BUBBLE_SIZE + BUBBLE_SPACE // 2) * GRID_HEIGHT

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

def get_center(cx, cy):
    shift = cy % 2
    x = cx * (BUBBLE_SIZE + BUBBLE_SPACE//2) + (BUBBLE_SIZE // 2 + BUBBLE_SPACE // 2) * (shift + 1)
    y = cy * (BUBBLE_SIZE + BUBBLE_SPACE//5) + BUBBLE_SIZE // 2 + BUBBLE_SPACE // 5
    return x, y

def get_distance(point1, point2):
    return math.sqrt(
        (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2
    )

def simple_neigbour_cells(cell):
    cx, cy = cell
    for next_cx, next_cy in [
        (cx, cy+1),
        (cx, cy-1),
        (cx+1, cy),
        (cx-1, cy),
        (cx+1, cy+1),
        (cx+1, cy-1),
        (cx-1, cy+1),
        (cx-1, cy-1),
    ]:
        if next_cx < 0 or next_cy < 0:
            continue
        if next_cx >= GRID_WIDTH or next_cy >= GRID_HEIGHT:
            continue
        yield (next_cx, next_cy)

#  1  2  3
#    4  5  6
#  7  8  9
#   10 11 12
def neigbour_cells(cell):
    cx, cy = cell
    if cy % 2 == 1: # 5 is selected
        neighbours = [
            #(cx-1, cy-1),   # 1
            (cx, cy-1),     # 2
            (cx+1, cy-1),   # 3
            (cx-1, cy),   # 4
            (cx+1, cy),   # 6
            #(cx-1, cy+1),   # 7
            (cx, cy+1),     # 8
            (cx+1, cy+1),   # 9
        ]
    else: # 8 is selected
        neighbours = [
            (cx-1, cy-1),   # 4
            (cx, cy-1),     # 5
            #(cx+1, cy-1),   # 6
            (cx-1, cy),   # 7
            (cx+1, cy),   # 9
            (cx-1, cy+1),   # 10
            (cx, cy+1),     # 11
            #(cx+1, cy+1),   # 12
        ]
    for next_cx, next_cy in neighbours:
        if next_cx < 0 or next_cy < 0:
            continue
        if next_cx >= GRID_WIDTH or next_cy >= GRID_HEIGHT:
            continue
        yield (next_cx, next_cy)

class Board:
    def __init__(self):
        self.next_bubble = None
        self.current_bubble = None
        # Group for all bubbles
        self.bubbles = pygame.sprite.Group()
        # Speed modifier
        self.speed = 3  # Default speed
        self.colors = colors

    def create_next_bubble(self):
        assert not self.next_bubble
        x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30
        color = random.choice(self.colors)
        self.next_bubble = Bubble(x, y, 0, 0, color)
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
        for cy in range(INIT_HEIGHT):
            for cx in range(GRID_WIDTH):
                color = random.choice(self.colors)
                x, y = get_center(cx, cy)
                bubble = Bubble(x, y, 0, 0, color)
                self.bubbles.add(bubble)

    def check_collisions(self):
        if not self.current_bubble:
            return
        bubble = self.current_bubble
        if get_distance(
            (self.current_bubble.x, self.current_bubble.y),
            (self.current_bubble.x, 0),
        ) < BUBBLE_SIZE * 0.7:
            self.handle_top_collision()
            return
        # Check for collision with other bubbles
        # The first False is for not killing the bubble being checked; the second is to use the collide_circle method
        collided_bubbles = pygame.sprite.spritecollide(
            bubble, self.bubbles, False, pygame.sprite.collide_circle)
        if len(collided_bubbles) > 1:  # It always finds itself, so more than 1 means it hit another bubble
            self.handle_bubble_collision(collided_bubbles)

    def handle_top_collision(self):
        self.snap()

    def handle_bubble_collision(self, collided_bubbles):
        for bubble in collided_bubbles:
            if bubble is self.current_bubble:
                continue
            distance = get_distance(
                (self.current_bubble.x, self.current_bubble.y),
                (bubble.x, bubble.y)
            )
            if distance < BUBBLE_SIZE * 0.7:
                self.snap()
                break

    def snap(self):
        assert self.current_bubble
        occupied = set()
        for bubble in self.bubbles:
            if bubble is self.current_bubble:
                continue
            occupied.add((bubble.x, bubble.y))

        closest_coordinates = None
        closest_distance = None
        for cy in range(GRID_HEIGHT):
            for cx in range(GRID_WIDTH):
                x, y = get_center(cx, cy)
                if (x, y) in occupied:
                    continue
                distance = get_distance((self.current_bubble.x, self.current_bubble.y), (x, y))
                if not closest_distance or closest_distance > distance:
                    closest_coordinates = (x, y)
                    closest_distance = distance
        assert closest_distance, occupied
        self.current_bubble.x, self.current_bubble.y = closest_coordinates
        self.current_bubble.dx = 0
        self.current_bubble.dy = 0
        self.current_bubble = None
        self.traverse(closest_coordinates)

    def traverse(self, point):
        # build grid
        grid_bubbles = self.build_grid()
        for cell, bubble in grid_bubbles.items():
            if not bubble:
                continue
            if (bubble.x, bubble.y) == point:
                start_cell = cell
        if self.match_color_count(start_cell, grid_bubbles) >= 3:
            self.kill_same_color(start_cell, grid_bubbles)

    def build_grid(self):
        position_to_bubble = {}
        for v in self.bubbles:
            position_to_bubble[(v.x, v.y)] = v
        grid_bubbles = {}
        start_cell = None
        for cy in range(GRID_HEIGHT):
            for cx in range(GRID_WIDTH):
                x, y = get_center(cx, cy)
                grid_bubbles[(cx, cy)] =  position_to_bubble.get((x, y))
        return grid_bubbles

    def match_color_count(self, start_cell, grid_bubbles):
        cells = [start_cell]
        seen = set()
        count = 0
        while cells:
            cell = cells.pop(0)
            seen.add(cell)
            bubble = grid_bubbles[cell]
            count += 1
            for next_cell in neigbour_cells(cell):
                if next_cell in seen:
                    continue
                next_bubble = grid_bubbles.get(next_cell)
                if not next_bubble:
                    continue
                if next_bubble.color != bubble.color:
                    continue
                cells.append(next_cell)
        return count

    def kill_same_color(self, start_cell, grid_bubbles):
        cells = [start_cell]
        seen = set()
        while cells:
            cell = cells.pop(0)
            seen.add(cell)
            bubble = grid_bubbles[cell]
            bubble.kill()
            for next_cell in neigbour_cells(cell):
                if next_cell in seen:
                    continue
                next_bubble = grid_bubbles.get(next_cell)
                if not next_bubble:
                    continue
                if next_bubble.color != bubble.color:
                    continue
                cells.append(next_cell)

    def remove_disjoint(self):
        grid_bubbles = self.build_grid()
        cells = []
        for cell, bubble in grid_bubbles.items():
            if not bubble:
                continue
            if cell[1] == 0:
                cells.append(cell)

        seen = set()
        while cells:
            cell = cells.pop(0)
            if cell in seen:
                continue
            seen.add(cell)
            bubble = grid_bubbles[cell]
            for next_cell in neigbour_cells(cell):
                if next_cell in seen:
                    continue
                next_bubble = grid_bubbles.get(next_cell)
                if not next_bubble:
                    continue
                cells.append(next_cell)

        for cell, bubble in grid_bubbles.items():
            if not bubble:
                continue
            if cell not in seen:
                bubble.kill()


    def check_state(self):
        # Current bubble become part of the board or destroyed
        if self.current_bubble is None and self.next_bubble is None:
            self.remove_disjoint()
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
        self.rect.x = self.x - BUBBLE_SIZE//2
        self.rect.y = self.y - BUBBLE_SIZE//2
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

