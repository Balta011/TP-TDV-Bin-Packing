#!/usr/bin/env python3
"""Dibuja una solucion como grafo: nodos = productos, aristas = similitud, color = camion.

Uso: python experimentacion/graficar_grafo.py --inst instancias/inst_25.txt --metodo ffd
"""
import argparse
import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from carpetas import preparar_carpeta


def leer_instancia(path):
    """Devuelve (n, C, pesos, temps, sim) leyendo la matriz completa."""
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


def correr(exe, inst, metodo, out, alpha, beta, delta, modo):
    if os.path.exists(exe):
        exe = os.path.abspath(exe)
    res = subprocess.run(
        [exe, inst, out, metodo, str(alpha), str(beta), str(delta), modo],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"ERROR corriendo {metodo}:\n{res.stderr}", file=sys.stderr)
        sys.exit(1)
    return leer_solucion(out)


def main():
    ap = argparse.ArgumentParser(description="Visualizar una solucion como grafo")
    ap.add_argument("--inst", required=True)
    ap.add_argument("--metodo", default="bfd", help="bfd | mochila | costo | meta | ffd")
    ap.add_argument("--exe", default="tp2.exe")
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--beta", default="auto", help='numero o "auto" = 1/S_max')
    ap.add_argument("--delta", type=float, default=float("inf"))
    ap.add_argument("--modo", default="delta", choices=["delta", "bandas", "hibrido"],
                    help="modo de temperatura (default: delta)")
    ap.add_argument("--umbral", type=float, default=0.4,
                    help="solo se dibujan aristas con similitud >= umbral (default 0.4)")
    ap.add_argument("--out", default=None, help="(default: en una carpeta nueva con fecha dentro de resultados/)")
    args = ap.parse_args()

    n, C, pesos, temps, sim = leer_instancia(args.inst)

    stem = os.path.splitext(os.path.basename(args.inst))[0]
    carpeta = preparar_carpeta("grafo", args, out=f"{args.metodo.upper()}_{stem}.png")
    tmp = f"{carpeta}/_tmp.out"
    camiones = correr(args.exe, args.inst, args.metodo, tmp, args.alpha, args.beta, args.delta, args.modo)
    if os.path.exists(tmp):
        os.remove(tmp)

    # Camion asignado a cada producto.
    camion_de = {}
    for k, bin_ in enumerate(camiones):
        for i in bin_:
            camion_de[i] = k

    # Construir el grafo: aristas solo por encima del umbral (para que se lea).
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i][j] >= args.umbral:
                G.add_edge(i, j, weight=sim[i][j])

    # Layout ponderado por similitud (nodos parecidos se atraen).
    pos = nx.spring_layout(G, weight="weight", seed=42, k=0.6, iterations=200)

    # Estilos de nodo.
    cmap = plt.cm.tab20
    K = len(camiones)
    colores = [cmap(camion_de.get(i, 0) % 20) for i in range(n)]
    tams = [120 + 400 * (pesos[i] / max(pesos)) for i in range(n)]

    fig, ax = plt.subplots(figsize=(11, 9))

    # Aristas: grosor y opacidad proporcionales a la similitud.
    for i, j, d in G.edges(data=True):
        ax.plot([pos[i][0], pos[j][0]], [pos[i][1], pos[j][1]],
                color="gray", alpha=0.15 + 0.5 * d["weight"],
                linewidth=0.4 + 2.2 * d["weight"], zorder=1)

    nx.draw_networkx_nodes(G, pos, node_color=colores, node_size=tams,
                           edgecolors="black", linewidths=0.6, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, ax=ax)

    # Leyenda: un color por camion.
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", color="w", label=f"Camion {k}",
               markerfacecolor=cmap(k % 20), markersize=9, markeredgecolor="black")
        for k in range(K)
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, title="Asignacion")

    delta_txt = "sin limite" if args.delta == float("inf") else f"{args.delta:g}"
    ax.set_title(
        f"Solucion como grafo  -  metodo={args.metodo}, K={K}\n"
        f"{os.path.basename(args.inst)} (n={n}, delta={delta_txt}, modo={args.modo})  |  "
        f"aristas: similitud >= {args.umbral:g}",
        fontsize=11,
    )
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(args.out, dpi=130)
    print(f"Grafo guardado en: {args.out}  (metodo={args.metodo}, K={K})")


if __name__ == "__main__":
    main()
