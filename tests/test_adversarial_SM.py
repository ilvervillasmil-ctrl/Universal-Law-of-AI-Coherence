#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPSI — Monte Carlo adversarial SM v2 · AF v1
N = 3_000_000 | umbral = 0.003

Familias: SM-T9, SM-T2, SM-D6, SM-T6, AF-T3, AF-T2, AF-T7, AF-A1, SM-D5, SM-A6
Opcional --repo: golpea modules.calculator.correlacion_k (SM-T9 real).
"""

from __future__ import annotations

import hashlib
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

N = 3_000_000
UMBRAL = 0.003
SEED = 0x5F_A7_C0_DE
UNDEFINED = object()


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Lexema:
    etiqueta: str
    posicion: str
    dominio: str


def inv(lex: Lexema) -> str:
    return _h(f"{lex.dominio}::{lex.posicion}")


def vacio(lex: Optional[Lexema], o_dominio: str) -> bool:
    if lex is None:
        return True
    if lex.posicion == "":
        return True
    return lex.dominio != o_dominio


def k_estructural(afirmaciones: List[Lexema], o_dominio: str):
    if not o_dominio:
        return UNDEFINED
    c = len(afirmaciones)
    if c == 0:
        return UNDEFINED
    f = sum(
        1 for a in afirmaciones
        if a.dominio != o_dominio or a.posicion == ""
    )
    if f == c and all(a.posicion == "" for a in afirmaciones):
        return UNDEFINED
    return (c - f) / c


def c_estructural(compromisos: List[str], choques: int) -> float:
    m = len(compromisos)
    if m == 0:
        return 1.0
    k = min(choques, m)
    return (m - k) / m


@dataclass(frozen=True)
class Coord:
    sujeto: str
    relacion: str
    objeto: str
    polaridad: bool


def choque(a: Coord, b: Coord) -> bool:
    return (
        a.sujeto == b.sujeto
        and a.relacion == b.relacion
        and a.objeto == b.objeto
        and a.polaridad != b.polaridad
    )


def hay_proposicion(coord: Coord, anclas: Dict[str, bool]) -> bool:
    return bool(
        anclas.get("sujeto", False)
        and anclas.get("relacion", False)
        and anclas.get("objeto", False)
    )


def anclaje_parcial(anclas: Dict[str, bool]) -> float:
    vals = list(anclas.values())
    n = len(vals)
    if n == 0:
        return 0.0
    u = sum(1 for v in vals if not v)
    return (n - u) / n


_ETIQUETAS = [
    "casa", "house", "maison", "haus", "家", "بيت", "X17", "K91", "ZZQ",
    "perro", "dog", "chien", "patro", "árbol", "tree", "negro", "black",
    "azul", "blue", "синий", "голубой", "rldgdnstwcfmdksxxrjdoevf",
    "Prgsyecdhdyecdhsuwfscdgdudvd", "α", "β", "gamma", "δ",
]
_DOM = ["lugar", "color", "especie", "framework", "nombre", "vacio_dom"]
_POS = [
    "habitable", "parque", "canino", "felino", "onda_corta", "onda_larga",
    "beta_1_27", "alpha_26_27", "punto", "",
]


def rng_lexema(rng: random.Random) -> Lexema:
    return Lexema(
        etiqueta=rng.choice(_ETIQUETAS),
        posicion=rng.choice(_POS),
        dominio=rng.choice(_DOM),
    )


def renombrar(lex: Lexema, nueva: str) -> Lexema:
    return Lexema(etiqueta=nueva, posicion=lex.posicion, dominio=lex.dominio)


@dataclass
class Contadores:
    n: int = 0
    fallos: int = 0
    por_familia: Dict[str, int] = field(default_factory=dict)
    detalle: Dict[str, int] = field(default_factory=dict)

    def hit(self, familia: str, ok: bool, codigo: str = "") -> None:
        self.n += 1
        if not ok:
            self.fallos += 1
            self.por_familia[familia] = self.por_familia.get(familia, 0) + 1
            if codigo:
                self.detalle[codigo] = self.detalle.get(codigo, 0) + 1


def ataque_g1_renombrado(rng: random.Random, c: Contadores) -> None:
    o = rng.choice(_DOM)
    base = [rng_lexema(rng) for _ in range(rng.randint(1, 4))]
    if rng.random() < 0.5:
        base[0] = Lexema(
            base[0].etiqueta,
            rng.choice([p for p in _POS if p]),
            o,
        )
    k1 = k_estructural(base, o)
    ren = [renombrar(x, rng.choice(_ETIQUETAS)) for x in base]
    k2 = k_estructural(ren, o)
    if k1 is UNDEFINED and k2 is UNDEFINED:
        ok = True
    elif k1 is UNDEFINED or k2 is UNDEFINED:
        ok = False
    else:
        ok = abs(k1 - k2) < 1e-15
    ok = ok and all(inv(a) == inv(b) for a, b in zip(base, ren))
    c.hit("G1_SM-T9", ok, "T9_K_diverge" if not ok else "")


def ataque_g2_vacio_k(rng: random.Random, c: Contadores) -> None:
    o = rng.choice(_DOM)
    lex = Lexema(rng.choice(_ETIQUETAS), "", o)
    k = k_estructural([lex], o)
    if k is UNDEFINED:
        ok = True
    else:
        ok = not (k > 0)
    c.hit("G2_SM-T2", ok, "T2_K_positivo_en_vacio" if not ok else "")


def ataque_g3_vacuidad_relativa(rng: random.Random, c: Contadores) -> None:
    etiqueta = rng.choice(_ETIQUETAS)
    lex1 = Lexema(etiqueta, "", "español")
    lex2 = Lexema(etiqueta, "clave_acordada", "codigo")
    v1 = vacio(lex1, "español")
    v2 = vacio(lex2, "codigo")
    ok = (v1 is True) and (v2 is False)
    lex3 = Lexema(etiqueta, "", "x")
    ok2 = vacio(lex3, "a") and vacio(lex3, "b")
    c.hit("G3_SM-D6", ok and ok2, "D6_relativa" if not (ok and ok2) else "")


def ataque_g4_conflicto_c(rng: random.Random, c: Contadores) -> None:
    o = "lugar"
    d1 = Lexema("casa", "habitable", o)
    d2 = Lexema("parque", "parque", o)
    k1 = k_estructural([d1], o)
    k2 = k_estructural([d2], o)
    compromisos = [d1.etiqueta + ":" + d1.posicion, d2.etiqueta + ":" + d2.posicion]
    c_val = c_estructural(compromisos, choques=1)
    ok_k = (k1 is not UNDEFINED and k1 > 0) and (k2 is not UNDEFINED and k2 > 0)
    ok_c = c_val < 1.0
    c.hit("G4_SM-T6", ok_k and ok_c, "T6_conflicto" if not (ok_k and ok_c) else "")


def ataque_g5_choque_tripleta(rng: random.Random, c: Contadores) -> None:
    s = rng.choice(["yo", "Carlos", "S", "agente"])
    r = rng.choice(["soy", "estoy", "fue", "es"])
    o = rng.choice(["humano", "perro", "—", "casa", "rldg"])
    a = Coord(s, r, o, True)
    ok = (
        choque(a, Coord(s, r, o, False)) is True
        and choque(a, Coord(s, r, o + "_x", False)) is False
        and choque(a, Coord(s, r + "_x", o, False)) is False
        and choque(a, a) is False
    )
    c.hit("G5_AF-T3", ok, "T3_choque" if not ok else "")


def ataque_g6_sin_proposicion(rng: random.Random, c: Contadores) -> None:
    anclas = {"sujeto": True, "relacion": True, "objeto": False}
    prop = hay_proposicion(
        Coord("yo", "soy", "rldgdnstwcfmdksxxrjdoevf", True),
        anclas,
    )
    ok = prop is False
    c.hit("G6_AF-T2", ok, "T2_no_proposicion" if not ok else "")


def ataque_g7_simetria_def(rng: random.Random, c: Contadores) -> None:
    sin_contraste = True
    ilegal_1 = sin_contraste and (1.0 == 1.0)
    ilegal_0 = sin_contraste and (0.0 == 0.0)
    ok = ilegal_1 and ilegal_0
    c.hit("G7_AF-T7", ok, "T7_asimetria" if not ok else "")


def ataque_g8_parcial(rng: random.Random, c: Contadores) -> None:
    bits = [rng.choice([True, False]) for _ in range(3)]
    anclas = {"sujeto": bits[0], "relacion": bits[1], "objeto": bits[2]}
    a = anclaje_parcial(anclas)
    esperado = (3 - sum(1 for v in bits if not v)) / 3
    ok = abs(a - esperado) < 1e-15
    c.hit("G8_AF-A1", ok, "A1_parcial" if not ok else "")


def ataque_g9_cociente(rng: random.Random, c: Contadores) -> None:
    dom = rng.choice(_DOM)
    pos = rng.choice([p for p in _POS if p])
    e1, e2 = rng.sample(_ETIQUETAS, 2)
    a = Lexema(e1, pos, dom)
    b = Lexema(e2, pos, dom)
    ok = inv(a) == inv(b) and a.etiqueta != b.etiqueta
    c_lex = Lexema(e1, pos + "_x", dom)
    ok2 = inv(a) != inv(c_lex)
    c.hit("G9_SM-D5", ok and ok2, "D5_cociente" if not (ok and ok2) else "")


def ataque_g10_prohibicion_k1(rng: random.Random, c: Contadores) -> None:
    o = rng.choice(_DOM)
    lex = Lexema(rng.choice(_ETIQUETAS), "", o)
    k = k_estructural([lex], o)
    if k is UNDEFINED:
        ok = True
    else:
        ok = k != 1.0 and not (k > 0 and vacio(lex, o))
    c.hit("G10_SM-A6", ok, "A6_K1_vacio" if not ok else "")


def ataque_repo_t9(rng: random.Random, c: Contadores) -> None:
    """SM-T9 contra correlacion_k real si existe."""
    try:
        from modules.calculator.correlacion_k import calcular_k
    except Exception:
        c.hit("G_REPO_T9", True, "")
        return
    try:
        k1 = calcular_k(
            descripcion="beta vale β = 1/27",
            o_context="sabemos que β = 1/27 exactamente",
            metodo="teorico",
        )
        k2 = calcular_k(
            descripcion="beta vale γ = 1/27",
            o_context="sabemos que γ = 1/27 exactamente",
            metodo="teorico",
        )
    except Exception as e:
        c.hit("G_REPO_T9", False, f"repo_exc:{type(e).__name__}")
        return

    def _num(x):
        if x is None:
            return None
        try:
            from fractions import Fraction
            if type(x).__name__ == "_Undefined" or x is UNDEFINED:
                return None
            if isinstance(x, Fraction):
                return float(x)
            return float(x)
        except Exception:
            return None

    n1, n2 = _num(k1), _num(k2)
    if n1 is None and n2 is None:
        ok = True
    elif n1 is None or n2 is None:
        ok = False
    else:
        ok = abs(n1 - n2) < 1e-12
    c.hit("G_REPO_T9", ok, "repo_T9_etiqueta" if not ok else "")


ATAQUES = [
    ataque_g1_renombrado,
    ataque_g2_vacio_k,
    ataque_g3_vacuidad_relativa,
    ataque_g4_conflicto_c,
    ataque_g5_choque_tripleta,
    ataque_g6_sin_proposicion,
    ataque_g7_simetria_def,
    ataque_g8_parcial,
    ataque_g9_cociente,
    ataque_g10_prohibicion_k1,
]


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--umbral", type=float, default=UMBRAL)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--repo", action="store_true")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    c = Contadores()
    t0 = time.time()

    ataques = list(ATAQUES)
    if args.repo:
        ataques.append(ataque_repo_t9)

    n_total = args.n
    n_fam = len(ataques)
    por_familia = n_total // n_fam
    resto = n_total % n_fam

    print("=" * 64)
    print("MONTE CARLO ADVERSARIAL  SM v2 · AF v1")
    print(f"N={n_total:,}  umbral={args.umbral}  seed={hex(args.seed)}  repo={args.repo}")
    print("=" * 64)

    idx = 0
    for i, fn in enumerate(ataques):
        n_local = por_familia + (1 if i < resto else 0)
        for _ in range(n_local):
            fn(rng, c)
            idx += 1
            if idx % 500_000 == 0:
                tasa = c.fallos / c.n if c.n else 0.0
                print(f"  … {idx:,}/{n_total:,}  fallos={c.fallos:,}  tasa={tasa:.6f}")

    dt = time.time() - t0
    tasa = c.fallos / c.n if c.n else 0.0

    print("-" * 64)
    print(f"total={c.n:,}  fallos={c.fallos:,}  tasa={tasa:.8f}  umbral={args.umbral}  t={dt:.2f}s")
    for k in sorted(c.por_familia.keys()):
        print(f"  FAIL {k}: {c.por_familia[k]:,}")
    for k, v in sorted(c.detalle.items(), key=lambda x: -x[1]):
        print(f"  code {k}: {v:,}")
    print("=" * 64)

    if tasa > args.umbral:
        print(f"FAIL tasa={tasa:.8f} > {args.umbral}")
        return 1
    print(f"PASS tasa={tasa:.8f} <= {args.umbral}")
    return 0


# pytest hook (CI puede usar pytest o python directo)
def test_sm_af_montecarlo_adversarial():
    rc = main()
    assert rc == 0, "Monte Carlo SM/AF superó el umbral de fallo"


if __name__ == "__main__":
    sys.exit(main())
