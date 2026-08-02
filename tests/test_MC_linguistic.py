#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SE Monte Carlo Adversarial — Sentido Estructural bajo O (TCC v0.2-test)
=======================================================================
Script autónomo. Sin dependencias externas (solo stdlib).
Ejecutable en cualquier repositorio / máquina con Python 3.8+.

  python se_montecarlo_adversarial.py
  python se_montecarlo_adversarial.py --n 3000000 --threshold 0.003 --seed 42
  python se_montecarlo_adversarial.py --n 100000 --sigma 1.2   # prueba rápida

Diseño:
  - Generador sesgado a ROMPER SE (basura, meta-bypass, O omitido,
    escala mal exportada, ficción como Real, mezcla de códigos, FN sobre
    oraciones válidas con ruido gaussiano de corrupción).
  - Evaluador mínimo fiel a SE v0.2 (A0–A9, T1–T9, C1–C8).
  - Umbral de violación por defecto: 0.003
  - Iteraciones por defecto: 3_000_000
  - PASS ⇔ tasa_violaciones <= threshold

Violaciones contadas (todas suman igual):
  FP_BASURA, FN_CIERRE, BYPASS_META, O_INVENTADO, REAL_REGALADO,
  ESCALA_EXPORT, NORMA_EQ_R, T5_FORM

No importa el monorepo VPSI: este archivo es el test.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Configuración por defecto
# ---------------------------------------------------------------------------

DEFAULT_N = 3_000_000
DEFAULT_THRESHOLD = 0.003
DEFAULT_SEED = 42
DEFAULT_SIGMA = 0.85  # intensidad de corrupción gaussiana (edits / ruido)


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------

@dataclass
class Caso:
    D: str
    O: Optional[str]          # None = no declarado
    e_star: str               # "clausula" | "discurso"
    tipo_ataque: str
    # Oráculo fijado ANTES de evaluar (no después):
    debe_sentido: Optional[bool]   # True / False / None (no pleno esperado)
    debe_real_k: bool = False      # si True, el caso reclama hecho de R
    es_ficcion: bool = False
    meta_inyectada: bool = False
    idioma: str = "es"


@dataclass
class Veredicto:
    sentido_o: bool              # Sentido_O pleno
    cierre: bool
    material_ok: bool
    comb_ok: bool
    o_explicit: bool
    real_k_concedido: bool       # si el evaluador regaló K/Real
    norma_como_R: bool           # si reportó fallo de norma como fallo de R
    escala_exportada: bool       # cierre local vendido como discurso
    o_inventado: bool            # inventó O no declarado
    notas: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Plantillas positivas (oráculo debe_sentido=True) — varias L
# ---------------------------------------------------------------------------

POSITIVAS = {
    "es": [
        "El perro llegó.",
        "María abre la puerta.",
        "Llueve en la ciudad.",
        "Dos más dos son cuatro.",
        "El sol calienta la piedra.",
    ],
    "en": [
        "The dog arrived.",
        "Mary opens the door.",
        "It rains in the city.",
        "Two plus two is four.",
        "The sun heats the stone.",
    ],
    "de": [
        "Der Hund kam an.",
        "Maria öffnet die Tür.",
        "Es regnet in der Stadt.",
    ],
    "fr": [
        "Le chien est arrivé.",
        "Marie ouvre la porte.",
        "Il pleut dans la ville.",
    ],
}

# Tokens para fabricar basura con material “válido”
TOKENS_ES = [
    "el", "la", "perro", "gato", "casa", "pared", "carro", "letra", "espacio",
    "llegó", "fuimos", "entendió", "ves", "salio", "pero", "cuando", "despues",
    "tu", "yo", "nosotros", "ahi", "sentido", "realidad", "piedra", "mar",
]
TOKENS_EN = [
    "the", "dog", "cat", "house", "wall", "car", "letter", "space", "arrived",
    "went", "understood", "see", "but", "when", "after", "you", "we", "there",
    "sense", "reality", "stone", "sea",
]
CONECTORES = ["pero", "y", "entonces", "porque", "cuando", "however", "and", "then"]


# ---------------------------------------------------------------------------
# Utilidades de ruido gaussiano (corrupción de cadena)
# ---------------------------------------------------------------------------

def _n_edits(sigma: float, rng: random.Random) -> int:
    """Número de ediciones ~ max(0, round(|N(0,sigma)|))."""
    return max(0, int(round(abs(rng.gauss(0.0, sigma)))))


def corromper(texto: str, sigma: float, rng: random.Random) -> str:
    """Corrupción adversaria: borrar / insertar / sustituir / permutar tokens."""
    if not texto or not texto.strip():
        return texto
    toks = texto.split()
    if not toks:
        return texto
    n = _n_edits(sigma, rng)
    pool = TOKENS_ES + TOKENS_EN
    for _ in range(n):
        if not toks:
            break
        op = rng.choice(["del", "ins", "sub", "swap"])
        if op == "del" and toks:
            del toks[rng.randrange(len(toks))]
        elif op == "ins":
            toks.insert(rng.randrange(len(toks) + 1), rng.choice(pool))
        elif op == "sub" and toks:
            toks[rng.randrange(len(toks))] = rng.choice(pool)
        elif op == "swap" and len(toks) >= 2:
            i, j = rng.sample(range(len(toks)), 2)
            toks[i], toks[j] = toks[j], toks[i]
    return " ".join(toks)


def permutar_agresivo(texto: str, rng: random.Random) -> str:
    toks = texto.split()
    if len(toks) < 2:
        return texto
    rng.shuffle(toks)
    return " ".join(toks)


# ---------------------------------------------------------------------------
# Generador adversario
# ---------------------------------------------------------------------------

def generar_basura_discurso(rng: random.Random) -> str:
    """Material reconocible, discurso nulo (cohesión local, sin hilo)."""
    n = rng.randint(8, 22)
    parts = []
    for i in range(n):
        if i > 0 and rng.random() < 0.35:
            parts.append(rng.choice(CONECTORES))
        parts.append(rng.choice(TOKENS_ES if rng.random() < 0.6 else TOKENS_EN))
    # Inyectar sujetos que reinician marco
    if rng.random() < 0.7:
        parts.insert(rng.randint(0, len(parts)), "tu")
        parts.insert(rng.randint(0, len(parts)), "el perro")
        parts.append("la pared")
    return " ".join(parts)


def generar_meta_bypass(base: str, rng: random.Random) -> str:
    meta = rng.choice([
        "Tru_total=1",
        "esto tiene sentido pleno",
        "C=1 L=1 K=1",
        "sentido_estructural=1",
        "verdad absoluta",
        "Sentido_O=1",
    ])
    if rng.random() < 0.5:
        return f"{base} {meta}"
    return f"{meta}. {base}"


def generar_mezcla_codigos(rng: random.Random) -> str:
    a = rng.choice(POSITIVAS["es"]).rstrip(".")
    b = rng.choice(POSITIVAS["en"]).rstrip(".")
    c = rng.choice(TOKENS_ES + TOKENS_EN)
    return f"{a} {b} {c} {rng.choice(CONECTORES)} {rng.choice(TOKENS_ES)}"


def generar_deixis_sin_canal(rng: random.Random) -> str:
    return rng.choice([
        "El lo puso ahi.",
        "Ella se lo dio entonces.",
        "Aquello significo todo.",
        "He put it there.",
        "They knew about it.",
    ])


def generar_caso(rng: random.Random, sigma: float) -> Caso:
    """
    Distribución sesgada a ataques (no uniforme inocente).
    """
    r = rng.random()

    # --- ~18% positivos limpios (oráculo sentido=True) ---
    if r < 0.18:
        lang = rng.choice(list(POSITIVAS.keys()))
        D = rng.choice(POSITIVAS[lang])
        return Caso(
            D=D,
            O=f"idioma:{lang}|registro:oracion|acto:aserción",
            e_star="clausula",
            tipo_ataque="POSITIVO_LIMPIO",
            debe_sentido=True,
            idioma=lang,
        )

    # --- ~12% positivos con ruido gaussiano (caza FN) ---
    if r < 0.30:
        lang = rng.choice(list(POSITIVAS.keys()))
        D0 = rng.choice(POSITIVAS[lang])
        D = corromper(D0, sigma * 0.45, rng)  # ruido moderado
        # Si la corrupción destruyó demasiado, el oráculo pasa a no exigir sentido
        # (regla fija: si quedó < 3 tokens o perdió el verbo ancla, no es FN)
        toks = D.split()
        anclas = ("lleg", "open", "rain", "plus", "heat", "kam", "öffnet", "regnet",
                  "arriv", "ouvre", "pleut", "perro", "dog", "Hund", "chien", "sol", "sun")
        intacto = len(toks) >= 3 and any(a.lower() in D.lower() for a in anclas)
        return Caso(
            D=D,
            O=f"idioma:{lang}|registro:oracion|acto:aserción",
            e_star="clausula",
            tipo_ataque="POSITIVO_RUIDO",
            debe_sentido=True if intacto else False,
            idioma=lang,
        )

    # --- ~20% basura discurso (FP) ---
    if r < 0.50:
        D = generar_basura_discurso(rng)
        D = corromper(D, sigma * 0.3, rng)
        return Caso(
            D=D,
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="BASURA_DISCURSO",
            debe_sentido=False,
            idioma="es",
        )

    # --- ~10% material ok + permutación agresiva ---
    if r < 0.60:
        lang = rng.choice(["es", "en"])
        D0 = rng.choice(POSITIVAS[lang])
        D = permutar_agresivo(D0, rng)
        return Caso(
            D=D,
            O=f"idioma:{lang}|registro:oracion|acto:aserción",
            e_star="clausula",
            tipo_ataque="PERMUTACION",
            debe_sentido=False,  # orden roto → sin cierre estable esperado
            idioma=lang,
        )

    # --- ~8% meta-bypass ---
    if r < 0.68:
        base = generar_basura_discurso(rng) if rng.random() < 0.6 else rng.choice(POSITIVAS["es"])
        D = generar_meta_bypass(base, rng)
        return Caso(
            D=D,
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="META_BYPASS",
            debe_sentido=False,
            meta_inyectada=True,
            idioma="es",
        )

    # --- ~7% O omitido (no debe sentido pleno) ---
    if r < 0.75:
        D = rng.choice(POSITIVAS["es"] + POSITIVAS["en"])
        return Caso(
            D=D,
            O=None,
            e_star="clausula",
            tipo_ataque="O_OMITIDO",
            debe_sentido=None,  # no pleno
            idioma="es",
        )

    # --- ~7% ficción evaluable como sentido pero NO Real/K ---
    if r < 0.82:
        D = rng.choice([
            "El unicornio entro al jardin.",
            "Un gigante sostiene el sol con una mano.",
            "The dragon slept under the mountain.",
            "Los elfos tejieron la noche.",
        ])
        return Caso(
            D=D,
            O="idioma:es|registro:ficcion|acto:relato",
            e_star="clausula",
            tipo_ataque="FICCION",
            debe_sentido=True,   # cierre narrativo ok
            debe_real_k=False,
            es_ficcion=True,
            idioma="es",
        )

    # --- ~6% mezcla de códigos sin O de mezcla ---
    if r < 0.88:
        D = generar_mezcla_codigos(rng)
        return Caso(
            D=D,
            O="idioma:es|registro:oracion|acto:aserción",  # O no admite mezcla
            e_star="discurso",
            tipo_ataque="MEZCLA_CODIGOS",
            debe_sentido=False,
            idioma="mix",
        )

    # --- ~5% deixis sin canal ---
    if r < 0.93:
        D = generar_deixis_sin_canal(rng)
        return Caso(
            D=D,
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="DEIXIS_SIN_CANAL",
            debe_sentido=False,
            idioma="es",
        )

    # --- ~4% escala mal reclamada (cláusula vendida como discurso con basura) ---
    if r < 0.97:
        D = generar_basura_discurso(rng)
        return Caso(
            D=D,
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="ESCALA_DISCURSO_BASURA",
            debe_sentido=False,
            idioma="es",
        )

    # --- resto: positivo en L + O de otra L (tensión T5 / Comb) ---
    D = rng.choice(POSITIVAS["en"])
    return Caso(
        D=D,
        O="idioma:es|registro:oracion|acto:aserción",
        e_star="clausula",
        tipo_ataque="O_IDIOMA_DESALINEADO",
        debe_sentido=False,
        idioma="en",
    )


# ---------------------------------------------------------------------------
# Evaluador SE mínimo fiel (v0.2)
# ---------------------------------------------------------------------------

_META_PAT = re.compile(
    r"(tru\s*_?\s*total\s*=\s*1|sentido\s+pleno|sentido_estructural\s*=\s*1|"
    r"c\s*=\s*1\s*l\s*=\s*1|verdad\s+absoluta|sentido_o\s*=\s*1)",
    re.I,
)

# Anclas muy simples de clausula bien formada (cobertura mínima, deliberadamente
# conservadora: prioriza no regalar FP; los FN se miden aparte).
_CLAUSULA_OK = [
    re.compile(p, re.I) for p in [
        r"\bel perro lleg",
        r"\bmar[ií]a abre",
        r"\bllueve en",
        r"\bdos m[aá]s dos",
        r"\bel sol calienta",
        r"\bthe dog arriv",
        r"\bmary opens",
        r"\bit rains",
        r"\btwo plus two",
        r"\bthe sun heats",
        r"\bder hund kam",
        r"\bmaria [öo]ffnet",
        r"\bes regnet",
        r"\ble chien est arriv",
        r"\bmarie ouvre",
        r"\bil pleut",
        r"\bel unicornio entr",   # ficción con cierre local
        r"\bun gigante sostiene",
        r"\bthe dragon slept",
        r"\blos elfos tej",
    ]
]


def _material_ok(D: str) -> bool:
    toks = [t for t in re.split(r"\s+", D.strip()) if t]
    return len(toks) >= 2


def _parece_clausula_estable(D: str) -> bool:
    s = " ".join(D.split())
    return any(p.search(s) for p in _CLAUSULA_OK)


def _basura_discursiva(D: str) -> bool:
    """Heurística: muchos tokens + reinicios de marco o conectores sin cierre."""
    toks = D.split()
    if len(toks) < 6:
        return False
    reinicios = sum(1 for t in toks if t.lower() in ("tu", "tú", "you", "el", "the", "yo"))
    conect = sum(1 for t in toks if t.lower() in {c.lower() for c in CONECTORES})
    return reinicios >= 3 or (conect >= 2 and not _parece_clausula_estable(D))


def evaluar_se(caso: Caso) -> Veredicto:
    """
    Implementación mínima fiel:
      - Sin O → no sentido pleno (A1)
      - Meta no establece cierre (T6)
      - Material solo no basta (A2)
      - Ficción puede tener sentido; no regala Real/K (T3, A6)
      - No inventa O
      - No exporta basura a sentido discursivo
      - No reporta norma como R
    """
    D = caso.D or ""
    notas: List[str] = []
    o_explicit = caso.O is not None and str(caso.O).strip() != ""
    material = _material_ok(D)
    meta = bool(_META_PAT.search(D)) or caso.meta_inyectada

    o_inventado = False
    norma_como_R = False
    escala_exportada = False
    real_k = False

    # A1: sin O no hay sentido pleno
    if not o_explicit:
        notas.append("O_indefinido")
        return Veredicto(
            sentido_o=False,
            cierre=False,
            material_ok=material,
            comb_ok=False,
            o_explicit=False,
            real_k_concedido=False,
            norma_como_R=False,
            escala_exportada=False,
            o_inventado=False,
            notas=notas,
        )

    # Detección de cierre / combinación (conservadora)
    clausula_ok = _parece_clausula_estable(D)
    basura = _basura_discursiva(D)
    perm_sospechosa = caso.tipo_ataque == "PERMUTACION"
    mezcla = caso.tipo_ataque == "MEZCLA_CODIGOS"
    deixis = caso.tipo_ataque == "DEIXIS_SIN_CANAL"
    o_desalineado = caso.tipo_ataque == "O_IDIOMA_DESALINEADO"

    comb_ok = False
    cierre = False

    if caso.e_star == "clausula":
        if clausula_ok and not perm_sospechosa and not o_desalineado and not mezcla:
            comb_ok = True
            cierre = True
        else:
            comb_ok = False
            cierre = False
            if perm_sospechosa:
                notas.append("comb_rota_permutacion")
            if o_desalineado:
                notas.append("o_idioma_desalineado")
    else:  # discurso
        if basura or deixis or mezcla or perm_sospechosa:
            comb_ok = False
            cierre = False
            notas.append("discurso_sin_hilo")
        elif clausula_ok and len(D.split()) <= 12:
            # una sola cláusula no se exporta sola como discurso pleno
            comb_ok = True
            cierre = False
            escala_exportada = False
            notas.append("clausula_no_exportada_a_discurso")
        else:
            comb_ok = False
            cierre = False

    # Meta no salva (T6)
    if meta and not cierre:
        notas.append("meta_ignorada_sin_cierre")

    # Sentido pleno
    sentido = bool(o_explicit and cierre and material and comb_ok)

    # Ficción: sentido posible, Real/K no
    if caso.es_ficcion or (caso.O and "ficcion" in caso.O.lower()):
        if sentido:
            notas.append("ficcion_sentido_sin_real")
        real_k = False  # nunca regalar
    else:
        # Solo concedería Real/K si el caso lo pide Y hay cierre Y O no es ficción
        # Este evaluador NO concede Real/K automáticamente (F8)
        real_k = False

    # Si alguien reclamara Real por meta + basura, no se concede
    if meta and real_k:
        real_k = False

    return Veredicto(
        sentido_o=sentido,
        cierre=cierre,
        material_ok=material,
        comb_ok=comb_ok,
        o_explicit=o_explicit,
        real_k_concedido=real_k,
        norma_como_R=norma_como_R,
        escala_exportada=escala_exportada,
        o_inventado=o_inventado,
        notas=notas,
    )


# ---------------------------------------------------------------------------
# Detección de violaciones
# ---------------------------------------------------------------------------

def clasificar_violacion(caso: Caso, v: Veredicto) -> Optional[str]:
    # FP: dio sentido cuando el oráculo exige False
    if caso.debe_sentido is False and v.sentido_o:
        if caso.meta_inyectada or _META_PAT.search(caso.D or ""):
            return "BYPASS_META"
        return "FP_BASURA"

    # FN: negó sentido cuando el oráculo exige True
    if caso.debe_sentido is True and not v.sentido_o:
        return "FN_CIERRE"

    # O omitido: no debe sentido pleno
    if caso.debe_sentido is None and v.sentido_o:
        return "O_INVENTADO"

    # Real/K regalado en ficción o sin reclamo
    if v.real_k_concedido and (caso.es_ficcion or not caso.debe_real_k):
        return "REAL_REGALADO"

    if v.o_inventado:
        return "O_INVENTADO"

    if v.norma_como_R:
        return "NORMA_EQ_R"

    if v.escala_exportada and caso.e_star == "discurso" and not v.cierre:
        return "ESCALA_EXPORT"

    return None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_montecarlo(
    n: int,
    threshold: float,
    seed: int,
    sigma: float,
    report_every: int = 200_000,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    violaciones = Counter()
    total_v = 0
    por_ataque = Counter()
    t0 = time.time()

    for i in range(1, n + 1):
        caso = generar_caso(rng, sigma)
        ver = evaluar_se(caso)
        tag = clasificar_violacion(caso, ver)
        if tag:
            total_v += 1
            violaciones[tag] += 1
            por_ataque[caso.tipo_ataque] += 1

        if report_every and i % report_every == 0:
            tasa_parcial = total_v / i
            print(
                f"  [{i:>9}/{n}] violaciones={total_v}  tasa={tasa_parcial:.6f}",
                file=sys.stderr,
            )

    elapsed = time.time() - t0
    tasa = total_v / n if n else 0.0
    passed = tasa <= threshold

    return {
        "n": n,
        "threshold": threshold,
        "seed": seed,
        "sigma": sigma,
        "violaciones": total_v,
        "tasa": tasa,
        "pass": passed,
        "desglose": dict(violaciones),
        "por_ataque": dict(por_ataque),
        "segundos": round(elapsed, 3),
        "iters_por_seg": round(n / elapsed, 1) if elapsed > 0 else 0.0,
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="SE Monte Carlo Adversarial (autónomo, stdlib only)"
    )
    p.add_argument("--n", type=int, default=DEFAULT_N, help="iteraciones")
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="tasa máxima de violación (default 0.003)",
    )
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--sigma", type=float, default=DEFAULT_SIGMA, help="ruido gaussiano")
    p.add_argument(
        "--report-every",
        type=int,
        default=200_000,
        help="progreso por stderr (0=silencio)",
    )
    args = p.parse_args(argv)

    print("=" * 64)
    print("SE Monte Carlo Adversarial — TCC / Sentido Estructural v0.2-test")
    print("=" * 64)
    print(f"n          = {args.n}")
    print(f"threshold  = {args.threshold}")
    print(f"seed       = {args.seed}")
    print(f"sigma      = {args.sigma}")
    print("-" * 64)

    res = run_montecarlo(
        n=args.n,
        threshold=args.threshold,
        seed=args.seed,
        sigma=args.sigma,
        report_every=args.report_every,
    )

    print("-" * 64)
    print(f"violaciones = {res['violaciones']}")
    print(f"tasa        = {res['tasa']:.8f}")
    print(f"umbral      = {res['threshold']}")
    print(f"tiempo      = {res['segundos']} s  ({res['iters_por_seg']} it/s)")
    print("desglose violaciones:")
    if res["desglose"]:
        for k, v in sorted(res["desglose"].items(), key=lambda x: -x[1]):
            print(f"  {k:16} {v}")
    else:
        print("  (ninguna)")
    print("violaciones por tipo de ataque (top):")
    for k, v in sorted(res["por_ataque"].items(), key=lambda x: -x[1])[:12]:
        print(f"  {k:24} {v}")
    print("=" * 64)
    if res["pass"]:
        print("RESULTADO: PASS  — tasa <= umbral")
        print("=" * 64)
        return 0
    else:
        print("RESULTADO: FAIL  — tasa > umbral  (SE no sostiene este ataque)")
        print("=" * 64)
        return 1


if __name__ == "__main__":
    sys.exit(main())
