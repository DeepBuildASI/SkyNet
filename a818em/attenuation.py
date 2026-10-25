# A818EM - Attenuation Calculator
# Calculates E-field at any ground distance from ground zero

import math
from config import HOB_KM, E0_KV_M

def attenuation_factor(d_km, HOB_km=HOB_KM):
    """Geometric attenuation F(d) = (HOB / sqrt(HOB^2 + d^2))^3"""
    return (HOB_km / math.sqrt(HOB_km**2 + d_km**2)) ** 3

def efield_at_distance(d_km, HOB_km=HOB_KM, E0=E0_KV_M):
    """E-field at ground distance d from ground zero (kV/m)."""
    return E0 * attenuation_factor(d_km, HOB_km)

if __name__ == "__main__":
    print("=== A818EM ATTENUATION TABLE ===")
    print(f"HOB: {HOB_KM} km | Peak E0: {E0_KV_M} kV/m")
    print()
    print(f"{'Distance (km)':<15} {'F(d)':<12} {'E-field (kV/m)'}")
    print("-" * 45)
    for d in [0, 100, 500, 1000, 1500, 2000, 2500]:
        F = attenuation_factor(d)
        E = efield_at_distance(d)
        print(f"{d:<15} {F:<12.4f} {E:.2f}")