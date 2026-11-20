#include "metaheuristica.h"

#include "busqueda_local.h"
#include "constructivas.h"

// TODO (grupo): implementar la metaheuristica.
// Hoy solo arma una solucion con FFD y le aplica la busqueda local una vez.
//
// Idea si eligen GRASP:
//   mejor = (ninguna)
//   repetir params.iteraciones veces:
//     1. construir una solucion con algo de azar: por ejemplo como FFD, pero
//        eligiendo al azar entre los mejores camiones candidatos de cada paso.
//        Usar std::mt19937 con params.semilla, asi los experimentos dan siempre
//        lo mismo.
//     2. mejorarla con busqueda_local(sol, alpha, beta, delta_temp, modo).
//     3. si sol.objetivo(alpha, beta) es menor que el de la mejor, guardarla.
//   devolver la mejor.
//
// La solucion final tiene que ser factible: sol.es_factible(delta_temp, modo).
Solucion metaheuristica(const Instancia& inst, const ParamsMeta& params) {
    Solucion sol = constructiva_first_fit(inst, params.alpha, params.beta,
                                          params.delta_temp, params.modo);
    sol = busqueda_local(std::move(sol), params.alpha, params.beta,
                         params.delta_temp, params.modo);
    return sol;
}
