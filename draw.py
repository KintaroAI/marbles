import pygame
import sys
import math
import random
import time
import inspect

# Initialize Pygame
pygame.init()

# Constants
BUBBLE_SIZE = 80
BUBBLE_SPACE = 16
GRID_WIDTH = 17
GRID_HEIGHT = 17
GAME_OVER_GRID_HEIGHT = 16
INIT_HEIGHT = 9
SHOW_STATS = True

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
GREY = (200, 200, 200)

PREVIEW_BUBBLE_X = SCREEN_WIDTH // 2
PREVIEW_BUBBLE_Y = SCREEN_HEIGHT - BUBBLE_SIZE - BUBBLE_SPACE

# Setup the display
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    #pygame.HWSURFACE | pygame.DOUBLEBUF
)
pygame.display.set_caption("Bubbles")
clock = pygame.time.Clock()
fps = 100  # Lower frame rate to reduce CPU load

GAME_OVER_EVENT = pygame.USEREVENT
STATE_CHANGE_EVENT = pygame.USEREVENT + 1
TRAVERSE_EVENT = pygame.USEREVENT + 2


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

def probe(name):
    stack = inspect.stack()
    # The caller information is in the first position after the current stack frame
    for caller in stack:
        frame = caller[0]
        info = inspect.getframeinfo(frame)
        # Print caller information
        print(f"{name}. Called at line {info.lineno}")

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
    REMOVE_DISJOINT = 'REMOVE_DISJOINT'
    RELOAD = 'RELOAD'
    ADVANCING = 'ADVANCING'  # second preview bubble -> preview bubble
    READY = 'READY'
    SHOOT = 'SHOOT'
    REMOVING_BUBBLES = 'REMOVING_BUBBLES'
    VALID_STATES = {
        (RELOAD, ADVANCING),
        (ADVANCING, READY),
        (READY, SHOOT),
        (SHOOT, REMOVING_BUBBLES),
        (REMOVING_BUBBLES, REMOVE_DISJOINT),
        (REMOVE_DISJOINT, REMOVING_BUBBLES),
        (REMOVE_DISJOINT, RELOAD),
    }
    def __init__(self):
        self.second_preview_bubble = None
        self.preview_bubble = None
        self.current_bubble = None
        # Group for all bubbles
        self.bubbles = pygame.sprite.Group()
        self.elements = pygame.sprite.Group()
        # Speed modifier
        self.speed = 15  # Default speed
        self.colors = colors
        self._state = Board.RELOAD
        self.removing_bubbles = []
        self.step = 0
        self.tries = -1
        self.refresh_tries()


    @property
    def state(self):
        return self._state  # Getter method

    @state.setter
    def state(self, state):
        print('Set state: old_state = %s, new_state = %s' % (self._state, state))
        # probe('Set state')
        self._state = state

    def trigger_game_over(self, win):
        probe("Game over")
        event = pygame.event.Event(GAME_OVER_EVENT, message=win)
        pygame.event.post(event)

    def trigger_state_change(self, state):
        key = (self.state, state)
        print('Trigger state change %s -> %s' % key)
        assert key in Board.VALID_STATES, 'Invalid key: %s' % (key,)
        # TODO: Check if state change from old state to new state is allowed.
        event = pygame.event.Event(STATE_CHANGE_EVENT, message=(self.state, state))
        pygame.event.post(event)

    def trigger_traverse(self, cell):
        event = pygame.event.Event(TRAVERSE_EVENT, message=cell)
        pygame.event.post(event)

    def refresh_tries(self):
        self.tries = TRIES[self.step % len(TRIES)]

    def advance(self):
        # Add new row on top
        grid = self.build_grid()
        for cell, bubble in grid.items():
            if not bubble:
                continue
            cx, cy = cell
            cy += 1
            bubble.set_cell_pos((cx, cy))

        cy = 0
        for cx in range(GRID_WIDTH):
            color = random.choice(self.colors)
            x, y = get_center(cx, cy)
            bubble = Bubble(x, y, 0, 0, color, cx, cy)
            self.bubbles.add(bubble)

    def advance_preview_bubble(self):
        assert self.state is Board.RELOAD
        assert not self.preview_bubble
        self.shoot_bubble_to_target(
            self.second_preview_bubble,
            (PREVIEW_BUBBLE_X, PREVIEW_BUBBLE_Y),
            self.speed*2
        )
        self.trigger_state_change(Board.ADVANCING)

    def create_second_preview_bubble(self):
        x, y = SCREEN_WIDTH // 4, SCREEN_HEIGHT - BUBBLE_SIZE - BUBBLE_SPACE
        color = random.choice(self.colors)
        self.second_preview_bubble = Bubble(x, y, 0, 0, color, -1, -1)
        self.second_preview_bubble.shimmer = Bubble.SHIMMER_MAX
        self.bubbles.add(self.second_preview_bubble)

    def shoot_bubble(self):
        if not self.preview_bubble:
            return
        assert self.state is Board.READY
        self.shoot_bubble_to_target(self.preview_bubble, pygame.mouse.get_pos())
        self.current_bubble = self.preview_bubble
        self.preview_bubble = None
        self.trigger_state_change(Board.SHOOT)

    def shoot_bubble_to_target(self, bubble, target, speed=None):
        if speed is None:
            speed = self.speed
        x, y = bubble.x, bubble.y
        target_x, target_y = target
        angle = math.atan2(target_y - y, target_x - x)
        bubble.set_speed(
            math.cos(angle) * speed,
            math.sin(angle) * speed
        )

    def update_colors(self):
        assert self.state is Board.RELOAD
        updated_colors = set()
        for bubble in self.bubbles:
            updated_colors.add(bubble.color)
        self.colors = list(updated_colors)

    def create_tries_counter_bubble(self):
        x, y = SCREEN_WIDTH // 6, SCREEN_HEIGHT - BUBBLE_SIZE - BUBBLE_SPACE
        color = GREY
        bubble = Bubble(x, y, 0, 0, color, -1, -1)
        bubble.shimmer = Bubble.SHIMMER_MAX
        self.elements.add(bubble)


    def init(self):
        pygame.event.clear()
        self.step = 0
        self.tries = -1
        self.second_preview_bubble = None
        self.preview_bubble = None
        self.current_bubble = None
        self.refresh_tries()
        self.state = Board.RELOAD
        self.colors = colors
        for bubble in list(self.bubbles):
            bubble.kill()
        for element in list(self.elements):
            element.kill()
        for _ in range(INIT_HEIGHT):
            self.advance()
        self.create_second_preview_bubble()
        self.create_tries_counter_bubble()

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
            if bubble is self.second_preview_bubble:
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

        closest_cell = None
        closest_distance = None
        for cy in range(GRID_HEIGHT):
            for cx in range(GRID_WIDTH):
                x, y = get_center(cx, cy)
                if (x, y) in occupied:
                    continue
                distance = get_distance((self.current_bubble.x, self.current_bubble.y), (x, y))
                if not closest_distance or closest_distance > distance:
                    closest_distance = distance
                    closest_cell = (cx, cy)
        assert closest_distance, occupied
        cx, cy = closest_cell
        self.current_bubble.set_cell_pos(closest_cell)
        self.current_bubble.set_speed(0, 0)
        self.current_bubble = None
        self.trigger_state_change(Board.REMOVING_BUBBLES)
        self.trigger_traverse(closest_cell)

    def traverse(self, start_cell):
        assert self.state is Board.REMOVING_BUBBLES
        grid_bubbles = self.build_grid()
        if self.match_color_count(start_cell, grid_bubbles) >= 3:
            self.kill_same_color(start_cell, grid_bubbles)
        else:
            self.tries -= 1
            if self.tries < 0:
                self.step += 1
                self.advance()
                self.refresh_tries()


    def build_grid(self):
        grid_bubbles = {}
        for bubble in self.bubbles:
            if bubble in [self.current_bubble, self.preview_bubble, self.second_preview_bubble]:
                continue
            grid_bubbles[(bubble.cx, bubble.cy)] = bubble
        return grid_bubbles

    def build_grid_old(self):
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
        assert self.state is Board.REMOVE_DISJOINT
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
                self.removing_bubbles.append(bubble)
        if self.removing_bubbles:
            self.trigger_state_change(Board.REMOVING_BUBBLES)
        else:
            self.trigger_state_change(Board.RELOAD)

    def check_removing_bubbles(self):
        assert self.state is Board.REMOVING_BUBBLES
        if not self.removing_bubbles:
            self.trigger_state_change(Board.REMOVE_DISJOINT)
            return
        bubble = self.removing_bubbles[0]
        if not bubble.alive():
            self.removing_bubbles.pop(0)
            return
        bubble.blow_step()

    def check_state(self):
        if self.state is Board.REMOVE_DISJOINT:
            self.remove_disjoint()

        if self.state is Board.RELOAD:
            # New game
            if len(self.bubbles) == 1:  # Only second preview bubble left
                self.trigger_game_over(win=True)
            else:
                self.update_colors()
                self.advance_preview_bubble()
        if self.state is Board.REMOVING_BUBBLES:
            self.check_removing_bubbles()
        if self.state is Board.ADVANCING:
            if self.second_preview_bubble.rect.collidepoint((PREVIEW_BUBBLE_X, PREVIEW_BUBBLE_Y)):
                self.preview_bubble = self.second_preview_bubble
                self.create_second_preview_bubble()
                self.preview_bubble.x, self.preview_bubble.y = (PREVIEW_BUBBLE_X, PREVIEW_BUBBLE_Y)
                self.preview_bubble.dx = 0
                self.preview_bubble.dy = 0
                self.preview_bubble.shimmer = Bubble.SHIMMER_MAX
                #self.state = Board.READY
                self.trigger_state_change(Board.READY)


    def start_shimmer(self, start_cell=(0, 0), same_color=False):
        grid_bubbles = self.build_grid()
        cells = [(start_cell, 0)]
        seen = set()
        while cells:
            cell, depth = cells.pop(0)
            seen.add(cell)
            bubble = grid_bubbles.get(cell)
            if bubble:
                bubble.start_shimmer(depth*5)
            for next_cell in neigbour_cells(cell):
                if next_cell in seen:
                    continue
                seen.add(next_cell)
                if same_color:
                    next_bubble = grid_bubbles.get(next_cell)
                    if not next_bubble:
                        continue
                    if not bubble or next_bubble.color != bubble.color:
                        continue
                cells.append((next_cell, depth+1))



class Bubble(pygame.sprite.Sprite):
    MAX_ENERGY = 10
    SHIMMER_MAX = 127
    SHIMMER_STEP = 5
    def __init__(self, x, y, dx, dy, color, cx, cy):
        super().__init__()
        self.color = color
        self.image = load_bubble_image(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.x = x
        self.y = y
        self.cx = cx
        self.cy = cy
        self.energy = Bubble.MAX_ENERGY
        self.shimmer = 0
        self.shimmer_direction = -Bubble.SHIMMER_STEP
        self.shimmer_start_count = None

    def start_shimmer(self, after_ticks=0):
        self.shimmer_start_count = after_ticks

    def update(self, mouse_pos):
        self.x = 1.0*self.x + self.dx
        self.y = 1.0*self.y + self.dy
        self.rect.x = self.x - BUBBLE_SIZE//2
        self.rect.y = self.y - BUBBLE_SIZE//2
        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
            self.dx = -self.dx
        if self.rect.top <= 0:
            self.dy = -self.dy

        self.shimmer += self.shimmer_direction
        if self.shimmer < 0:
            self.shimmer = 0
        if self.shimmer >= Bubble.SHIMMER_MAX:
            self.shimmer = Bubble.SHIMMER_MAX
            self.shimmer_direction = -Bubble.SHIMMER_STEP
        if self.rect.collidepoint(mouse_pos) and not self.shimmer:
            board.start_shimmer(start_cell=(self.cx, self.cy), same_color=True)
        if self.shimmer_start_count is not None:
            if self.shimmer_start_count <= 0:
                self.shimmer_start_count = None
                self.shimmer_direction = Bubble.SHIMMER_STEP
            else:
                self.shimmer_start_count -= 1
        self.image.set_alpha(255 - self.shimmer)

    def set_cell_pos(self, cell):
        cx, cy = cell
        x, y = get_center(cx, cy)
        self.x = x
        self.y = y
        self.cx = cx
        self.cy = cy
        #print(cx, cy, GAME_OVER_GRID_HEIGHT)
        if (cy + 1) >= GAME_OVER_GRID_HEIGHT:
            print('cx = %s, cy = %s' % (cx, cy))
            board.trigger_game_over(win=False)

    def set_speed(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def blow_step(self):
        self.energy -= 1
        self.y += 1.0
        self.image.set_alpha(255.0*self.energy/Bubble.MAX_ENERGY)
        if self.energy <= 0:
            self.kill()

def draw_multiline_text(surface, text, pos, font, color=(255, 255, 255), line_spacing=6):
    x, y = pos
    lines = text
    if isinstance(text, str):
        lines = [line for line in text.split('\n')]

    for line in lines:
        line_surface = font.render(line, True, color)
        surface.blit(line_surface, (x, y))
        y += font.get_height() + line_spacing  # Move y position for the next line

def on_game_over(board, win):
    board.init()
    board.start_shimmer()

def on_state_change(board, from_state, to_state):
    assert board.state == from_state, '%s != %s' % (board.state, from_state)
    print('State change %s -> %s' % (from_state, to_state))
    board.state = to_state

# Main game loop
running = True
board = Board()
board.init()
force_refresh = False
last_changed_time = time.time()
last_pos = None
board.start_shimmer()

# Text info
stats_font = pygame.font.Font(None, 36)
tries_font = pygame.font.Font(None, 80)
#stats = []
pause = False
while running:
    mouse_pos = pygame.mouse.get_pos()
    if mouse_pos != last_pos:
        last_pos = mouse_pos
        last_changed_time = time.time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == GAME_OVER_EVENT:
            on_game_over(board, event.message)
            break
        if event.type == STATE_CHANGE_EVENT:
            on_state_change(board, *(event.message))
        if event.type == TRAVERSE_EVENT:
            board.traverse(event.message)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                board.shoot_bubble()
            if event.button == pygame.BUTTON_RIGHT:
                #board.start_shimmer()
                #force_refresh = True
                pause = not pause

    clock.tick(fps)
    if pause:
        continue

    if board.state != Board.READY or force_refresh or last_changed_time > time.time() - 20.0:
        force_refresh = False

        if not int(random.random()*100000):
            board.start_shimmer()

        # Update game state
        board.bubbles.update(mouse_pos)

        board.check_collisions()

        board.check_state()

        # Draw everything
        screen.fill(BACKGROUND)
        board.bubbles.draw(screen)
        board.elements.draw(screen)
        tries_text_color = (125, 125, 125)
        tries_text = tries_font.render('%s' % board.tries, True, tries_text_color)
        tries_text_rect = tries_text.get_rect(center=(SCREEN_WIDTH // 6, SCREEN_HEIGHT - BUBBLE_SIZE - BUBBLE_SPACE))
        screen.blit(tries_text, tries_text_rect)

        if SHOW_STATS:
            stats = [
                'board.state = %s' % board.state,
                'board.tries = %s' % board.tries,
                'bubbles count = %s' % len(board.bubbles),
            ]
            #if len(stats) > 50:
            #    stats.pop(0)
            draw_multiline_text(screen, stats, (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 200), stats_font)
        pygame.display.flip()

pygame.quit()
sys.exit()

