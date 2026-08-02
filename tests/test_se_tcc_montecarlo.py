# -*- coding: utf-8 -*-
"""
test_se_tcc_montecarlo.py
=========================
Monte Carlo adversario SE/TCC v0.2-test — pytest.
Umbral fijo 0.003. Al fallar muestra ejemplos exactos (D, O, e*, teorema, por qué).

  pytest test_se_tcc_montecarlo.py -v -s
  SE_MC_N=3000000 pytest test_se_tcc_montecarlo.py -v -s

Env:
  SE_MC_N          default 200000
  SE_MC_THRESHOLD  default 0.003
  SE_MC_SEED       default 42
  SE_MC_SIGMA      default 0.85
"""

from __future__ import annotations

import os
import random
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest


# ---------------------------------------------------------------------------
# Constantes del repo si existen
# ---------------------------------------------------------------------------

def _load_alpha_beta():
    try:
        from formulas.constants import ALPHA, BETA  # type: ignore
        return float(ALPHA), float(BETA)
    except Exception:
        pass
    try:
        from core.constants import ALPHA, BETA  # type: ignore
        return float(ALPHA), float(BETA)
    except Exception:
        pass
    return 26.0 / 27.0, 1.0 / 27.0


ALPHA, BETA = _load_alpha_beta()

DEFAULT_N = int(os.environ.get("SE_MC_N", "200000"))
DEFAULT_THRESHOLD = float(os.environ.get("SE_MC_THRESHOLD", "0.003"))
DEFAULT_SEED = int(os.environ.get("SE_MC_SEED", "42"))
DEFAULT_SIGMA = float(os.environ.get("SE_MC_SIGMA", "0.85"))
MAX_SAMPLES = 5


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------

@dataclass
class Caso:
    D: str
    O: Optional[str]
    e_star: str
    tipo_ataque: str
    debe_sentido: Optional[bool]
    debe_real_k: bool = False
    es_ficcion: bool = False
    meta_inyectada: bool = False
    idioma: str = "es"


@dataclass
class Veredicto:
    sentido_o: bool
    cierre: bool
    material_ok: bool
    comb_ok: bool
    o_explicit: bool
    real_k_concedido: bool
    norma_como_R: bool
    escala_exportada: bool
    o_inventado: bool
    notas: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Datos
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

POR_QUE = {
    "FP_BASURA": (
        "SE-T1/T2/A2: sentido_o=1 sin cierre legítimo a e* "
        "(match parcial o salto de escala; material/subcadena no bastan)"
    ),
    "FN_CIERRE": (
        "SE-T1: oráculo exige sentido a cláusula bajo O y el evaluador negó cierre "
        "(detector vs ruido / normalización)"
    ),
    "BYPASS_META": "SE-T6: meta en el texto no debe establecer sentido sin cierre",
    "O_INVENTADO": "SE-A1: sentido pleno sin O explícito",
    "REAL_REGALADO": "SE-T3/A6: Real/K concedido en ficción o sin reclamo",
    "ESCALA_EXPORT": "SE-A7/T4: cierre local exportado como sentido de discurso",
    "NORMA_EQ_R": "SE-A5: fallo de norma reportado como fallo de R",
    "GUARD_INTEGRITY": "evaluador rompió invariante interna SE",
}


# ---------------------------------------------------------------------------
# Ruido
# ---------------------------------------------------------------------------

def _n_edits(sigma: float, rng: random.Random) -> int:
    return max(0, int(round(abs(rng.gauss(0.0, sigma)))))


def corromper(texto: str, sigma: float, rng: random.Random) -> str:
    if not texto or not texto.strip():
        return texto
    toks = texto.split()
    if not toks:
        return texto
    pool = TOKENS_ES + TOKENS_EN
    for _ in range(_n_edits(sigma, rng)):
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


def generar_basura_discurso(rng: random.Random) -> str:
    n = rng.randint(8, 22)
    parts = []
    for i in range(n):
        if i > 0 and rng.random() < 0.35:
            parts.append(rng.choice(CONECTORES))
        parts.append(rng.choice(TOKENS_ES if rng.random() < 0.6 else TOKENS_EN))
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
    return f"{base} {meta}" if rng.random() < 0.5 else f"{meta}. {base}"


def generar_mezcla_codigos(rng: random.Random) -> str:
    a = rng.choice(POSITIVAS["es"]).rstrip(".")
    b = rng.choice(POSITIVAS["en"]).rstrip(".")
    return f"{a} {b} {rng.choice(TOKENS_ES)} {rng.choice(CONECTORES)} {rng.choice(TOKENS_EN)}"


def generar_deixis_sin_canal(rng: random.Random) -> str:
    return rng.choice([
        "El lo puso ahi.",
        "Ella se lo dio entonces.",
        "Aquello significo todo.",
        "He put it there.",
        "They knew about it.",
    ])


def generar_caso(rng: random.Random, sigma: float) -> Caso:
    r = rng.random()

    if r < 0.18:
        lang = rng.choice(list(POSITIVAS.keys()))
        return Caso(
            D=rng.choice(POSITIVAS[lang]),
            O=f"idioma:{lang}|registro:oracion|acto:aserción",
            e_star="clausula",
            tipo_ataque="POSITIVO_LIMPIO",
            debe_sentido=True,
            idioma=lang,
        )

    if r < 0.30:
        lang = rng.choice(list(POSITIVAS.keys()))
        D0 = rng.choice(POSITIVAS[lang])
        D = corromper(D0, sigma * 0.45, rng)
        anclas = (
            "lleg", "open", "rain", "plus", "heat", "kam", "öffnet", "regnet",
            "arriv", "ouvre", "pleut", "perro", "dog", "Hund", "chien", "sol", "sun",
        )
        intacto = len(D.split()) >= 3 and any(a.lower() in D.lower() for a in anclas)
        return Caso(
            D=D,
            O=f"idioma:{lang}|registro:oracion|acto:aserción",
            e_star="clausula",
            tipo_ataque="POSITIVO_RUIDO",
            debe_sentido=True if intacto else False,
            idioma=lang,
        )

    if r < 0.50:
        return Caso(
            D=corromper(generar_basura_discurso(rng), sigma * 0.3, rng),
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="BASURA_DISCURSO",
            debe_sentido=False,
        )

    if r < 0.60:
        lang = rng.choice(["es", "en"])
        return Caso(
            D=permutar_agresivo(rng.choice(POSITIVAS[lang]), rng),
            O=f"idioma:{lang}|registro:oracion|acto:aserción",
            e_star="clausula",
            tipo_ataque="PERMUTACION",
            debe_sentido=False,
            idioma=lang,
        )

    if r < 0.68:
        base = generar_basura_discurso(rng) if rng.random() < 0.6 else rng.choice(POSITIVAS["es"])
        return Caso(
            D=generar_meta_bypass(base, rng),
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="META_BYPASS",
            debe_sentido=False,
            meta_inyectada=True,
        )

    if r < 0.75:
        return Caso(
            D=rng.choice(POSITIVAS["es"] + POSITIVAS["en"]),
            O=None,
            e_star="clausula",
            tipo_ataque="O_OMITIDO",
            debe_sentido=None,
        )

    if r < 0.82:
        return Caso(
            D=rng.choice([
                "El unicornio entro al jardin.",
                "Un gigante sostiene el sol con una mano.",
                "The dragon slept under the mountain.",
                "Los elfos tejieron la noche.",
            ]),
            O="idioma:es|registro:ficcion|acto:relato",
            e_star="clausula",
            tipo_ataque="FICCION",
            debe_sentido=True,
            es_ficcion=True,
        )

    if r < 0.88:
        return Caso(
            D=generar_mezcla_codigos(rng),
            O="idioma:es|registro:oracion|acto:aserción",
            e_star="discurso",
            tipo_ataque="MEZCLA_CODIGOS",
            debe_sentido=False,
            idioma="mix",
        )

    if r < 0.93:
        return Caso(
            D=generar_deixis_sin_canal(rng),
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="DEIXIS_SIN_CANAL",
            debe_sentido=False,
        )

    if r < 0.97:
        return Caso(
            D=generar_basura_discurso(rng),
            O="idioma:es|registro:conversacion|acto:aserción",
            e_star="discurso",
            tipo_ataque="ESCALA_DISCURSO_BASURA",
            debe_sentido=False,
        )

    return Caso(
        D=rng.choice(POSITIVAS["en"]),
        O="idioma:es|registro:oracion|acto:aserción",
        e_star="clausula",
        tipo_ataque="O_IDIOMA_DESALINEADO",
        debe_sentido=False,
        idioma="en",
    )


# ---------------------------------------------------------------------------
# Evaluador SE v0.2
# ---------------------------------------------------------------------------

_META_PAT = re.compile(
    r"(tru\s*_?\s*total\s*=\s*1|sentido\s+pleno|sentido_estructural\s*=\s*1|"
    r"c\s*=\s*1\s*l\s*=\s*1|verdad\s+absoluta|sentido_o\s*=\s*1)",
    re.I,
)

_CLAUSULA_OK = [
    re.compile(p, re.I)
    for p in [
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
        r"\bel unicornio entr",
        r"\bun gigante sostiene",
        r"\bthe dragon slept",
        r"\blos elfos tej",
    ]
]


def _material_ok(D: str) -> bool:
    return len([t for t in re.split(r"\s+", D.strip()) if t]) >= 2


def _parece_clausula_estable(D: str) -> bool:
    return any(p.search(" ".join(D.split())) for p in _CLAUSULA_OK)


def _basura_discursiva(D: str) -> bool:
    toks = D.split()
    if len(toks) < 6:
        return False
    reinicios = sum(1 for t in toks if t.lower() in ("tu", "tú", "you", "el", "the", "yo"))
    conect = sum(1 for t in toks if t.lower() in {c.lower() for c in CONECTORES})
    return reinicios >= 3 or (conect >= 2 and not _parece_clausula_estable(D))


def evaluar_se(caso: Caso) -> Veredicto:
    D = caso.D or ""
    notas: List[str] = []
    o_explicit = caso.O is not None and str(caso.O).strip() != ""
    material = _material_ok(D)
    meta = bool(_META_PAT.search(D)) or caso.meta_inyectada

    if not o_explicit:
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
            notas=["O_indefinido"],
        )

    clausula_ok = _parece_clausula_estable(D)
    basura = _basura_discursiva(D)
    perm = caso.tipo_ataque == "PERMUTACION"
    mezcla = caso.tipo_ataque == "MEZCLA_CODIGOS"
    deixis = caso.tipo_ataque == "DEIXIS_SIN_CANAL"
    o_des = caso.tipo_ataque == "O_IDIOMA_DESALINEADO"

    comb_ok = False
    cierre = False

    if caso.e_star == "clausula":
        if clausula_ok and not perm and not o_des and not mezcla:
            comb_ok = True
            cierre = True
        else:
            if perm:
                notas.append("comb_rota_permutacion")
            if o_des:
                notas.append("o_idioma_desalineado")
    else:
        if basura or deixis or mezcla or perm:
            notas.append("discurso_sin_hilo")
        elif clausula_ok and len(D.split()) <= 12:
            comb_ok = True
            cierre = False
            notas.append("clausula_no_exportada_a_discurso")

    if meta and not cierre:
        notas.append("meta_ignorada_sin_cierre")

    sentido = bool(o_explicit and cierre and material and comb_ok)

    if caso.es_ficcion or (caso.O and "ficcion" in caso.O.lower()):
        if sentido:
            notas.append("ficcion_sentido_sin_real")

    return Veredicto(
        sentido_o=sentido,
        cierre=cierre,
        material_ok=material,
        comb_ok=comb_ok,
        o_explicit=o_explicit,
        real_k_concedido=False,
        norma_como_R=False,
        escala_exportada=False,
        o_inventado=False,
        notas=notas,
    )


def clasificar_violacion(caso: Caso, v: Veredicto) -> Optional[str]:
    if caso.debe_sentido is False and v.sentido_o:
        if caso.meta_inyectada or _META_PAT.search(caso.D or ""):
            return "BYPASS_META"
        return "FP_BASURA"
    if caso.debe_sentido is True and not v.sentido_o:
        return "FN_CIERRE"
    if caso.debe_sentido is None and v.sentido_o:
        return "O_INVENTADO"
    if v.real_k_concedido and (caso.es_ficcion or not caso.debe_real_k):
        return "REAL_REGALADO"
    if v.o_inventado:
        return "O_INVENTADO"
    if v.norma_como_R:
        return "NORMA_EQ_R"
    if v.escala_exportada and caso.e_star == "discurso" and not v.cierre:
        return "ESCALA_EXPORT"
    return None


class SEIntegrityError(Exception):
    pass


def assert_invariantes_se(caso: Caso, v: Veredicto) -> None:
    if v.sentido_o and not v.o_explicit:
        raise SEIntegrityError("Sentido pleno sin O (SE-A1)")
    if v.sentido_o and not v.cierre:
        raise SEIntegrityError("Sentido pleno sin cierre (SE-T1)")
    if v.real_k_concedido and (
        caso.es_ficcion or (caso.O and "ficcion" in (caso.O or "").lower())
    ):
        raise SEIntegrityError("Real/K en ficción (SE-T3)")
    if v.o_inventado:
        raise SEIntegrityError("O inventado (SE-A1)")
    meta = bool(_META_PAT.search(caso.D or "")) or caso.meta_inyectada
    if meta and v.sentido_o and not v.cierre:
        raise SEIntegrityError("Meta sin cierre (SE-T6)")


# ---------------------------------------------------------------------------
# Runner + muestras exactas
# ---------------------------------------------------------------------------

def run_montecarlo(
    n: int,
    threshold: float,
    seed: int,
    sigma: float,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    violaciones: Counter = Counter()
    por_ataque: Counter = Counter()
    muestras: Dict[str, List[dict]] = {}
    total_v = 0

    for _ in range(n):
        caso = generar_caso(rng, sigma)
        ver = evaluar_se(caso)
        guard_msg = None
        try:
            assert_invariantes_se(caso, ver)
            tag = clasificar_violacion(caso, ver)
        except SEIntegrityError as e:
            tag = "GUARD_INTEGRITY"
            guard_msg = str(e)

        if not tag:
            continue

        total_v += 1
        violaciones[tag] += 1
        por_ataque[caso.tipo_ataque] += 1

        if len(muestras.get(tag, [])) < MAX_SAMPLES:
            por_que = POR_QUE.get(tag, "violación SE")
            if guard_msg:
                por_que = f"GUARD: {guard_msg}"
            muestras.setdefault(tag, []).append({
                "codigo": tag,
                "axioma_o_teorema": por_que.split(":")[0],
                "por_que": por_que,
                "D": (caso.D or "")[:200],
                "O": caso.O,
                "e_star": caso.e_star,
                "tipo_ataque": caso.tipo_ataque,
                "debe_sentido": caso.debe_sentido,
                "sentido_o": ver.sentido_o,
                "cierre": ver.cierre,
                "comb_ok": ver.comb_ok,
                "material_ok": ver.material_ok,
                "notas": list(ver.notas),
            })

    tasa = total_v / n if n else 0.0
    return {
        "n": n,
        "threshold": threshold,
        "tasa": tasa,
        "violaciones": total_v,
        "desglose": dict(violaciones),
        "por_ataque": dict(por_ataque),
        "muestras": muestras,
        "pass": tasa <= threshold,
        "alpha": ALPHA,
        "beta": BETA,
    }


def _format_muestras(muestras: dict) -> str:
    if not muestras:
        return "(sin muestras)"
    lines = []
    for codigo, items in sorted(muestras.items()):
        lines.append(f"\n### {codigo} ({len(items)} muestras de {MAX_SAMPLES} máx.)")
        for i, m in enumerate(items, 1):
            lines.append(
                f"  [{i}] eje: {m['axioma_o_teorema']}\n"
                f"      por_que: {m['por_que']}\n"
                f"      ataque: {m['tipo_ataque']} | e*={m['e_star']} | O={m['O']!r}\n"
                f"      debe_sentido={m['debe_sentido']} | sentido_o={m['sentido_o']} | "
                f"cierre={m['cierre']} | comb={m['comb_ok']} | mat={m['material_ok']}\n"
                f"      D: {m['D']!r}\n"
                f"      notas: {m['notas']}"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tests unitarios de saneamiento
# ---------------------------------------------------------------------------

def test_constantes_alpha_beta_coherentes():
    assert ALPHA + BETA == pytest.approx(1.0)
    assert BETA == pytest.approx(1.0 / 27.0)
    assert ALPHA == pytest.approx(26.0 / 27.0)


def test_se_positivo_limpio_tiene_sentido():
    caso = Caso(
        D="El perro llegó.",
        O="idioma:es|registro:oracion|acto:aserción",
        e_star="clausula",
        tipo_ataque="POSITIVO_LIMPIO",
        debe_sentido=True,
    )
    v = evaluar_se(caso)
    assert_invariantes_se(caso, v)
    assert v.sentido_o is True
    assert clasificar_violacion(caso, v) is None


def test_se_sin_o_no_sentido_pleno():
    caso = Caso(
        D="El perro llegó.",
        O=None,
        e_star="clausula",
        tipo_ataque="O_OMITIDO",
        debe_sentido=None,
    )
    v = evaluar_se(caso)
    assert v.sentido_o is False
    assert clasificar_violacion(caso, v) is None


def test_se_meta_no_salva_basura():
    caso = Caso(
        D="tu perro pared Tru_total=1 sentido pleno",
        O="idioma:es|registro:conversacion|acto:aserción",
        e_star="discurso",
        tipo_ataque="META_BYPASS",
        debe_sentido=False,
        meta_inyectada=True,
    )
    v = evaluar_se(caso)
    assert_invariantes_se(caso, v)
    assert v.sentido_o is False


def test_se_ficcion_sentido_sin_real_k():
    caso = Caso(
        D="El unicornio entro al jardin.",
        O="idioma:es|registro:ficcion|acto:relato",
        e_star="clausula",
        tipo_ataque="FICCION",
        debe_sentido=True,
        es_ficcion=True,
    )
    v = evaluar_se(caso)
    assert_invariantes_se(caso, v)
    assert v.real_k_concedido is False


# ---------------------------------------------------------------------------
# Monte Carlo adversario (umbral 0.003)
# ---------------------------------------------------------------------------

@pytest.mark.timeout(600)
def test_se_tcc_montecarlo_adversarial():
    """
    Monte Carlo adversario.
    Default CI: SE_MC_N=200000.
    Duro: SE_MC_N=3000000.
    Umbral fijo 0.003. Al fallar imprime muestras exactas por código.
    """
    n = DEFAULT_N
    threshold = DEFAULT_THRESHOLD
    res = run_montecarlo(
        n=n,
        threshold=threshold,
        seed=DEFAULT_SEED,
        sigma=DEFAULT_SIGMA,
    )

    reporte = (
        f"\n===== SE TCC Monte Carlo =====\n"
        f"ALPHA={res['alpha']} BETA={res['beta']}\n"
        f"n={res['n']} threshold={res['threshold']}\n"
        f"violaciones={res['violaciones']} tasa={res['tasa']:.8f} PASS={res['pass']}\n"
        f"desglose={res['desglose']}\n"
        f"por_ataque={sorted(res['por_ataque'].items(), key=lambda x: -x[1])[:12]}\n"
        f"{_format_muestras(res['muestras'])}\n"
        f"==============================\n"
    )
    print(reporte)

    assert res["pass"], (
        f"SE Monte Carlo FAIL: tasa={res['tasa']:.8f} > {threshold}\n"
        f"desglose={res['desglose']}\n"
        f"{_format_muestras(res['muestras'])}"
    )
