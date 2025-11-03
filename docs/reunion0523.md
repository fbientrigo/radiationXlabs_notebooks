# Resumen de la reunión 2025-05-23

## 1. Contexto y objetivos generales  
Para validar un dispositivo para ATLAS es imprescindible cuantificar su resistencia a la radiación. El Prof. entregará datos de tres pruebas de irradiación en CHARM:  
- **FirstRun**, **SecondRun**, **ThirdRun**  
Cada “run” reproduce distintas condiciones para estimar la tasa de fallos equivalentes a años de operación en ATLAS.

## 2. CHARM Facility  
- Instalación en CERN que simula el “mixed field” de ATLAS:  
  - Mezcla de electrones, piones, kaones, neutrones…  
  - Campo modulado con capas de plomo para igualar el espectro de ATLAS.  
  - Intensidad ≫ ATLAS: en 1 semana simula 10 años de dosis.  
- Se usan factores de seguridad en:  
  - **TID** (Total Ionizing Dose)  
  - **1 MeV n-eq** (neutrones equivalentes)  
  - **Hadrons totales**

## 3. Métricas clave  
- **MTBF** (Mean Time Between Failures): intervalo medio entre fallos detectados  
- **Bit-flip**: errores de bit en chips o ADC  
- **Fluence**: partículas acumuladas en cierto intervalo

## 4. Flujo de trabajo de datos  
1. **Adquisición** (carpeta `0_raw/`):  
   - TCMS_RadTest → directorios `data_run/`, `data_run_trenz/`  
   - DMM (`.dat`), VERDAQ8 (`.dat`, `.csv`), archivos empaquetados (`.tar`, `.zip`)  
2. **Preprocesamiento** (carpeta `1_src/`):  
   - `read_data.py`, `monitor_*.py`, `plot_data.py` → convierten hex a valores numéricos  
   - Macros ROOT (`process_time.cxx`, `get_reliability.cxx`) → extraen timestamps y calculan MTBF  
3. **Exploración** (carpeta `notebooks/FirstRunAna`):  
   - Notebooks Jupyter para graficar corriente y errores  
   - Ajuste de sampling uniforme  
4. **Análisis avanzados** (carpeta `2_processed/` + `analysis/`):  
   - Merged CSV de runs, filtrado de artefactos (`testlist.txt`)  
   - Históricos `.root` y figuras (`signals_post.png`, `FailDT_dist_sep.gif`)  
5. **Resultados finales** (carpeta `results/`):  
   - Figuras y tablas pulidas para el paper

## 5. Análisis de formas de onda  
- Se generaron **waveforms** cuadradas/senoidales de corriente.  
- Interés en cuantificar cambios sutiles (deformaciones de fase/amplitud) tras irradiación:  
  - A simple vista parecen iguales, pero puede haber variaciones pequeñas.  
  - **Propuesta**: usar análisis **wavelet** para detectar desplazamientos de fase y distorsiones armónicas.  
- Relación con bit-flip en ADC: no trivial, hay múltiples subsistemas (amplificación, muestreo, conversión).

## 6. Tareas pendientes y necesidades  
- Extraer **timestamps** directamente de los archivos de corriente, asegurar muestreo uniforme.  
- Centralizar todos los datos de `FirstRun` en `0_raw/FirstRun/` y documentar su propósito.  
- Desarrollar script unificado (`read_data.py`) que lea y convierta todos los formatos (`.dat`, `.csv`, `.root`).  
- Filtrar series por recuento de muestras y anotar periodos faltantes.  
- Definir esquema de paper (borrador lunes): estructura de secciones y figuras.

---

## Términos importantes

| Término              | Definición breve                                                                    |
|----------------------|-------------------------------------------------------------------------------------|
| **TID**              | Dosis total ionizante acumulada (krad(Si) u otra unidad).                          |
| **1 MeV n-eq**       | Fluencia de neutrones equivalente a 1 MeV.                                          |
| **MTBF**             | Tiempo medio entre fallos, estimado estadísticamente.                               |
| **Bit-flip**         | Cambio inesperado de un bit lógico (0→1 o 1→0) en la memoria o registro.            |
| **Wavelet**          | Función de análisis tiempo-frecuencia para detectar cambios localizados en la señal.|

---

## Objetivos SMART y pasos accionables

1. **(S) Consolidar datos “FirstRun”**  
   - **M**: Todos los archivos `.dat`/`.csv` de FirstRun en `0_raw/FirstRun/`  
   - **A**: Copiar y renombrar en un único subdirectorio  
   - **R**: Facilita procesamiento uniforme  
   - **T**: Completar antes del **28 may 2025**

2. **(S) Extraer y uniformar timestamps**  
   - **M**: Script que genera CSV uniformes con columnas `[timestamp, value]`  
   - **A**: Adaptar `read_data.py` + `process_time.cxx`  
   - **R**: Necesario para análisis temporal comparativo  
   - **T**: Entregar prototipo antes del **30 may 2025**

3. **(S) Implementar análisis wavelet**  
   - **M**: Generar al menos 3 rangos de frecuencias y detectar desplazamientos de fase  
   - **A**: Usar librería PyWavelets en Jupyter  
   - **R**: Identificar deformaciones sutiles en waveforms  
   - **T**: Primer informe de resultados para **2 jun 2025**

4. **(S) Filtrado de artefactos y calidad de datos**  
   - **M**: Lista `filtered/testlist.txt` con segmentos válidos >1000 muestras  
   - **A**: Crear función de Python que descarte secciones incompletas  
   - **R**: Mejora la robustez de los histogramas y MTBF  
   - **T**: Finalizar antes del **1 jun 2025**

5. **(S) Borrador de esquema de paper**  
   - **M**: Documento con secciones: Introducción, Metodología, Resultados, Discusión, Conclusión  
   - **A**: Basarse en este README + notas de reunión  
   - **R**: Sirve de hoja de ruta para redacción  
   - **T**: Presentar borrador en la reunión del **lunes 26 may 2025**

---

Con estos objetivos y pasos claros, avanzamos de forma estructurada hacia el análisis y la redacción final. ¡Manos a la obra!
