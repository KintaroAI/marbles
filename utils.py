import math
import logging
import pygame

from constants import BUBBLE_SIZE, BUBBLE_SPACE, GRID_WIDTH, GRID_HEIGHT

logger = logging.getLogger(__name__)


def border_color(color):
    return tuple([0.7*x for x in color])


def check_color_max(c):
    if c > 255:
        return 255
    return c


def highlight_color(color):
    return tuple([check_color_max(1.3*x) for x in color])


def load_bubble_image(color):
    surface = pygame.Surface((BUBBLE_SIZE, BUBBLE_SIZE), pygame.SRCALPHA)
    border_width = 6
    pygame.draw.circle(surface, border_color(color), (BUBBLE_SIZE // 2, BUBBLE_SIZE // 2), BUBBLE_SIZE // 2)
    pygame.draw.circle(surface, color, (BUBBLE_SIZE // 2, BUBBLE_SIZE // 2), BUBBLE_SIZE // 2 - border_width)
    pygame.draw.circle(surface, highlight_color(color), (BUBBLE_SIZE // 2, BUBBLE_SIZE // 2), BUBBLE_SIZE // 5)
    return surface


def get_center(cx, cy):
    shift = cy % 2
    x = cx * (BUBBLE_SIZE + BUBBLE_SPACE//2) + (BUBBLE_SIZE // 2 + BUBBLE_SPACE // 2) * (shift + 1)
    y = cy * (BUBBLE_SIZE * 0.8 + BUBBLE_SPACE) + BUBBLE_SIZE // 2 + BUBBLE_SPACE
    return x, y


def get_distance(point1, point2):
    return math.sqrt(
        (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2
    )


def simple_neighbour_cells(cell):
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
def neighbour_cells(cell):
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


def draw_multiline_text(surface, text, pos, font, color=(255, 255, 255), line_spacing=6):
    x, y = pos
    lines = text
    if isinstance(text, str):
        lines = [line for line in text.split('\n')]

    for line in lines:
        line_surface = font.render(line, True, color)
        surface.blit(line_surface, (x, y))
        y += font.get_height() + line_spacing
