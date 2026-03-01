import pygame
import sys
import random
import time
import logging

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BUBBLE_SIZE, BUBBLE_SPACE,
    BACKGROUND, SHOW_STATS, GREEN, RED, ORANGE, GREY,
    GAME_OVER_EVENT, STATE_CHANGE_EVENT, TRAVERSE_EVENT,
    DEBUG,
)
from utils import draw_multiline_text
from board import Board
from stats import GameStats, snapshot_stats_file, load_aggregate_stats

logger = logging.getLogger(__name__)

# Game-over screen colors
PANEL_BG = (40, 50, 80)
PANEL_BORDER = (255, 255, 255)
TEXT_WHITE = (255, 255, 255)
TEXT_DIM = (170, 170, 190)
BUTTON_COLOR = GREEN
BUTTON_HOVER = (130, 255, 60)
BUTTON_TEXT_COLOR = (40, 50, 80)
HIGHLIGHT_COLOR = ORANGE


def format_duration(seconds):
    if seconds is None:
        return "--"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    if minutes > 0:
        return "%dm %ds" % (minutes, secs)
    return "%ds" % secs


def start_new_game(board, game_stats):
    """Reset stats and record initial board state for a new game."""
    game_stats.reset()
    game_stats.record_game_start(
        bubble_count=len(board.bubbles),
        color_count=len(board.colors),
    )


def on_game_over(board, game_stats, win):
    """Finalize stats and return the record. Does NOT reinitialize the board."""
    return game_stats.finalize(
        win=win,
        bubbles_remaining=len(board.bubbles),
        rows_advanced=board.step,
    )


def on_state_change(board, from_state, to_state):
    assert board.state == from_state, '%s != %s' % (board.state, from_state)
    if DEBUG:
        logger.debug('State change %s -> %s', from_state, to_state)
    board.state = to_state


def draw_game_over_screen(screen, record, aggregates, stats_font, title_font):
    """Draw the game-over overlay. Returns the 'New Game' button rect."""
    sw, sh = screen.get_size()

    # Semi-transparent overlay
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    # Panel
    panel_w = min(1200, sw - 80)
    panel_h = min(1100, sh - 80)
    panel_x = (sw - panel_w) // 2
    panel_y = (sh - panel_h) // 2
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=20)
    pygame.draw.rect(screen, PANEL_BORDER, panel_rect, width=3, border_radius=20)

    # Title
    is_win = record["result"] == "win"
    title_text = "YOU WIN!" if is_win else "GAME OVER"
    title_color = GREEN if is_win else RED
    title_surface = title_font.render(title_text, True, title_color)
    title_rect = title_surface.get_rect(centerx=sw // 2, top=panel_y + 25)
    screen.blit(title_surface, title_rect)

    # Divider below title
    div_y = title_rect.bottom + 15
    pygame.draw.line(screen, GREY,
                     (panel_x + 40, div_y), (panel_x + panel_w - 40, div_y), 2)

    # Column layout
    left_x = panel_x + 60
    center_x = sw // 2
    right_x = center_x + 50
    header_y = div_y + 20

    # Column headers
    hdr_left = stats_font.render("THIS GAME", True, TEXT_WHITE)
    hdr_right = stats_font.render("ALL-TIME BEST", True, TEXT_WHITE)
    screen.blit(hdr_left, (left_x, header_y))
    screen.blit(hdr_right, (right_x, header_y))

    # Vertical divider
    col_div_top = header_y
    col_div_bottom = header_y + 700
    pygame.draw.line(screen, GREY, (center_x, col_div_top), (center_x, col_div_bottom), 1)

    # Stat rows
    row_y = header_y + 50
    row_h = 42
    label_font = stats_font

    def is_record(current, best, lower_is_better=False):
        if best is None or aggregates is None:
            return False
        if lower_is_better:
            return current <= best
        return current >= best

    def draw_row(label, value, best_label=None, best_value=None,
                 lower_is_better=False, indent=False):
        nonlocal row_y
        x = left_x + (30 if indent else 0)

        # Left column — current game
        highlight = best_value is not None and is_record(value, best_value, lower_is_better)
        color = HIGHLIGHT_COLOR if highlight else TEXT_WHITE
        text = "%s: %s" % (label, value)
        surf = label_font.render(text, True, color)
        screen.blit(surf, (x, row_y))

        # Right column — all-time best
        if best_label is not None and aggregates is not None:
            best_text = "%s: %s" % (best_label, best_value if best_value is not None else "--")
            best_surf = label_font.render(best_text, True, TEXT_DIM)
            screen.blit(best_surf, (right_x, row_y))

        row_y += row_h

    # Result row
    result_str = "WIN" if is_win else "LOSS"
    result_surf = label_font.render("Result: %s" % result_str, True, GREEN if is_win else RED)
    screen.blit(result_surf, (left_x, row_y))
    if aggregates:
        wr = "%.0f%%" % (aggregates["win_rate"] * 100)
        screen.blit(label_font.render("Win Rate: %s" % wr, True, TEXT_DIM), (right_x, row_y))
    row_y += row_h

    # Duration
    draw_row("Duration", format_duration(record["duration_sec"]),
             "Best Time", format_duration(aggregates["best_duration"]) if aggregates else None,
             lower_is_better=True)

    # Active Time
    draw_row("Active Time", format_duration(record["active_play_time_sec"]),
             "Best Active", format_duration(aggregates["best_active_time"]) if aggregates else None,
             lower_is_better=True)

    # Shots Fired
    draw_row("Shots Fired", record["shots_fired"],
             "Fewest Shots", aggregates["fewest_shots"] if aggregates else None,
             lower_is_better=True)

    # Accuracy
    draw_row("Accuracy", "%.1f%%" % (record["accuracy"] * 100),
             "Best Accuracy", "%.1f%%" % (aggregates["best_accuracy"] * 100) if aggregates else None)

    # Bubbles Destroyed
    draw_row("Bubbles Destroyed", record["bubbles_destroyed"],
             "Most Destroyed", aggregates["most_destroyed"] if aggregates else None)

    # Sub-rows for match/disjoint
    draw_row("By Match", record["bubbles_destroyed_by_match"], indent=True)
    draw_row("By Disjoint", record["bubbles_destroyed_by_disjoint"], indent=True)

    # Max Match
    draw_row("Max Match", record["max_match_size"],
             "Best Match", aggregates["best_max_match"] if aggregates else None)

    # Matches Made
    draw_row("Matches Made", record["matches_made"],
             "Most Matches", aggregates["most_matches"] if aggregates else None)

    # Rows Advanced
    draw_row("Rows Advanced", record["rows_advanced"],
             "Fewest Rows", aggregates["fewest_rows"] if aggregates else None,
             lower_is_better=True)

    # Aggregate summary divider
    summary_y = row_y + 15
    pygame.draw.line(screen, GREY,
                     (panel_x + 40, summary_y), (panel_x + panel_w - 40, summary_y), 2)

    # Aggregate summary
    if aggregates:
        gp = aggregates["games_played"]
        w = aggregates["wins"]
        l = aggregates["losses"]
        wr = aggregates["win_rate"] * 100
        summary_text = "%d games  -  %d wins (%.0f%%)  -  %d losses" % (gp, w, wr, l)
    else:
        summary_text = "First game - no history yet"
    summary_surf = label_font.render(summary_text, True, TEXT_WHITE)
    summary_rect = summary_surf.get_rect(centerx=sw // 2, top=summary_y + 15)
    screen.blit(summary_surf, summary_rect)

    # New Game button
    btn_w, btn_h = 300, 65
    button_rect = pygame.Rect(0, 0, btn_w, btn_h)
    button_rect.centerx = sw // 2
    button_rect.bottom = panel_y + panel_h - 30

    mouse_pos = pygame.mouse.get_pos()
    is_hover = button_rect.collidepoint(mouse_pos)
    btn_color = BUTTON_HOVER if is_hover else BUTTON_COLOR
    pygame.draw.rect(screen, btn_color, button_rect, border_radius=15)
    btn_text = label_font.render("NEW GAME", True, BUTTON_TEXT_COLOR)
    btn_text_rect = btn_text.get_rect(center=button_rect.center)
    screen.blit(btn_text, btn_text_rect)

    return button_rect


def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.HWSURFACE | pygame.DOUBLEBUF
    )
    pygame.display.set_caption("Bubbles")
    clock = pygame.time.Clock()
    fps = 120

    snapshot_stats_file()

    game_stats = GameStats()
    board = Board(stats=game_stats)
    board.init()
    start_new_game(board, game_stats)
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
                # Finalize stats
                record = on_game_over(board, game_stats, event.message)
                aggregates = load_aggregate_stats()

                # Game-over screen sub-loop
                button_rect = pygame.Rect(0, 0, 0, 0)
                waiting = True
                while waiting and running:
                    for ev in pygame.event.get():
                        if ev.type == pygame.QUIT:
                            running = False
                            waiting = False
                        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == pygame.BUTTON_LEFT:
                            if button_rect.collidepoint(ev.pos):
                                waiting = False
                        if ev.type == pygame.KEYDOWN:
                            if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                                waiting = False
                    clock.tick(fps)
                    button_rect = draw_game_over_screen(
                        screen, record, aggregates, stats_font, tries_font)
                    pygame.display.flip()

                # Reinitialize for next game
                if running:
                    board.init()
                    board.start_shimmer()
                    start_new_game(board, game_stats)
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
