# A818EM - Full Integrated Simulation
# Geo + Coverage + Attenuation + Coupling = Final Result

from geo import haversine_km, bearing_deg
from coverage import full_coverage_report
from attenuation import efield_at_distance
from coupling import coupled_energy, kill_decision, required_efield
from config import HOB_KM, CHIP_THRESHOLD_J

def simulate(gz_lat, gz_lon, tgt_lat, tgt_lon, HOB_km=HOB_KM, name="Target"):
    """Full EMP simulation from Ground Zero to Target."""
    d_km = haversine_km(gz_lat, gz_lon, tgt_lat, tgt_lon)
    b_deg = bearing_deg(gz_lat, gz_lon, tgt_lat, tgt_lon)
    coverage = full_coverage_report(HOB_km)

    in_coverage = d_km <= coverage["radius_km"]
    E_target = efield_at_distance(d_km, HOB_km) if in_coverage else 0.0
    E_chip = coupled_energy(E_target) if in_coverage else 0.0
    result = kill_decision(E_chip) if in_coverage else "OUT_OF_RANGE"
    E_req = required_efield()

    return {
        "name": name,
        "distance_km": d_km,
        "bearing_deg": b_deg,
        "in_coverage": in_coverage,
        "coverage_radius_km": coverage["radius_km"],
        "efield_kv_m": E_target,
        "coupled_j": E_chip,
        "threshold_j": CHIP_THRESHOLD_J,
        "result": result,
        "required_efield_kv_m": E_req
    }

def print_sim(r):
    print("=" * 60)
    print(f"  TARGET: {r['name']}")
    print("=" * 60)
    print(f"  Distance:          {r['distance_km']:.1f} km")
    print(f"  Bearing:           {r['bearing_deg']:.1f} deg")
    print(f"  Coverage radius:   {r['coverage_radius_km']:.1f} km")
    print(f"  In coverage:       {r['in_coverage']}")
    print("-" * 60)
    print(f"  E-field at target: {r['efield_kv_m']:.2f} kV/m")
    print(f"  Coupled energy:    {r['coupled_j']:.2e} J")
    print(f"  Chip threshold:    {r['threshold_j']:.2e} J")
    print(f"  Required E-field:  {r['required_efield_kv_m']:.2f} kV/m")
    print("-" * 60)
    print(f"  RESULT:            {r['result']}")
    print("=" * 60)
    print()

if __name__ == "__main__":
    # Ground Zero: Islamabad
    gz_lat, gz_lon = 33.6844, 73.0479

    print()
    print("A818EM FULL SIMULATION")
    print(f"Ground Zero: Islamabad ({gz_lat}N, {gz_lon}E)")
    print(f"Height of Burst: {HOB_KM} km")
    print()

    targets = [
        ("Lahore",   31.5204, 74.3587),
        ("Peshawar", 34.0151, 71.5249),
        ("Kabul",    34.5553, 69.2075),
        ("Delhi",    28.6139, 77.2090),
        ("Quetta",   30.1798, 66.9750),
        ("Karachi",  24.8607, 67.0011),
    ]

    for name, lat, lon in targets:
        r = simulate(gz_lat, gz_lon, lat, lon, name=name)
        print_sim(r)