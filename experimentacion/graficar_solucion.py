#!/usr/bin/env python3
"""Grafica una solucion ya calculada (lo usa el modo interactivo de tp2).

Uso: python experimentacion/graficar_solucion.py --inst <instancia> --sol <solucion.out> --heuristica FFD --out <grafico.png>
"""
import argparse
import math
import os
import sys

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print(f"  Falta matplotlib en este Python: {sys.executable}")
    print(f'  Instalalo con:  "{sys.executable}" -m pip install matplotlib')
    sys.exit(2)


def leer_instancia(path):
    with open(path, "r", encoding="utf-8") as f:
        tok = f.read().split()
    it = iter(tok)
    n = int(next(it))
    C = float(next(it))
    pesos, temps = [], []
    for _ in range(n):
        pesos.append(float(next(it)))
        temps.append(float(next(it)))
    sim = [[float(next(it)) for _ in range(n)] for _ in range(n)]
    return n, C, pesos, temps, sim


def leer_solucion(path):
    camiones = []
    with open(path, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                camiones.append([int(x) for x in linea.split()])
    return camiones


def main():
    ap = argparse.ArgumentParser(description="Graficar una solucion")
    ap.add_argument("--inst", required=True)
    ap.add_argument("--sol", required=True)
    ap.add_argument("--heuristica", default="?")
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--beta", default="auto",
                    help='numero o "auto" = 1/S_max (camiones primero)')
    ap.add_argument("--delta", type=float, default=float("inf"))
    ap.add_argument("--modo", default="ninguno")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    n, C, pesos, temps, sim = leer_instancia(args.inst)
    camiones = leer_solucion(args.sol)

    K = len(camiones)
    cargas = [sum(pesos[i] for i in b) for b in camiones]
    S = sum(sim[b[a]][b[c]] for b in camiones for a in range(len(b)) for c in range(a + 1, len(b)))
    S_max = sum(sim[i][j] for i in range(n) for j in range(i + 1, n))
    if args.beta == "auto":
        beta = 1.0 / S_max if S_max > 0 else 0.0
        beta_txt = f"beta=1/S_max (S_max={S_max:.1f})"
    else:
        beta = float(args.beta)
        beta_txt = f"beta={beta:g}"
    objetivo = args.alpha * K - beta * S
    L = math.ceil(sum(pesos) / C)
    ocup = 100.0 * sum(cargas) / (C * K) if K else 0.0

    fig, ax = plt.subplots(figsize=(max(8, 0.55 * K + 4), 6))
    x = list(range(K))
    colores = [plt.cm.RdYlGn(min(c / C, 1.0)) for c in cargas]
    ax.bar(x, cargas, color=colores, edgecolor="black", linewidth=0.5)
    ax.axhline(C, color="red", linestyle="--", linewidth=1.2, label=f"Capacidad C = {C:g}")

    for k, b in enumerate(camiones):
        if b:
            tmin = min(temps[i] for i in b)
            tmax = max(temps[i] for i in b)
            etiqueta = f"{tmin:g}°" if tmin == tmax else f"[{tmin:g}, {tmax:g}]°"
            ax.text(k, cargas[k] + C * 0.02, etiqueta, ha="center", va="bottom",
                    fontsize=7 if K > 12 else 8)

    ax.set_xticks(x)
    ax.set_xlabel("Camion")
    ax.set_ylabel("Peso cargado")
    ax.set_ylim(0, C * 1.2)
    ax.legend(loc="upper right", fontsize=8)
    ax.text(0.01, 0.97, f"Ocupacion media: {ocup:.1f}%   ·   cota inferior L = {L}",
            transform=ax.transAxes, fontsize=8, va="top")

    if args.modo == "ninguno":
        temp_txt = "sin restriccion de temperatura"
    elif args.modo == "bandas":
        temp_txt = "temperatura: bandas fijas"
    else:
        temp_txt = f"temperatura: {args.modo} (delta = {args.delta:g})"

    fig.suptitle(f"Heuristica: {args.heuristica}   ·   Instancia: {os.path.basename(args.inst)}",
                 fontsize=14, fontweight="bold")
    ax.set_title(f"n={n}, C={C:g}, alpha={args.alpha:g}, {beta_txt}, {temp_txt}\n"
                 f"K = {K}   ·   similitud S = {S:.2f}   ·   objetivo = {objetivo:.3f}",
                 fontsize=10)

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=130)
    print(f"  Grafico guardado en: {args.out}")


if __name__ == "__main__":
    main()
