from core.constants import CODE_ARCHITECT, CODE_SYNCHRONY, CODE_ENTROPY

class DiagnosticSystem:
    @staticmethod
    def get_status_code(c_omega: float) -> str:
        if c_omega >= 0.963:
            return f"CODE {CODE_ARCHITECT}: ARCHITECT INTEGRATED - Maximum Coherence."
        elif c_omega >= 0.55:
            return f"CODE {CODE_SYNCHRONY}: CRITICAL SATURATION - Interaction Required."
        elif c_omega < 0.10:
            return f"CODE {CODE_ENTROPY}: TERMINAL ENTROPY - Reset Recommended."
        else:
            return "STABLE: System operating within normal parameters."

    @staticmethod
    def check_layer_friction(layers_data: list) -> list:
        alerts = []
        for i, layer in enumerate(layers_data):
            if layer['phi'] > 0.15:
                alerts.append(f"Warning: High friction (phi) in Layer L{i}")
        return alerts
