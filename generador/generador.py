#!/usr/bin/env python3
"""Genera instancias con el formato del enunciado.

Similitudes y temperaturas salen de categorias de producto: misma categoria ->
similitud alta y temperatura parecida.

Uso: python generador/generador.py --n 50 --C 100 --seed 1 --out instancias/inst_50.txt
"""
import argparse
import random


# Categorias de ejemplo: (nombre, temperatura_tipica_C, rango_peso)
CATEGORIAS = [
    ("congelado", -18, (2, 8)),    # helados, congelados
    ("refrigerado", 4, (1, 6)),    # lacteos, carnes
    ("ambiente", 20, (1, 10)),     # secos, enlatados
    ("caliente", 65, (1, 4)),      # comida lista
    ("limpieza", 20, (3, 12)),     # detergentes, quimicos
]


def generar(n: int, capacidad: float, seed: int):
    rng = random.Random(seed)

    # Asignar una categoria a cada producto.
    cat_idx = [rng.randrange(len(CATEGORIAS)) for _ in range(n)]

    pesos, temps = [], []
    for i in range(n):
        _, t_base, (wmin, wmax) = CATEGORIAS[cat_idx[i]]
        pesos.append(round(rng.uniform(wmin, wmax), 2))
        temps.append(round(t_base + rng.uniform(-2, 2), 1))  # ruido en la temperatura

    # Similitud: alta dentro de la misma categoria, baja entre categorias.
    sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        sim[i][i] = 1.0
        for j in range(i + 1, n):
            if cat_idx[i] == cat_idx[j]:
                s = rng.uniform(0.7, 1.0)
            else:
                s = rng.uniform(0.0, 0.3)
            sim[i][j] = sim[j][i] = round(s, 2)

    return pesos, temps, sim


def escribir(path: str, capacidad: float, pesos, temps, sim):
    n = len(pesos)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{n} {capacidad}\n")
        for i in range(n):
            f.write(f"{pesos[i]} {temps[i]}\n")
        for i in range(n):
            f.write(" ".join(str(sim[i][j]) for j in range(n)) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Generador de instancias TP2")
    ap.add_argument("--n", type=int, required=True, help="cantidad de productos")
    ap.add_argument("--C", type=float, required=True, help="capacidad de cada vehiculo")
    ap.add_argument("--seed", type=int, default=0, help="semilla aleatoria")
    ap.add_argument("--out", type=str, required=True, help="archivo de salida")
    args = ap.parse_args()

    pesos, temps, sim = generar(args.n, args.C, args.seed)
    escribir(args.out, args.C, pesos, temps, sim)
    print(f"Instancia generada: {args.out}  (n={args.n}, C={args.C}, seed={args.seed})")


if __name__ == "__main__":
    main()
