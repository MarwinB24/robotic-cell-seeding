import sys
from pathlib import Path

import pygame
import numpy as np

# Allow running this file directly from /sim
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plate.well_plates import Plates  # uses your existing class


WINDOW_W, WINDOW_H = 1200, 800
FPS = 60

# Visual scaling
MM_TO_PX = 4.0
MARGIN_X = 120
MARGIN_Y = 100

BG = (22, 24, 29)
GRID = (70, 78, 92)
WELL = (130, 190, 255)
WELL_HIGHLIGHT = (255, 215, 64)
TOP_LEFT_COLOR = (255, 120, 120)
TEXT = (230, 230, 230)
AXIS = (120, 130, 150)


def mm_to_px(x_mm, y_mm):
    x_px = int(MARGIN_X + x_mm * MM_TO_PX)
    y_px = int(MARGIN_Y + y_mm * MM_TO_PX)
    return x_px, y_px


def draw_axes(screen):
    pygame.draw.line(screen, AXIS, (MARGIN_X, 30), (MARGIN_X, WINDOW_H - 30), 1)
    pygame.draw.line(screen, AXIS, (30, MARGIN_Y), (WINDOW_W - 30, MARGIN_Y), 1)


def build_plate_points(plate: Plates, plate_type: str, marker_bottom_left, x_apart, y_apart):
    top_left = plate.marker_to_well(x_apart, y_apart, marker_bottom_left)
    points = plate.well_coordinate(plate_type, top_left)  # Nx2 numpy array
    return top_left, points


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Plate Well Simulator (Pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)

    plate = Plates()

    plate_types = ["96well", "24well", "12well", "6well"]
    idx = 0
    plate_type = plate_types[idx]

    # Marker origin in mm (you can tune these live)
    marker_bottom_left = [0.0, 0.0]

    # Default offsets from marker to top-left well (A1)
    # Uses values from your config when available
    x_apart = Plates.PLATE_CONFIGS[plate_type].get("xApart", 0.0)
    y_apart = Plates.PLATE_CONFIGS[plate_type].get("yApart", 0.0)

    selected = 0
    running = True

    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # Cycle plate type
                elif event.key == pygame.K_TAB:
                    idx = (idx + 1) % len(plate_types)
                    plate_type = plate_types[idx]
                    x_apart = Plates.PLATE_CONFIGS[plate_type].get("xApart", x_apart)
                    y_apart = Plates.PLATE_CONFIGS[plate_type].get("yApart", y_apart)
                    selected = 0

                # Move marker origin
                elif event.key == pygame.K_LEFT:
                    marker_bottom_left[0] -= 1.0
                elif event.key == pygame.K_RIGHT:
                    marker_bottom_left[0] += 1.0
                elif event.key == pygame.K_UP:
                    marker_bottom_left[1] -= 1.0
                elif event.key == pygame.K_DOWN:
                    marker_bottom_left[1] += 1.0

                # Adjust offsets
                elif event.key == pygame.K_a:
                    x_apart -= 1.0
                elif event.key == pygame.K_d:
                    x_apart += 1.0
                elif event.key == pygame.K_w:
                    y_apart += 1.0
                elif event.key == pygame.K_s:
                    y_apart -= 1.0

                # Step selected well
                elif event.key == pygame.K_COMMA:
                    selected -= 1
                elif event.key == pygame.K_PERIOD:
                    selected += 1

        top_left, points = build_plate_points(
            plate, plate_type, tuple(marker_bottom_left), x_apart, y_apart
        )

        if len(points) > 0:
            selected %= len(points)

        screen.fill(BG)
        draw_axes(screen)

        # Draw top-left reference point
        top_left_px = mm_to_px(top_left[0], top_left[1])
        pygame.draw.circle(screen, TOP_LEFT_COLOR, top_left_px, 6)

        # Draw wells
        for i, (x_mm, y_mm) in enumerate(points):
            p = mm_to_px(float(x_mm), float(y_mm))
            color = WELL_HIGHLIGHT if i == selected else WELL
            radius = 7 if i == selected else 5
            pygame.draw.circle(screen, color, p, radius)

        # Draw "tool head" at selected well
        if len(points) > 0:
            sx, sy = points[selected]
            sx_px, sy_px = mm_to_px(float(sx), float(sy))
            pygame.draw.circle(screen, (255, 80, 80), (sx_px, sy_px), 11, 2)

        # HUD
        hud = [
            f"Plate: {plate_type}   (TAB to cycle)",
            f"Marker bottom-left (mm): ({marker_bottom_left[0]:.1f}, {marker_bottom_left[1]:.1f})  [Arrow keys]",
            f"xApart: {x_apart:.1f} mm  [A/D]",
            f"yApart: {y_apart:.1f} mm  [W/S]",
            f"Selected well idx: {selected} / {max(0, len(points)-1)}  [< / >]",
            f"Total wells: {len(points)}",
            f"FPS: {clock.get_fps():.1f}",
            "Esc to quit",
        ]

        y = 20
        for line in hud:
            surf = font.render(line, True, TEXT)
            screen.blit(surf, (20, y))
            y += 26

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()