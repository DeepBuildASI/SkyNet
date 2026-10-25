# A818EM - Main Calculator
# Combines coverage + attenuation + coupling into one output

from coverage import full_coverage_report
from attenuation import efield_at_distance
from coupling import coupled_energy, kill_decision, required_efield
from config import HOB_KM, CHIP_THRESHOLD_J

def full_report(HOB_km, target_distance_km):
    """Complete EMP analysis for one target."""
    coverage = full_coverage_report(HOB_km)
    E_target = efield_at_distance(target_distance_km, HOB_km)
    E_chip = coupled_energy(E_target)
    result = kill_decision(E_chip)
    E_req = required_efield()

    return {
        "HOB_km": HOB_km,
        "coverage_radius_km": coverage["radius_km"],
        "coverage_area_acres": coverage["area_acres"],
        "target_distance_km": target_distance_km,
        "efield_at_target_kv_m": E_target,
        "coupled_energy_j": E_chip,
        "chip_threshold_j": CHIP_THRESHOLD_J,
        "result": result,
        "required_efield_kv_m": E_req
    }

def print_report(r):
    print("=" * 55)
    print("       A818EM - EMP EFFECT REPORT")
    print("=" * 55)
    print(f"Height of Burst:        {r['HOB_km']} km")
    print(f"Coverage Radius:        {r['coverage_radius_km']:.1f} km")
    print(f"Coverage Area:          {r['coverage_area_acres']:.2e} acres")
    print("-" * 55)
    print(f"Target Distance:        {r['target_distance_km']:.1f} km")
    print(f"E-field at Target:      {r['efield_at_target_kv_m']:.2f} kV/m")
    print(f"Coupled Energy:         {r['coupled_energy_j']:.2e} J")
    print(f"Chip Threshold:         {r['chip_threshold_j']:.2e} J")
    print(f"Required E-field:       {r['required_efield_kv_m']:.2f} kV/m")
    print("-" * 55)
    print(f"RESULT:                 {r['result']}")
    print("=" * 55)

if __name__ == "__main__":
    # Test at multiple distances
    for d in [0, 100, 300, 500, 700, 1000, 1500, 2000, 2500]:
        report = full_report(500.0, d)
        print_report(report)
        print()