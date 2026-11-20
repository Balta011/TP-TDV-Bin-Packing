#!/usr/bin/env python3
"""Ventana animada con la construccion de una solucion, paso a paso.

Uso: python experimentacion/ver_construccion.py --inst <instancia> --traza <archivo.traza> --heuristica FFD
Teclas: espacio = play/pausa, flechas = paso a paso.
"""
import argparse
import math
import os
import sys

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.patches import Patch
    from matplotlib.widgets import Button, Slider
except ImportError:
    print(f"  Falta matplotlib en este Python: {sys.executable}")
    print(f'  Instalalo con:  "{sys.executable}" -m pip install matplotlib networkx')
    sys.exit(2)

try:
    import networkx as nx
except ImportError:
    nx = None


# ---------------------------------------------------------------------------
# Lectura de datos
# ---------------------------------------------------------------------------
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


def leer_traza(path):
    """Lista de pasos: (producto, camion, abrio_nuevo, [candidatos])."""
    pasos = []
    with open(path, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            prod, dest, nuevo, cand = linea.split()
            candidatos = [] if cand == "-" else [int(c) for c in cand.split(",")]
            pasos.append((int(prod), int(dest), nuevo == "1", candidatos))
    return pasos


# ---------------------------------------------------------------------------
# Layout del grafo: un grupo por componente, ordenados de frio a caliente
# ---------------------------------------------------------------------------
def calcular_posiciones(n, temps, aristas):
    if nx is None:  # sin networkx: circulo ordenado por temperatura
        orden = sorted(range(n), key=lambda i: temps[i])
        pos = {}
        for r, i in enumerate(orden):
            ang = 2 * math.pi * r / n
            pos[i] = (math.cos(ang), math.sin(ang))
        return pos

    G = nx.Graph()
    G.add_nodes_from(range(n))
    for i, j, s in aristas:
        G.add_edge(i, j, weight=s)

    comps = sorted(nx.connected_components(G),
                   key=lambda c: sum(temps[i] for i in c) / len(c))
    if len(comps) > 12:  # demasiados grupos sueltos: un unico layout
        return nx.spring_layout(G, weight="weight", seed=42)

    ncols = max(1, math.ceil(math.sqrt(len(comps) * 1.6)))
    pos = {}
    for idx, comp in enumerate(comps):
        sub = G.subgraph(comp)
        escala = min(0.95, 0.3 + 0.09 * math.sqrt(len(comp)))
        if len(comp) == 1:
            local = {next(iter(comp)): (0.0, 0.0)}
        else:
            local = nx.spring_layout(sub, weight="weight", seed=42, scale=escala)
        cx = (idx % ncols) * 2.2
        cy = -(idx // ncols) * 2.2
        for i, (x, y) in local.items():
            pos[i] = (cx + x, cy + y)
    return pos


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Ver la construccion de una solucion")
    ap.add_argument("--inst", required=True)
    ap.add_argument("--traza", required=True)
    ap.add_argument("--heuristica", default="?")
    ap.add_argument("--delta", default="inf")
    ap.add_argument("--modo", default="ninguno")
    ap.add_argument("--umbral", type=float, default=0.5,
                    help="se dibujan aristas con similitud >= umbral")
    ap.add_argument("--vel", type=float, default=4.0, help="pasos por segundo")
    ap.add_argument("--guardar", default="",
                    help="en vez de abrir la ventana, guarda una foto del paso --paso en este PNG")
    ap.add_argument("--paso", type=int, default=-1, help="paso a fotografiar (default: el ultimo)")
    args = ap.parse_args()

    if args.guardar:
        matplotlib.use("Agg")

    n, C, pesos, temps, sim = leer_instancia(args.inst)
    pasos = leer_traza(args.traza)
    N = len(pasos)
    K_final = max(d for _, d, _, _ in pasos) + 1 if pasos else 0
    nombre_inst = os.path.basename(args.inst)

    aristas = [(i, j, sim[i][j]) for i in range(n) for j in range(i + 1, n)
               if sim[i][j] >= args.umbral]
    pos = calcular_posiciones(n, temps, aristas)
    xs = [pos[i][0] for i in range(n)]
    ys = [pos[i][1] for i in range(n)]
    wmax = max(pesos)
    tam = [35 + 260 * (pesos[i] / wmax) for i in range(n)]

    # Colores bien distintos entre camiones consecutivos.
    paleta = (list(plt.cm.tab10.colors) + list(plt.cm.Dark2.colors)
              + list(plt.cm.Set1.colors) + list(plt.cm.tab20b.colors))

    def color(k):
        return paleta[k % len(paleta)]

    GRIS = (0.85, 0.85, 0.85, 1.0)

    # --- Figura y ejes -------------------------------------------------------
    fig = plt.figure(figsize=(14, 8))
    try:
        fig.canvas.manager.set_window_title(f"Construccion: {args.heuristica} - {nombre_inst}")
    except Exception:
        pass
    if args.modo == "ninguno":
        temp_txt = "sin restriccion de temperatura"
    elif args.modo == "bandas":
        temp_txt = "temperatura: bandas fijas"
    else:
        temp_txt = f"temperatura: {args.modo} (delta = {args.delta})"
    fig.suptitle(f"Heuristica: {args.heuristica}   ·   Instancia: {nombre_inst}   ·   "
                 f"n = {n}, C = {C:g}, {temp_txt}", fontsize=13, fontweight="bold")

    ax_g = fig.add_axes([0.01, 0.24, 0.57, 0.66])
    ax_b = fig.add_axes([0.63, 0.31, 0.35, 0.58])
    ax_g.set_axis_off()
    ax_g.set_title("Grafo de similitud  (color = camion, gris = sin ubicar)", fontsize=11)

    # Aristas de fondo (todas las similitudes fuertes, muy tenues).
    ax_g.add_collection(LineCollection(
        [[pos[i], pos[j]] for i, j, _ in aristas],
        colors=[(0.5, 0.5, 0.5, 0.10)], linewidths=0.6, zorder=1))
    # Aristas dentro de un mismo camion (se actualizan en cada paso).
    lc_dentro = LineCollection([], linewidths=1.8, zorder=2)
    ax_g.add_collection(lc_dentro)
    nodos = ax_g.scatter(xs, ys, s=tam, c=[GRIS] * n, edgecolors="gray",
                         linewidths=0.5, zorder=3)
    aro = ax_g.scatter([0], [0], s=[600], facecolors="none", edgecolors="#E3A21A",
                       linewidths=3, zorder=4)
    aro.set_visible(False)
    ax_g.set_aspect("equal", adjustable="datalim")
    ax_g.margins(0.12)

    txt_paso = fig.text(0.02, 0.165, "", fontsize=12, fontweight="bold")
    txt_decision = fig.text(0.02, 0.125, "", fontsize=11)
    txt_parcial = fig.text(0.02, 0.085, "", fontsize=11, color="#20368a")

    # --- Dibujo de un estado ---------------------------------------------------
    estado = {"k": 0, "play": True}

    def dibujar(k):
        estado["k"] = k
        asign = [-1] * n
        carga = [0.0] * K_final
        tmin = [None] * K_final
        tmax = [None] * K_final
        for (i, d, _, _) in pasos[:k]:
            asign[i] = d
            carga[d] += pesos[i]
            tmin[d] = temps[i] if tmin[d] is None else min(tmin[d], temps[i])
            tmax[d] = temps[i] if tmax[d] is None else max(tmax[d], temps[i])
        abiertos = max(asign) + 1 if k > 0 else 0

        actual = pasos[k - 1] if k > 0 else None
        candidatos = set(actual[3]) if actual else set()

        # Nodos: color del camion; borde grueso si su camion es candidato.
        caras, bordes, anchos = [], [], []
        for i in range(n):
            d = asign[i]
            if d < 0:
                caras.append(GRIS)
                bordes.append((0.6, 0.6, 0.6, 1))
                anchos.append(0.4)
            else:
                caras.append(color(d))
                vec = d in candidatos
                bordes.append((0, 0, 0, 1) if vec else (0.25, 0.25, 0.25, 1))
                anchos.append(1.6 if vec else 0.5)
        nodos.set_facecolors(caras)
        nodos.set_edgecolors(bordes)
        nodos.set_linewidths(anchos)

        # Aristas entre productos similares que van en el mismo camion.
        segs, cols = [], []
        S = 0.0
        for i, j, s in aristas:
            if asign[i] >= 0 and asign[i] == asign[j]:
                segs.append([pos[i], pos[j]])
                c = color(asign[i])
                cols.append((c[0], c[1], c[2], 0.75))
        lc_dentro.set_segments(segs)
        lc_dentro.set_color(cols if cols else [(0, 0, 0, 0)])
        for a in range(n):  # similitud parcial con TODOS los pares (no solo aristas)
            if asign[a] < 0:
                continue
            for b in range(a + 1, n):
                if asign[b] == asign[a]:
                    S += sim[a][b]

        if actual:
            i = actual[0]
            aro.set_offsets([[pos[i][0], pos[i][1]]])
            aro.set_sizes([tam[i] * 3.2 + 120])
            aro.set_visible(True)
        else:
            aro.set_visible(False)

        # Barras: el vecindario de camiones del paso actual.
        ax_b.cla()
        x = list(range(K_final))
        for d in range(K_final):
            if d >= abiertos:
                continue
            es_cand = d in candidatos
            elegido = actual is not None and actual[1] == d
            base = carga[d]
            if elegido:
                base = carga[d] - pesos[actual[0]]
            visible = es_cand or elegido or actual is None
            ax_b.bar(d, base, color=color(d), alpha=1.0 if visible else 0.28,
                     edgecolor="black" if es_cand else "none",
                     linewidth=2.2 if es_cand else 0)
            if elegido:
                ax_b.bar(d, pesos[actual[0]], bottom=base, color="#F2C14E",
                         edgecolor="black", linewidth=1.4)
            if tmin[d] is not None:
                etiqueta = (f"{tmin[d]:g}°" if tmin[d] == tmax[d]
                            else f"[{tmin[d]:g}, {tmax[d]:g}]°")
                ax_b.text(d, carga[d] + C * 0.02, etiqueta, ha="center", va="bottom",
                          fontsize=7 if K_final > 10 else 8,
                          alpha=1.0 if visible else 0.4)
        ax_b.axhline(C, color="red", linestyle="--", linewidth=1.2)
        ax_b.set_xlim(-0.6, max(K_final, 1) - 0.4)
        ax_b.set_ylim(0, C * 1.22)
        ax_b.set_xticks(x)
        ax_b.set_xlabel("Camion")
        ax_b.set_ylabel("Peso cargado")
        ax_b.set_title("Camiones y vecindario del paso actual", fontsize=11)
        ax_b.legend(handles=[
            Patch(facecolor="white", edgecolor="black", linewidth=2, label="candidato (entra)"),
            Patch(facecolor="#F2C14E", edgecolor="black", label="producto recien cargado"),
            Patch(facecolor="lightgray", alpha=0.5, label="no entra"),
            plt.Line2D([0], [0], color="red", linestyle="--", label=f"capacidad C = {C:g}"),
        ], loc="upper right", fontsize=8)

        # Textos.
        heur = args.heuristica.upper()
        if actual is None:
            txt_paso.set_text(f"Paso 0 / {N}  ·  todavia no se ubico ningun producto")
            if heur == "MOCHILA":
                txt_decision.set_text("MOCHILA arma un camion por vez, empezando por el producto mas pesado.")
            else:
                txt_decision.set_text(f"{args.heuristica} va a recorrer los productos de mayor a menor peso.")
        else:
            i, d, nuevo, cand = actual
            txt_paso.set_text(f"Paso {k} / {N}  ·  producto {i}  (peso {pesos[i]:g}, {temps[i]:g} °C)")
            if heur == "MOCHILA":
                if nuevo:
                    txt_decision.set_text(f"MOCHILA abre el camion {d} con el producto mas pesado que queda")
                else:
                    txt_decision.set_text(f"MOCHILA lo carga en el camion {d}: es parte del grupo que mas lo llena")
            elif not cand:
                txt_decision.set_text(f"Vecindario: no entra en ningun camion abierto  ->  abre el camion {d}")
            else:
                lista = ", ".join(str(c) for c in cand[:12]) + (" ..." if len(cand) > 12 else "")
                regla = {"FFD": "el primero",
                         "BFD": "el mas lleno",
                         "COSTO": "el que menos empeora la nota (mas similitud)"}.get(heur, "uno")
                txt_decision.set_text(f"Vecindario: entra en los camiones {{{lista}}}  ->  "
                                      f"{args.heuristica} elige {regla}: camion {d}")
        txt_parcial.set_text(f"Solucion parcial: {abiertos} camiones  ·  similitud S = {S:.2f}  ·  "
                             f"productos ubicados {k} / {n}")
        fig.canvas.draw_idle()

    # Modo foto: dibuja un paso y lo guarda, sin ventana ni controles.
    if args.guardar:
        estado["play"] = False
        dibujar(N if args.paso < 0 else max(0, min(N, args.paso)))
        fig.savefig(args.guardar, dpi=110)
        print(f"  Foto guardada en: {args.guardar}")
        return

    # --- Controles ----------------------------------------------------------
    def ir(k):
        dibujar(max(0, min(N, k)))

    b_inicio = Button(fig.add_axes([0.63, 0.13, 0.065, 0.05]), "|< Inicio")
    b_atras = Button(fig.add_axes([0.70, 0.13, 0.065, 0.05]), "< Paso")
    b_play = Button(fig.add_axes([0.77, 0.13, 0.065, 0.05]), "Pausa")
    b_adel = Button(fig.add_axes([0.84, 0.13, 0.065, 0.05]), "Paso >")
    b_fin = Button(fig.add_axes([0.91, 0.13, 0.065, 0.05]), "Fin >|")
    s_vel = Slider(fig.add_axes([0.70, 0.06, 0.24, 0.03]), "Velocidad",
                   1, 30, valinit=args.vel, valstep=1)

    def set_play(on):
        estado["play"] = on
        b_play.label.set_text("Pausa" if on else "Play")
        fig.canvas.draw_idle()

    b_inicio.on_clicked(lambda _: (set_play(False), ir(0)))
    b_atras.on_clicked(lambda _: (set_play(False), ir(estado["k"] - 1)))
    b_adel.on_clicked(lambda _: (set_play(False), ir(estado["k"] + 1)))
    b_fin.on_clicked(lambda _: (set_play(False), ir(N)))

    def toggle(_=None):
        if not estado["play"] and estado["k"] >= N:
            ir(0)  # si termino, Play vuelve a empezar
        set_play(not estado["play"])

    b_play.on_clicked(toggle)

    timer = fig.canvas.new_timer(interval=int(1000 / args.vel))

    def tick():
        if estado["play"]:
            if estado["k"] < N:
                ir(estado["k"] + 1)
            else:
                set_play(False)

    timer.add_callback(tick)

    def cambiar_vel(v):
        timer.stop()
        timer.interval = int(1000 / v)
        timer.start()

    s_vel.on_changed(cambiar_vel)

    def tecla(ev):
        if ev.key == " ":
            toggle()
        elif ev.key == "right":
            set_play(False)
            ir(estado["k"] + 1)
        elif ev.key == "left":
            set_play(False)
            ir(estado["k"] - 1)
        elif ev.key == "home":
            set_play(False)
            ir(0)
        elif ev.key == "end":
            set_play(False)
            ir(N)

    fig.canvas.mpl_connect("key_press_event", tecla)

    dibujar(0)
    timer.start()
    # Guardamos referencias para que los widgets no se borren.
    fig._widgets = (b_inicio, b_atras, b_play, b_adel, b_fin, s_vel, timer)
    plt.show()


if __name__ == "__main__":
    main()
