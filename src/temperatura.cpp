#include "temperatura.h"

#include <cmath>
#include <stdexcept>

static const std::vector<double> SP = {-18.0, 4.0, 20.0, 65.0};

const std::vector<double>& setpoints() { return SP; }

int banda(double t) {
    int mejor = 0;
    double d = std::abs(t - SP[0]);
    for (int k = 1; k < static_cast<int>(SP.size()); ++k) {
        double dk = std::abs(t - SP[k]);
        if (dk < d) {
            d = dk;
            mejor = k;
        }
    }
    return mejor;
}

bool temp_bin_ok(ModoTemp modo, double tmin, double tmax, double delta) {
    const double eps = 1e-9;
    switch (modo) {
        case ModoTemp::DELTA:
            return (tmax - tmin) <= delta + eps;
        case ModoTemp::BANDAS:
            // La banda crece con la temperatura: alcanza con mirar los extremos.
            return banda(tmin) == banda(tmax);
        case ModoTemp::HIBRIDO:
            for (double s : SP)
                if (s >= tmax - delta - eps && s <= tmin + delta + eps) return true;
            return false;
    }
    return true;
}

ModoTemp parse_modo_temp(const std::string& s) {
    if (s == "delta") return ModoTemp::DELTA;
    if (s == "bandas") return ModoTemp::BANDAS;
    if (s == "hibrido") return ModoTemp::HIBRIDO;
    throw std::runtime_error("Modo de temperatura desconocido: " + s +
                             " (use delta | bandas | hibrido)");
}

std::string nombre_modo(ModoTemp m) {
    switch (m) {
        case ModoTemp::DELTA: return "delta";
        case ModoTemp::BANDAS: return "bandas";
        case ModoTemp::HIBRIDO: return "hibrido";
    }
    return "?";
}
