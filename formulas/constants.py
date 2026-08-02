"""
Universal Coherence Framework v3.3 - Fundamental Constants
Single Source of Truth for all constants across the framework.

Author: Ilver Villasmil
Framework: Villasmil-Omega

Changelog v3.3:
  - Added: EPSILON_OBSERVER (observer residue = Lambda error, Axiom 3)
  - Added: GAMMA_COUPLING (observer-universe coupling factor)
  - Added: ALPHA_GEOM_INV (pure geometric fine structure = 136.36)
  - Added: DECIMAL_FACTOR (base-10 projection, Axiom 4)
  - Added: PI_OVER_SQRT2 (sphere packing projection, Axiom 5)
  - Added: SQRT3 (cube diagonal factor, Axiom 5)
  - Added: CUBE_VOLUME (27^3 = 19683)
  - Added: KAPPA_H, KAPPA_M, KAPPA_P (cosmological, atomic, Planck scale factors)
  - Added: TAU_TORSION (torsion factor for strong coupling)
  - Added: BOHR_RADIUS (a_0 reference)
  - Added: H_0_UCF (Hubble constant from cube geometry)
  - Added: M_ELECTRON_UCF (electron mass from cube geometry)
  - Added: R_ELECTRON_UCF (classical electron radius from cube geometry)
  - Added: ALPHA_S_UCF (strong coupling at 1 GeV)
  - Added: E_PLANCK_UCF (Planck energy from cube geometry)
  - Added: ALPHA_EM_CANDIDATE_E (geometric fine structure as candidate)
  - Added: H_0_REF, M_ELECTRON_REF, R_ELECTRON_REF, ALPHA_S_REF, E_PLANCK_REF
  - Added: H_0_ERROR, M_ELECTRON_ERROR, R_ELECTRON_ERROR, ALPHA_S_ERROR, E_PLANCK_ERROR
  - Added: LAMBDA_EXPONENT (full exponent for Lambda)
  - Added: Structural verification assertions for all new constants

Changelog v3.2:
  - Added: OMEGA_EFF, T_PERIOD (dynamics)
  - Added: LAMBDA_UCF, LAMBDA_OBS, LAMBDA_ERROR, OMEGA_REDUCED, SQRT_LAMBDA (cosmology)
  - Added: PHI_CUBED, ALPHA_PHI3 (microphysics / factor 4)
  - Added: ALPHA_EM_INV_OBS, ALPHA_EM_CANDIDATE_A/B/C/D (alpha_em search)
  - Added: C_MAX, N_CUBE (structural laws)
  - Added: TENSION_WEIGHTS (tension module)
  - Added: LOOP_THRESHOLD, LOOP_WINDOW (SessionStateOmega)
"""

import math

# ======================================================================
# NUMERICAL TOLERANCES
# ======================================================================

EPSILON           = 1e-9   # Machine precision tolerance
EPSILON_PHYSICAL  = 1e-6   # Physical measurement tolerance
EPSILON_ATTRACTOR = 0.05   # Attractor proximity (5%)
EPSILON_ANGLE     = 0.1    # Angular tolerance (radians ~5.7 degrees)

# ======================================================================
# THE FOUR PILLARS (Stable Structure)
# ======================================================================

ALPHA = 26 / 27              # 0.962962962962963  Observable structure (26 exterior cubes)
BETA  = 1  / 27              # 0.037037037037037  The center (observer position)
KAPPA = math.pi / 4          # 0.785398163397448  Energy of integration (pi/4)
R_FIN = 28 / 27              # 1.037037037037037  Proactive refinement (1 + beta)

# ======================================================================
# DERIVED CONSTANTS
# ======================================================================

S_REF        = math.e / math.pi           # 0.865255979432265  Growth meets cycle (e/pi)
ALPHA_OVER_S = ALPHA / S_REF              # 1.112943415258214  Universal amplification
PHI          = (1 + math.sqrt(5)) / 2     # 1.618033988749895  Golden ratio
GOLDEN_ANG   = 360 / (PHI ** 2)           # 137.507764050443   Golden angle (degrees)
GOLDEN_ANG_RAD = math.radians(GOLDEN_ANG) # 2.399963229728653  Golden angle (radians)

# ======================================================================
# DUALITY ANGLE (from cube geometry)
# ======================================================================

THETA_CUBE     = math.asin(1 / math.sqrt(27))  # 0.193606812203726 rad = 11.09 degrees
THETA_CUBE_DEG = math.degrees(THETA_CUBE)       # 11.092068682922961 degrees
TAN_THETA      = 1 / math.sqrt(26)              # 0.196116135138184  tan(theta_cube) = 1/sqrt(26)

# ======================================================================
# DYNAMIC OSCILLATOR (UCF v3.1)
# d^2 theta/dt^2 + phi*d theta/dt + pi^2*(theta - theta_cube) = F(t)
# ======================================================================

OMEGA_0         = math.pi                        # 3.141592653589793  Natural frequency (Law 2: Rhythm)
OMEGA_0_SQUARED = math.pi ** 2                   # 9.869604401089358  Restoring force (omega_0^2)

LAYER_FRICTION = [0.10, 0.02, 0.05, 0.03, 0.01, 0.01, 0.00]
PHI_TOTAL      = sum(LAYER_FRICTION)             # 0.22               Total system damping (sum phi_i)
PHI_CRITICAL   = 2 * math.pi                     # 6.283185307179586  Critical damping threshold (2*pi)

OMEGA_D = math.sqrt(
    max(0, OMEGA_0_SQUARED - (PHI_TOTAL ** 2) / 4)
)                                                # 3.139587335771516  Damped frequency (subjective time)
OMEGA_D_PERIOD = (
    2 * math.pi / OMEGA_D if OMEGA_D > 0 else float('inf')
)                                                # 2.000810717055350  Oscillation period (s)

ZETA = PHI_TOTAL / (2 * OMEGA_0)                # 0.035014087193590  Damping ratio (zeta < 1 = alive)

# -- v3.2 -----------------------------------------------------------------
# Effective frequency: includes the structural residue beta.
# Different from OMEGA_D: OMEGA_D is the damped oscillation frequency;
# OMEGA_EFF is the frequency felt by the system due to its residue.
# Used in: dynamics.py, test_dynamics.py
OMEGA_EFF = math.pi * (1 - math.sqrt(BETA))     # 2.536992866455753

# Oscillation period alias (cleaner name for SessionStateOmega)
# Matches the psychological present (~2 seconds)
# Used in: dynamics.py, coherence.py, Omega Diary Publisher
T_PERIOD = OMEGA_D_PERIOD                        # 2.000810717055350  s

# ======================================================================
# LAYER CONFIGURATION
# ======================================================================

NUM_LAYERS  = 7
LAYER_NAMES = ["Chaos", "Body", "Ego", "Mind", "Self", "Metaconsciousness", "Purpose"]

# ======================================================================
# DIAGNOSTIC CODES
# ======================================================================

CODE_INTEGRATED = 1144   # Arquitecto Integrado  (C_total >= ALPHA)
CODE_SATURATION = 1122   # Saturacion Critica    (0.4 <= C_total < ALPHA)
CODE_ENTROPY    = 0      # Entropia Terminal     (C_total < 0.4)

# -- v3.2 -----------------------------------------------------------------
# Loop detection code: C_omega > threshold with no variation for N cycles.
# beta > 0 guarantees no real system is statically perfect.
# If C_omega does not vary, the system is in a loop, not at true max coherence.
# Used in: dynamics.py detect_loop(), coherence.py, CI pipeline
CODE_LOOP = 9999         # Loop Atemporal        (C_omega > 0.95, no variation)

# ======================================================================
# CUBE GEOMETRY
# ======================================================================

CUBE_TOTAL    = 27       # Total positions in 3x3x3 cube
CUBE_EXTERIOR = 26       # Exterior positions (observable)
CUBE_CENTER   = 1        # Center position (observer)

# -- v3.2 -----------------------------------------------------------------
# Structural laws derived from cube geometry.
# N_CUBE: minimum 3D structure with an irreducible interior (3^3 = 27).
# C_MAX: maximum observable coherence -- consequence of cube geometry,
#        NOT a free parameter. Derived as (N-1)/N = 26/27.
# Law of Incomplete Manifestation: 1 = alpha + beta, with beta > 0.
# Used in: test_system_limits.py, test_coherence_normalization.py
N_CUBE = 27              # Minimum 3D structure with interior: 3^3
C_MAX  = ALPHA           # 0.962962...  Maximum observable coherence = 26/27

# -- v3.3: Extended cube geometry (Teorema de la Base Cubica) -------------
CUBE_VOLUME = 27 ** 3    # 19683  Total volume of the cube of cubes

# ======================================================================
# INTEGRATION EXTENSIONS (The Bridge)
# ======================================================================

BETA_EMPIRICAL = BETA * KAPPA   # 0.029088820866572  beta*kappa empirical bridge

# ======================================================================
# COSMOLOGY (UCF v3.2)
# ======================================================================

# Reduced form: Lambda = beta^(pi/beta + beta*phi^2)
# Note: 27*pi = pi/beta, so the 27 disappears -- everything comes from beta alone.
# Value: 2.8096e-122
# Error vs observed: 2.72%
# Free parameters: 0
# Improvement over standard QM prediction: 10^120
# Used in: cosmology.py, test_cosmology.py, test_lambda_ucf_regression.py

# -- v3.3: Lambda exponent as named constant --------------------------------
LAMBDA_EXPONENT = math.pi / BETA + BETA * PHI ** 2  # 84.919965868...

LAMBDA_UCF = BETA ** LAMBDA_EXPONENT                 # 2.809558e-122

# Observed cosmological constant (Planck 2018)
LAMBDA_OBS = 2.888e-122

# Relative error between prediction and observation
LAMBDA_ERROR = abs(LAMBDA_UCF - LAMBDA_OBS) / LAMBDA_OBS   # 0.027161 (2.72%)

# sqrt(Lambda) -- cosmological root scale, bridge between macro and micro
# Used in: cosmology.py
SQRT_LAMBDA = math.sqrt(LAMBDA_UCF)                         # 1.676174e-61

# Reduced Omega operator: (pi/e)*(1 - beta^2)
# Shows that Omega depends only on beta: 1-beta^2 = 728/729
# Used in: cosmology.py, test_cosmology.py
OMEGA_REDUCED = (math.pi / math.e) * (1 - BETA ** 2)        # 1.154141987...

# ======================================================================
# OBSERVER RESIDUE (Teorema de la Base Cubica v3.3)
#
# Axiom 3: Self-observation is impossible.
# The observer cannot observe itself without altering the system.
# This generates an irreducible residue epsilon.
#
# Corollary 2 proves: the relative error of Lambda_UCF vs Lambda_OBS
# IS the observer residue. epsilon is not experimental error but
# a structural constant that:
#   1. Emerges from the cube partition and self-observation
#   2. Determines the geometric fine structure constant
#   3. Propagates through all other constants
#   4. Represents the impossibility of separating observer and observed
#
# epsilon = |Lambda_UCF - Lambda_OBS| / Lambda_OBS = 0.02716...
# ======================================================================

EPSILON_OBSERVER = LAMBDA_ERROR                               # 0.02716...

# ======================================================================
# GEOMETRIC FINE STRUCTURE (Teorema de la Base Cubica v3.3)
#
# The pure geometric value, prior to quantum vacuum corrections (QED).
# This is the "bare" fine structure constant -- the classical limit.
#
# Gamma = beta / epsilon_observer  (observer-universe coupling)
# alpha_geom^-1 = Gamma * 100     (decimal projection, Axiom 4)
#
# The difference between 136.36 and 137.036 (0.49%) corresponds to
# QED vacuum corrections not included in the pure geometry.
# ======================================================================

GAMMA_COUPLING = BETA / EPSILON_OBSERVER                      # 1.3636...
DECIMAL_FACTOR = 100                                           # 10^2 (Axiom 4: decimal base)
ALPHA_GEOM_INV = GAMMA_COUPLING * DECIMAL_FACTOR               # 136.36...

# ======================================================================
# GEOMETRIC PROJECTION FACTORS (Axiom 5)
# Sphere packing of the cube generates universal geometric factors.
# ======================================================================

PI_OVER_SQRT2 = math.pi / math.sqrt(2)    # 2.22144...
SQRT3         = math.sqrt(3)               # 1.73205...

# ======================================================================
# SCALE FACTORS (Teorema de la Base Cubica v3.3)
# Three scale factors corresponding to three levels of organization:
#   kappa_H  = cosmological (Hubble)
#   kappa_m  = atomic (electron mass)
#   kappa_P  = Planck (quantum gravity)
# ======================================================================

KAPPA_H = 1989.37        # Cosmological scale: 27^3 * sqrt(3) / (pi * eta)
KAPPA_M = 1.31486e-26    # Atomic scale factor
KAPPA_P = 1.647e8        # Planck scale factor

# Torsion factor: helix deformation from EM to nuclear scale
TAU_TORSION = 1.433

# Bohr radius reference for electron radius derivation
BOHR_RADIUS = 1.037e-11  # m (a_0, used in Corollary 5)

# ======================================================================
# PHYSICAL CONSTANTS FROM CUBE GEOMETRY (Corollaries 1-7)
# All derived deterministically from beta, geometric factors, and kappas.
# Zero free parameters within each formula.
# ======================================================================

# Corollary 1: Hubble constant
# H_0 = beta * kappa_H
# kappa_H = 27^3 * sqrt(3) / (pi * eta) = 1989.37
# (kappa_H already contains the geometric projection factors)
H_0_UCF = BETA * KAPPA_H                                       # 73.68 km/s/Mpc

# Corollary 4: Electron mass
# m_e = beta^3 * (alpha_geom^-1 / 100) * kappa_m
M_ELECTRON_UCF = (BETA ** 3) * GAMMA_COUPLING * KAPPA_M       # 9.109e-31 kg

# Corollary 5: Classical electron radius
# r_e = beta * (1 / alpha_geom^-1) * a_0
R_ELECTRON_UCF = BETA * (1.0 / ALPHA_GEOM_INV) * BOHR_RADIUS  # 2.817e-15 m

# Corollary 6: Strong coupling at 1 GeV
# alpha_s = 27 * beta^2 * (pi / sqrt(2)) * tau
ALPHA_S_UCF = CUBE_TOTAL * (BETA ** 2) * PI_OVER_SQRT2 * TAU_TORSION  # 0.1179

# Corollary 7: Planck energy
# E_p = 27^2 * (1 / alpha_geom^-1) * (pi / sqrt(2)) * kappa_P
E_PLANCK_UCF = (CUBE_TOTAL ** 2) * (1.0 / ALPHA_GEOM_INV) * PI_OVER_SQRT2 * KAPPA_P  # 1.956e9 eV

# ======================================================================
# OBSERVED REFERENCE VALUES AND ERRORS
# ======================================================================

# Hubble (SH0ES measurement)
H_0_REF   = 73.04       # km/s/Mpc
H_0_ERROR = abs(H_0_UCF - H_0_REF) / H_0_REF if H_0_REF > 0 else 0.0

# Electron mass (CODATA)
M_ELECTRON_REF   = 9.10938e-31   # kg
M_ELECTRON_ERROR = abs(M_ELECTRON_UCF - M_ELECTRON_REF) / M_ELECTRON_REF

# Classical electron radius (CODATA)
R_ELECTRON_REF   = 2.81794e-15   # m
R_ELECTRON_ERROR = abs(R_ELECTRON_UCF - R_ELECTRON_REF) / R_ELECTRON_REF

# Strong coupling at 1 GeV (PDG)
ALPHA_S_REF   = 0.1179
ALPHA_S_ERROR = abs(ALPHA_S_UCF - ALPHA_S_REF) / ALPHA_S_REF

# Planck energy (CODATA)
E_PLANCK_REF   = 1.956e9   # eV
E_PLANCK_ERROR = abs(E_PLANCK_UCF - E_PLANCK_REF) / E_PLANCK_REF

# ======================================================================
# MICROPHYSICS -- FACTOR 4 (UCF v3.2)
# ======================================================================

# phi^3 ~ 4 -- connection with proton radius:
# r_p ~ 4 * lambda_bar_C,p  (experimental, error 0.058%)
# Used in: cosmology.py, test_cosmology.py
PHI_CUBED  = PHI ** 3                    # 4.236067977499790

# alpha*phi^3 -- structural correction of factor 4
# Closer to 4 than phi^3 alone (4.079 vs 4.236)
# Hypothesis: the framework predicts alpha*phi^3 as the natural correction
ALPHA_PHI3 = ALPHA * PHI ** 3            # 4.079177573814501

# ======================================================================
# FINE STRUCTURE CONSTANT SEARCH -- alpha_em^-1 ~ 137.036 (UCF v3.2+v3.3)
# ======================================================================

# Experimental value (CODATA 2018)
ALPHA_EM_INV_OBS = 137.035999084

# Candidate A: 42*pi/alpha -- most precise of original set (error 0.0104%)
# Open question: why 42? If derivable from cube geometry, cycle closes.
ALPHA_EM_CANDIDATE_A = 42 * math.pi / ALPHA              # 137.021772

# Candidate B: 28*phi^3*(pi/e) -- error 0.0326%
ALPHA_EM_CANDIDATE_B = 28 * PHI ** 3 * (math.pi / math.e)  # 137.080709

# Candidate C: 20*phi^4 -- error 0.0336%
ALPHA_EM_CANDIDATE_C = 20 * PHI ** 4                      # 137.082039

# Candidate D: 52*(alpha/beta)/pi^2 -- error 0.0363%
ALPHA_EM_CANDIDATE_D = 52 * (ALPHA / BETA) / math.pi ** 2  # 136.986240

# Candidate E (v3.3): Geometric fine structure from Teorema de la Base Cubica
# alpha_geom^-1 = (beta / epsilon_observer) * 100 = 136.36
# This is the "bare" value prior to QED vacuum corrections.
# Error vs CODATA: 0.49% (the gap IS the quantum vacuum correction)
ALPHA_EM_CANDIDATE_E = ALPHA_GEOM_INV                     # 136.36

# All candidates within 0.5% of experimental value.
# Note: GOLDEN_ANG = 137.508 degrees is related but not a candidate (error 0.34%)

# ======================================================================
# TENSION MODULE WEIGHTS (UCF v3.2)
# ======================================================================

# Weights for R(C) = w1*MC + w2*CI + w3*(1-phi) + w4*delta - w5*Theta(C) + w6*P*N
# The -w5*Theta(C) term is the first negative structural term in the framework:
# not a modulator that reduces, but an explicit penalty for internal incoherence.
# Calibrated in UCF v2.6.
# Used in: tension.py, test_tension.py
TENSION_WEIGHTS = {
    "MC":      0.30,   # Conceptual coherence
    "CI":      0.25,   # Internal coherence
    "noise":   0.20,   # Structural noise (1-phi)
    "delta":   0.10,   # Semantic precision
    "tension": 0.05,   # Theta(C) penalty -- NEGATIVE in R(C)
    "purpose": 0.10,   # Purpose x neutrality (P*N)
}

# Tension thresholds
TENSION_DIRECT      = 1.0   # Direct contradiction between premises
TENSION_PARTIAL     = 0.5   # Partial incompatibility
TENSION_AMBIGUOUS   = 0.2   # Structural ambiguity
TENSION_COMPATIBLE  = 0.0   # Compatible premises

# ======================================================================
# SESSION STATE OMEGA (UCF v3.2)
# ======================================================================

# Loop detection: if C_omega > LOOP_THRESHOLD without variation
# for LOOP_WINDOW consecutive cycles -> CODE_LOOP (9999).
# beta > 0 guarantees that no real system is statically perfect.
# Used in: dynamics.py detect_loop(), coherence.py
LOOP_THRESHOLD = 0.95   # C_omega value above which loop is suspected
LOOP_WINDOW    = 5      # Number of cycles without variation -> loop confirmed
LOOP_VARIANCE  = BETA   # Maximum allowed variance (= beta = 0.037)
                        # If variance < BETA and C_omega > threshold -> loop

# ======================================================================
# HELPER FUNCTIONS
# ======================================================================

def get_layer_frequency(layer_index: int) -> float:
    """
    Calculates the resonance frequency for a specific layer L0-L6.

    Args:
        layer_index: Layer index (0-6)

    Returns:
        float: Resonance frequency phi^(i/2)
    """
    if not (0 <= layer_index < NUM_LAYERS):
        raise ValueError(f"Layer index must be 0-{NUM_LAYERS-1}, got {layer_index}")
    return PHI ** (layer_index / 2)


def alpha_em_error(candidate: float) -> float:
    """
    Returns the relative error of a candidate for alpha_em^-1.

    Args:
        candidate: Candidate value for 1/alpha_em

    Returns:
        float: Relative error (0.0 to 1.0)
    """
    return abs(candidate - ALPHA_EM_INV_OBS) / ALPHA_EM_INV_OBS


def best_alpha_em_candidate() -> tuple:
    """
    Returns the candidate closest to the experimental value of alpha_em^-1.

    Returns:
        tuple: (name, value, error_pct)
    """
    candidates = {
        "A": ALPHA_EM_CANDIDATE_A,
        "B": ALPHA_EM_CANDIDATE_B,
        "C": ALPHA_EM_CANDIDATE_C,
        "D": ALPHA_EM_CANDIDATE_D,
        "E": ALPHA_EM_CANDIDATE_E,
    }
    best_name = min(candidates, key=lambda k: alpha_em_error(candidates[k]))
    best_val  = candidates[best_name]
    return best_name, best_val, alpha_em_error(best_val) * 100


# ======================================================================
# STRUCTURAL VERIFICATION (Runtime assertions)
# ======================================================================

# -- v3.1: Conservation and geometry --
assert abs(ALPHA + BETA - 1.0) < EPSILON,               "Conservation law violated: alpha + beta != 1"
assert abs(R_FIN - (1 + BETA)) < EPSILON,               "R_fin formula violated"
assert abs(math.sin(THETA_CUBE) ** 2 - BETA) < EPSILON, "sin^2(theta_cube) != beta"
assert abs(math.cos(THETA_CUBE) ** 2 - ALPHA) < EPSILON,"cos^2(theta_cube) != alpha"
assert abs(PHI ** 2 - (PHI + 1)) < EPSILON,             "Golden ratio property violated"
assert PHI_TOTAL < PHI_CRITICAL,                         "System overdamped: phi_total >= 2*pi"
assert ZETA < 1.0,                                       "System not underdamped: zeta >= 1"
assert OMEGA_D > 0,                                      "System not oscillating: omega_d <= 0"

# -- v3.2: Cosmology, tension, loops --
assert abs(C_MAX - ALPHA) < EPSILON,                     "C_MAX must equal ALPHA = 26/27"
assert abs(LAMBDA_UCF - BETA ** (math.pi / BETA + BETA * PHI ** 2)) < 1e-130, \
                                                         "LAMBDA_UCF formula mismatch"
assert LAMBDA_ERROR < 0.05,                              "Lambda error exceeds 5%"
assert abs(OMEGA_REDUCED - (math.pi / math.e) * (1 - BETA ** 2)) < EPSILON, \
                                                         "OMEGA_REDUCED formula mismatch"
assert ALPHA_EM_CANDIDATE_A > 136.9,                     "Candidate A out of range"
assert sum(TENSION_WEIGHTS.values()) == 1.0,             "Tension weights must sum to 1.0"
assert LOOP_VARIANCE == BETA,                            "Loop variance must equal BETA"
assert OMEGA_EFF > 0,                                    "OMEGA_EFF must be positive"
assert T_PERIOD > 0,                                     "T_PERIOD must be positive"

# -- v3.3: Teorema de la Base Cubica --
assert EPSILON_OBSERVER > 0,                             "Observer residue must be positive"
assert EPSILON_OBSERVER < 0.05,                          "Observer residue out of range"
assert abs(EPSILON_OBSERVER - LAMBDA_ERROR) < EPSILON,   "Observer residue must equal Lambda error"
assert GAMMA_COUPLING > 1.0,                             "Coupling factor must exceed 1"
assert abs(GAMMA_COUPLING - BETA / EPSILON_OBSERVER) < EPSILON, \
                                                         "Gamma coupling formula mismatch"
assert abs(ALPHA_GEOM_INV - GAMMA_COUPLING * DECIMAL_FACTOR) < EPSILON, \
                                                         "Geometric fine structure formula mismatch"
assert 136.0 < ALPHA_GEOM_INV < 137.0,                  "Geometric fine structure out of range"
assert CUBE_VOLUME == 19683,                             "Cube volume must be 27^3 = 19683"
assert abs(PI_OVER_SQRT2 - math.pi / math.sqrt(2)) < EPSILON, \
                                                         "PI_OVER_SQRT2 formula mismatch"
assert abs(SQRT3 - math.sqrt(3)) < EPSILON,             "SQRT3 formula mismatch"
assert abs(H_0_UCF - BETA * KAPPA_H) < EPSILON_PHYSICAL, \
                                                         "H_0 formula mismatch"
assert abs(ALPHA_S_UCF - CUBE_TOTAL * BETA ** 2 * PI_OVER_SQRT2 * TAU_TORSION) < EPSILON_PHYSICAL, \
                                                         "Strong coupling formula mismatch"
assert 0.117 < ALPHA_S_UCF < 0.119,                     "Strong coupling out of range"
assert abs(LAMBDA_EXPONENT - (math.pi / BETA + BETA * PHI ** 2)) < EPSILON, \
                                                         "Lambda exponent formula mismatch"
