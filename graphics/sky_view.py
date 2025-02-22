import matplotlib.pyplot as plt
from skyfield.api import Topos, EarthSatellite

def draw_sky(satellites, location, time, title="Starlink satellites positions on the sky"):
    plt.figure(figsize=(10, 10))
    for sat in satellites:
        difference = sat - location
        topocentric = difference.at(time)
        alt, az, _ = topocentric.altaz()
        plt.polar(az.radians, 90 - alt.degrees, 'bo', markersize=8, label=sat.name)
    plt.title(title, pad=20)
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.grid(True)
    plt.ylim(0, 90)
    plt.show()