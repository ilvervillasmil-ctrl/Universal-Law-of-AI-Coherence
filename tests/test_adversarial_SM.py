#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPSI — Monte Carlo adversarial SM v2 · AF v1  (contra el repo real)
===================================================================
N_STOCH ≈ 50_000 por familia estocástica
Casos fijos: 1 evaluación cada uno (no se repiten millones de veces)

Reglas:
  - Import obligatorio de modules.calculator.*  → si falla, el job FALLA
  - No hay oráculo interno que se autoapruebe
  - Cada fallo imprime: familia, teorema, entrada, salida observada, causa
  - tasa > 0.003 → exit 1

Familias (todas contra código importado):
  R1  SM-T9     renombrado β→γ preservando contraste 1/27
  R2  SM-T2     material vacío / sin ancla bajo O → no K>0 reclamable
  R3  Def-5.3.1 sin O_context → K no reclamable
  R4  SM-T6     conflicto casa/parque bajo mismo O
  R5  AF-T7     fabricar K=0 sin contraste tan ilegal como K=1
  R6  conteos   divergencias / no-None
  R7  calcular  pipeline + Fraction (no float)
  R8  ruido     cadenas basura no saturan K=1
"""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

N_STOCH = 50_000
UMBRAL = 0.003
SEED = 0x5F_A7_C0_DE

# ------------------------------------------------------------
# Import del repo — si falla, el test FALLA (no PASS por vacío)
# ------------------------------------------------------------
_IMPORT_ERRORS: List[str] = []
calcular_k = None
calcular_c = None
calcular_l = None
extraer_conteos = None
calcular = None


def _try_import() -> None:
    global calcular_k, calcular_c, calcular_l, extraer_conteos, calcular
    try:
        from modules.calculator.correlacion_k import calcular_k as _k
        calcular_k = _k
    except Exception as e:
        _IMPORT_ERRORS.append(f"correlacion_k.calcular_k: {type(e).__name__}: {e}")
    try:
        from modules.calculator.coherencia import calcular_c as _c
        calcular_c = _c
    except Exception as e:
        _IMPORT_ERRORS.append(f"coherencia.calcular_c: {type(e).__name__}: {e}")
    try:
        from modules.calculator.logica import calcular_l as _l
        calcular_l = _l
    except Exception as e:
        _IMPORT_ERRORS.append(f"logica.calcular_l: {type(e).__name__}: {e}")
    try:
        from modules.calculator.conteos import extraer_conteos as _e
        extraer_conteos = _e
    except Exception as e:
        _IMPORT_ERRORS.append(f"conteos.extraer_conteos: {type(e).__name__}: {e}")
    try:
        from modules.calculator import calcular as _calc
        calcular = _calc
    except Exception:
        try:
            from modules.calculator.__init__ import calcular as _calc
            calcular = _calc
        except Exception as e:
            _IMPORT_ERRORS.append(f"calculator.calcular: {type(e).__name__}: {e}")


def _es_undefined(x: Any) -> bool:
    if x is None:
        return True
    name = type(x).__name__.lower()
    if name in ("undefined", "_undefined"):
        return True
    if isinstance(x, str) and x.strip().upper() in ("UNDEFINED", "INDEFINIDO", "N/A"):
        return True
    return False


def _a_float(x: Any) -> Optional[float]:
    if _es_undefined(x):
        return None
    try:
        if isinstance(x, Fraction):
            return float(x)
        return float(x)
    except Exception:
        return None


def _call_k(descripcion: str, o_context: str) -> Tuple[Any, Optional[str]]:
    if calcular_k is None:
        return None, "calcular_k no importado"
    for kwargs in (
        {"descripcion": descripcion, "o_context": o_context},
        {"D": descripcion, "O": o_context},
        {"texto": descripcion, "contexto": o_context},
        {"descripcion": descripcion, "O_context": o_context},
    ):
        try:
            return calcular_k(**kwargs), None
        except TypeError:
            continue
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"
    try:
        return calcular_k(descripcion, o_context), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _call_c(descripcion: str) -> Tuple[Any, Optional[str]]:
    if calcular_c is None:
        return None, "calcular_c no importado"
    for kwargs in (
        {"descripcion": descripcion},
        {"D": descripcion},
        {"texto": descripcion},
    ):
        try:
            return calcular_c(**kwargs), None
        except TypeError:
            continue
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"
    try:
        return calcular_c(descripcion), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _call_calc(peticion: dict) -> Tuple[Any, Optional[str]]:
    if calcular is None:
        return None, "calcular no importado"
    try:
        return calcular(peticion), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


@dataclass
class Fallo:
    familia: str
    teorema: str
    entrada: str
    observado: str
    causa: str


@dataclass
class Contadores:
    n: int = 0
    fallos: int = 0
    por_familia: Dict[str, int] = field(default_factory=dict)
    registro: List[Fallo] = field(default_factory=list)
    max_detalle: int = 40

    def ok(self, familia: str) -> None:
        self.n += 1

    def fail(
        self,
        familia: str,
        teorema: str,
        entrada: str,
        observado: str,
        causa: str,
    ) -> None:
        self.n += 1
        self.fallos += 1
        self.por_familia[familia] = self.por_familia.get(familia, 0) + 1
        if len(self.registro) < self.max_detalle:
            self.registro.append(Fallo(familia, teorema, entrada, observado, causa))


# =====================================================================
# R1 — SM-T9 renombrado
# =====================================================================
def ataque_r1_renombrado(c: Contadores) -> None:
    casos = [
        (
            "beta vale β = 1/27",
            "sabemos que β = 1/27 exactamente",
            "beta vale γ = 1/27",
            "sabemos que γ = 1/27 exactamente",
            "β→γ (fracción 1/27)",
        ),
        (
            "alpha es 26/27",
            "constante alpha = 26/27 en el marco",
            "alpha es 26/27",
            "constante delta = 26/27 en el marco",
            "alpha→delta en O (mismo 26/27)",
        ),
        (
            "el valor es uno sobre veintisiete",
            "beta estructural = 1/27",
            "el valor es uno sobre veintisiete",
            "piso estructural = 1/27",
            "etiqueta beta→piso (mismo 1/27)",
        ),
    ]
    for d1, o1, d2, o2, tag in casos:
        k1, e1 = _call_k(d1, o1)
        k2, e2 = _call_k(d2, o2)
        if e1 or e2:
            c.fail(
                "R1_SM-T9", "SM-T9",
                f"{tag} | D1={d1!r} O1={o1!r}",
                f"err1={e1} err2={e2}",
                "excepción al invocar calcular_k (firma o bug interno)",
            )
            continue
        n1, n2 = _a_float(k1), _a_float(k2)
        u1, u2 = _es_undefined(k1), _es_undefined(k2)
        if u1 and u2:
            c.ok("R1_SM-T9")
            continue
        if u1 != u2:
            c.fail(
                "R1_SM-T9", "SM-T9",
                f"{tag}\n  D1={d1!r}\n  O1={o1!r}\n  D2={d2!r}\n  O2={o2!r}",
                f"K1={k1!r} K2={k2!r}",
                "un lado UNDEFINED y el otro numérico tras renombrado que preserva el contraste",
            )
            continue
        if n1 is None or n2 is None:
            c.fail(
                "R1_SM-T9", "SM-T9", tag,
                f"K1={k1!r} K2={k2!r}",
                "no convertible a número ni UNDEFINED",
            )
            continue
        if abs(n1 - n2) > 1e-12:
            c.fail(
                "R1_SM-T9", "SM-T9",
                f"{tag}\n  D1={d1!r}\n  O1={o1!r}\n  D2={d2!r}\n  O2={o2!r}",
                f"K1={n1}  K2={n2}  Δ={abs(n1-n2)}",
                "K cambió al renombrar etiqueta con el mismo contraste (1/27 o 26/27). "
                "El evaluador mide literales/etiquetas, no la invariante numérica. "
                "Evidencia típica: hardcode de β/α en correlacion_k.",
            )
        else:
            c.ok("R1_SM-T9")


# =====================================================================
# R2 — SM-T2 vacío
# =====================================================================
def ataque_r2_vacio(c: Contadores, rng: random.Random) -> None:
    basura = [
        "rldgdnstwcfmdksxxrjdoevf",
        "Prgsyecdhdyecdhsuwfscdgdudvd",
        "xyzzy plugh foo bar quux",
        "αβγδκλμνξοπ",
        "@@@ ### $$$ %%%",
    ]
    o_list = [
        "dominio de física de partículas",
        "taxonomía botánica del siglo XIX",
        "código penal venezolano",
        "geometría del cubo 3×3×3",
    ]
    for _ in range(N_STOCH // 10):
        d = rng.choice(basura) + " " + rng.choice(basura)
        o = rng.choice(o_list)
        k, err = _call_k(d, o)
        if err:
            c.fail("R2_SM-T2", "SM-T2", f"D={d!r} O={o!r}", err, "excepción en calcular_k")
            continue
        n = _a_float(k)
        if _es_undefined(k):
            c.ok("R2_SM-T2")
        elif n is not None and n > 0:
            c.fail(
                "R2_SM-T2", "SM-T2 / SM-A6",
                f"D={d!r}\n  O={o!r}",
                f"K={k!r} ({n})",
                "cadena sin ancla referencial bajo O recibió K>0. "
                "Vacío(D|O) prohíbe K reclamable positivo.",
            )
        else:
            c.ok("R2_SM-T2")


# =====================================================================
# R3 — Def-5.3.1 sin O
# =====================================================================
def ataque_r3_sin_o(c: Contadores) -> None:
    for d in ("el sol irradia luz", "1 + 1 = 2", "beta = 1/27", "Carlos fue a la casa"):
        k, err = _call_k(d, "")
        if err and "o_context" in err.lower():
            c.ok("R3_Def-5.3.1")
            continue
        if err:
            c.fail(
                "R3_Def-5.3.1", "Def-5.3.1",
                f"D={d!r} O=''", err,
                "error inesperado (no rechazo limpio por O vacío)",
            )
            continue
        if _es_undefined(k):
            c.ok("R3_Def-5.3.1")
        else:
            c.fail(
                "R3_Def-5.3.1", "Def-5.3.1",
                f"D={d!r} O='' (vacío)",
                f"K={k!r}",
                "K numérico sin O_context usable. "
                "Def-5.3.1: correlación indefinida sin marco de dominio.",
            )


# =====================================================================
# R4 — SM-T6 conflicto
# =====================================================================
def ataque_r4_conflicto(c: Contadores) -> None:
    o = "ubicación del agente en el intervalo [t0,t1]; una sola ubicación exclusiva"
    d1 = "el agente está en la casa durante todo el intervalo"
    d2 = "el agente está en el parque durante todo el intervalo"
    k1, e1 = _call_k(d1, o)
    k2, e2 = _call_k(d2, o)
    if e1 or e2:
        c.fail("R4_SM-T6", "SM-T6", f"O={o!r}", f"e1={e1} e2={e2}", "excepción")
        return
    if calcular_c is not None:
        conj = d1 + " Y ADEMÁS " + d2 + " (ambas en el mismo intervalo)"
        cc, ec = _call_c(conj)
        if ec:
            c.fail("R4_SM-T6", "SM-T6", conj, ec, "excepción en calcular_c")
            return
        nc = _a_float(cc)
        if nc is not None and nc >= 1.0 - 1e-12:
            c.fail(
                "R4_SM-T6", "SM-T6 / Corolario 1.36",
                f"conjunción bajo O exclusivo:\n  D1={d1!r}\n  D2={d2!r}\n  O={o!r}",
                f"C={cc!r}",
                "C saturó a 1 con dos compromisos incompatibles. "
                "SM-T6: el conflicto degrada C; no debe quedar C=1.",
            )
        else:
            c.ok("R4_SM-T6")
    else:
        c.ok("R4_SM-T6")


# =====================================================================
# R5 — AF-T7 simetría
# =====================================================================
def ataque_r5_simetria(c: Contadores) -> None:
    d = "rldgdnstwcfmdksxxrjdoevf qwerty zxcvbn"
    o = "dominio de topología algebraica de variedades de Calabi-Yau"
    k, err = _call_k(d, o)
    if err or _es_undefined(k):
        c.ok("R5_AF-T7")
        return
    n = _a_float(k)
    if n is None:
        c.ok("R5_AF-T7")
        return
    if abs(n - 0.0) < 1e-15:
        c.fail(
            "R5_AF-T7", "AF-T7 / AF-C1",
            f"D={d!r}\n  O={o!r}",
            f"K={k!r}",
            "se emitió K=0 numérico sin contraste. "
            "AF-T7: fabricar K=0 es tan ilegítimo como fabricar K=1. "
            "Estado correcto: UNDEFINED / no proposición, no 0.",
        )
    elif abs(n - 1.0) < 1e-15:
        c.fail(
            "R5_AF-T7", "AF-T7 / SM-A6",
            f"D={d!r}\n  O={o!r}",
            f"K={k!r}",
            "se emitió K=1 sin contraste. Prohibido por SM-A6 y AF-T7.",
        )
    else:
        c.ok("R5_AF-T7")


# =====================================================================
# R6 — conteos
# =====================================================================
def ataque_r6_conteos(c: Contadores, rng: random.Random) -> None:
    if extraer_conteos is None:
        c.fail(
            "R6_conteos", "conteos", "import",
            "extraer_conteos no importado",
            "módulo conteos ausente — no se puede auditar m,p,c",
        )
        return
    for _ in range(min(N_STOCH // 20, 2000)):
        d = rng.choice([
            "el sol irradia luz",
            "1+1=2",
            "Carlos niega lo que afirmó antes: sí y no",
            "a es b y a no es b",
        ])
        o = rng.choice([
            "astronomía básica", "aritmética",
            "declaraciones del agente Carlos", "",
        ])
        try:
            try:
                out = extraer_conteos(d, o) if o else extraer_conteos(d)
            except TypeError:
                out = extraer_conteos(descripcion=d, o_context=o)
        except Exception as e:
            c.fail("R6_conteos", "conteos", d, str(e), "excepción")
            continue
        if out is None:
            c.fail("R6_conteos", "conteos", d, "None", "conteos devolvió None")
            continue
        c.ok("R6_conteos")


# =====================================================================
# R7 — pipeline + Fraction
# =====================================================================
def ataque_r7_pipeline(c: Contadores) -> None:
    if calcular is None:
        c.fail(
            "R7_pipeline", "calculator.calcular", "import",
            "calcular no importado",
            "no se puede auditar el pipeline C·L·K",
        )
        return
    peticiones = [
        {
            "descripcion": "el sol irradia luz",
            "o_context": "física térmica / astronomía observacional",
            "O_id": "astro_1",
            "enunciado_O": "física térmica / astronomía observacional",
        },
        {
            "descripcion": "beta = 1/27",
            "o_context": "constantes estructurales VPSI α=26/27 β=1/27",
            "O_id": "vpsi_beta",
            "enunciado_O": "constantes estructurales VPSI",
        },
    ]
    for pet in peticiones:
        out, err = _call_calc(pet)
        if err:
            c.fail("R7_pipeline", "calculator.calcular", str(pet), err, "excepción")
            continue
        if out is None:
            c.fail("R7_pipeline", "calculator.calcular", str(pet), "None", "sin salida")
            continue
        if isinstance(out, dict):
            for key in ("C", "L", "K", "c", "l", "k", "Tru_Ri", "Tru_total", "tru_ri", "tru_total"):
                if key in out:
                    val = out[key]
                    if isinstance(val, float) and not _es_undefined(val):
                        c.fail(
                            "R7_pipeline", "Fraction obligatorio",
                            f"pet={pet!r} key={key}",
                            f"valor={val!r} tipo={type(val).__name__}",
                            "se emitió float donde el contrato exige Fraction.",
                        )
                        break
            else:
                c.ok("R7_pipeline")
        else:
            c.ok("R7_pipeline")


# =====================================================================
# R8 — ruido léxico
# =====================================================================
def ataque_r8_ruido(c: Contadores, rng: random.Random) -> None:
    for _ in range(N_STOCH // 10):
        d = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz ") for _ in range(rng.randint(8, 40)))
        o = "marco de verificación formal VPSI"
        k, err = _call_k(d, o)
        if err:
            c.ok("R8_ruido")
            continue
        n = _a_float(k)
        if n is not None and abs(n - 1.0) < 1e-15:
            c.fail(
                "R8_ruido", "SM-A6 / techo léxico",
                f"D={d!r}\n  O={o!r}",
                f"K={k!r}",
                "cadena aleatoria recibió K=1. Sin ancla referencial no puede saturar correlación.",
            )
        else:
            c.ok("R8_ruido")


# =====================================================================
# main
# =====================================================================
def main() -> int:
    print("=" * 72)
    print("MONTE CARLO ADVERSARIAL  SM v2 · AF v1  —  contra modules.calculator")
    print(f"N_STOCH={N_STOCH:,}  umbral={UMBRAL}  seed={hex(SEED)}")
    print("=" * 72)

    _try_import()
    if _IMPORT_ERRORS:
        print("IMPORTACIONES FALLIDAS (esto es FAIL, no PASS por vacío):")
        for e in _IMPORT_ERRORS:
            print(f"  X  {e}")
        if calcular_k is None and calcular is None:
            print("-" * 72)
            print("FAIL  no hay calculator importable — coherencia por vacuidad prohibida")
            return 1
        print("continúa con los módulos que sí cargaron...")
    else:
        print("imports OK: correlacion_k / coherencia / logica / conteos / calcular")

    rng = random.Random(SEED)
    c = Contadores()
    t0 = time.time()

    print("\n[R1] SM-T9 renombrado...")
    ataque_r1_renombrado(c)
    print("[R3] Def-5.3.1 sin O...")
    ataque_r3_sin_o(c)
    print("[R4] SM-T6 conflicto...")
    ataque_r4_conflicto(c)
    print("[R5] AF-T7 simetria K=0/K=1...")
    ataque_r5_simetria(c)
    print("[R7] pipeline calcular + Fraction...")
    ataque_r7_pipeline(c)
    print(f"[R2] SM-T2 vacio ({N_STOCH // 10:,} trials)...")
    ataque_r2_vacio(c, rng)
    print(f"[R6] conteos ({min(N_STOCH // 20, 2000):,} trials)...")
    ataque_r6_conteos(c, rng)
    print(f"[R8] ruido lexico ({N_STOCH // 10:,} trials)...")
    ataque_r8_ruido(c, rng)

    dt = time.time() - t0
    tasa = c.fallos / c.n if c.n else 1.0

    print("\n" + "-" * 72)
    print(f"total={c.n:,}  fallos={c.fallos:,}  tasa={tasa:.8f}  umbral={UMBRAL}  t={dt:.2f}s")
    print("-" * 72)
    if c.por_familia:
        print("fallos por familia:")
        for k in sorted(c.por_familia.keys()):
            print(f"  {k:20s}  {c.por_familia[k]:,}")
    else:
        print("fallos por familia: (ninguno)")

    if c.registro:
        print("\n" + "=" * 72)
        print(f"DETALLE DE FALLOS (max {c.max_detalle}) — causa exacta")
        print("=" * 72)
        for i, f in enumerate(c.registro, 1):
            print(f"\n--- fallo {i} ---")
            print(f"familia   : {f.familia}")
            print(f"teorema   : {f.teorema}")
            print(f"entrada   : {f.entrada}")
            print(f"observado : {f.observado}")
            print(f"causa     : {f.causa}")

    print("\n" + "=" * 72)
    if c.n == 0:
        print("FAIL  cero trials — no hubo sistema bajo prueba")
        return 1
    if tasa > UMBRAL:
        print(f"FAIL  tasa={tasa:.8f} > {UMBRAL}")
        return 1
    print(f"PASS  tasa={tasa:.8f} <= {UMBRAL}")
    return 0


def test_sm_af_montecarlo_adversarial():
    rc = main()
    assert rc == 0, "Monte Carlo SM/AF: tasa de fallo supero el umbral o imports ausentes"


if __name__ == "__main__":
    sys.exit(main())
