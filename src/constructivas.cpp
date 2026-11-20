#include "constructivas.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <vector>

static bool g_traza = false;
static std::string g_archivo_traza;

void set_traza_consola(bool activa) { g_traza = activa; }
void set_traza_archivo(const std::string& path) { g_archivo_traza = path; }

// Estado de un camion mientras se arma la solucion.
struct EstadoCamion {
    double carga = 0.0;
    double tmin = 0.0;
    double tmax = 0.0;
    bool vacio = true;
};

static std::vector<int> orden_por_peso_desc(const Instancia& inst) {
    std::vector<int> orden(inst.n);
    std::iota(orden.begin(), orden.end(), 0);
    std::stable_sort(orden.begin(), orden.end(),
                     [&](int a, int b) { return inst.peso[a] > inst.peso[b]; });
    return orden;
}

// ¿Entra el producto i en el camion e, por peso y por temperatura?
static bool cabe(const EstadoCamion& e, int i, const Instancia& inst,
                 double delta_temp, ModoTemp modo) {
    if (e.carga + inst.peso[i] > inst.capacidad + 1e-9) return false;
    double nuevo_min = e.vacio ? inst.temperatura[i] : std::min(e.tmin, inst.temperatura[i]);
    double nuevo_max = e.vacio ? inst.temperatura[i] : std::max(e.tmax, inst.temperatura[i]);
    return temp_bin_ok(modo, nuevo_min, nuevo_max, delta_temp);
}

static void agregar(EstadoCamion& e, int i, const Instancia& inst) {
    if (e.vacio) {
        e.tmin = e.tmax = inst.temperatura[i];
        e.vacio = false;
    } else {
        e.tmin = std::min(e.tmin, inst.temperatura[i]);
        e.tmax = std::max(e.tmax, inst.temperatura[i]);
    }
    e.carga += inst.peso[i];
}

// Registra los pasos de una construccion: en consola y/o en el archivo que lee
// la ventana animada.
struct Traza {
    const Instancia& inst;
    std::ofstream archivo;
    int paso = 0;

    Traza(const Instancia& i, const std::string& nombre, const std::string& detalle) : inst(i) {
        if (!g_archivo_traza.empty()) {
            archivo.open(g_archivo_traza);
            archivo << "# heuristica: " << nombre << "\n"
                    << "# producto destino nuevo candidatos\n";
        }
        if (g_traza)
            std::cout << "\n=== Construyendo la solucion con " << nombre << " ===\n"
                      << "  (" << detalle << ")\n\n";
    }

    // El producto i se cargo en el camion 'destino' (que ahora pesa 'carga').
    // 'candidatos' son los camiones donde podia ir; 'nuevo' si se abrio en este paso.
    void registrar(int i, const std::vector<int>& candidatos, int destino, bool nuevo, double carga) {
        if (g_traza) {
            std::cout << "  [" << std::setw(3) << paso + 1 << "] producto " << std::setw(3) << i
                      << "  (peso " << std::setw(5) << inst.peso[i]
                      << ", " << std::setw(5) << inst.temperatura[i] << " C)   candidatos: ";
            if (candidatos.empty()) {
                std::cout << "ninguno";
            } else {
                std::cout << "{";
                const size_t mostrar = std::min<size_t>(candidatos.size(), 8);
                for (size_t c = 0; c < mostrar; ++c) std::cout << (c ? ", " : "") << candidatos[c];
                if (candidatos.size() > mostrar) std::cout << ", ...";
                std::cout << "}";
            }
            std::cout << (nuevo ? "  -> abre camion " : "  -> camion ") << destino
                      << "  (carga " << carga << "/" << inst.capacidad << ")\n";
        }
        if (archivo.is_open()) {
            archivo << i << ' ' << destino << ' ' << (nuevo ? 1 : 0) << ' ';
            if (candidatos.empty()) archivo << '-';
            for (size_t c = 0; c < candidatos.size(); ++c) archivo << (c ? "," : "") << candidatos[c];
            archivo << '\n';
        }
        ++paso;
    }

    void terminar(int K) {
        if (g_traza) std::cout << "\n  Listo: " << K << " camiones.\n";
    }
};

// ---------------------------------------------------------------------------
// FFD y BFD
// ---------------------------------------------------------------------------

// Parte comun de FFD y BFD: solo cambia como se elige entre los camiones candidatos.
static Solucion construir(const Instancia& inst, double delta_temp, ModoTemp modo,
                          bool best_fit, const char* nombre) {
    Solucion sol(inst);
    std::vector<EstadoCamion> estado;
    Traza traza(inst, nombre, "productos ordenados de mayor a menor peso");

    for (int i : orden_por_peso_desc(inst)) {
        std::vector<int> candidatos;
        for (int k = 0; k < sol.K(); ++k)
            if (cabe(estado[k], i, inst, delta_temp, modo)) candidatos.push_back(k);

        int destino = -1;
        if (!candidatos.empty()) {
            destino = candidatos[0];
            if (best_fit) {
                for (int k : candidatos)
                    if (estado[k].carga > estado[destino].carga) destino = k;
            }
        }

        const bool nuevo = (destino == -1);
        if (nuevo) {
            sol.bins.push_back({});
            estado.push_back(EstadoCamion{});
            destino = sol.K() - 1;
        }
        sol.bins[destino].push_back(i);
        agregar(estado[destino], i, inst);
        traza.registrar(i, candidatos, destino, nuevo, estado[destino].carga);
    }

    traza.terminar(sol.K());
    return sol;
}

Solucion constructiva_first_fit(const Instancia& inst, double alpha, double beta,
                                double delta_temp, ModoTemp modo) {
    (void)alpha;
    (void)beta;
    return construir(inst, delta_temp, modo, false, "FFD (First-Fit Decreasing)");
}

Solucion constructiva_best_fit(const Instancia& inst, double alpha, double beta,
                               double delta_temp, ModoTemp modo) {
    (void)alpha;
    (void)beta;
    return construir(inst, delta_temp, modo, true, "BFD (Best-Fit Decreasing)");
}

// ---------------------------------------------------------------------------
// MOCHILA: un camion por vez
// ---------------------------------------------------------------------------

// Grupos de productos que pueden viajar con la semilla sin romper la temperatura.
// Esta armado para que CUALQUIER subconjunto de un grupo sea valido junto a la
// semilla, asi la mochila puede elegir libremente adentro de cada grupo.
static std::vector<std::vector<int>> grupos_por_temperatura(const Instancia& inst, int semilla,
                                                            const std::vector<int>& quedan,
                                                            double delta, ModoTemp modo) {
    const double eps = 1e-9;
    const double ts = inst.temperatura[semilla];
    std::vector<std::vector<int>> grupos;

    // Agrega el grupo de productos (sin la semilla) cuya temperatura cumple 'dentro'.
    auto agregar_grupo = [&](auto dentro) {
        std::vector<int> g;
        for (int c : quedan)
            if (c != semilla && dentro(inst.temperatura[c])) g.push_back(c);
        if (std::find(grupos.begin(), grupos.end(), g) == grupos.end()) grupos.push_back(g);
    };

    if (modo == ModoTemp::BANDAS) {
        const int b = banda(ts);
        agregar_grupo([&](double t) { return banda(t) == b; });
    } else if (std::isinf(delta)) {
        agregar_grupo([](double) { return true; });
    } else if (modo == ModoTemp::DELTA) {
        // Ventanas [L, L + delta] que contienen a la semilla. Alcanza con probar
        // como L la temperatura de cada producto entre ts - delta y ts.
        std::vector<double> bordes;
        for (int c : quedan) {
            const double t = inst.temperatura[c];
            if (t >= ts - delta - eps && t <= ts + eps) bordes.push_back(t);
        }
        std::sort(bordes.begin(), bordes.end());
        bordes.erase(std::unique(bordes.begin(), bordes.end()), bordes.end());
        for (double L : bordes)
            agregar_grupo([&](double t) { return t >= L - eps && t <= L + delta + eps; });
    } else {  // HIBRIDO: un grupo por cada setpoint al que llega la semilla
        for (double s : setpoints())
            if (std::abs(ts - s) <= delta + eps)
                agregar_grupo([&](double t) { return std::abs(t - s) <= delta + eps; });
        if (grupos.empty()) grupos.push_back({});  // la semilla no llega a ningun setpoint
    }
    return grupos;
}

// Mochila 0/1: de los candidatos, el grupo de mayor peso total que entra en 'libre'.
// Programacion dinamica sobre el peso pasado a enteros (por defecto, centesimos).
static std::vector<int> mochila(const Instancia& inst, const std::vector<int>& candidatos,
                                double libre) {
    double escala = 100.0;
    while (escala > 1.0 && libre * escala > 2e6) escala /= 10.0;  // limita la memoria
    const int cap = static_cast<int>(std::floor(libre * escala + 1e-6));
    if (cap <= 0 || candidatos.empty()) return {};

    // Pesos redondeados para arriba: nunca se pasa de la capacidad real.
    std::vector<int> w(candidatos.size());
    for (size_t a = 0; a < candidatos.size(); ++a)
        w[a] = static_cast<int>(std::ceil(inst.peso[candidatos[a]] * escala - 1e-6));

    // alcanzable[c]: algun grupo suma exactamente c. ultimo[c]: el candidato con
    // el que se llego a c (sirve para reconstruir el grupo).
    std::vector<char> alcanzable(cap + 1, 0);
    std::vector<int> ultimo(cap + 1, -1);
    alcanzable[0] = 1;
    for (size_t a = 0; a < candidatos.size(); ++a) {
        if (w[a] <= 0) continue;
        for (int c = cap; c >= w[a]; --c) {  // de mayor a menor: cada producto una sola vez
            if (!alcanzable[c] && alcanzable[c - w[a]]) {
                alcanzable[c] = 1;
                ultimo[c] = static_cast<int>(a);
            }
        }
    }

    int mejor = cap;
    while (mejor > 0 && !alcanzable[mejor]) --mejor;

    std::vector<int> grupo;
    for (int c = mejor; c > 0; c -= w[ultimo[c]]) grupo.push_back(candidatos[ultimo[c]]);
    return grupo;
}

Solucion constructiva_mochila(const Instancia& inst, double alpha, double beta,
                              double delta_temp, ModoTemp modo) {
    (void)alpha;
    (void)beta;  // decide solo por peso y temperatura
    Solucion sol(inst);
    Traza traza(inst, "MOCHILA", "un camion por vez, empezando por el producto mas pesado");

    std::vector<int> quedan = orden_por_peso_desc(inst);
    while (!quedan.empty()) {
        // 1. Cada camion arranca por el producto mas pesado que queda: los chicos
        //    se acomodan facil en cualquier camion y los pesados no.
        const int semilla = quedan.front();
        const double libre = inst.capacidad - inst.peso[semilla];

        // 2 y 3. Para cada grupo compatible en temperatura, la mochila que mas llena.
        std::vector<int> elegido;
        double mejor_carga = -1.0;
        for (const auto& candidatos : grupos_por_temperatura(inst, semilla, quedan, delta_temp, modo)) {
            std::vector<int> grupo = mochila(inst, candidatos, libre);
            double carga = 0.0;
            for (int j : grupo) carga += inst.peso[j];
            if (carga > mejor_carga + 1e-9) {
                mejor_carga = carga;
                elegido = grupo;
            }
        }

        // 4. Cargar el camion (de mayor a menor peso, para que la animacion se lea mejor).
        const int k = sol.K();
        sol.bins.push_back({semilla});
        double carga = inst.peso[semilla];
        traza.registrar(semilla, {}, k, true, carga);

        std::stable_sort(elegido.begin(), elegido.end(),
                         [&](int a, int b) { return inst.peso[a] > inst.peso[b]; });
        for (int j : elegido) {
            sol.bins[k].push_back(j);
            carga += inst.peso[j];
            traza.registrar(j, {k}, k, false, carga);
        }

        // Sacar de 'quedan' lo que se cargo, manteniendo el orden por peso.
        std::vector<char> cargado(inst.n, 0);
        cargado[semilla] = 1;
        for (int j : elegido) cargado[j] = 1;
        quedan.erase(std::remove_if(quedan.begin(), quedan.end(), [&](int x) { return cargado[x]; }),
                     quedan.end());
    }

    traza.terminar(sol.K());
    return sol;
}

// ---------------------------------------------------------------------------
// COSTO: al camion donde menos empeora la funcion objetivo
// ---------------------------------------------------------------------------
Solucion constructiva_costo(const Instancia& inst, double alpha, double beta,
                            double delta_temp, ModoTemp modo) {
    Solucion sol(inst);
    std::vector<EstadoCamion> estado;
    Traza traza(inst, "COSTO", "productos de mayor a menor peso");

    for (int i : orden_por_peso_desc(inst)) {
        std::vector<int> candidatos;
        for (int k = 0; k < sol.K(); ++k)
            if (cabe(estado[k], i, inst, delta_temp, modo)) candidatos.push_back(k);

        // Sumar i al camion k cambia el objetivo en -beta * (similitud de i con lo
        // que ya lleva k). Abrir un camion nuevo lo cambia en +alpha.
        int destino = -1;
        double mejor = 0.0;
        for (int k : candidatos) {
            double similitud = 0.0;
            for (int j : sol.bins[k]) similitud += inst.sim(i, j);
            const double costo = -beta * similitud;
            if (destino == -1 || costo < mejor - 1e-12) {
                destino = k;
                mejor = costo;
            }
        }
        // Solo abre un camion si es estrictamente mas barato (o si no entra en ninguno).
        if (destino != -1 && alpha < mejor - 1e-12) destino = -1;

        const bool nuevo = (destino == -1);
        if (nuevo) {
            sol.bins.push_back({});
            estado.push_back(EstadoCamion{});
            destino = sol.K() - 1;
        }
        sol.bins[destino].push_back(i);
        agregar(estado[destino], i, inst);
        traza.registrar(i, candidatos, destino, nuevo, estado[destino].carga);
    }

    traza.terminar(sol.K());
    return sol;
}
