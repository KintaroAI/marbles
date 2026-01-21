import pygame
import sys
import math
import random
import time

# Initialize Pygame
pygame.init()

# Constants
BUBBLE_SIZE = 80
BUBBLE_SPACE = 16
GRID_WIDTH = 17
GRID_HEIGHT = 15
INIT_HEIGHT = 9

SCREEN_WIDTH = (BUBBLE_SIZE + BUBBLE_SPACE // 2) * GRID_WIDTH + BUBBLE_SIZE // 2 + BUBBLE_SPACE
SCREEN_HEIGHT = (BUBBLE_SIZE + BUBBLE_SPACE // 2) * GRID_HEIGHT

TRIES = [5, 4, 3, 2, 1, 0]

# Colors
BACKGROUND = (160, 192, 255)
PURPLE= (101, 35, 148)
BLUE = (1, 154, 255)
PINK = (249, 115, 223)
RED = (255, 20, 20)
GREEN = (101, 255, 1)
ORANGE = (254, 183, 42)

# Setup the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bubbles")
clock = pygame.time.Clock()
fps = 100  # Lower frame rate to reduce CPU load


def border_color(color):
    return tuple([0.7*x for x in color])

def check_color_max(c):
    if c > 255:
        return 255
    return c

def highlight_color(color):
    return tuple([check_color_max(1.3*x) for x in color])

# Load bubble images or use simple circles
def load_bubble_image(color):
    # Placeholder for loading a bubble image
    surface = pygame.Surface((BUBBLE_SIZE, BUBBLE_SIZE), pygame.SRCALPHA)
    border_width = 6
    pygame.draw.circle(surface, border_color(color), (BUBBLE_SIZE // 2, BUBBLE_SIZE // 2), BUBBLE_SIZE // 2)
    pygame.draw.circle(surface, color, (BUBBLE_SIZE // 2, BUBBLE_SIZE // 2), BUBBLE_SIZE // 2 - border_width)
    pygame.draw.circle(surface, highlight_color(color), (BUBBLE_SIZE // 2, BUBBLE_SIZE // 2), BUBBLE_SIZE // 5)
    return surface

# Bubble colors
colors = [PINK, RED, PURPLE, BLUE, GREEN, ORANGE]

def get_center(cx, cy):
    shift = cy % 2
    x = cx * (BUBBLE_SIZE + BUBBLE_SPACE//2) + (BUBBLE_SIZE // 2 + BUBBLE_SPACE // 2) * (shift + 1)
    y = cy * (BUBBLE_SIZE *0.8 + BUBBLE_SPACE) + BUBBLE_SIZE // 2 + BUBBLE_SPACE
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
    RELOAD = 0
    READY = 1
    SHOOT = 2
    REMOVING_BUBBLES = 3
    def __init__(self):
        self.next_bubble = None
        self.current_bubble = None
        # Group for all bubbles
        self.bubbles = pygame.sprite.Group()
        # Speed modifier
        self.speed = 15  # Default speed
        self.colors = colors
        self.state = Board.RELOAD
        self.removing_bubbles = []
        self.step = 0
        self.tries = -1
        self.refresh_tries()

    def refresh_tries(self):
        self.tries = TRIES[self.step % len(TRIES)]

    def advance(self):
        # Add new row on top
        grid = self.build_grid()
        for cell, bubble in grid.items():
            if not bubble:
                continue
            cx, cy = cell
            x, y = get_center(cx, cy + 1)
            bubble.x = x
            bubble.y = y
        cy = 0
        for cx in range(GRID_WIDTH):
            color = random.choice(self.colors)
            x, y = get_center(cx, cy)
            bubble = Bubble(x, y, 0, 0, color)
            self.bubbles.add(bubble)

    def create_next_bubble(self):
        assert self.state is Board.RELOAD
        assert not self.next_bubble
        x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30
        color = random.choice(self.colors)
        self.next_bubble = Bubble(x, y, 0, 0, color)
        self.bubbles.add(self.next_bubble)
        self.state = Board.READY

    def shoot_bubble(self):
        if not self.next_bubble:
            return
        assert self.state is Board.READY
        x, y = self.next_bubble.x, self.next_bubble.y
        mouse_x, mouse_y = pygame.mouse.get_pos()
        angle = math.atan2(mouse_y - y, mouse_x - x)
        self.next_bubble.dx = math.cos(angle) * self.speed
        self.next_bubble.dy = math.sin(angle) * self.speed
        self.current_bubble = self.next_bubble
        self.next_bubble = None
        self.state = Board.SHOOT

    def update_colors(self):
        assert self.state is Board.RELOAD
        updated_colors = set()
        for bubble in self.bubbles:
            updated_colors.add(bubble.color)
        self.colors = list(updated_colors)

    def init(self):
        self.state = Board.RELOAD
        self.colors = colors
        for _ in range(INIT_HEIGHT):
            self.advance()

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
        assert self.state is Board.SHOOT
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
        self.state = Board.REMOVING_BUBBLES
        self.traverse(closest_coordinates)

    def traverse(self, point):
        assert self.state is Board.REMOVING_BUBBLES
        # build grid
        grid_bubbles = self.build_grid()
        for cell, bubble in grid_bubbles.items():
            if not bubble:
                continue
            if (bubble.x, bubble.y) == point:
                start_cell = cell
        if self.match_color_count(start_cell, grid_bubbles) >= 3:
            self.kill_same_color(start_cell, grid_bubbles)
        else:
            self.tries -= 1
            if self.tries < 0:
                self.step += 1
                self.advance()
                self.refresh_tries()


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
        assert self.state is Board.REMOVING_BUBBLES
        cells = [start_cell]
        seen = set()
        while cells:
            cell = cells.pop(0)
            seen.add(cell)
            bubble = grid_bubbles[cell]
            self.removing_bubbles.append(bubble)
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
        assert self.state is Board.RELOAD
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
                self.state = Board.REMOVING_BUBBLES
                self.removing_bubbles.append(bubble)

    def check_removing_bubbles(self):
        assert self.state is Board.REMOVING_BUBBLES
        if not self.removing_bubbles:
            self.state = Board.RELOAD
            return
        bubble = self.removing_bubbles[0]
        if not bubble.alive():
            self.removing_bubbles.pop(0)
            return
        bubble.blow_step()

    def check_state(self):
        if self.state is Board.RELOAD:
            self.remove_disjoint()

        if self.state is Board.RELOAD:
            # New game
            if len(self.bubbles) == 0:
                self.init()
            else:
                self.update_colors()
                self.create_next_bubble()
        if self.state is Board.REMOVING_BUBBLES:
            self.check_removing_bubbles()



class Bubble(pygame.sprite.Sprite):
    MAX_ENERGY = 10
    def __init__(self, x, y, dx, dy, color):
        super().__init__()
        self.color = color
        self.image = load_bubble_image(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.x = x
        self.y = y
        self.energy = Bubble.MAX_ENERGY

    def update(self, mouse_pos):
        self.x = 1.0*self.x + self.dx
        self.y = 1.0*self.y + self.dy
        self.rect.x = self.x - BUBBLE_SIZE//2
        self.rect.y = self.y - BUBBLE_SIZE//2
        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
            self.dx = -self.dx
        if self.rect.top <= 0:
            self.dy = -self.dy
        if self.rect.collidepoint(mouse_pos):
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)

    def blow_step(self):
        self.energy -= 1
        self.y += 1.0
        self.image.set_alpha(255.0*self.energy/Bubble.MAX_ENERGY)
        if self.energy <= 0:
            self.kill()


# Main game loop
running = True
board = Board()
board.init()
force_refresh = False
last_changed_time = time.time()
last_pos = None
while running:
    mouse_pos = pygame.mouse.get_pos()
    if mouse_pos != last_pos:
        last_pos = mouse_pos
        last_changed_time = time.time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                board.shoot_bubble()
            if event.button == pygame.BUTTON_RIGHT:
                board.advance()
                force_refresh = True

    if board.state != Board.READY or force_refresh or last_changed_time > time.time() - 20.0:
        force_refresh = False

        # Update game state
        board.bubbles.update(mouse_pos)

        board.check_collisions()

        board.check_state()

        # Draw everything
        screen.fill(BACKGROUND)
        board.bubbles.draw(screen)
        pygame.display.flip()
    clock.tick(fps)

pygame.quit()
sys.exit()

