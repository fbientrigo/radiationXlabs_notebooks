# Roadmap unificado CHARM_TEST

## Visión global
- Mantener la estructura histórica del repositorio (`0_raw/`, `1_logs/`, `1_src/`, `2_processed/`, `analysis/`, `docs/`, `results/`) como base para la trazabilidad de datos y scripts.【F:new/README.md†L5-L49】
- Tratar los runs según la campaña documentada: Run 1 (Trenz + mezzanine), Run 2 (solo Trenz) y Run 3 (solo CPLD), prestando atención a los cambios de área efectiva al comparar tasas.【F:new/docs/reunion0606.md†L18-L41】
- Priorizar las entregas semanales descritas en el README histórico, incorporando las mejoras y anotaciones de `new/` sin perder coherencia con el mapa de conocimientos original.【F:README.md†L72-L194】【F:new/notebooks/README.md†L1-L79】

## Semana 1 – verDAQ y DRS4
1. **Inventario y limpieza**
   - Normalizar nombres de ejes en FFT/Wavelet según las pautas de la reunión del 5 de junio (reemplazar “grupo”→“evento”, etiquetar amplitudes).【F:new/docs/reunion0606.md†L9-L26】
   - Consolidar parsing de dumps adicionales (`verDAQ8_data_2022_05_24_235910_00011.dat`) dentro del notebook oficial `0530_verdaq_grouping.ipynb` para cubrir dry-runs previos.【F:new/notebooks/0530_verdaq_grouping.ipynb†L1-L40】
2. **Analítica**
   - Mantener los estudios de muestreo uniforme y scalogramas (`0526` y `0527`) como puerta de entrada a los análisis de verDAQ.【F:README.md†L96-L148】
3. **Testing sugerido**
   - Verificar consistencia temporal con datos de `0_raw/verDAQ8_data_*` y aplicar control de monotonicidad antes de escalamientos FFT.

## Semana 2 – Corriente DMM y sincronización con Beam
1. **Preprocesamiento DMM**
   - Unificar el parsing de corrientes Trenz/CPLD incorporando el dataset del 27 de mayo (`dmm_data6894024_2022_05_27_212453_all.dat`) como caso de dry-run, asegurando compatibilidad Windows/Linux.【F:new/notebooks/0602_current.ipynb†L1-L28】
   - Mantener el notebook `0602_dmm_current.ipynb` como referencia principal de histogramas y series IDC/IAC.【F:README.md†L196-L250】
2. **Beam ON/OFF y merges**
   - Automatizar el filtrado de segmentos beam OFF antes de correlacionar con DMM, tal como se acordó en la reunión del 5 de junio.【F:new/docs/reunion0606.md†L27-L40】
   - Completar el merge asof (`0603_dmm_plus_beam`) reutilizando las validaciones introducidas en `0718b_beam_data.ipynb` (detección de acumulados monotónicos).【F:new/notebooks/0718b_beam_data.ipynb†L1-L40】
3. **Testing sugerido**
   - Dataset recomendado: `0_raw/Campaign2/beam/*merged.csv` y `0_raw/dmm_data_2022_06_02-14_all.dat`. Validar con métricas IDC/IAC vs TID.

## Semana 3 – CPLD, bitflips y caracterización
1. **Ingesta CPLD**
   - Consolidar `cpld_pipeline` desde los notebooks `0717_lib_cpld*.ipynb`, parametrizando rutas por campaña y registrando resets y bit flips corregidos (kernel `[0,1,1]`).【F:new/notebooks/0717_lib_cpld.ipynb†L1-L60】【F:new/notebooks/0717_lib_cpld_camp2.ipynb†L1-L40】
   - Migrar la limpieza previa (`parse_message`, validación hex) documentada en `0627_clpd_datatypes.ipynb` a `lib/cpld_io.py` para dejar un único punto de entrada.【F:new/notebooks/0627_clpd_datatypes.ipynb†L1-L35】
2. **Bitflips y eventos**
   - Relacionar eventos CPLD con beam mediante el pipeline integral de `0804_PIPE_cpld_beam.ipynb`, que define tiempos equivalentes y compara Runs 2/3 considerando el área activa.【F:new/notebooks/0804_PIPE_cpld_beam.ipynb†L1-L60】
3. **Testing sugerido**
   - Usar fixtures existentes (`tests/test_cpld_decode.py`) y extender con datos reales de `0_raw/Campaign2/cpld/run/` y `0_raw/Campaign3/cpld/run/`.

## Semana 4 – Integración global y modelado de confiabilidad
1. **DataFrame maestro**
   - Integrar verDAQ, DMM, CPLD y Beam en un timeline común, reutilizando las funciones de merge y escalado (`compute_scaled_time_clipped`) descritas en la familia de notebooks `0826`.【F:new/notebooks/0826_bathub_poisson_lib.ipynb†L1-L120】
2. **Radbin & Poisson**
   - Formalizar la librería `radbin` como paquete interno (fluencia escalada, IC exactos, comparación de áreas) y replicar los flujos para Run 2 (32 subsistemas) y Run 3 (16 subsistemas).【F:new/notebooks/0826_bathub_poisson_lib.ipynb†L1-L160】【F:new/notebooks/0826_bathub_poisson_lib_run2.ipynb†L1-L120】
   - Incorporar las correcciones basadas en Melanie Berg (`0829_bathub_corrections.ipynb`) para analizar la evolución de la sección eficaz σ_SEF y definir bins por LET.【F:new/notebooks/0829_bathub_corrections.ipynb†L1-L120】
   - Conservar `0820_bathub_poisson.ipynb` como cuaderno de diagnóstico previo (distribución de factores de escalado, sanity checks).【F:new/notebooks/0820_bathub_poisson.ipynb†L1-L40】
3. **Testing sugerido**
   - Ejecutar los tests de aceptación provistos en `new/notebooks/tests/test_acceptance.py` y validar contra `radbin` usando datos sintéticos antes de aplicar a Campaign 2/3.【F:new/notebooks/tests/test_acceptance.py†L1-L44】

## Semana 5 – Documentación y entrega
1. **Reporte final**
   - Seguir el entregable descrito en el roadmap base (informe PDF + presentación) incluyendo los hallazgos sobre Poisson/Weibull y comparativa de campañas.【F:README.md†L250-L332】
2. **Notas y anexos**
   - Mantener el notebook legado `CPLD_data_ana_Run3.ipynb` en `archive/` como referencia histórica y documentar cualquier diferencia respecto a la nueva pipeline.【F:new/notebooks/CPLD_data_ana_Run3.ipynb†L1-L20】
3. **Checklist final**
   - Verificar que todos los merges respeten los periodos beam ON, que las métricas clave (TID, HEH, N1MeV) se reporten con unidades consistentes y que los scripts estén versionados en `1_src/` según la guía de fuentes.【F:new/docs/CHARM_1_src.md†L1-L120】

## Testing transversal recomendado
- **verDAQ & DMM**: Reprocesar los notebooks base con datasets históricos (`verDAQ8_data_2022_05_26_*`, `dmm_data_2022_06_02-14_all.dat`) y comparar contra resultados previos para garantizar reproducibilidad.
- **CPLD**: Ejecutar `pytest tests/test_cpld_decode.py` y extenderlo con escenarios extraídos de `cpld_pipeline` (Campaign 2/3).【F:tests/test_cpld_decode.py†L1-L80】
- **Radbin**: Correr los tests sintéticos (`new/notebooks/tests/test_acceptance.py`) antes de aplicar ajustes finales de LET y σ_SEF.【F:new/notebooks/tests/test_acceptance.py†L1-L44】

