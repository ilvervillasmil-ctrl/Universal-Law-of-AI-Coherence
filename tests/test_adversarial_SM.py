#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONTE CARLO ADVERSARIAL  SM v2 · AF v1  —  PORTABLE

Corre en cualquier repositorio. Localiza la raiz subiendo desde el archivo
hasta encontrar un directorio 'modules', y descubre el calculador sin
depender del nombre del repo ni de rutas fijas.

REGLAS

  1. Solo mide codigo IMPORTADO del repo. No hay oraculo interno que se
     autoapruebe: si el test trae su propia formula, mide su propia
     coherencia y no la del sistema.
  2. Import fallido = FAIL, nunca PASS por vacio.
  3. Un trial que devuelve UNDEFINED en todas las rutas NO cuenta como
     exito: cuenta como VACIO, en su propio contador.
  4. Familias de caso fijo se juzgan por CERO FALLOS.
     La tasa solo aplica a familias con muestreo real.
  5. Cada fallo imprime familia, teorema, entrada, salida y causa.

Uso:
    pytest tests/test_montecarlo_sm_af.py
    python  tests/test_montecarlo_sm_af.py
    python  tests/test_montecarlo_sm_af.py --n 5000 --umbral 0.01 --verbose
"""

from __future__ import annotations

import importlib
import random
import sys
import time
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ===============================================================
# SEGMENTO 1 --- PARAMETROS
# ===============================================================

N_STOCH = 5_000          # trials por familia estocastica
UMBRAL = 0.003           # solo para familias estocasticas
SEED = 0x5F_A7_C0_DE
VERBOSE = False

# Rutas de modulo candidatas. Se prueban en orden; la primera que
# importe gana. Anadir aqui una ruta nueva no obliga a tocar nada mas.
CANDIDATOS_K = [
    ("modules.calculator.correlacion_k", "calcular_k"),
    ("modules.calculator", "calcular_k"),
    ("calculator.correlacion_k", "calcular_k"),
]
CANDIDATOS_C = [
    ("modules.calculator.coherencia", "calcular_c"),
    ("modules.calculator", "calcular_c"),
    ("calculator.coherencia", "calcular_c"),
]
CANDIDATOS_L = [
    ("modules.calculator.logica", "calcular_l"),
    ("modules.calculator", "calcular_l"),
    ("calculator.logica", "calcular_l"),
]
CANDIDATOS_PIPE = [
    ("modules.calculator", "calcular"),
    ("calculator", "calcular"),
]

# Metodos a probar. Probar solo el default deja rutas enteras sin tocar:
# si 'operacional' ignora la descripcion, todos los ataques de texto
# devuelven UNDEFINED y el test pasa sin haber medido nada.
METODOS = ("operacional", "teorico")

# ===============================================================
# SEGMENTO 2 --- LOCALIZACION DE LA RAIZ
# ===============================================================

def raiz_repo() -> Optional[Path]:
    """
    Sube desde este archivo buscando un directorio que contenga 'modules'
    o 'calculator'. No depende del nombre del repositorio.
    """
    aqui = Path(__file__).resolve()
    for base in [aqui.parent] + list(aqui.parents):
        for marca in ("modules", "calculator"):
            if (base / marca).is_dir():
                return base
    return None


def preparar_sys_path() -> Optional[Path]:
    raiz = raiz_repo()
    if raiz is not None and str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    return raiz

# ===============================================================
# SEGMENTO 3 --- DESCUBRIMIENTO
# ===============================================================

_ERRORES_IMPORT: List[str] = []


def _descubrir(candidatos: List[Tuple[str, str]], etiqueta: str):
    """Devuelve la primera funcion importable de la lista, o None."""
    intentos = []
    for modulo, nombre in candidatos:
        try:
            mod = importlib.import_module(modulo)
        except Exception as e:
            intentos.append(f"{modulo}: {type(e).__name__}")
            continue
        fn = getattr(mod, nombre, None)
        if callable(fn):
            return fn, f"{modulo}.{nombre}"
        intentos.append(f"{modulo}: sin '{nombre}'")
    _ERRORES_IMPORT.append(f"{etiqueta} no encontrado -> {'; '.join(intentos)}")
    return None, None

# ===============================================================
# SEGMENTO 4 --- NORMALIZACION DE VALORES
# ===============================================================

def es_undefined(x: Any) -> bool:
    if x is None:
        return True
    if type(x).__name__.lower().lstrip("_") == "undefined":
        return True
    if isinstance(x, str) and x.strip().upper() in ("UNDEFINED", "INDEFINIDO", "N/A"):
        return True
    return False


def a_num(x: Any) -> Optional[float]:
    if es_undefined(x):
        return None
    if isinstance(x, bool):
        return None
    try:
        return float(x)
    except Exception:
        return None


def es_float_crudo(x: Any) -> bool:
    """float donde el contrato exige Fraction."""
    return isinstance(x, float) and not isinstance(x, bool)

# ===============================================================
# SEGMENTO 5 --- INVOCACION TOLERANTE A FIRMA
# ===============================================================

def _invocar(fn, variantes: List[Dict[str, Any]]) -> Tuple[Any, Optional[str]]:
    """
    Prueba varias formas de llamada. La primera que no lance TypeError
    por firma es la buena. Un TypeError de firma no es un fallo del
    sistema: es que el test no sabe llamarlo.
    """
    if fn is None:
        return None, "no importado"
    ultimo = None
    for kw in variantes:
        try:
            return fn(**kw), None
        except TypeError as e:
            ultimo = f"TypeError: {e}"
            continue
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"
    return None, ultimo or "ninguna firma aceptada"


def llamar_k(fn, descripcion: str, o_context: str, metodo: str):
    return _invocar(fn, [
        {"descripcion": descripcion, "o_context": o_context, "metodo": metodo},
        {"descripcion": descripcion, "o_context": o_context},
        {"D": descripcion, "O": o_context},
        {"texto": descripcion, "contexto": o_context},
    ])


def llamar_c(fn, descripcion: str, compromisos, contradicciones, metodo: str):
    return _invocar(fn, [
        {"compromisos": compromisos, "contradicciones": contradicciones,
         "metodo": metodo},
        {"descripcion": descripcion, "metodo": metodo},
        {"descripcion": descripcion},
        {"D": descripcion},
    ])


def llamar_l(fn, descripcion: str, posturas, reversiones, metodo: str):
    return _invocar(fn, [
        {"posturas": posturas, "reversiones": reversiones, "metodo": metodo},
        {"descripcion": descripcion, "metodo": metodo},
        {"descripcion": descripcion},
    ])

# ===============================================================
# SEGMENTO 6 --- CONTADORES
# ===============================================================

@dataclass
class Fallo:
    familia: str
    teorema: str
    entrada: str
    observado: str
    causa: str


@dataclass
class Familia:
    nombre: str
    fija: bool                  # True: se juzga por cero fallos
    ok: int = 0
    fallos: int = 0
    vacios: int = 0             # ni ok ni fallo: el sistema no respondio

    @property
    def n(self) -> int:
        return self.ok + self.fallos + self.vacios

    @property
    def medidos(self) -> int:
        return self.ok + self.fallos

    @property
    def tasa(self) -> float:
        return self.fallos / self.medidos if self.medidos else 0.0


@dataclass
class Registro:
    familias: Dict[str, Familia] = field(default_factory=dict)
    detalle: List[Fallo] = field(default_factory=list)
    max_detalle: int = 30

    def familia(self, nombre: str, fija: bool) -> Familia:
        if nombre not in self.familias:
            self.familias[nombre] = Familia(nombre, fija)
        return self.familias[nombre]

    def ok(self, nombre: str, fija: bool = True) -> None:
        self.familia(nombre, fija).ok += 1

    def vacio(self, nombre: str, fija: bool = True) -> None:
        """
        El sistema devolvio UNDEFINED en todas las rutas: no se midio.
        No es exito. Contar esto como ok infla el denominador y
        esconde los fallos reales bajo el umbral.
        """
        self.familia(nombre, fija).vacios += 1

    def fail(self, nombre: str, teorema: str, entrada: str,
             observado: str, causa: str, fija: bool = True) -> None:
        self.familia(nombre, fija).fallos += 1
        if len(self.detalle) < self.max_detalle:
            self.detalle.append(Fallo(nombre, teorema, entrada, observado, causa))

# ===============================================================
# SEGMENTO 7 --- MATERIAL DE ATAQUE
# ===============================================================

# Pares renombrados: mismo contraste, etiqueta distinta.
PARES_RENOMBRE = [
    ("beta vale β = 1/27", "sabemos que β = 1/27 exactamente",
     "beta vale γ = 1/27", "sabemos que γ = 1/27 exactamente",
     "β→γ conservando 1/27"),
    ("alpha es 26/27", "constante alpha = 26/27 en el marco",
     "alpha es 26/27", "constante delta = 26/27 en el marco",
     "alpha→delta en O, mismo 26/27"),
    ("la casa esta en la colina", "ubicacion de la casa en la colina",
     "la X17 esta en la Q44", "ubicacion de la X17 en la Q44",
     "casa→X17, colina→Q44"),
    ("el perro corre", "conducta del perro observada",
     "el K91 corre", "conducta del K91 observada",
     "perro→K91"),
]

BASURA = [
    "rldgdnstwcfmdksxxrjdoevf",
    "Prgsyecdhdyecdhsuwfscdgdudvd",
    "xyzzy plugh foo bar quux",
    "@@@ ### $$$ %%%",
    "qwertyuiop asdfghjkl zxcvbnm",
]

DOMINIOS = [
    "dominio de fisica de particulas",
    "taxonomia botanica del siglo XIX",
    "geometria del cubo 3x3x3",
    "marco de verificacion formal VPSI",
]

# ===============================================================
# SEGMENTO 8 --- ATAQUES
# ===============================================================
#
# Cada ataque prueba TODOS los metodos declarados. Si una ruta responde
# con numero y otra con UNDEFINED, se juzga la que respondio: el sistema
# tiene ese comportamiento aunque no sea el camino por defecto.

def _k_por_metodos(fn, d: str, o: str) -> Dict[str, Any]:
    """Devuelve {metodo: valor} para las rutas que respondieron algo."""
    out = {}
    for m in METODOS:
        v, err = llamar_k(fn, d, o, m)
        if err is None:
            out[m] = v
    return out


def ataque_r1_renombrado(reg: Registro, fn_k) -> None:
    """SM-T9: renombrar preservando el contraste no debe alterar K."""
    if fn_k is None:
        reg.fail("R1_SM-T9", "SM-T9", "import", "calcular_k ausente",
                 "sin calculador de K no hay nada que medir")
        return

    for d1, o1, d2, o2, tag in PARES_RENOMBRE:
        m1 = _k_por_metodos(fn_k, d1, o1)
        m2 = _k_por_metodos(fn_k, d2, o2)
        if not m1 or not m2:
            reg.vacio("R1_SM-T9")
            continue

        medido = False
        for m in METODOS:
            if m not in m1 or m not in m2:
                continue
            k1, k2 = m1[m], m2[m]
            u1, u2 = es_undefined(k1), es_undefined(k2)
            if u1 and u2:
                continue                      # esa ruta no midio
            medido = True
            if u1 != u2:
                reg.fail(
                    "R1_SM-T9", "SM-T9",
                    f"[{m}] {tag}\n    D1={d1!r}\n    O1={o1!r}\n"
                    f"    D2={d2!r}\n    O2={o2!r}",
                    f"K1={k1!r}  K2={k2!r}",
                    "un lado UNDEFINED y el otro numerico tras renombrado "
                    "que preserva el contraste",
                )
                continue
            n1, n2 = a_num(k1), a_num(k2)
            if n1 is None or n2 is None:
                reg.fail("R1_SM-T9", "SM-T9", f"[{m}] {tag}",
                         f"K1={k1!r} K2={k2!r}",
                         "valor no numerico ni UNDEFINED")
            elif abs(n1 - n2) > 1e-12:
                reg.fail(
                    "R1_SM-T9", "SM-T9",
                    f"[{m}] {tag}\n    D1={d1!r}\n    O1={o1!r}\n"
                    f"    D2={d2!r}\n    O2={o2!r}",
                    f"K1={n1}  K2={n2}  delta={abs(n1-n2)}",
                    "K cambio al renombrar con el mismo contraste. "
                    "El evaluador mide etiquetas, no invariantes.",
                )
            else:
                reg.ok("R1_SM-T9")
        if not medido:
            reg.vacio("R1_SM-T9")


def ataque_r2_sin_o(reg: Registro, fn_k) -> None:
    """Def-5.3.1: sin O usable, K no es reclamable."""
    if fn_k is None:
        reg.fail("R2_Def-5.3.1", "Def-5.3.1", "import", "calcular_k ausente",
                 "sin calculador no hay nada que medir")
        return

    for d in ("el sol irradia luz", "1 + 1 = 2", "beta = 1/27",
              "Carlos fue a la casa"):
        for m in METODOS:
            k, err = llamar_k(fn_k, d, "", m)
            if err is not None:
                reg.ok("R2_Def-5.3.1")       # rechazo por firma o excepcion
                continue
            if es_undefined(k):
                reg.ok("R2_Def-5.3.1")
            else:
                reg.fail(
                    "R2_Def-5.3.1", "Def-5.3.1",
                    f"[{m}] D={d!r}  O='' (vacio)",
                    f"K={k!r}",
                    "K reclamado sin O usable. Def-5.3.1: sin marco de "
                    "dominio la correlacion es indefinida, no un numero.",
                )


def ataque_r3_vacio(reg: Registro, fn_k, rng: random.Random) -> None:
    """SM-T2 / SM-A6: material sin ancla no puede recibir K>0."""
    if fn_k is None:
        reg.fail("R3_SM-T2", "SM-T2", "import", "calcular_k ausente",
                 "sin calculador no hay nada que medir", fija=True)
        return

    for _ in range(N_STOCH):
        d = rng.choice(BASURA) + " " + rng.choice(BASURA)
        o = rng.choice(DOMINIOS)
        vals = _k_por_metodos(fn_k, d, o)
        if not vals:
            reg.vacio("R3_SM-T2", fija=False)
            continue
        medido = False
        for m, k in vals.items():
            if es_undefined(k):
                continue
            medido = True
            n = a_num(k)
            if n is not None and n > 0:
                reg.fail(
                    "R3_SM-T2", "SM-T2 / SM-A6",
                    f"[{m}] D={d!r}\n    O={o!r}",
                    f"K={k!r}",
                    "cadena sin ancla referencial bajo O recibio K>0",
                    fija=False,
                )
            else:
                reg.ok("R3_SM-T2", fija=False)
        if not medido:
            reg.vacio("R3_SM-T2", fija=False)


def ataque_r4_simetria(reg: Registro, fn_k) -> None:
    """AF-T7 / AF-C1: sin contraste, ni K=1 ni K=0. UNDEFINED."""
    if fn_k is None:
        reg.fail("R4_AF-T7", "AF-T7", "import", "calcular_k ausente",
                 "sin calculador no hay nada que medir")
        return

    casos = [
        ("rldgdnstwcfmdksxxrjdoevf qwerty zxcvbn",
         "topologia algebraica de variedades de Calabi-Yau"),
        ("Yo soy rldgdnstwcfmdksxxrjdoevf",
         "identidad del emisor"),
    ]
    for d, o in casos:
        vals = _k_por_metodos(fn_k, d, o)
        if not vals:
            reg.vacio("R4_AF-T7")
            continue
        medido = False
        for m, k in vals.items():
            if es_undefined(k):
                continue
            medido = True
            n = a_num(k)
            if n is None:
                reg.ok("R4_AF-T7")
            elif abs(n) < 1e-15:
                reg.fail(
                    "R4_AF-T7", "AF-T7 / AF-C1",
                    f"[{m}] D={d!r}\n    O={o!r}",
                    f"K={k!r}",
                    "K=0 fabricado sin contraste. Fabricar 0 es tan "
                    "ilegitimo como fabricar 1: el estado correcto es "
                    "UNDEFINED, no cero.",
                )
            elif abs(n - 1.0) < 1e-15:
                reg.fail(
                    "R4_AF-T7", "AF-T7 / SM-A6",
                    f"[{m}] D={d!r}\n    O={o!r}",
                    f"K={k!r}",
                    "K=1 sobre material sin ancla",
                )
            else:
                reg.ok("R4_AF-T7")
        if not medido:
            reg.vacio("R4_AF-T7")


def ataque_r5_conflicto(reg: Registro, fn_c) -> None:
    """
    SM-T6 / Corolario 1.36: dos compromisos incompatibles degradan C.

    Se alimentan los conteos que la ruta operacional espera. Pasar una
    concatenacion de texto deja C en UNDEFINED y el conflicto no se
    evalua.
    """
    if fn_c is None:
        reg.fail("R5_SM-T6", "SM-T6", "import", "calcular_c ausente",
                 "sin calculador de C no hay nada que medir")
        return

    d1 = "el agente esta en la casa durante todo el intervalo"
    d2 = "el agente esta en el parque durante todo el intervalo"

    for m in METODOS:
        c_val, err = llamar_c(fn_c, d1 + " y ademas " + d2,
                              [d1, d2], 1, m)
        if err is not None:
            reg.vacio("R5_SM-T6")
            continue
        if es_undefined(c_val):
            reg.vacio("R5_SM-T6")
            continue
        n = a_num(c_val)
        if n is None:
            reg.vacio("R5_SM-T6")
        elif n >= 1.0 - 1e-12:
            reg.fail(
                "R5_SM-T6", "SM-T6 / Corolario 1.36",
                f"[{m}] compromisos=[D1, D2], contradicciones=1\n"
                f"    D1={d1!r}\n    D2={d2!r}",
                f"C={c_val!r}",
                "C saturo a 1 con dos compromisos incompatibles. "
                "El conflicto degrada C; no puede quedar en 1.",
            )
        else:
            reg.ok("R5_SM-T6")


def ataque_r6_invariancia_l(reg: Registro, fn_l) -> None:
    """L: sin reversiones, L=1. Con reversiones, L<1."""
    if fn_l is None:
        reg.fail("R6_L", "L = 1 - r/p", "import", "calcular_l ausente",
                 "sin calculador de L no hay nada que medir")
        return

    posturas = ["p1", "p2", "p3", "p4"]
    for m in METODOS:
        sin_rev, e1 = llamar_l(fn_l, "sin reversiones", posturas, 0, m)
        con_rev, e2 = llamar_l(fn_l, "con reversiones", posturas, 2, m)
        if e1 or e2 or es_undefined(sin_rev) or es_undefined(con_rev):
            reg.vacio("R6_L")
            continue
        a, b = a_num(sin_rev), a_num(con_rev)
        if a is None or b is None:
            reg.vacio("R6_L")
        elif not (b < a):
            reg.fail(
                "R6_L", "L = 1 - r/p",
                f"[{m}] posturas=4, reversiones 0 vs 2",
                f"L(r=0)={sin_rev!r}  L(r=2)={con_rev!r}",
                "reversiones no degradaron L",
            )
        else:
            reg.ok("R6_L")


def ataque_r7_exactitud(reg: Registro, fn_pipe) -> None:
    """
    Fraction obligatorio: ningun factor ni resultado puede ser float.

    Se declara PENDIENTE, no OK, si el pipeline devuelve None en todos
    los factores: no hay nada cuyo tipo comprobar.
    """
    if fn_pipe is None:
        reg.fail("R7_Fraction", "Fraction obligatorio", "import",
                 "calcular ausente", "sin pipeline no hay salida que auditar")
        return

    peticiones = [
        {"descripcion": "el sol irradia luz",
         "o_context": "fisica termica / astronomia observacional",
         "O_id": "astro_1", "enunciado_O": "fisica termica",
         "compromisos": ["c1", "c2"], "contradicciones": 0,
         "posturas": ["p1"], "reversiones": 0,
         "afirmaciones": ["a1"], "afirmaciones_falsas": 0},
    ]
    claves = ("C", "L", "K", "c", "l", "k",
              "Tru_Ri", "Tru_total", "tru_ri", "tru_total")

    for pet in peticiones:
        for m in METODOS:
            p = dict(pet, metodo=m)
            try:
                out = fn_pipe(p)
            except Exception as e:
                reg.fail("R7_Fraction", "pipeline", str(p)[:120],
                         f"{type(e).__name__}: {e}", "excepcion en calcular()")
                continue
            if not isinstance(out, dict):
                reg.vacio("R7_Fraction")
                continue

            presentes = [k for k in claves
                         if k in out and not es_undefined(out[k])]
            if not presentes:
                reg.vacio("R7_Fraction")
                continue

            malos = [(k, out[k]) for k in presentes if es_float_crudo(out[k])]
            if malos:
                reg.fail(
                    "R7_Fraction", "Fraction obligatorio",
                    f"[{m}] peticion con conteos completos",
                    ", ".join(f"{k}={v!r} ({type(v).__name__})"
                              for k, v in malos),
                    "float donde el contrato exige Fraction: la ruta de "
                    "decision pierde exactitud",
                )
            else:
                reg.ok("R7_Fraction")

# ===============================================================
# SEGMENTO 9 --- INFORME
# ===============================================================

def informe(reg: Registro, raiz, origenes: Dict[str, Optional[str]],
            dt: float, umbral: float) -> int:
    print("\n" + "-" * 72)
    print(f"{'FAMILIA':22s} {'TIPO':6s} {'OK':>7s} {'FALLO':>7s} "
          f"{'VACIO':>7s} {'TASA':>10s}")
    print("-" * 72)

    fallos_fijos = 0
    peor_tasa = 0.0
    familias_vacias = []

    for nombre in sorted(reg.familias):
        f = reg.familias[nombre]
        tipo = "fija" if f.fija else "estoc"
        tasa = f"{f.tasa:.6f}" if f.medidos else "  n/a"
        print(f"{nombre:22s} {tipo:6s} {f.ok:>7,} {f.fallos:>7,} "
              f"{f.vacios:>7,} {tasa:>10s}")
        if f.fija:
            fallos_fijos += f.fallos
        else:
            peor_tasa = max(peor_tasa, f.tasa)
        if f.medidos == 0:
            familias_vacias.append(nombre)

    print("-" * 72)

    if reg.detalle:
        print("\n" + "=" * 72)
        print(f"DETALLE DE FALLOS (max {reg.max_detalle})")
        print("=" * 72)
        for i, f in enumerate(reg.detalle, 1):
            print(f"\n--- fallo {i} ---")
            print(f"  familia   : {f.familia}")
            print(f"  teorema   : {f.teorema}")
            print(f"  entrada   : {f.entrada}")
            print(f"  observado : {f.observado}")
            print(f"  causa     : {f.causa}")

    print("\n" + "=" * 72)
    print("VEREDICTO")
    print("=" * 72)
    print(f"  raiz detectada    : {raiz}")
    for etiq, origen in origenes.items():
        print(f"  {etiq:18s}: {origen or 'NO ENCONTRADO'}")
    print(f"  tiempo            : {dt:.2f}s")
    print(f"  fallos en fijas   : {fallos_fijos}   (criterio: cero)")
    print(f"  peor tasa estoc.  : {peor_tasa:.6f}   (umbral: {umbral})")

    if familias_vacias:
        print(f"\n  FAMILIAS SIN MEDICION: {familias_vacias}")
        print("  Ninguna ruta devolvio valor. No es exito: no se midio nada.")

    rc = 0
    if fallos_fijos > 0:
        print(f"\nFAIL  {fallos_fijos} fallo(s) en familias de caso fijo")
        rc = 1
    if peor_tasa > umbral:
        print(f"\nFAIL  tasa {peor_tasa:.6f} > umbral {umbral}")
        rc = 1
    if familias_vacias:
        print(f"\nFAIL  {len(familias_vacias)} familia(s) sin una sola medicion")
        rc = 1
    if rc == 0:
        print("\nPASS  cero fallos en fijas, tasa bajo umbral, "
              "todas las familias midieron")
    print("=" * 72)
    return rc

# ===============================================================
# SEGMENTO 10 --- MAIN
# ===============================================================

def main(argv: Optional[List[str]] = None) -> int:
    global N_STOCH, VERBOSE

    import argparse
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--n", type=int, default=N_STOCH)
    ap.add_argument("--umbral", type=float, default=UMBRAL)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv if argv is not None else [])

    N_STOCH = args.n
    VERBOSE = args.verbose

    raiz = preparar_sys_path()

    print("=" * 72)
    print("MONTE CARLO ADVERSARIAL  SM v2 / AF v1  —  contra el repo")
    print(f"N_STOCH={N_STOCH:,}  umbral={args.umbral}  seed={hex(args.seed)}")
    print("=" * 72)

    if raiz is None:
        print("FAIL  no se encontro raiz de repositorio "
              "(ningun ancestro con 'modules' o 'calculator')")
        return 1

    fn_k, org_k = _descubrir(CANDIDATOS_K, "calcular_k")
    fn_c, org_c = _descubrir(CANDIDATOS_C, "calcular_c")
    fn_l, org_l = _descubrir(CANDIDATOS_L, "calcular_l")
    fn_p, org_p = _descubrir(CANDIDATOS_PIPE, "calcular")

    origenes = {"calcular_k": org_k, "calcular_c": org_c,
                "calcular_l": org_l, "calcular": org_p}

    if _ERRORES_IMPORT:
        print("\nIMPORTS NO RESUELTOS (esto es FAIL, no PASS por vacio):")
        for e in _ERRORES_IMPORT:
            print(f"  X  {e}")

    if fn_k is None and fn_p is None:
        print("\nFAIL  no hay calculador importable. "
              "Coherencia por vacuidad prohibida.")
        return 1

    rng = random.Random(args.seed)
    reg = Registro()
    t0 = time.time()

    print("\n[R1] SM-T9  renombrado ...")
    ataque_r1_renombrado(reg, fn_k)
    print("[R2] Def-5.3.1  sin O ...")
    ataque_r2_sin_o(reg, fn_k)
    print("[R4] AF-T7  simetria K=0 / K=1 ...")
    ataque_r4_simetria(reg, fn_k)
    print("[R5] SM-T6  conflicto de invariantes ...")
    ataque_r5_conflicto(reg, fn_c)
    print("[R6] L = 1 - r/p ...")
    ataque_r6_invariancia_l(reg, fn_l)
    print("[R7] Fraction obligatorio ...")
    ataque_r7_exactitud(reg, fn_p)
    print(f"[R3] SM-T2  vacio ({N_STOCH:,} trials) ...")
    ataque_r3_vacio(reg, fn_k, rng)

    return informe(reg, raiz, origenes, time.time() - t0, args.umbral)

# ===============================================================
# SEGMENTO 11 --- ENTRADA PYTEST
# ===============================================================

def test_montecarlo_sm_af():
    """
    parse_args recibe lista vacia: pytest pone sus propios argumentos en
    sys.argv y argparse los rechazaria con SystemExit(2).
    """
    rc = main([])
    assert rc == 0, (
        "Monte Carlo SM/AF: fallos en familias fijas, tasa sobre umbral, "
        "o familias sin una sola medicion. Ver detalle arriba."
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
