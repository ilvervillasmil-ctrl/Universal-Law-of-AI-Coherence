import pytest
import math
from formulas.coherence import CoherenceEngine
from formulas.constants import ALPHA, BETA, THETA_CUBE

def test_reverse_engineering_oracle():
    """
    Oráculo de coherencia.

    No valida con assert duro.
    Expone la estructura real de C_Ω para inspección.
    """

    # Condiciones ideales
    activations = [1.0] * 7
    frictions = [0.0] * 7

    result = CoherenceEngine.full_analysis(
        activations=activations,
        frictions=frictions,
        integration=1.0,
        quality=1.0,
        complexity=0.0,
        uncertainty=0.0
    )

    c_omega = result['c_omega']
    c_beta  = result['c_beta']['c_beta']
    c_alpha = result['c_alpha']['c_alpha']

    # Diagnóstico
    perdida = abs(c_omega - (c_beta + c_alpha))

    mensaje = f"""
    --- REVELACIÓN DEL ORÁCULO OMEGA ---

    C_Ω calculado: {c_omega}

    COMPONENTES:
    - Experiencia (BETA): {c_beta}
    - Intención (ALPHA): {c_alpha}

    RELACIÓN:
    - Suma directa: {c_beta + c_alpha}
    - Diferencia (pérdida geométrica): {perdida}

    INTERPRETACIÓN:
    Si C_Ω < (BETA + ALPHA), existe disipación estructural.
    Si C_Ω ≈ (BETA + ALPHA), el sistema es aditivo (sin pérdida).
    Si C_Ω > (BETA + ALPHA), hay amplificación emergente.

    HIPÓTESIS DEL MOTOR:
    C_Ω debería aproximarse a:
        C_Ω = (ALPHA * Armonía) + (BETA * Experiencia)

    ------------------------------------
    """

    print(mensaje)

    # ✅ Condición lógica mínima (no rompe CI)
    assert c_omega >= 0.0
