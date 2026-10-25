# A818EM - Coverage Calculator
# Calculates EMP coverage radius and area from HOB

import math
from config import RE_KM, ACRES_PER_KM2

def coverage_radius(HOB_km):
    """Tangent radius of EMP coverage (km)."""
    return math.sqrt(2 * RE_KM * HOB_km)

def coverage_area_km2(radius_km):
    """Circular coverage area in km^2."""
    return math.pi * radius_km ** 2

def coverage_area_acres(area_km2):
    """Convert km^2 to acres."""
    return area_km2 * ACRES_PER_KM2

def full_coverage_report(HOB_km):
    """Complete coverage calculation."""
    R = coverage_radius(HOB_km)
    A_km2 = coverage_area_km2(R)
    A_acres = coverage_area_acres(A_km2)
    return {
        "HOB_km": HOB_km,
        "radius_km": R,
        "area_km2": A_km2,
        "area_acres": A_acres
    }

if __name__ == "__main__":
    report = full_coverage_report(500.0)
    print("=== A818EM COVERAGE REPORT ===")
    print(f"HOB: {report['HOB_km']} km")
    print(f"Radius: {report['radius_km']:.1f} km")
    print(f"Area: {report['area_km2']:.0f} km^2")
    print(f"Area: {report['area_acres']:.0f} acres")