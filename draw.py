import pygame
import sys
import random
import time
import logging

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BUBBLE_SIZE, BUBBLE_SPACE,
    BACKGROUND, SHOW_STATS,
    GAME_OVER_EVENT, STATE_CHANGE_EVENT, TRAVERSE_EVENT,
    DEBUG,
)
from utils import draw_multiline_text
from board import Board

logger = logging.getLogger(__name__)


def on_game_over(board, win):
    board.init()
    board.start_shimmer()


def on_state_change(board, from_state, to_state):
    assert board.state == from_state, '%s != %s' % (board.state, from_state)
    if DEBUG:
        logger.debug('State change %s -> %s', from_state, to_state)
    board.state = to_state


def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.HWSURFACE | pygame.DOUBLEBUF
    )
    pygame.display.set_caption("Bubbles")
    clock = pygame.time.Clock()
    fps = 120

    board = Board()
    board.init()
    force_refresh = False
    last_changed_time = time.time()
    last_pos = None
    board.start_shimmer()

    stats_font = pygame.font.Font(None, 36)
    tries_font = pygame.font.Font(None, 80)
    pause = False
    running = True

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
                    pause = not pause

        clock.tick(fps)
        if pause:
            continue

        if board.state != Board.READY or force_refresh or last_changed_time > time.time() - 20.0:
            force_refresh = False

            if not int(random.random() * 100000):
                board.start_shimmer()

            board.bubbles.update(mouse_pos)
            board.check_collisions()
            board.check_state()

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
                draw_multiline_text(screen, stats, (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 200), stats_font)
            pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    main()
