#ifndef TEMPERATURA_H
#define TEMPERATURA_H

#include <string>
#include <vector>

// Formas de modelar la temperatura (siempre como restriccion):
//   DELTA:   en cada camion, max(t) - min(t) <= delta.
//   BANDAS:  cada camion lleva productos de una sola categoria fija.
//   HIBRIDO: hay un setpoint a <= delta de todos los productos del camion.
enum class ModoTemp { DELTA, BANDAS, HIBRIDO };

// Temperaturas fijas de la heladera: -18, 4, 20 y 65 grados.
const std::vector<double>& setpoints();

// Indice del setpoint mas cercano a t.
int banda(double t);

// ¿Un camion con temperaturas entre tmin y tmax cumple la restriccion?
bool temp_bin_ok(ModoTemp modo, double tmin, double tmax, double delta);

ModoTemp parse_modo_temp(const std::string& s);
std::string nombre_modo(ModoTemp m);

#endif
