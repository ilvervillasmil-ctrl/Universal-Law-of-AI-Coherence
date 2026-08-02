import math
from .constants import PHI, NUM_LAYERS, GOLDEN_ANG_RAD


class ResonanceLogic:
    """
    Inter-layer Resonance (rho): how well layers resonate with each other.
    rho = 1: perfect resonance
    rho = 0: layers disconnected
    """

    @staticmethod
    def calculate_layer_frequency(layer_index):
        """nu_i = PHI^(i/2). Higher layers vibrate faster."""
        return PHI ** (layer_index / 2)

    @staticmethod
    def calculate_phase_alignment(e_i, e_j):
        """Phase alignment between two layers: min/max ratio."""
        if e_i == 0 or e_j == 0:
            return 0.0
        return min(e_i, e_j) / max(e_i, e_j)

    @staticmethod
    def pair_resonance(e_i, e_j, phase_diff=0.0):
        """Resonance between two adjacent layers."""
        if e_i == 0 or e_j == 0:
            return 0.0
        magnitude = 2 * math.sqrt(e_i * e_j) / (e_i + e_j)
        phase_factor = (1 + math.cos(phase_diff)) / 2
        return magnitude * phase_factor

    @staticmethod
    def compute(energies):
        """rho = mean resonance across all adjacent layer pairs."""
        if sum(energies) == 0:
            return 0.0
        total = 0.0
        pairs = 0
        for i in range(len(energies) - 1):
            total += ResonanceLogic.pair_resonance(energies[i], energies[i + 1])
            pairs += 1
        return total / pairs if pairs > 0 else 0.0
