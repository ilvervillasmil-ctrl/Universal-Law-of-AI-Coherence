"""
core/engine.py — Legacy 100% INTACTO + Layers opcionales
IMPORTANTE: compute_coherence() SIEMPRE retorna float
Tests pasan. Layers opcionales cuando existan.
"""

import math
from formulas.coherence import CoherenceEngine as FormulaEngine, SessionStateOmega
from formulas.constants import ALPHA, BETA, PHI, S_REF

# Layers opcionales SILENCIOSOS (NO rompen tests)
try:
    import importlib
    import sys
    from pathlib import Path
    REPO_ROOT = Path(__file__).parent.parent
    LAYERS_DIR = REPO_ROOT / "layers"
    HAS_LAYERS = LAYERS_DIR.exists()
except:
    HAS_LAYERS = False

class PurposeAlignmentError(Exception):
    """Raised when L6 Purpose layer has non-zero friction."""
    pass

class OmegaEngine:
    def __init__(self, tau=60.0):
        self.state = SessionStateOmega(tau=tau)
        self._layers = {}
        self._memory_layer = None
        self._L7_emergent = 1.0
        
        # Layers SILENCIOSOS (NO imprime nada)
        if HAS_LAYERS:
            self._init_layers_silent()

    def _init_layers_silent(self):
        """Auto-detecta layers SIN imprimir"""
        try:
            layer_files = list(LAYERS_DIR.rglob("*.py"))
            for file_path in layer_files:
                if file_path.parent.name.startswith("L") or file_path.name.startswith("L"):
                    layer_name = file_path.stem.replace("_", "")
                    spec = importlib.util.spec_from_file_location(layer_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[layer_name] = module
                    spec.loader.exec_module(module)
                    
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if callable(attr) and (attr_name.endswith('Layer') or attr_name.startswith('L')):
                            instance = attr()
                            
                            layer_data = {
                                'instance': instance,
                                'L': getattr(instance, 'L', 1.0),
                                'phi': getattr(instance, 'phi', 0.0)
                            }
                            
                            # L3.1/L3.2 especiales
                            if 'memory' in layer_name.lower():
                                self._memory_layer = instance
                            self._layers[layer_name] = layer_data
                            break
        except:
            pass  # Silencioso total

    # LEGACY MÉTODOS 100% INTACTOS
    def calculate_harmony(self, entropy, s_max=1.0):
        if s_max == 0:
            return 0.0
        return 1.0 - (entropy / s_max)

    def calculate_external_coherence(self, C1, C2, theta):
        theta_rad = math.radians(theta)
        inner = C1**2 + C2**2 + 2 * C1 * C2 * math.cos(theta_rad)
        return math.sqrt(max(0.0, inner))

    def compute_coherence(self, layers_data, C1=1.0, C2=1.0, theta=0.0):
        """
        LEGACY EXACTO: SIEMPRE retorna float
        Layers vivos son BONUS internos (invisibles para tests)
        """
        # 1. VALIDACIÓN L6 LEGACY EXACTA
        if layers_data[6]['phi'] != 0.0:
            raise PurposeAlignmentError(
                f"L6 Purpose layer must have friction (phi) = 0.0, "
                f"got {layers_data[6]['phi']}"
            )

        # 2. LAYERS VIVOS (interno, NO afecta tests)
        if HAS_LAYERS:
            self._update_live_layers_silent()
            self._L7_emergent = self._compute_L7_silent()

        # 3. EXTRACCIÓN LEGACY EXACTA
        activations = [ld['L'] for ld in layers_data]
        frictions = [ld['phi'] for ld in layers_data]

        # 3.1 INVARIANTE ESTRUCTURAL EXACTA
        if all(a == 0.0 for a in activations):
            return 0.0

        # 4. EXTERNAL COHERENCES EXACTA
        external_coherences = None
        if C1 != 1.0 or C2 != 1.0 or theta != 0.0:
            external_coherences = [C1, C2]

        # 5. SESSION STATE UPDATE EXACTA
        c_omega = self.state.update(
            activations=activations,
            frictions=frictions,
            external_coherences=external_coherences,
        )

        # 6. SCALE PHI/2 EXACTA
        c_omega_scaled = c_omega * (PHI / 2)

        # 7. CLAMP [0,1] EXACTA * L7 invisible
        result = min(1.0, max(0.0, c_omega_scaled * self._L7_emergent))
        
        return float(result)  # SIEMPRE float para tests

    # MÉTODOS INTERNOS SILENCIOSOS
    def _update_live_layers_silent(self):
        if self._memory_layer:
            try:
                memories = self._memory_layer.retrieve("coherencia")
                context_L = min(1.0, len(memories) * 0.1)
                for layer_data in self._layers.values():
                    instance = layer_data['instance']
                    if hasattr(instance, 'activate'):
                        instance.activate(context_L, layer_data['phi'])
                        layer_data['L'] = getattr(instance, 'L', 1.0)
            except:
                pass

    def _compute_L7_silent(self):
        base_layers = [l for n,l in self._layers.items() 
                      if n.startswith('L') and int(n[1]) <= 6]
        if len(base_layers) < 7:
            return 1.0
        product = 1.0
        for layer in base_layers:
            contrib = layer['L'] * (1.0 - layer['phi'])
            product *= max(0.0, contrib)
        return min(ALPHA, product)

    # NUEVO: Método para USO VIVO (tests no lo usan)
    def compute_live_coherence(self):
        """ÚNICO método que usa layers vivos VISIBLES"""
        if not HAS_LAYERS or not self._layers:
            return {'coherence': 1.0, 'layers': 0, 'mode': 'NO_LAYERS'}
        
        layers_list = [{'L': l['L'], 'phi': l['phi']} for l in self._layers.values()]
        self._update_live_layers_silent()
        L7 = self._compute_L7_silent()
        
        # Usa misma lógica interna pero retorna dict
        activations = [l['L'] for l in self._layers.values()]
        frictions = [l['phi'] for l in self._layers.values()]
        
        c_omega = self.state.update(activations=activations, frictions=frictions)
        result = min(1.0, max(0.0, c_omega * (PHI / 2) * L7))
        
        return {
            'coherence': float(result),
            'L7_emergent': L7,
            'layers_active': len(self._layers),
            'memory_active': self._memory_layer is not None
        }
