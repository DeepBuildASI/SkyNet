# A818EM - Geographic Distance Calculator
# Haversine formula for ground distance from Ground Zero to Target

import math

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points on Earth (km)."""
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def bearing_deg(lat1, lon1, lat2, lon2):
    """Initial bearing from point 1 to point 2 (degrees)."""
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl)
    brng = math.degrees(math.atan2(x, y))
    return (brng + 360) % 360

if __name__ == "__main__":
    # Ground Zero: Islamabad
    gz_lat, gz_lon = 33.6844, 73.0479

    # Test targets
    targets = [
        ("Lahore",       31.5204, 74.3587),
        ("Karachi",      24.8607, 67.0011),
        ("Peshawar",     34.0151, 71.5249),
        ("Quetta",       30.1798, 66.9750),
        ("Kabul",        34.5553, 69.2075),
        ("Delhi",        28.6139, 77.2090),
    ]

    print("=== A818EM GEO DISTANCE FROM ISLAMABAD ===")
    print(f"Ground Zero: {gz_lat}N, {gz_lon}E")
    print()
    print(f"{'Target':<12} {'Distance (km)':<15} {'Bearing (deg)'}")
    print("-" * 45)
    for name, lat, lon in targets:
        d = haversine_km(gz_lat, gz_lon, lat, lon)
        b = bearing_deg(gz_lat, gz_lon, lat, lon)
        print(f"{name:<12} {d:<15.1f} {b:.1f}")