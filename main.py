import requests
from skyfield.api import EarthSatellite, load, wgs84
import pygame
import math
import numpy as np

def fetch_active_satellites_tle():
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text.splitlines()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch TLE data: {e}")
        return None

def draw_high_res_angle(surface, center, radius, angle_deg, color):
    angle_rad = angle_deg * 3.14159 / 180
    num_segments = 50
    for i in range(num_segments + 1):
        theta1 = i * angle_rad / num_segments
        theta2 = (i + 1) * angle_rad / num_segments
        x1 = center[0] + radius * math.cos(theta1)
        y1 = center[1] + radius * math.sin(theta1)
        x2 = center[0] + radius * math.cos(theta2)
        y2 = center[1] + radius * math.sin(theta2)
        pygame.draw.line(surface, color, (x1, y1), (x2, y2), 2)
    
    pygame.draw.line(surface, (100, 100, 100), center, 
                     (center[0] + radius * math.cos(0), center[1] + radius * math.sin(0)), 1)
    pygame.draw.line(surface, color, center, 
                     (center[0] + radius * math.cos(angle_rad), center[1] + radius * math.sin(angle_rad)), 2)
    
    font: pygame.font.Font = pygame.font.Font(None, 20)
    label = font.render(f"{angle_deg:.1f}°", True, color)
    label_x = center[0] + (radius + 20) * math.cos(angle_rad / 2)
    label_y = center[1] + (radius + 20) * math.sin(angle_rad / 2)
    surface.blit(label, (label_x - 10, label_y - 10))

def draw_dashed_line(surface, color, start, end, dash_length=10, gap_length=10):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = (dx**2 + dy**2)**0.5
    if distance == 0:
        return
    dashes = int(distance / (dash_length + gap_length))
    for i in range(dashes):
        t_start = i * (dash_length + gap_length) / distance
        t_end = (i * (dash_length + gap_length) + dash_length) / distance
        if t_end > 1:
            t_end = 1
        dash_start_x = start[0] + dx * t_start
        dash_start_y = start[1] + dy * t_start
        dash_end_x = start[0] + dx * t_end
        dash_end_y = start[1] + dy * t_end
        pygame.draw.line(surface, color, (dash_start_x, dash_start_y), (dash_end_x, dash_end_y), 2)

def get_elliptical_position(satellite, ts, t):
    """Calculate 2D position for an elliptical orbit, including eccentricity and inclination."""
    geocentric = satellite.at(t)
    position_km = geocentric.position.km  
    
    x, y, z = position_km
    
    inclination = satellite.model.inclo * 180 / math.pi  
    eccentricity = satellite.model.ecco 
    
    angle = math.radians(inclination)
    x_rot = x * math.cos(angle) - y * math.sin(angle)
    y_rot = x * math.sin(angle) + y * math.cos(angle)
    
    distance = math.sqrt(x_rot**2 + y_rot**2)
    semi_major_axis = satellite.model.a 
    if semi_major_axis is None or semi_major_axis <= 0:
        semi_major_axis = distance  
    
    eccentricity_factor = 1 + eccentricity
    x_elliptical = x_rot * eccentricity_factor
    y_elliptical = y_rot
    
    return x_elliptical, y_elliptical

def draw_3d_like_earth(surface, center, radius):
    """Draw a high-resolution Earth with a 3D-like appearance using concentric circles and shading."""
    earth_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    num_rings = 50  
    for r in range(radius, 0, -1):
        shade = int(255 * (r / radius) * 0.7 + 30) 
        pygame.draw.circle(earth_surface, (0, 0, shade, 255), (radius, radius), r, 1)
    
    pygame.draw.circle(earth_surface, (0, 0, 150, 255), (radius, radius), radius // 2)
    
    surface.blit(earth_surface, (center[0] - radius, center[1] - radius))

def main():
    pygame.init()
    screen = pygame.display.set_mode((1600, 900)) 
    pygame.display.set_caption("ActiveSatellitesTracker") 
    clock = pygame.time.Clock()
    ts = load.timescale()
    large_font: pygame.font.Font = pygame.font.Font(None, 48)
    small_font: pygame.font.Font = pygame.font.Font(None, 28)
    scale_font: pygame.font.Font = pygame.font.Font(None, 24)

    tle_lines = fetch_active_satellites_tle()
    if tle_lines is None:
        print("Exiting due to TLE fetch failure")
        pygame.quit()
        return

    satellites = []
    for i in range(0, min(len(tle_lines), 900), 3):
        if i + 2 < len(tle_lines):
            satellites.append(EarthSatellite(tle_lines[i + 1], tle_lines[i + 2], tle_lines[i], ts))

    zoom = 1.0
    offset_x, offset_y = 0, 0  
    screen_width, screen_height = 1600, 900  
    earth_radius = 6371 
    max_distance = 50000  

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                zoom += event.y * 0.1
                zoom = max(0.1, min(zoom, 5.0))
            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                offset_x += event.rel[0]
                offset_y += event.rel[1]

        screen.fill((0, 0, 0))
        t = ts.now()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        scale_factor = screen_width / (2 * max_distance) 
        earth_radius_pixels = int(earth_radius * scale_factor * zoom) 
        earth_center = (screen_width // 2 + offset_x, screen_height // 2 + offset_y)  
        print(f"Earth center: x={earth_center[0]}, y={earth_center[1]}, radius={earth_radius_pixels} px") 

        draw_3d_like_earth(screen, earth_center, earth_radius_pixels)

        hovered_sat = None
        for sat in satellites:
            try:
                x, y = get_elliptical_position(sat, ts, t) 
                x_scaled = (x * scale_factor * zoom) + (screen_width // 2) + offset_x
                y_scaled = (y * scale_factor * zoom) + (screen_height // 2) + offset_y
                if 0 <= x_scaled < screen_width and 0 <= y_scaled < screen_height:
                    pygame.draw.circle(screen, (255, 255, 255), (int(x_scaled), int(y_scaled)), 2)
                    if abs(mouse_x - x_scaled) < 5 and abs(mouse_y - y_scaled) < 5:
                        hovered_sat = sat
                        hovered_pos = sat.at(t)
            except ValueError:
                continue

        if hovered_sat:
            altitude = hovered_pos.distance().km - earth_radius
            velocity = (sum(v ** 2 for v in hovered_pos.velocity.km_per_s) ** 0.5)
            inclination = hovered_sat.model.inclo * 180 / 3.14159

            text_lines = [
                f"{hovered_sat.name}",
                f"Altitude: {altitude:.1f} km",
                f"Velocity: {velocity:.1f} km/s"
            ]
            
            name_width = large_font.size(text_lines[0])[0] + 20
            detail_width = max(small_font.size(line)[0] for line in text_lines[1:]) + 20
            text_width = max(name_width, detail_width)
            text_height = large_font.size(text_lines[0])[1] + 2 * small_font.size(text_lines[1])[1] + 20
            box_x = mouse_x + 10
            box_y = mouse_y - 20 - text_height
            if box_x + text_width > screen_width:
                box_x = mouse_x - text_width - 10
            if box_y < 0:
                box_y = mouse_y + 20
            pygame.draw.rect(screen, (50, 50, 50), (box_x, box_y, text_width, text_height), border_radius=5)
            
            name_text = large_font.render(text_lines[0], True, (255, 255, 255))
            screen.blit(name_text, (box_x + 10, box_y + 5))
            for i, line in enumerate(text_lines[1:], 1):
                detail_text = small_font.render(line, True, (255, 255, 255))
                screen.blit(detail_text, (box_x + 10, box_y + 5 + large_font.size(text_lines[0])[1] + (i - 1) * small_font.size(line)[1]))

            arc_center = (box_x + text_width + 40, box_y + text_height // 2)
            arc_radius = 30
            draw_high_res_angle(screen, arc_center, arc_radius, inclination, (255, 255, 0))

        scale_length_km = 5000 
        scale_length_pixels = int(scale_length_km * scale_factor * zoom)
        scale_x, scale_y = 50, screen_height - 50
        pygame.draw.line(screen, (255, 255, 255), (scale_x, scale_y), (scale_x + scale_length_pixels, scale_y), 2)
        pygame.draw.line(screen, (255, 255, 255), (scale_x, scale_y - 5), (scale_x, scale_y + 5), 2)
        pygame.draw.line(screen, (255, 255, 255), (scale_x + scale_length_pixels, scale_y - 5), 
                         (scale_x + scale_length_pixels, scale_y + 5), 2)
        scale_text = scale_font.render(f"{scale_length_km} km", True, (255, 255, 255))
        screen.blit(scale_text, (scale_x + scale_length_pixels // 2 - 20, scale_y + 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
