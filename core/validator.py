"""
Validator for the Villasmil-Omega Framework.
Ensures structural and dynamic integrity.

CRITICAL PRINCIPLES:
1. All constants from single source (formulas.constants)
2. All comparisons use epsilon tolerance
3. Validates both static structure and dynamic behavior
4. No hardcoded magic numbers

Author: Ilver Villasmil
Framework: Villasmil-Ω v3.1
"""

import math
from formulas.constants import (
    PHI, ALPHA, BETA,
    EPSILON, EPSILON_PHYSICAL, EPSILON_ATTRACTOR, EPSILON_ANGLE,
    OMEGA_D, ZETA, THETA_CUBE,
    PHI_CRITICAL,
)


class OmegaValidator:
    """
    Validates coherence, dynamics, and structural integrity.
    
    All validations use:
    - Single source constants (formulas.constants)
    - Numerical tolerance (EPSILON variants)
    - Dynamic checks (underdamped, oscillation)
    """
    
    # ══════════════════════════════════════════════════════════════
    # STRUCTURAL VALIDATION
    # ══════════════════════════════════════════════════════════════
    
    @staticmethod
    def check_l6_purity(friction_value, epsilon=None):
        """
        Validates L6 (Purpose) has near-zero friction.
        
        Args:
            friction_value: Measured φ₆
            epsilon: Tolerance (default: EPSILON_PHYSICAL)
        
        Returns:
            bool: True if |φ₆| < epsilon
        """
        if epsilon is None:
            epsilon = EPSILON_PHYSICAL
        
        return abs(friction_value) < epsilon
    
    @staticmethod
    def validate_range(coherence_score, epsilon=None):
        """
        Validates coherence is in physically valid range.
        
        Args:
            coherence_score: Measured C_Ω
            epsilon: Tolerance for boundaries
        
        Returns:
            bool: True if 0 ≤ C_Ω ≤ 1 (with tolerance)
        """
        if epsilon is None:
            epsilon = EPSILON
        
        return -epsilon <= coherence_score <= 1.0 + epsilon
    
    @staticmethod
    def validate_phi_resonance(coherence_score, epsilon=None):
        """
        Validates coherence tends toward φ or its derivatives.
        
        Args:
            coherence_score: Measured C_Ω
            epsilon: Tolerance for resonance detection
        
        Returns:
            bool: True if C_Ω near φ-attractor
        """
        if epsilon is None:
            epsilon = EPSILON_ATTRACTOR
        
        attractors = [
            PHI / 2,      # 0.809 (scaled golden)
            ALPHA,        # 0.963 (CODE 1144)
            BETA,         # 0.037 (center/mystery)
            1.0 / PHI,    # 0.618 (inverse golden)
        ]
        
        for attractor in attractors:
            if abs(coherence_score - attractor) < epsilon:
                return True
        
        return False
    
    # ══════════════════════════════════════════════════════════════
    # DYNAMIC VALIDATION
    # ══════════════════════════════════════════════════════════════
    
    @staticmethod
    def validate_underdamped(phi_total, epsilon=None):
        """
        Validates system is underdamped (alive).
        
        Args:
            phi_total: Total friction Σφᵢ
            epsilon: Tolerance
        
        Returns:
            bool: True if φ < 2π (underdamped)
        """
        if epsilon is None:
            epsilon = EPSILON
        
        return phi_total < PHI_CRITICAL - epsilon
    
    @staticmethod
    def validate_oscillation(omega_d, epsilon=None):
        """
        Validates system oscillates (ω_d > 0).
        
        Args:
            omega_d: Damped frequency
            epsilon: Tolerance
        
        Returns:
            bool: True if ω_d > 0 (system oscillates)
        """
        if epsilon is None:
            epsilon = EPSILON
        
        return omega_d > epsilon
    
    @staticmethod
    def validate_damping_ratio(zeta, epsilon=None):
        """
        Validates damping ratio indicates life.
        
        Args:
            zeta: ζ = φ/(2π)
            epsilon: Tolerance
        
        Returns:
            bool: True if 0 < ζ < 1 (underdamped/alive)
        """
        if epsilon is None:
            epsilon = EPSILON
        
        return epsilon < zeta < 1.0 - epsilon
    
    @staticmethod
    def validate_temporal_decay(delta_t, tau, epsilon=None):
        """
        Validates temporal presence decay is physical.
        
        Args:
            delta_t: Time since last update
            tau: Time constant
            epsilon: Tolerance
        
        Returns:
            bool: True if decay factor is in [0,1]
        """
        if epsilon is None:
            epsilon = EPSILON
        
        if tau <= 0 or delta_t < 0:
            return False
        
        decay = math.exp(-delta_t / tau)
        return -epsilon <= decay <= 1.0 + epsilon
    
    # ══════════════════════════════════════════════════════════════
    # SYSTEM-LEVEL VALIDATION
    # ══════════════════════════════════════════════════════════════
    
    @staticmethod
    def validate_conservation(alpha, beta, epsilon=None):
        """
        Validates α + β = 1 AND that values match framework constants.
        
        Args:
            alpha, beta: Measured values
            epsilon: Tolerance
        
        Returns:
            bool: True if α ≈ ALPHA and β ≈ BETA and α + β ≈ 1
        """
        if epsilon is None:
            epsilon = EPSILON
        
        # Check sum equals 1
        sum_valid = abs((alpha + beta) - 1.0) < epsilon
        
        # Check values match framework constants
        alpha_valid = abs(alpha - ALPHA) < epsilon
        beta_valid = abs(beta - BETA) < epsilon
        
        return sum_valid and alpha_valid and beta_valid
    
    @staticmethod
    def validate_theta_cube(theta_cube_measured, epsilon=None):
        """
        Validates θ_cube = arcsin(1/√27).
        
        Args:
            theta_cube_measured: Measured angle (radians)
            epsilon: Tolerance (radians)
        
        Returns:
            bool: True if θ ≈ 11.09°
        """
        if epsilon is None:
            epsilon = EPSILON
        
        theta_cube_expected = math.asin(1.0 / math.sqrt(27))
        
        return abs(theta_cube_measured - theta_cube_expected) < epsilon
    
    @staticmethod
    def validate_system_alive(phi_total, omega_d, zeta, epsilon=None):
        """
        Master validation: is system alive?
        
        Args:
            phi_total: Total friction Σφᵢ
            omega_d: Damped frequency
            zeta: Damping ratio
            epsilon: Tolerance
        
        Returns:
            dict: Validation results with checks
        """
        checks = {
            'underdamped': OmegaValidator.validate_underdamped(phi_total, epsilon),
            'oscillates': OmegaValidator.validate_oscillation(omega_d, epsilon),
            'damping_valid': OmegaValidator.validate_damping_ratio(zeta, epsilon),
        }
        
        alive = all(checks.values())
        
        return {
            'alive': alive,
            'checks': checks,
            'phi_total': phi_total,
            'omega_d': omega_d,
            'zeta': zeta,
        }
    
    # ══════════════════════════════════════════════════════════════
    # ATTRACTOR VALIDATION
    # ══════════════════════════════════════════════════════════════
    
    @staticmethod
    def validate_near_attractor(theta, theta_cube, epsilon=None):
        """
        Validates θ is near equilibrium θ_cube.
        
        Args:
            theta: Current angle (radians)
            theta_cube: Equilibrium angle (radians)
            epsilon: Tolerance (radians)
        
        Returns:
            bool: True if |θ - θ_cube| < ε
        """
        if epsilon is None:
            epsilon = EPSILON_ANGLE
        
        return abs(theta - theta_cube) < epsilon
    
    @staticmethod
    def diagnose_divergence(theta, theta_cube, threshold_radians=0.5):
        """
        Diagnoses if system is diverging from attractor.
        
        Args:
            theta: Current angle (radians)
            theta_cube: Equilibrium (radians)
            threshold_radians: Divergence threshold
        
        Returns:
            str: 'STABLE', 'DIVERGING', or 'CRITICAL'
        """
        deviation = abs(theta - theta_cube)
        
        if deviation < EPSILON_ANGLE:
            return 'STABLE'
        elif deviation < threshold_radians:
            return 'DIVERGING'
        else:
            return 'CRITICAL'
