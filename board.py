import math
import random
import logging
import pygame

from constants import (
    BUBBLE_SIZE, GRID_WIDTH, GRID_HEIGHT, INIT_HEIGHT,
    SCREEN_WIDTH, SCREEN_HEIGHT, BUBBLE_SPACE,
    PREVIEW_BUBBLE_X, PREVIEW_BUBBLE_Y,
    GAME_OVER_EVENT, STATE_CHANGE_EVENT, TRAVERSE_EVENT,
    TRIES, GREY, COLORS, DEBUG,
)
from utils import get_center, get_distance, neighbour_cells
from bubble import Bubble

logger = logging.getLogger(__name__)


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
        self.speed = 12  # Default speed
        self.colors = list(COLORS)
        self._state = Board.RELOAD
        self.removing_bubbles = []
        self.step = 0
        self.tries = -1
        self.refresh_tries()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if DEBUG:
            logger.debug('Set state: old_state = %s, new_state = %s', self._state, state)
        self._state = state

    def trigger_game_over(self, win):
        logger.debug("Game over (win=%s)", win)
        event = pygame.event.Event(GAME_OVER_EVENT, message=win)
        pygame.event.post(event)

    def trigger_state_change(self, state):
        key = (self.state, state)
        if DEBUG:
            logger.debug('Trigger state change %s -> %s', *key)
        assert key in Board.VALID_STATES, 'Invalid key: %s' % (key,)
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
            bubble = Bubble(x, y, 0, 0, color, cx, cy, board=self)
            self.bubbles.add(bubble)

    def advance_preview_bubble(self):
        assert self.state is Board.RELOAD
        assert not self.preview_bubble
        self.shoot_bubble_to_target(
            self.second_preview_bubble,
            (PREVIEW_BUBBLE_X, PREVIEW_BUBBLE_Y),
            self.speed * 2
        )
        self.trigger_state_change(Board.ADVANCING)

    def create_second_preview_bubble(self):
        x, y = SCREEN_WIDTH // 4, SCREEN_HEIGHT - BUBBLE_SIZE - BUBBLE_SPACE
        color = random.choice(self.colors)
        self.second_preview_bubble = Bubble(x, y, 0, 0, color, -1, -1, board=self)
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
        bubble = Bubble(x, y, 0, 0, color, -1, -1, board=self)
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
        self.colors = list(COLORS)
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
        collided_bubbles = pygame.sprite.spritecollide(
            bubble, self.bubbles, False, pygame.sprite.collide_circle)
        if len(collided_bubbles) > 1:
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
            if bubble is self.second_preview_bubble:
                continue
            occupied.add((bubble.cx, bubble.cy))

        closest_cell = None
        closest_distance = None
        for cy in range(GRID_HEIGHT):
            for cx in range(GRID_WIDTH):
                if (cx, cy) in occupied:
                    continue
                x, y = get_center(cx, cy)
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

    def match_color_count(self, start_cell, grid_bubbles):
        cells = [start_cell]
        seen = {start_cell}
        count = 0
        while cells:
            cell = cells.pop(0)
            bubble = grid_bubbles[cell]
            count += 1
            for next_cell in neighbour_cells(cell):
                if next_cell in seen:
                    continue
                next_bubble = grid_bubbles.get(next_cell)
                if not next_bubble:
                    continue
                if next_bubble.color != bubble.color:
                    continue
                seen.add(next_cell)
                cells.append(next_cell)
        return count

    def kill_same_color(self, start_cell, grid_bubbles):
        assert self.state is Board.REMOVING_BUBBLES
        cells = [start_cell]
        seen = {start_cell}
        while cells:
            cell = cells.pop(0)
            bubble = grid_bubbles[cell]
            self.removing_bubbles.append(bubble)
            for next_cell in neighbour_cells(cell):
                if next_cell in seen:
                    continue
                next_bubble = grid_bubbles.get(next_cell)
                if not next_bubble:
                    continue
                if next_bubble.color != bubble.color:
                    continue
                seen.add(next_cell)
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
            for next_cell in neighbour_cells(cell):
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
        elif self.state is Board.RELOAD:
            if len(self.bubbles) == 1:  # Only second preview bubble left
                self.trigger_game_over(win=True)
            else:
                self.update_colors()
                self.advance_preview_bubble()
        elif self.state is Board.REMOVING_BUBBLES:
            self.check_removing_bubbles()
        elif self.state is Board.ADVANCING:
            if self.second_preview_bubble.rect.collidepoint((PREVIEW_BUBBLE_X, PREVIEW_BUBBLE_Y)):
                self.preview_bubble = self.second_preview_bubble
                self.create_second_preview_bubble()
                self.preview_bubble.x, self.preview_bubble.y = (PREVIEW_BUBBLE_X, PREVIEW_BUBBLE_Y)
                self.preview_bubble.dx = 0
                self.preview_bubble.dy = 0
                self.preview_bubble.shimmer = Bubble.SHIMMER_MAX
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
                bubble.start_shimmer(depth * 5)
            for next_cell in neighbour_cells(cell):
                if next_cell in seen:
                    continue
                seen.add(next_cell)
                if same_color:
                    next_bubble = grid_bubbles.get(next_cell)
                    if not next_bubble:
                        continue
                    if not bubble or next_bubble.color != bubble.color:
                        continue
                cells.append((next_cell, depth + 1))
