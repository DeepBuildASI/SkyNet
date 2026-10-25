# A818EM - EMP Simulation Configuration
# Fixed parameters for 500 km HOB scenario

# ===== BURST PARAMETERS =====
HOB_KM = 500.0                # Height of Burst (km)
E0_KV_M = 50.0                # Peak E-field at ground zero (kV/m)
RISE_TIME_NS = 5.0            # Rise time (nanoseconds)
HALF_VALUE_NS = 200.0         # Time to half value (nanoseconds)

# ===== WAVEFORM CONSTANTS =====
K = 1.050                     # Waveform constant
ALPHA = 4.0e6                 # Decay rate (s^-1)
BETA = 4.76e8                 # Rise constant (s^-1)

# ===== EARTH CONSTANTS =====
RE_KM = 6370.0                # Earth radius (km)
Z0_OHMS = 377.0               # Impedance of free space (ohms)
ACRES_PER_KM2 = 247.105       # Conversion factor

# ===== TARGET CHIP PARAMETERS =====
TRACE_LENGTH_M = 0.05         # 5 cm trace acting as antenna
TRACE_WIDTH_M = 0.0002        # 0.2 mm trace width
COUPLING_EFFICIENCY = 0.05    # 5% coupling
PULSE_DURATION_S = 1.0e-6     # 1 microsecond
CHIP_THRESHOLD_J = 1.0e-7     # 100 nanojoules damage threshold

# ===== ANTENNA PARAMETERS =====
ANTENNA_GAIN = 20.0           # Directional antenna gain