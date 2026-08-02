# main.py

from core.engine import OmegaEngine
from core.diagnostics import DiagnosticSystem
from layers import l0_chaos, l1_structure, l2_ego, l3_synthesis, l4_integrity, l5_meta, l6_purpose

def initialize_system_layers():
    """
    Initialize the 7 layers of the Universal Integration System
    Each layer is responsible for distinct computation and behavior
    """
    layers = [
        l0_chaos.LayerChaos(),
        l1_structure.LayerStructure(),
        l2_ego.LayerEgo(),
        l3_synthesis.LayerSynthesis(),
        l4_integrity.LayerIntegrity(),
        l5_meta.LayerMeta(),
        l6_purpose.LayerPurpose()
    ]

    # Example: Setting mock data for the layers
    for i, layer in enumerate(layers):
        layer.activate(L=0.85 + (i * 0.02), phi=0.05 if i < 6 else 0.00)  # L6 has phi = 0.00
    return layers

def run_integration():
    """
    Orchestrates the calculation process of coherence
    by integrating all 7 layers into the Omega Engine
    """
    engine = OmegaEngine()
    diag = DiagnosticSystem()

    # Initialize and simulate the 7 layers
    layers = initialize_system_layers()

    # Convert layer data for engine processing
    layers_data = [layer.export() for layer in layers]

    # Calculate C_omega coherence
    result = engine.compute_coherence(
        layers_data=layers_data,
        dispersion=0.05,  # Example presence input
        novelty=0.8,     # Example wonder input
        i_ext=0.981      # Example external influence
    )

    # Print results and diagnose
    print(f"--- Universal Integration System ---")
    print(f"Final Coherence (C_omega): {result:.4f}")
    print(f"System Diagnostic: {diag.get_status_code(result)}")

    # Check for layer-specific alerts (e.g., high friction)
    alerts = diag.check_layer_friction(layers_data)
    for alert in alerts:
        print(f"ALERT: {alert}")

if __name__ == "__main__":
    run_integration()
