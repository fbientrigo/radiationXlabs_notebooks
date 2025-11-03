# Notas consolidadas

## Beam y caracterización de campaña
- Inicio oficial del beam para la CPLD el **14 de septiembre a las 21 h**, con mensajes corruptos detectados el 15 de septiembre a las 16 h; la tarjeta utilizó ≈44 % de registros y 61 % de LUTs disponibles tras Run 2.【F:new/notes/0720_beam_chracter.md†L1-L17】
- Conversión empírica entre magnitudes de radiación para el entorno CHARM/ATLAS: \(10^9\,\text{HEH/cm}^2 \approx 10^{10}\,\text{neq/cm}^2 \approx 1\,\text{Gy}\); permite normalizar TID y N1MeV al diseñar índices de envejecimiento.【F:new/notes/0720_beam_chracter.md†L36-L56】
- Modelo propuesto para tasas de SEU: intensidad Poisson no homogénea \(\lambda(t) = \sigma_{SEU}(\varepsilon(t))\,\phi_H(t)\) modulada por la confiabilidad de Weibull acumulada; la historia de dosis se captura mediante \(\varepsilon = \tfrac{TID}{1\,\text{Gy}} + \tfrac{N1MeV}{10^{10}\,\text{neq/cm}^2}\).【F:new/notes/0720_beam_chracter.md†L56-L88】

## Pipelines CPLD y bitflips
- `parse_message` limpia dumps ASCII reemplazando `*` y separadores `#`, valida campos hexadecimales y arma matrices de bits (`masked0/1`) antes de generar estadísticas; sirve como preprocesamiento para `cpld_pipeline`.【F:new/notebooks/0627_clpd_datatypes.ipynb†L1-L40】
- `cpld_pipeline` aplica un kernel `[0,1,1]` para aislar bitflips que se recuperan tras reset, mide tiempos de reseteo y exporta CSV limpios por campaña (`Campaign3` en la versión base, `Campaign2` en la variante).【F:new/notebooks/0717_lib_cpld.ipynb†L1-L70】【F:new/notebooks/0717_lib_cpld_camp2.ipynb†L1-L35】
- El pipeline combinado (`0804_PIPE_cpld_beam.ipynb`) procesa datos secos y en beam de Campaigns 2/3, confirma ausencia de daño permanente tras Run 2, incorpora tiempo equivalente basado en flujo HEH y recuerda ajustar por área activa (32 vs 16 subsistemas).【F:new/notebooks/0804_PIPE_cpld_beam.ipynb†L1-L60】

## Beam y merges temporales
- `0718_lib_beam.ipynb` introduce la función `beam_pipeline` con control de monotonía y cálculo de tasa de dosis a partir de diferencias temporales, detectando casos sin archivos `merged_data.csv` para Campaign 3.【F:new/notebooks/0718_lib_beam.ipynb†L1-L35】【F:new/notebooks/0718_lib_beam.ipynb†L36-L44】
- `0718b_beam_data.ipynb` documenta rutas reales de Campaign 2 (`0_raw/Campaign2/beam/*merged.csv`), verificando la concatenación de runs y ofreciendo chequeos gráficos para acumulados.【F:new/notebooks/0718b_beam_data.ipynb†L1-L28】

## Modelado estadístico y radbin
- `0820_bathub_poisson.ipynb` cuantifica los factores de escalado de fluencia (mediana = 1, p90 ≈ 1.78, p99 ≈ 6.24) antes de aplicar `radbin`, sirviendo como sanity check sobre la estabilidad del flujo.【F:new/notebooks/0820_bathub_poisson.ipynb†L19-L24】
- La familia `0826_bathub_poisson_lib*.ipynb` describe la API `radbin`: cálculo de tiempos escalados, bins por fluencia/reset, intervalos de confianza exactos (Garwood) y normalización por área para comparar campañas; incluye pruebas de tendencia Poisson y síntesis de datos.【F:new/notebooks/0826_bathub_poisson_lib.ipynb†L1-L140】【F:new/notebooks/0826_bathub_poisson_lib_run2.ipynb†L1-L100】
- `0829_bathub_corrections.ipynb` adapta `radbin` con recomendaciones de Melanie Berg: análisis por LET, seguimiento de la sección eficaz σ_SEF y reducción de ventanas temporales para estudiar evolución del hazard. También cita la necesidad de contrastar con \(\chi^2/ndof\).【F:new/notebooks/0829_bathub_corrections.ipynb†L1-L110】【F:new/notebooks/8029_correcciones.md†L1-L12】
- Los tests sintéticos (`new/notebooks/tests/test_acceptance.py`) validan conteos, escalados y consistencia de bins (`build_and_summarize`, `poisson_trend_test`), proporcionando un arnés para regresiones antes de usar datos reales.【F:new/notebooks/tests/test_acceptance.py†L1-L38】

## Documentación y reuniones
- La reunión del 23 de mayo define objetivos SMART: centralizar datos de FirstRun, uniformar timestamps, aplicar wavelets y preparar un borrador de paper, reforzando la hoja de ruta de las primeras semanas.【F:new/docs/reunion0523.md†L1-L80】
- El acta del 5 de junio resume pendientes de instrumentación (renombrar ejes FFT, filtrar beam OFF, describir runs) y asigna responsables con fechas límite a mediados de junio.【F:new/docs/reunion0606.md†L9-L43】
- `CHARM_1_src.md` cataloga scripts/macros en `1_src/`, clarificando qué archivos generan histogramas TTF, monitorean corrientes y procesan dumps CPLD; referencia clave para documentar la pipeline final.【F:new/docs/CHARM_1_src.md†L1-L120】
- `CPLD_data_ana_Run3.ipynb` queda como guía original del profesor para interpretar datos de CPLD (Run 3), útil para contrastar resultados actuales antes de archivarlo formalmente.【F:new/notebooks/CPLD_data_ana_Run3.ipynb†L1-L12】

