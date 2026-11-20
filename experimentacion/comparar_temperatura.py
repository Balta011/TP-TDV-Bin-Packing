#!/usr/bin/env python3
"""Compara los tres modelos de temperatura (delta, bandas, hibrido) variando delta.

Uso: python experimentacion/comparar_temperatura.py --instdir instancias/lote
"""
import argparse
import glob
import os
import subprocess
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from carpetas import preparar_carpeta

MODOS = ["delta", "bandas", "hibrido"]
COLOR = {"delta": "#1D9E75", "bandas": "#E24B4A", "hibrido": "#378ADD"}
ETIQ = {"delta": "Δ (relativo)", "bandas": "bandas fijas", "hibrido": "híbrido"}


def contar_camiones(path):
    k = 0
    with open(path, "r", encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                k += 1
    return k


def correr(exe, inst, out, delta, modo):
    if os.path.exists(exe):
        exe = os.path.abspath(exe)
    res = subprocess.run(
        [exe, inst, out, "bfd", "1", "auto", str(delta), modo],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"ERROR {modo} d={delta} en {inst}:\n{res.stderr}", file=sys.stderr)
        sys.exit(1)
    return contar_camiones(out)


def main():
    ap = argparse.ArgumentParser(description="Comparar los 3 modelos de temperatura")
    ap.add_argument("--instdir", default="instancias/lote")
    ap.add_argument("--exe", default="tp2.exe")
    ap.add_argument("--out", default=None, help="(default: en una carpeta nueva con fecha dentro de resultados/)")
    args = ap.parse_args()

    instancias = sorted(glob.glob(os.path.join(args.instdir, "*.txt")))
    if not instancias:
        print(f"No hay instancias en {args.instdir}", file=sys.stderr)
        sys.exit(1)

    deltas = [2, 4, 6, 8, 10, 12, 14, 16, 20, 24, 30, 40]
    carpeta = preparar_carpeta("comparacion_temperatura", args, out="comparacion_temperatura.png")
    tmp = f"{carpeta}/_tmp.out"

    # media[modo][delta] = K medio sobre las instancias
    media = {m: {} for m in MODOS}
    for modo in MODOS:
        for d in deltas:
            ks = [correr(args.exe, inst, tmp, d, modo) for inst in instancias]
            media[modo][d] = sum(ks) / len(ks)
    if os.path.exists(tmp):
        os.remove(tmp)

    fig, ax = plt.subplots(figsize=(10, 6))
    for modo in MODOS:
        ys = [media[modo][d] for d in deltas]
        ax.plot(deltas, ys, marker="o", color=COLOR[modo], label=ETIQ[modo], linewidth=2)

    ax.set_xlabel("Tolerancia Δ (grados)")
    ax.set_ylabel("Camiones (K medio sobre %d instancias)" % len(instancias))
    ax.set_title("Costo en camiones de cada modelo de temperatura\n"
                 "(BFD · menos camiones = mejor)")
    ax.legend(title="Modelo de temperatura")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(args.out, dpi=130)

    print(f"Grafico guardado en: {args.out}")
    with open(f"{carpeta}/k_medio_por_modelo.csv", "w", encoding="utf-8") as f:
        f.write("delta," + ",".join(MODOS) + "\n")
        for d in deltas:
            f.write(f"{d}," + ",".join(f"{media[m][d]:.4f}" for m in MODOS) + "\n")
    print(f"Tabla guardada en: {carpeta}/k_medio_por_modelo.csv")
    print("\nK medio por modelo:")
    print(f"{'delta':>6} | " + " | ".join(f"{m:>8}" for m in MODOS))
    for d in deltas:
        print(f"{d:>6} | " + " | ".join(f"{media[m][d]:>8.2f}" for m in MODOS))


if __name__ == "__main__":
    main()
