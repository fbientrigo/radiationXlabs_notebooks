## Plan de fusión
| original | new | acción | razón | testing | prioridad |
|-----------|-----|--------|--------|----------|------------|
| 0526_verdaq_sampling_hyp.ipynb | new/notebooks/0526_verdaq_sampling_hyp.ipynb | archivar duplicado | Contenido idéntico; mantener una sola copia en `root/` para evitar doble mantenimiento. | no | baja |
| 0527_verdaq_scalegram.ipynb | new/notebooks/0527_verdaq_scalegram.ipynb | archivar duplicado | Notebook sin diferencias; consolidar en la versión histórica. | no | baja |
| 0530_verdaq_grouping.ipynb | new/notebooks/0530_verdaq_grouping.ipynb | fusionar | La versión nueva procesa dumps adicionales (`data_verdaq/2022_05_24`), útil para runs previos; parametrizar rutas en la versión oficial. | sí | alta |
| 0602_dmm_current.ipynb | new/notebooks/0602_dmm_current.ipynb | archivar duplicado | Coincide con la versión estable que usa el merge DMM+beam de junio. | no | baja |
| — | new/notebooks/0602_current.ipynb | fusionar | Aporta parsing de un dry-run (27 mayo) y compatibilidad con rutas Windows, complementando el notebook principal de corrientes. | no | media |
| 0603_beam_data_view.ipynb | new/notebooks/0603_beam_data_view.ipynb | archivar duplicado | Igual a la versión base de exploración de beam; solo mantener la copia raíz. | no | baja |
| 0603_dmm_plus_beam.ipynb | new/notebooks/0603_dmm_plus_beam.ipynb | archivar duplicado | Reproduce exactamente el merge asof existente; se puede referenciar la versión raíz. | no | baja |
| 0610_cross_data.ipynb | new/notebooks/0610_cross_data.ipynb | archivar duplicado | Sin cambios frente al original; unificar documentación en un único notebook. | no | baja |
| — | new/notebooks/0627_clpd_datatypes.ipynb | fusionar | Documenta limpieza avanzada (ROOT + kernel hex) previa a `cpld_pipeline`; migrar funciones útiles a `lib/cpld_io.py`. | sí | alta |
| — | new/notebooks/0717_lib_cpld.ipynb | fusionar | Define `cpld_pipeline` con validaciones y exporta CSV de Campaign 3; debe integrarse como referencia oficial para bitflips. | sí | alta |
| — | new/notebooks/0717_lib_cpld_camp2.ipynb | fusionar | Variante ajustada a Campaign 2 que revela diferencias de resets/area; conviene parametrizar campaña en la librería. | sí | alta |
| — | new/notebooks/0718_lib_beam.ipynb | fusionar | Implementa `beam_pipeline` y control de monotonicidad; base para la ingesta oficial de beam. | sí | alta |
| — | new/notebooks/0718b_beam_data.ipynb | fusionar | Notebook operacional para Campaign 2 (`*merged.csv`) con verificaciones; trasladar ejemplos y validaciones a la guía principal. | sí | alta |
| — | new/notebooks/0804_PIPE_cpld_beam.ipynb | fusionar | Ensambla pipelines CPLD+beam (runs 2 y 3), introduce tiempo equivalente y comparaciones de área; imprescindible para etapa de integración. | sí | alta |
| — | new/notebooks/0820_bathub_poisson.ipynb | fusionar | Resume chequeos de estabilidad (medianas/p90 de escalados) previos a radbin; útil como cuaderno de diagnóstico. | sí | media |
| — | new/notebooks/0826_bathub_poisson_lib.ipynb | fusionar | Documenta la librería `radbin` (fluencia escalada, Garwood CI) y debe convertirse en notebook oficial de metodología. | sí | crítica |
| — | new/notebooks/0826_bathub_poisson_lib_run2.ipynb | fusionar | Replica el flujo `radbin` sobre Run 2 (área 32 subsistemas) para comparar campañas; integrar como ejemplo avanzado. | sí | crítica |
| — | new/notebooks/0829_bathub_corrections.ipynb | fusionar | Ajusta `radbin` con criterios de Melanie Berg (LET, σ_SEF) y define nuevas métricas; imprescindible para interpretación final. | sí | crítica |
| — | new/notebooks/CPLD_data_ana_Run3.ipynb | archivar (referencia) | Notebook legado entregado por el profesor; conservar en `archive/` como contexto histórico sin mezclar con la pipeline actual. | no | baja |

## Orden sugerido
1. 0526_verdaq_sampling_hyp.ipynb
2. 0527_verdaq_scalegram.ipynb
3. 0530_verdaq_grouping.ipynb
4. 0602_dmm_current.ipynb
5. 0602_current.ipynb
6. 0603_beam_data_view.ipynb
7. 0603_dmm_plus_beam.ipynb
8. 0610_cross_data.ipynb
9. 0627_clpd_datatypes.ipynb
10. 0717_lib_cpld.ipynb
11. 0717_lib_cpld_camp2.ipynb
12. 0718_lib_beam.ipynb
13. 0718b_beam_data.ipynb
14. 0620_cpld_bitflips.ipynb
15. 0804_PIPE_cpld_beam.ipynb
16. 0820_bathub_poisson.ipynb
17. 0826_bathub_poisson_lib.ipynb
18. 0826_bathub_poisson_lib_run2.ipynb
19. 0829_bathub_corrections.ipynb

