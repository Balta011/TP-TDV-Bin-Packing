#!/usr/bin/env python3
"""Grafica las heuristicas lado a lado sobre una instancia (una barra por camion).

Por defecto compara BFD, MOCHILA y COSTO.

Uso: python experimentacion/comparar_constructivas.py --inst instancias/inst_60.txt [--delta 6] [--modo delta]
"""
import argparse
import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")  # backend sin ventana: guarda a archivo
import matplotlib.pyplot as plt

from carpetas import preparar_carpeta


def leer_instancia(path):
    """Devuelve (n, C, pesos, temps, sim)."""
    with open(path, "r", encoding="utf-8") as f:
        tokens = f.read().split()
    it = iter(tokens)
    n = int(next(it))
    C = float(next(it))
    pesos, temps = [], []
    for _ in range(n):
        pesos.append(float(next(it)))
        temps.append(float(next(it)))
    sim = [[float(next(it)) for _ in range(n)] for _ in range(n)]
    return n, C, pesos, temps, sim


def leer_solucion(path):
    """Devuelve una lista de camiones; cada camion es una lista de indices."""
    camiones = []
    with open(path, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                camiones.append([int(x) for x in linea.split()])
    return camiones


def similitud_total(camiones, sim):
    return sum(sim[b[a]][b[c]] for b in camiones for a in range(len(b)) for c in range(a + 1, len(b)))


def correr(exe, inst, metodo, out, alpha, beta, delta, modo):
    """Corre tp2 y devuelve (camiones, objetivo_reportado)."""
    # En Windows el directorio actual no esta en el PATH: usamos ruta absoluta.
    if os.path.exists(exe):
        exe = os.path.abspath(exe)
    res = subprocess.run(
        [exe, inst, out, metodo, str(alpha), str(beta), str(delta), modo],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"ERROR corriendo {metodo}:\n{res.stderr}", file=sys.stderr)
        sys.exit(1)
    # El resumen va por stderr: "Metodo: bfd | modo: delta | K = 5 | objetivo = 4.5"
    objetivo = None
    for linea in res.stderr.splitlines():
        if "objetivo" in linea:
            try:
                objetivo = float(linea.split("objetivo =")[1].strip())
            except (IndexError, ValueError):
                pass
    return leer_solucion(out), objetivo


def graficar_barras(ax, camiones, pesos, temps, C, titulo):
    """Dibuja las cargas de cada camion como barras, con la linea de capacidad.
    Anota el rango de temperatura [min, max] de cada camion arriba de su barra."""
    cargas = [sum(pesos[i] for i in bin_) for bin_ in camiones]
    x = list(range(len(cargas)))

    # Color segun que tan lleno va (verde lleno -> rojo vacio).
    colores = [plt.cm.RdYlGn(min(carga / C, 1.0)) for carga in cargas]
    ax.bar(x, cargas, color=colores, edgecolor="black", linewidth=0.5)

    ax.axhline(C, color="red", linestyle="--", linewidth=1.2, label=f"Capacidad C = {C:g}")

    # Rango de temperatura de cada camion, arriba de la barra.
    for k, bin_ in enumerate(camiones):
        if bin_:
            tmin = min(temps[i] for i in bin_)
            tmax = max(temps[i] for i in bin_)
            etiqueta = f"{tmin:g}°" if tmin == tmax else f"[{tmin:g}, {tmax:g}]°"
            ax.text(k, cargas[k] + C * 0.02, etiqueta,
                    ha="center", va="bottom", fontsize=6 if len(camiones) > 10 else 7)

    ax.set_xticks(x)
    ax.set_xlabel("Camion")
    ax.set_ylabel("Peso cargado")
    ax.set_title(titulo, fontsize=10)
    ax.set_ylim(0, C * 1.20)
    ax.legend(loc="upper right", fontsize=8)

    # Ocupacion promedio como texto.
    if cargas:
        ocup = 100.0 * sum(cargas) / (C * len(cargas))
        ax.text(0.02, 0.97, f"Ocupacion media: {ocup:.1f}%",
                transform=ax.transAxes, fontsize=8, va="top")


def main():
    ap = argparse.ArgumentParser(description="Comparar heuristicas graficamente sobre una instancia")
    ap.add_argument("--inst", required=True, help="archivo de instancia")
    ap.add_argument("--metodos", default="bfd,mochila,costo",
                    help="heuristicas a comparar, separadas por coma (default: bfd,mochila,costo)")
    ap.add_argument("--exe", default="tp2.exe", help="ejecutable tp2 (default: tp2.exe)")
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--beta", default="auto", help='numero o "auto" = 1/S_max')
    ap.add_argument("--delta", type=float, default=float("inf"),
                    help="tolerancia termica por camion (default: sin limite)")
    ap.add_argument("--modo", default="delta", choices=["delta", "bandas", "hibrido"],
                    help="modo de temperatura (default: delta)")
    ap.add_argument("--out", default=None, help="(default: en una carpeta nueva con fecha dentro de resultados/)")
    args = ap.parse_args()

    metodos = [m.strip() for m in args.metodos.split(",") if m.strip()]
    n, C, pesos, temps, sim = leer_instancia(args.inst)

    stem = os.path.splitext(os.path.basename(args.inst))[0]
    carpeta = preparar_carpeta("comparacion_constructivas", args, out=f"comparacion_{stem}.png")

    # Correr cada heuristica.
    resultados = []
    for m in metodos:
        tmp = f"{carpeta}/_tmp_{m}.out"
        camiones, objetivo = correr(args.exe, args.inst, m, tmp, args.alpha, args.beta, args.delta, args.modo)
        if os.path.exists(tmp):
            os.remove(tmp)
        resultados.append((m.upper(), camiones, objetivo, similitud_total(camiones, sim)))

    mejor = min(r[2] for r in resultados if r[2] is not None)

    delta_txt = "sin limite" if args.delta == float("inf") else f"{args.delta:g}"
    fig, axes = plt.subplots(1, len(resultados), figsize=(6 * len(resultados), 5.5), sharey=True,
                             squeeze=False)
    fig.suptitle(
        f"Instancia: {os.path.basename(args.inst)}  "
        f"(n={n}, C={C:g}, alpha={args.alpha:g}, beta={args.beta}, delta={delta_txt}, modo={args.modo})",
        fontsize=12,
    )
    for ax, (nombre, camiones, objetivo, S) in zip(axes[0], resultados):
        marca = "   ← mejor" if objetivo is not None and abs(objetivo - mejor) < 1e-9 else ""
        graficar_barras(ax, camiones, pesos, temps, C,
                        f"{nombre}{marca}\nK = {len(camiones)}   ·   S = {S:.2f}   ·   objetivo = {objetivo:.3f}")

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(args.out, dpi=130)
    print(f"Grafico guardado en: {args.out}")
    for nombre, camiones, objetivo, S in resultados:
        print(f"  {nombre:8} -> K = {len(camiones)}, S = {S:.2f}, objetivo = {objetivo:.4f}")


if __name__ == "__main__":
    main()
