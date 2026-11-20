#include "solucion.h"

#include <algorithm>
#include <fstream>
#include <stdexcept>

double Solucion::peso_bin(const std::vector<int>& bin) const {
    double total = 0.0;
    for (int i : bin) total += inst->peso[i];
    return total;
}

double Solucion::similitud_bin(const std::vector<int>& bin) const {
    double total = 0.0;
    for (size_t a = 0; a < bin.size(); ++a)
        for (size_t b = a + 1; b < bin.size(); ++b)
            total += inst->sim(bin[a], bin[b]);
    return total;
}

bool Solucion::es_factible(double delta_temp, ModoTemp modo) const {
    if (inst == nullptr) return false;

    std::vector<int> veces(inst->n, 0);
    for (const auto& bin : bins) {
        if (peso_bin(bin) > inst->capacidad + 1e-9) return false;
        if (!bin.empty()) {
            double tmin = inst->temperatura[bin[0]];
            double tmax = tmin;
            for (int i : bin) {
                tmin = std::min(tmin, inst->temperatura[i]);
                tmax = std::max(tmax, inst->temperatura[i]);
            }
            if (!temp_bin_ok(modo, tmin, tmax, delta_temp)) return false;
        }
        for (int i : bin) {
            if (i < 0 || i >= inst->n) return false;
            veces[i]++;
        }
    }
    for (int v : veces)
        if (v != 1) return false;
    return true;
}

double Solucion::objetivo(double alpha, double beta) const {
    double suma_sim = 0.0;
    for (const auto& bin : bins) suma_sim += similitud_bin(bin);
    return alpha * K() - beta * suma_sim;
}

void Solucion::escribir(const std::string& path) const {
    std::ofstream out(path);
    if (!out) throw std::runtime_error("No se pudo escribir la salida: " + path);

    for (const auto& bin : bins) {
        if (bin.empty()) continue;
        for (size_t idx = 0; idx < bin.size(); ++idx) {
            if (idx > 0) out << ' ';
            out << bin[idx];
        }
        out << '\n';
    }
}
