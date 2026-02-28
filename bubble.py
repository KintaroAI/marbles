import logging
import pygame

from constants import (
    BUBBLE_SIZE, SCREEN_WIDTH, GAME_OVER_GRID_HEIGHT, DEBUG,
)
from utils import load_bubble_image, get_center

logger = logging.getLogger(__name__)


class Bubble(pygame.sprite.Sprite):
    MAX_ENERGY = 10
    SHIMMER_MAX = 127
    SHIMMER_STEP = 5

    def __init__(self, x, y, dx, dy, color, cx, cy, board=None):
        super().__init__()
        self.board = board
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
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        self.rect.x = self.x - BUBBLE_SIZE // 2
        self.rect.y = self.y - BUBBLE_SIZE // 2
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
        if self.rect.collidepoint(mouse_pos) and not self.shimmer and self.board:
            self.board.start_shimmer(start_cell=(self.cx, self.cy), same_color=True)
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
        if (cy + 1) >= GAME_OVER_GRID_HEIGHT:
            if DEBUG:
                logger.debug('cx = %s, cy = %s', cx, cy)
            if self.board:
                self.board.trigger_game_over(win=False)

    def set_speed(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def blow_step(self):
        self.energy -= 1
        self.y += 1.0
        self.image.set_alpha(255.0 * self.energy / Bubble.MAX_ENERGY)
        if self.energy <= 0:
            self.kill()
