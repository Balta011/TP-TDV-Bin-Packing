"""Carpetas con fecha y hora para guardar los resultados de cada corrida de un script."""
import os
import time


def preparar_carpeta(nombre, args, **archivos):
    """Decide donde guardar las salidas de un script.

    `archivos` dice, para cada argumento de salida de `args` (por ejemplo out=...),
    el nombre de archivo que va dentro de la carpeta nueva. Si alguno de esos
    argumentos no se paso a mano, crea resultados/<nombre>_AAAA-MM-DD_HH-MM-SS
    (con _2, _3... si ya existe), pone ahi esos archivos y anota los parametros
    en parametros.txt. Si se pasaron todos a mano, usa la carpeta del primero.
    Devuelve la carpeta.
    """
    if all(getattr(args, clave) is not None for clave in archivos):
        primero = getattr(args, next(iter(archivos)))
        carpeta = os.path.dirname(primero) or "."
        os.makedirs(carpeta, exist_ok=True)
        return carpeta

    marca = time.strftime("%Y-%m-%d_%H-%M-%S")
    base = f"resultados/{nombre}_{marca}"
    carpeta, extra = base, 2
    while os.path.exists(carpeta):
        carpeta = f"{base}_{extra}"
        extra += 1
    os.makedirs(carpeta)

    for clave, archivo in archivos.items():
        if getattr(args, clave) is None:
            setattr(args, clave, f"{carpeta}/{archivo}")

    with open(f"{carpeta}/parametros.txt", "w", encoding="utf-8") as f:
        f.write(f"fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        for clave, valor in vars(args).items():
            f.write(f"{clave}: {valor}\n")
    return carpeta
