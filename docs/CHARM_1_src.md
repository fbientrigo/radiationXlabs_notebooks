# Guia de Sources

Se analizo superficialmente cada uno de los archivos en la carpeta `1_src/` a lo que se genero una descripcion breve del funcionamiento a manera de entender como calza con el resto de la pipeline

# 1_src/ — Scripts y Macros de Procesamiento

Este directorio contiene los scripts y macros (Python y C/C++ para ROOT) que implementan:

- Lectura y conversión de datos crudos (DMM, VERDAQ8, CPLD)  
- Cálculo de métricas de fiabilidad y fluencia  
- Generación de histogramas “time-to-failure” (TTF)  
- Visualización interactiva de waveforms y distribuciones  

Cada archivo se documenta a continuación con:

- **Propósito**: qué hace  
- **Inputs**: archivos o directorios que utiliza  
- **Salida / comportamiento**: resultado principal  

---

## cpld_TTF_2.C

**Propósito**  
Dibuja un histograma ROOT de “Time to Failure” para el segundo run de CPLD, y muestra estadísticas de media y desviación estándar.

**Inputs**  
Ninguno en tiempo de ejecución (valores “hardcoded” en el macro).

**Salida / comportamiento**  
- Histograma `hr2TTF__1` con 100 bins entre 0–1000 s  
- Estadísticas de entries, mean, stddev  
- Lienzo ROOT interactivo con título y cuadrícula

---

## cpld_TTF_3.C

**Propósito**  
Análogo a `cpld_TTF_2.C`, pero para el tercer run de CPLD.

**Inputs**  
Valores “hardcoded” de fallos en bins (via `SetBinContent`).

**Salida / comportamiento**  
- Histograma `hr3TTF__1` con 100 bins entre 0–1000 s  
- Estadísticas de entries, mean, stddev  
- Lienzo ROOT con estilo idéntico al run 2

---

## get_reliability.cxx

**Propósito**  
Calcula y grafica, para Second & Third Run, la fluencia acumulada, errores de bits y métricas TTF/FTF.

**Inputs**  
- `beam_data_second_run.root` / `beam_data_third_run.root`  
- `cpld_data_second_run.root` / `cpld_data_third_run.root`

**Salida / comportamiento**  
- Histogramas ROOT:  
  - `hr2B`, `hr3B`: fluence vs tiempo  
  - `hr2`, `hr3`: errores de bits vs tiempo  
  - `hr2TTF`, `hr3TTF`: time-to-failure  
  - `hr2FTF`, `hr3FTF`: fluence-to-failure  
- Dibujos secuenciales en un canvas “c”

---

## makeCPLD_pics_bkup.cxx

**Propósito**  
Genera gráficos de evolución temporal de cada uno de los 32 bits del CPLD en un `TMultiGraph`.

**Inputs**  
- `cpld_data.root` (árbol `tr` con ramas `t` y `bit[32]`)

**Salida / comportamiento**  
- `TMultiGraph` con 32 curvas (un color por bit)  
- Leyenda coloreada con nombres `bit0`…`bit31`  
- Canvas ROOT de 960×720 px

---

## monitor_current.py

**Propósito**  
Grafica las lecturas de corriente (IDC e IAC) a partir de un archivo DMM en `dataC/`.

**Inputs**  
- Archivo `.dat` de DMM con timestamps Unix y dos columnas de corriente

**Salida / comportamiento**  
- Figura Matplotlib con dos subplots (IDC en el primer eje, IAC en el segundo)  
- Conversión de timestamp a `datetime64[s]` y ajuste horario (+2 h)

___


## monitor_data_C.py

**Propósito**  
Lectura y visualización en tiempo real de datos digitales (VERDAQ8) y de corriente (DMM), combinando tres tipos de gráficos:
1. **Waveforms**: secuencias de muestras de 8 canales.  
2. **Histograma**: distribución de amplitudes de cada canal.  
3. **Corriente**: evolución temporal de las lecturas IDC e IAC.

**Inputs**  
- `datadir` (por defecto `"data/"`): carpeta con archivos VERDAQ8 (`.dat`).  
- `datadirC` (por defecto `"dataC/"`): carpeta con archivos DMM (`.dat`).  

**Salida / comportamiento**  
- Abre tres figuras Matplotlib ubicadas en posiciones fijas en pantalla.  
- `DATA_MONITOR.plot()`: dibuja los **NPTS** últimos puntos de las formas de onda y del histograma.  
- `DATA_MONITOR.draw()`: actualiza la figura de corriente y pausa de 20 s antes de refrescar.  
- Manejador de línea de comandos:  
  ```bash
  python monitor_data_C.py path/to/verdaq_file.dat path/to/dmm_file.dat
````

o, sin argumentos, itera sobre los últimos archivos en `data/` y `dataC/` en bucle.

---

## monitor\_data.py

**Propósito**
Visualizar en bucle dinámico únicamente los **waveforms** y los **histogramas** de los datos VERDAQ8 de TCMS.

**Inputs**

* `datadir` (hardcodeado como `"data_run/VERDAQ8_data/"`): carpeta con archivos `.dat`.

**Salida / comportamiento**

* Dos figuras Matplotlib:

  1. Waveforms de 9 subplots (un canal por subplot).
  2. Histogramas 3×3 de las últimas **NPTS** muestras.
* Ciclo infinito que va refrescando cada 20 s.
* Uso:

  ```bash
  python monitor_data.py path/to/verdaq_file.dat
  ```

  o sin argumentos, toma siempre el archivo más reciente de `data_run/VERDAQ8_data/`.

---

## plot\_data.py

**Propósito**
Script rápido para graficar, con Pandas y Matplotlib, el último archivo VERDAQ8 de la carpeta `data_debug/VERDAQ8_data/`.

**Inputs**

* Carpeta `data_debug/VERDAQ8_data/` con archivos `.dat` de VERDAQ8.

**Salida / comportamiento**

* Lee el último archivo, filtra las líneas con “#”, convierte hex a entero y dibuja cada canal en un subplot independiente.
* Uso:

  ```bash
  python plot_data.py
  ```

---

## process\_time.cxx

**Propósito**
Esqueleto de macro ROOT/C++ para parsear cadenas de fecha/hora de formato `"%m/%d/%Y %I:%M:%S %p"` usando `strptime`.

**Inputs**

* Variables ROOT `TString t` con timestamp en formato texto.

**Salida / comportamiento**

* Convierte `t` a `struct tm tm_s` y está listo para extenderse con procesamiento adicional.

---

## testplot.py

**Propósito**
Demo de Matplotlib que genera de forma interactiva curvas de $x^n$ para $n=1\ldots4$.

**Inputs**
— Ninguno.

**Salida / comportamiento**

* Crea un plot en bucle con eje X en $[-50,50]$ y eje Y en $[0,10000]$.
* Cada iteración traza $x^n$, pausa 1 s antes de continuar.

---

## tr.C / tr.h

**Propósito**
Clase Root auto-generada para manejar el TTree `"tr"` dentro de `cpld_data.root`, con métodos estándar:

* `Init()`, `GetEntry()`, `LoadTree()`, `Loop()`, `Show()`, `Notify()`.

**Inputs**

* Archivo ROOT `cpld_data.root` con un árbol `tr` que contiene ramas:

  * `Double_t t`
  * `Int_t bit[32]`

**Salida / comportamiento**

* `Loop()`: recorre todas las entradas del árbol sin filtrar (esqueleto para usuario).
* Permite extensión para análisis personalizado dentro de ROOT.

---

## verdaq\_ana.py

**Propósito**
Carga un archivo de datos VERDAQ8, convierte valores hexadecimales a enteros y datetime, prepara DataFrame para análisis.

**Inputs**

* Archivo `.dat` de VERDAQ8 (p.ej. `verDAQ8_data_2022_05_25-29_all.dat`).

**Salida / comportamiento**

* DataFrame de Pandas con:

  * Columna 0: timestamp convertido a `datetime64[s]` y corregido +2 h.
  * Columnas 1–9: valores convertidos de hex a `int` o `'nan'`.
* Ejemplo de uso:

  ```bash
  python verdaq_ana.py verDAQ8_data_2022_05_25-29_all.dat
  ```

---
