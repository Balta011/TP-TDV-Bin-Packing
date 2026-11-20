#ifndef CONSTRUCTIVAS_H
#define CONSTRUCTIVAS_H

#include <limits>

#include "instancia.h"
#include "solucion.h"
#include "temperatura.h"

constexpr double SIN_RESTRICCION_TEMP = std::numeric_limits<double>::infinity();

// Traza de la construccion: en consola y/o en un archivo (lo lee la ventana animada).
void set_traza_consola(bool activa);
void set_traza_archivo(const std::string& path);

// FFD: de mayor a menor peso, cada producto al primer camion donde entra.
// Ya no es una de las heuristicas del TP (es casi igual a BFD); queda como base
// para la metaheuristica y algunos scripts.
Solucion constructiva_first_fit(const Instancia& inst, double alpha, double beta,
                                double delta_temp = SIN_RESTRICCION_TEMP,
                                ModoTemp modo = ModoTemp::DELTA);

// BFD: de mayor a menor peso, cada producto al camion mas lleno donde entra.
Solucion constructiva_best_fit(const Instancia& inst, double alpha, double beta,
                               double delta_temp = SIN_RESTRICCION_TEMP,
                               ModoTemp modo = ModoTemp::DELTA);

// MOCHILA: un camion por vez; arranca por el producto mas pesado que queda y lo
// completa con el grupo de productos que mas lo llena.
Solucion constructiva_mochila(const Instancia& inst, double alpha, double beta,
                              double delta_temp = SIN_RESTRICCION_TEMP,
                              ModoTemp modo = ModoTemp::DELTA);

// COSTO: de mayor a menor peso, cada producto al camion donde menos empeora
// la funcion objetivo alpha * K - beta * S.
Solucion constructiva_costo(const Instancia& inst, double alpha, double beta,
                            double delta_temp = SIN_RESTRICCION_TEMP,
                            ModoTemp modo = ModoTemp::DELTA);

#endif
