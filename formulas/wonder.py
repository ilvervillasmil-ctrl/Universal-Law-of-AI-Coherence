import math
from .constants import S_REF


class WonderLogic:
    """
    Wonder/Awe: A = 1 - e^(-N/k)

    N = number of novel experiences
    k = saturation constant (defaults to S_REF when invalid)
    A -> 1 = beginner's mind (full wonder)
    A -> 0 = cynicism (structurally toxic)
    """

    @staticmethod
    def compute(novelty, sensitivity=5.0):
        """A = 1 - e^(-N/k)"""
        k = sensitivity if sensitivity > 0 else S_REF
        return 1.0 - math.exp(-max(0, novelty) / k)

    @staticmethod
    def compute_a(novelty, sensitivity=5.0):
        """Alias: A = 1 - e^(-N/k)"""
        return WonderLogic.compute(novelty, sensitivity)

    @staticmethod
    def from_state(curiosity=5, openness=5, routine=5):
        """Compute from human-readable values (0-10 scales)."""
        novelty = (curiosity + openness) / 2
        sensitivity = max(0.5, 10 - routine)
        return WonderLogic.compute(novelty, sensitivity)
