#ifndef METAHEURISTICA_H
#define METAHEURISTICA_H

#include <limits>

#include "instancia.h"
#include "solucion.h"
#include "temperatura.h"

// ===========================================================================
// TODO (grupo): METAHEURISTICA. El enunciado pide una (GRASP, VNS, Tabu, ...).
// ParamsMeta junta todo lo que se puede tunear en la experimentacion.
// Agregar aca los parametros propios de la metaheuristica que elijan
// (por ejemplo, para GRASP, cuantos candidatos se sortean en cada paso).
// ===========================================================================
struct ParamsMeta {
    double alpha = 1.0;
    double beta = 1.0;  // el main la reemplaza por la que se pidio (por defecto 1/S_max)
    double delta_temp = std::numeric_limits<double>::infinity();
    ModoTemp modo = ModoTemp::DELTA;
    int iteraciones = 1000;
    unsigned semilla = 42;
};

Solucion metaheuristica(const Instancia& inst, const ParamsMeta& params);

#endif
