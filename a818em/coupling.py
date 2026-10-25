# A818EM - Chip Coupling Calculator
# Calculates energy coupled into chip traces from E-field

import math
from config import (
    Z0_OHMS, TRACE_LENGTH_M, TRACE_WIDTH_M,
    COUPLING_EFFICIENCY, PULSE_DURATION_S, CHIP_THRESHOLD_J
)

def energy_density(E_kv_m):
    """Energy density S = E^2 / (2*Z0) in W/m^2."""
    E_v_m = E_kv_m * 1000.0
    return (E_v_m ** 2) / (2 * Z0_OHMS)

def effective_area(L_m=TRACE_LENGTH_M, W_m=TRACE_WIDTH_M):
    """Effective antenna area of trace (m^2)."""
    return L_m * W_m

def coupled_energy(E_kv_m, L_m=TRACE_LENGTH_M, W_m=TRACE_WIDTH_M,
                   eta=COUPLING_EFFICIENCY, t_p=PULSE_DURATION_S):
    """Energy coupled into chip (Joules)."""
    S = energy_density(E_kv_m)
    A_eff = effective_area(L_m, W_m)
    return S * A_eff * eta * t_p

def kill_decision(E_chip_j, threshold_j=CHIP_THRESHOLD_J):
    """Return FRIED or SURVIVED."""
    return "FRIED" if E_chip_j >= threshold_j else "SURVIVED"

def required_efield(threshold_j=CHIP_THRESHOLD_J, L_m=TRACE_LENGTH_M,
                    W_m=TRACE_WIDTH_M, eta=COUPLING_EFFICIENCY,
                    t_p=PULSE_DURATION_S):
    """Required E-field to kill chip (kV/m)."""
    A_eff = L_m * W_m
    S_req = threshold_j / (A_eff * eta * t_p)
    E_v_m = math.sqrt(2 * Z0_OHMS * S_req)
    return E_v_m / 1000.0

if __name__ == "__main__":
    print("=== A818EM COUPLING TEST ===")
    print(f"Trace: {TRACE_LENGTH_M*1000:.1f} mm x {TRACE_WIDTH_M*1000:.2f} mm")
    print(f"Coupling efficiency: {COUPLING_EFFICIENCY}")
    print(f"Chip threshold: {CHIP_THRESHOLD_J:.2e} J")
    print()
    E_req = required_efield()
    print(f"Required E-field for kill: {E_req:.2f} kV/m")
    print()
    print(f"{'E-field (kV/m)':<18} {'E_chip (J)':<16} {'Result'}")
    print("-" * 45)
    for E in [1, 5, 10, 15, 20, 25, 30, 50]:
        E_chip = coupled_energy(E)
        result = kill_decision(E_chip)
        print(f"{E:<18} {E_chip:<16.2e} {result}")