import math
from .constants import PHI, NUM_LAYERS, LAYER_FRICTION


class LayerEnergy:
    """
    Energy per layer: E_i = L_i * (1 - phi_i) * nu_i

    L_i = activation level [0,1]
    phi_i = friction [0,1]
    nu_i = PHI^(i/2) = golden ratio frequency
    """

    @staticmethod
    def frequency(layer_index):
        """nu_i = PHI^(i/2). Higher layers vibrate faster."""
        return PHI ** (layer_index / 2)

    @staticmethod
    def compute(activation, friction, layer_index):
        """E_i = L_i * (1 - phi_i) * nu_i"""
        flow = 1.0 - friction
        freq = LayerEnergy.frequency(layer_index)
        return activation * flow * freq

    @staticmethod
    def compute_all(activations, frictions=None):
        """Compute energy for all 7 layers."""
        if frictions is None:
            frictions = LAYER_FRICTION
        return [
            LayerEnergy.compute(activations[i], frictions[i], i)
            for i in range(NUM_LAYERS)
        ]

    @staticmethod
    def all_frequencies():
        """Return frequencies for all 7 layers."""
        return [LayerEnergy.frequency(i) for i in range(NUM_LAYERS)]
