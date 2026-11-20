#include "busqueda_local.h"

// TODO (grupo): implementar RELOCATE.
// Pasos sugeridos:
//   1. Para cada producto i (que esta en el camion a) y cada camion b != a:
//   2.   chequear que i entra en b: peso de b + peso de i <= C, y temperatura
//        de b con i agregado valida (temp_bin_ok).
//   3.   calcular cuanto cambia el objetivo SIN recalcular todo:
//          perdida  = suma de sim(i, j) para j en a (sin contar a i)
//          ganancia = suma de sim(i, j) para j en b
//          vacia    = 1 si a se queda sin productos, 0 si no
//          cambio   = -alpha * vacia - beta * (ganancia - perdida)
//   4.   si cambio < 0 mejora: mover i, borrar a si quedo vacio y devolver true.
//   Variante: en vez de aplicar la primera mejora, recorrer todo y aplicar la
//   mejor (primera mejora vs. mejor mejora es algo para comparar en el informe).
bool operador_relocate(Solucion& sol, double alpha, double beta,
                       double delta_temp, ModoTemp modo) {
    (void)sol;
    (void)alpha;
    (void)beta;
    (void)delta_temp;
    (void)modo;
    return false;
}

// TODO (grupo): implementar SWAP.
// Pasos sugeridos:
//   1. Para cada par de productos i (camion a) y j (camion b), con a != b:
//   2.   chequear capacidad: peso(a) - w_i + w_j <= C  y  peso(b) - w_j + w_i <= C.
//   3.   chequear temperatura: a sin i y con j, y b sin j y con i (temp_bin_ok).
//   4.   cambio de similitud (k recorre los demas productos de cada camion):
//          en a: - suma sim(i, k) + suma sim(j, k)
//          en b: - suma sim(j, k) + suma sim(i, k)
//        cambio = -beta * (cambio en a + cambio en b)     (K no cambia)
//   5.   si cambio < 0 mejora: intercambiar i y j y devolver true.
bool operador_swap(Solucion& sol, double alpha, double beta,
                   double delta_temp, ModoTemp modo) {
    (void)sol;
    (void)alpha;
    (void)beta;
    (void)delta_temp;
    (void)modo;
    return false;
}

Solucion busqueda_local(Solucion inicial, double alpha, double beta,
                        double delta_temp, ModoTemp modo) {
    Solucion actual = std::move(inicial);
    bool mejoro = true;
    while (mejoro) {
        mejoro = false;
        if (operador_relocate(actual, alpha, beta, delta_temp, modo)) mejoro = true;
        if (operador_swap(actual, alpha, beta, delta_temp, modo)) mejoro = true;
    }
    return actual;
}
