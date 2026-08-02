import math
from .constants import NUM_LAYERS


class NegentropyCalculator:
    """
    Negentropy: N = 1 - S/S_max

    Consciousness is NEGENTROPY. It reduces disorder.
    Harmony IS negentropy: H(S) = N
    """

    S_MAX = math.log(NUM_LAYERS)

    @staticmethod
    def shannon_entropy(energies):
        """S = -sum(p_i * ln(p_i))"""
        total = sum(energies)
        if total == 0:
            return NegentropyCalculator.S_MAX
        entropy = 0.0
        for e in energies:
            if e > 0:
                p = e / total
                entropy -= p * math.log(p)
        return entropy

    @staticmethod
    def compute(energies):
        """N = 1 - S/S_max. Returns negentropy [0,1]."""
        s = NegentropyCalculator.shannon_entropy(energies)
        return 1.0 - s / NegentropyCalculator.S_MAX

    @staticmethod
    def harmony(energies):
        """H(S) = N. Harmony IS negentropy."""
        return NegentropyCalculator.compute(energies)
