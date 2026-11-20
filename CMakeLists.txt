cmake_minimum_required(VERSION 3.15)
project(tp2_cargas CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

add_executable(tp2
  src/main.cpp
  src/instancia.cpp
  src/solucion.cpp
  src/temperatura.cpp
  src/constructivas.cpp
  src/busqueda_local.cpp
  src/metaheuristica.cpp
)

if(MSVC)
  target_compile_options(tp2 PRIVATE /O2 /W4)
else()
  target_compile_options(tp2 PRIVATE -O2 -Wall -Wextra)
  # Linkeo estatico: ejecutable portable (sin depender de DLLs del runtime).
  # Util en MinGW/Windows y para que el corrector pueda ejecutarlo sin problemas.
  if(WIN32)
    target_link_options(tp2 PRIVATE -static -static-libgcc -static-libstdc++)
  endif()
endif()
