import pygame
from skyfield.api import Topos, EarthSatellite
import math

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Active Satellites Orbit View (2D)")
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)

def draw_orbits(satellites, location, time):
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill(BLACK)
        pygame.draw.circle(screen, WHITE, (WIDTH // 2, HEIGHT // 2), 50)
        for sat in satellites:
            difference = sat - location
            topocentric = difference.at(time)
            alt, az, distance = topocentric.altaz()
            scale = 0.05
            x = WIDTH // 2 + math.cos(az.radians) * (distance.km * scale)
            y = HEIGHT // 2 - math.sin(az.radians) * (distance.km * scale)
            x = max(0, min(x, WIDTH))
            y = max(0, min(y, HEIGHT))
            pygame.draw.circle(screen, BLUE, (int(x), int(y)), 5)
            font = pygame.font.SysFont(None, 24)
            text = font.render(sat.name, True, WHITE)
            screen.blit(text, (x + 10, y - 10))
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()