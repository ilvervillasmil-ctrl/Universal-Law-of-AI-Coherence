# formulas/interaction.py
"""
ExternalInteraction - Combina coherencias externas vía ley del coseno.
Soporta escalares, pares, tripletas. Compatible con todos los tests existentes.
"""

import math
from typing import Iterable, Tuple, Union, List

Number = Union[int, float]
Item = Union[Number, Tuple[Number, Number], Tuple[Number, Number, Number]]


class ExternalInteraction:
    """
    Modela interacción entre coherencias externas usando ley del coseno:
    
    C_total² = C1² + C2² + 2·C1·C2·cos(θ)
    
    Casos especiales:
    • θ=0 (love): C1 + C2
    • θ=π (conflict): |C1 - C2|
    • θ=π/2 (independence): √(C1² + C2²)
    """

    # --- FUNCIONES BÁSICAS (tests explícitos) ---

    @staticmethod
    def love(c1: Number, c2: Number) -> float:
        """θ=0: C1 + C2"""
        return float(c1) + float(c2)

    @staticmethod
    def conflict(c1: Number, c2: Number) -> float:
        """θ=π: |C1 - C2|"""
        return abs(float(c1) - float(c2))

    @staticmethod
    def independence(c1: Number, c2: Number) -> float:
        """θ=π/2: √(C1² + C2²)"""
        c1 = float(c1)
        c2 = float(c2)
        return math.hypot(c1, c2)

    # --- NÚCLEO GEOMÉTRICO ---

    @staticmethod
    def compute_pair(c1: Number, c2: Number, theta: Number = 0.0) -> float:
        """
        Combina dos coherencias con ángulo θ (radianes).
        
        Firma compatible con tests existentes:
        • compute_pair(c1, c2) → θ=0 (love)
        • compute_pair(c1, c2, θ) → ángulo explícito
        """
        c1 = float(c1)
        c2 = float(c2)
        theta = float(theta)

        # Casos límite por robustez numérica
        if abs(theta) < 1e-12:
            return ExternalInteraction.love(c1, c2)
        if abs(theta - math.pi) < 1e-12:
            return ExternalInteraction.conflict(c1, c2)
        if abs(theta - math.pi / 2) < 1e-12:
            return ExternalInteraction.independence(c1, c2)

        # Ley del coseno general
        cos_t = math.cos(theta)
        val_sq = c1 * c1 + c2 * c2 + 2.0 * c1 * c2 * cos_t
        
        # Clamp numérico para ruido negativo mínimo
        if val_sq < 0 and val_sq > -1e-15:
            val_sq = 0.0
        return math.sqrt(max(0.0, val_sq))

    # --- COERCIÓN FLEXIBLE ---

    @staticmethod
    def _coerce_item(item: Item) -> Tuple[float, float, float]:
        """
        Convierte item a (c1, c2, θ):
        
        • float x           → (x, 0.0, 0.0)
        • (x,)             → (x, 0.0, 0.0)  
        • (c1, c2)         → (c1, c2, 0.0)
        • (c1, c2, θ)      → (c1, c2, θ)
        """
        if isinstance(item, (int, float)):
            return float(item), 0.0, 0.0

        if isinstance(item, (tuple, list)):
            if len(item) == 1:
                return float(item[0]), 0.0, 0.0
            if len(item) == 2:
                return float(item[0]), float(item[1]), 0.0
            if len(item) == 3:
                return float(item[0]), float(item[1]), float(item[2])

        raise TypeError(f"Unsupported interaction item: {item!r}")

    # --- COMBINACIÓN MÚLTIPLE ---

    @staticmethod
    def compute_multi(items: Iterable[Item]) -> float:
        """
        Combina colección de coherencias/pares/tripletas.
        
        Tests esperados:
        • compute_multi([]) → 0.0
        • compute_multi([0.75]) → 0.75  
        • compute_multi([0.3, 0.4, 0.3]) → 1.0 (suma θ=0)
        """
        items = list(items)
        if not items:
            return 0.0

        # Único item: devolver su valor intrínseco
        if len(items) == 1:
            c1, c2, theta = ExternalInteraction._coerce_item(items[0])
            if c2 == 0.0 and abs(theta) < 1e-12:
                return c1  # Escalar puro → mismo valor
            return ExternalInteraction.compute_pair(c1, c2, theta)

        # Múltiples items: reducción acumulativa θ=0 (love)
        total = 0.0
        for item in items:
            c1, c2, theta = ExternalInteraction._coerce_item(item)
            block = ExternalInteraction.compute_pair(c1, c2, theta)
            total = ExternalInteraction.compute_pair(total, block, 0.0)

        return total
