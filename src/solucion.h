#ifndef SOLUCION_H
#define SOLUCION_H

#include <limits>
#include <string>
#include <vector>

#include "instancia.h"
#include "temperatura.h"

// Una solucion: bins[k] es la lista de productos que van en el camion k.
struct Solucion {
    const Instancia* inst = nullptr;
    std::vector<std::vector<int>> bins;

    Solucion() = default;
    explicit Solucion(const Instancia& i) : inst(&i) {}

    // Cantidad de camiones (cuenta tambien los vacios: conviene borrarlos).
    int K() const { return static_cast<int>(bins.size()); }

    // Peso total de un camion.
    double peso_bin(const std::vector<int>& bin) const;

    // Suma de similitudes de los pares dentro de un camion.
    double similitud_bin(const std::vector<int>& bin) const;

    // Capacidad respetada, cada producto una sola vez y temperatura valida.
    bool es_factible(double delta_temp = std::numeric_limits<double>::infinity(),
                     ModoTemp modo = ModoTemp::DELTA) const;

    // Funcion objetivo a minimizar: alpha * K - beta * S.
    double objetivo(double alpha, double beta) const;

    // Escribe la solucion: una linea por camion con los indices de sus productos.
    void escribir(const std::string& path) const;
};

#endif
