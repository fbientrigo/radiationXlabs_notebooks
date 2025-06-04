# Índice General del Análisis de Radiación
Radiation analysis project related to the intake radiation from CHARM, how it affects measurements at different ways.


## 0. Cronograma y Entregables

### 0.1. Semana 1: verDAQ

* **Tareas**:

  1. Configuracion del proyecto, orden de ficheros y exploracion de los datos
  2. Preprocesamiento de verDAQ (CWT, FFT)

* **Entregable**:

  * Notebooks:
  - 0526_verdaq_sampling_hyp.ipynb
    - Pruebas a la hipotesis de datos sampleados uniformemente
  - 0527_verdaq_scalegram.ipynb
    - primeras aplicaciones de CWT, bajo el supuesto de datos uniformes
  - 0530_verdaq_grouping.ipynb
    - Se elimina el concepto de datos uniformes y se acepta la hipotesis de agrupamientos, se usa FFT


### 0.2. Semana 2: Beam y fusión con Trenz

* **Tareas**:
  1. Preprocesamiento de DMM\_Trenz (histogramas, series temporales, detección inicial de picos)
  2. Concatenación de runs de beam (df\_beam)
  3. Merge asof `df_trenz` + `df_beam` → `df_all_trenz`
  4. Graficar IDC vs TID, IAC vs HEH, primeras interpretaciones

* **Entregable**:

  * Notebook «Parte\_2\_Trenz\_Beam.ipynb» con código de merge y gráficos

### 0.3. Semana 3: DMM\_CPLD y bitﬂips

* **Tareas**:

  1. Limpieza de DMM\_CPLD, merge con beam → `df_all_cpld`
  2. Preprocesamiento de bitflips, merge con `df_all_cpld` y `df_beam`
  3. Estadísticas básicas de bitflips vs dosis (Poisson?)
* **Entregable**:

  * Notebook «Parte\_3\_CPLD\_Bitflips.ipynb» con análisis de bitflips

### 0.4. Semana 4: Integración completa y modelado predictivo

* **Tareas**:

  1. Merge global: verDAQ + Trenz + CPLD + Beam + Bitflips
  2. Generación de visualizaciones integradas
  3. Modelado regresivo y/o clasificación de latch-up
  4. Dashboard interactivo con widgets
* **Entregable**:

  * Notebook «Parte\_4\_Integración\_Modelado.ipynb»
  * Dashboard en Jupyter (o Voila/Streamlit si aplica)

### 0.5. Semana 5: Documentación final y presentación

* **Tareas**:

  1. Redacción del informe resumen
  2. Preparación de diapositivas para presentación (PowerPoint o similar)
  3. Revisión de código, limpieza de notebooks y anexos

* **Entregable**:

  * Informe final «Análisis\_Radiación\_FINAL.pdf»
  * Presentación «Análisis\_Radiación\_PPT.pptx»


 

## 1. Análisis de Voltaje con verDAQ
### 1.1. Descripción de los datos verDAQ
- Formato del fichero de salida verDAQ
- Interpretación de canales y unidades
- Estructura temporal de los datos (timestamps y agrupación en batches)

### 1.2. Preprocesamiento de la señal de voltaje
- Conversión de timestamps a formato `datetime`
- Detección y corrección de valores repetidos o faltantes
- Normalización y filtrado inicial (filtro de mediana o promedio)

### 1.3. Transformada Wavelet Continua (CWT)
- Concepto de **scales** y relación con la frecuencia (Nyquist)
- Selección de la wavelet (‘morl’) y parámetros
- Cálculo de `pywt.cwt( … )` paso a paso
  - Generación de datos simulados de ejemplo
  - Definición de rangos de escala (`scales = np.arange(1, 128)`)
  - Interpretación de la salida: `coeffs` vs. `freqs`
- Visualización del **scalogram** (mapa de coeficientes vs. tiempo)
- Interpretación de características significativas en el dominio tiempo-escala

### 1.4. Transformada Rápida de Fourier (FFT)
- Fundamentos de la FFT y relación con densidad espectral de potencia
- Aplicación de `np.fft.fft` sobre ventanas de la señal
- Diseño de ventanas deslizantes para análisis espectral (tamaño, solapamiento)
- Visualización de módulos y fases
  - Gráficos de espectro global
  - Espectrograma (espectro vs. tiempo)
- Interpretación de picos espectrales y su relación con eventos de radiación

### 1.5. Resultados y Conclusiones Parciales de verDAQ
- Eventos de caída o variación brusca de voltaje detectados con CWT
- Frecuencias dominantes extraídas por FFT: posibles señales de interferencia
- Resumen de patrones de interés que se detectan antes/durante/tras el paso del beam

 

## 2. Análisis de Corriente con DMM
### 2.1. Descripción de los datos DMM
- Tipos de dispositivos:  
  - **FPGA Trenz** (placa principal)  
  - **CPLD** (plataforma secundaria)  
- Formato de los ficheros `dmm_data_YYYY_MM_DD_all_trenz.dat` y `dmm_data_…_cpld.dat`
- Campos principales:  
  1. `timestamp` (float UNIX)  
  2. `IDC_str` (corriente DC en notación científica)  
  3. `IAC_str` (corriente AC RMS en notación científica)

### 2.2. Preprocesamiento y Conversión de Unidades
- Conversión de `timestamp` → `datetime64[s]` (+ ajuste de huso horario)
- Limpieza de cadenas IDC/IAC (eliminar “+”, convertir a `float64`)
- Detección de valores faltantes, duplicados o espurios
- Revisión de intervalos de muestreo (esperados ~4 s)

### 2.3. Histogramas de Corriente (IDC)
- Generación de histograma global de `IDC` (rango 0.0–1.6 A, 50 bins)
- Identificación de “modos” de consumo:  
  - **Modo apagado** (~0 A)  
  - **Modo idle/espera** (~0.08 A–0.12 A)  
  - **Modo activo/pico** (~1.2 A–1.4 A)
- Análisis de la distribución diaria/por tramo de dosis  
  - Histogramas por día o por intervalos de TID  
  - Comparación de medias y varianzas en cada intervalo

### 2.4. Serie Temporal de IDC e IAC
- Gráficos de `IDC` vs. `Time`  
  - Línea continua + marcadores puntuales  
  - Detección visual de caídas abruptas a 0 A  
- Gráficos de `IAC` vs. `Time`  
  - Valores RMS de ruido (µA)  
  - Identificación de incrementos de ruido durante exposición
- Superposición de `IDC` e `IAC` en un mismo eje temporal  
  - Doble eje Y (azul para IDC, naranja para IAC)  
  - Organización en un solo gráfico

### 2.5. Detección de Eventos (Latch-Ups y Picos)
- Definición de umbrales para identificación de eventos:  
  - **Umbral apagado**: `IDC < 0.01 A`  
  - **Umbral idle mínimo**: `0.06 A < IDC < 0.12 A`  
- Algoritmo automático para extraer “eventos de latch-up”:  
  1. Buscar transiciones repentina de idle → apagado → recuperación  
  2. Anotar timestamp, duración de apagado, dosis correspondiente  
  3. Contar eventos por Gy de radiación
- Tabla final de eventos con columnas:  

```
───────────────────────────────────
Time\_event │ IDC\_event │ TID\_event │ HEH\_event │ N1MeV\_event │ Duración
───────────────────────────────────
2022-09-15 12:34:52 │ 0.00 A │ 0.35 Gy │  150 k  │  45 k  │ 8 s
…

```


## 3. Análisis de Bitflips en CPLD
*(Esta sección se activará una vez dispongamos de los logs de bitflips)*
### 3.1. Descripción de Logs de Bitflips
- Formato del fichero de bitflips (ej. `bitflips_log.txt`)
- Campos típicos:  
- `timestamp`  
- `dirección de bit` (byte, bit)  
- `valor anterior` → `nuevo valor`
- Contexto: frecuencia de lectura de registros de memoria, método de muestreo

### 3.2. Preprocesamiento de Registros de Bitflips
- Conversión de `timestamp` a `datetime64`  
- Parsing de líneas de texto a DataFrame con columnas:  

```
Time │ ByteAddr │ BitIdx │ OrigVal │ NewVal
````

- Eliminación de duplicados (caso de relecturas idénticas)
- Unificación de zonas horarias con `df_beam` y `df_corriente`

### 3.3. Estadística de Bitflips vs Dosis y Corriente
- Merge asof de bitflips con `df_beam` → asociar cada flip a su TID, HEH, N1MeV  
- Merge asof de bitflips con `df_trenz` (y `df_cpld`) → ver estado de IDC/IAC en el instante del flip  
- Tablas y gráficas:  
- **Número acumulado de bitflips vs TID**  
- **Tasa de bitflips por Gy**  
- **Bitflips vs corrientes pico** (¿ocurren más flips cuando la corriente se vuelve inestable?)  
- Detección de regiones críticas (por dosis o corriente) donde la probabilidad de flip aumenta bruscamente


## 4. Análisis de Datos de Beam en CHARM
### 4.1. Descripción de los Archivos de Beam
- Tipos de contadores:  
1. **TID_RAW1** (dosis acumulada en Gy)  
2. **HEH** (High Energy Hadrons contados)  
3. **N1MeV_RAW0** (neutrones > 1 MeV contados)  
- Frecuencia de muestreo (timestamps en ms o ns)

### 4.2. Preprocesamiento y Concatenación de Runs
- Lectura de CSVs por run:  
```python
df0 = pd.read_csv("RUN_8_USER_/data_CHARMB_7.csv")
df1 = pd.read_csv("RUN_9_USER_/data_CHARMB_7.csv")
df2 = pd.read_csv("RUN_10_USER_/data_CHARMB_7.csv")
df3 = pd.read_csv("RUN_10_USER_/data_CHARMB_7_2.csv")
````

* Cambio de nombres (e.g. `TID_RAW1` → `TID`, `N1MeV_RAW0` → `N1MeV`)
* Conversión de `Time` a `datetime64[ns]`
* Acumulación progresiva:

  * Sumar al run *i* el último valor acumulado del run *i−1*
  * Conseguir una curva de contadores que solo crece monotónicamente

### 4.3. Cálculo de Tasas de Dosis y Equivalencias LHC

* Definición de periodo de interés (`t_start`, `t_end`)
* Cálculo de:

  ```python
  dt = t_end - t_start
  TID_avg_CHARM = TID_final / dt.total_seconds()    # en Gy/s
  TID_avg_LHC    = 123. / (10*365*24*60*60)         # ~3.9e-7 Gy/s (referencia P2)
  ```
* Cálculo de factor de escala:

  * `factor = TID_avg_CHARM / TID_avg_LHC`
  * Interpretación: “1 s en CHARM equivale a X s/días en P2”


## 5. Fusión de Datos: Voltaje, Corriente y Beam

*(El objetivo es generar un DataFrame integrado que contenga, en cada fila, todas las variables relevantes para cada instante de muestreo de corriente o voltaje.)*

### 5.1. Merge asof entre verDAQ y Beam

1. Partir de `df_verdaq` (preprocesado con CWT/FFT) indexado por `Time`
2. Partir de `df_beam` indexado por `Time`
3. Aplicar:

   ```python
   df_verdaq = df_verdaq.reset_index().sort_values("Time")
   df_beam   = df_beam.reset_index().sort_values("Time")
   df_vb = pd.merge_asof(
       df_verdaq,
       df_beam[["Time", "TID", "HEH", "N1MeV"]],
       on="Time",
       direction="backward"
   ).set_index("Time")
   ```
4. Resultado: columnas `[Voltaje, CWT_coeffs, FFT_spectrum, TID, HEH, N1MeV]`

### 5.2. Merge asof entre DMM\_Trenz y Beam

1. `df_trenz` (indexado por `Time`)
2. `df_beam` (indexado por `Time`)
3. Aplicar:

   ```python
   df_tr = df_trenz.reset_index().sort_values("Time")
   df_beam = df_beam.reset_index().sort_values("Time")
   df_tb = pd.merge_asof(
       df_tr,
       df_beam[["Time", "TID", "HEH", "N1MeV"]],
       on="Time",
       direction="backward"
   ).set_index("Time")
   ```

### 5.3. Merge asof entre DMM\_CPLD y Beam

* Proceso análogo al de Trenz, obteniendo `df_cb` con columnas `[IDC_CPLD, IAC_CPLD, TID, HEH, N1MeV]`

### 5.4. Estructura Final del DataFrame Integrado

* Posibles estrategias:

  1. **Unificar todo en una sola tabla**:

     ```text
     Time │ Voltaje_DAQ │ CWT_… │ FFT_… │ IDC_Trenz │ IAC_Trenz │ IDC_CPLD │ IAC_CPLD │ TID │ HEH │ N1MeV
     ```

     * Rondas de resampling (por ej. a 1 s) para sincronizar todos los muestreos
  2. **Mantener tres tablas distintas** (verDAQ, Trenz, CPLD), cada una mergeada con beam, y unirlas posteriormente por `Time` con un merge tipo `outer`.
* Verificación de consistencia:

  * Que no haya valores `NaN` inesperados en las columnas de `TID/HEH/N1MeV`
  * Que los muestreos de corriente y voltaje no queden demasiado “espaciados” tras el resampleo

 

## 6. Análisis Combinado y Visualización

### 6.1. IDC vs TID: Correlación Directa

* **Gráfico scatter**: `df_all["TID"]` vs `df_all["IDC_Trenz"]`

  * Observación de clusters y colas
  * Marcar los puntos correspondientes a eventos de latch-up (IDC\_Trenz < 0.01 A) en rojo
* **Histograma de eventos de latch-up vs TID**

  * Distribución (binned) de dosis al momento de caída a 0 A

### 6.2. IAC vs HEH y N1MeV: Correlación de Ruido

* **Scatter**: `IAC_Trenz (µA)` vs `HEH`
* **Scatter**: `IAC_Trenz (µA)` vs `N1MeV`
* Cálculo de coeficientes de correlación (Pearson/Spearman)

### 6.3. Voltaje DAQ vs Corriente: Análisis de Potencia

* Cálculo de `P(t) = V_DAQ(t) × IDC_Trenz(t)`
* **Serie temporal** de potencia vs tiempo, superpuesta con dosis
* **Mapa de calor**: ejes `TID` vs `IDC` coloreado por `V_DAQ` o `P`
* Detección de caídas de voltaje correlacionadas con picos de corriente (lags y latencias)

### 6.4. Mapas de Calor / Scatter 3D Multidimensional

* **Scatter 3D**: `[TID, HEH, IDC_Trenz]`
* **Heatmap 2D**:

  * Eje X = `TID_bin` (agrupado)
  * Eje Y = `IDC_bin` (agrupado)
  * Valor de calor = densidad de puntos o frecuencia de eventos
* Interpretación de “regiones críticas” donde la placa está en alto riesgo de latch-up

### 6.5. Dashboards Interactivos (Notebook Widgets)

* Uso de `ipywidgets` para crear controles deslizantes de rango de tiempo y dosis
* Gráficas dinámicas:

  * Checkbox para activar/desactivar visualización de `CWT` o `FFT`
  * Slider para elegir ventana de análisis de corriente (por ejemplo, “Solo mostrar días X a Y”)
* Exportación automática de figuras o resúmenes estadísticos a PDF/HTML

 

## 7. Modelado Estadístico y Predictivo

### 7.1. Regresión Multivariable: IDC \~ Dosis + HEH + N1MeV

* Definición de variables predictoras:

  * `X = [TID, HEH_rate (ΔHEH/Δt), N1MeV_rate (ΔN1MeV/Δt), Voltaje_DAQ]`
  * `y = IDC_Trenz`
* División de datos en sets de entrenamiento y prueba (Time-split o k-fold temporal)
* Ajuste de modelos lineales y regularizados (Ridge, Lasso)
* Evaluación de métricas (R², RMSE) y análisis de residuales

### 7.2. Detección de Cambios (Changepoint) en IDC

* Concepto de *“changepoint detection”* (rupturas en media o varianza)
* Uso de la librería `ruptures` en Python:

  * Aplicar método PELT o Binary Segmentation sobre `IDC_Trenz`
  * Identificar segmentos de “comportamiento estable” vs “transitorio”
* Comparar los cambios detectados con eventos de beam (picos de dosis) y logs de bitflips

### 7.3. Clasificador de “Lllegada de Latch-Up”

* Formar un dataset where each row es:

  ```
  [IDC(t−n), IAC(t−n), ΔIDC, ΔIAC, TID_rate, HEH_rate, N1MeV_rate] → Etiqueta: {0 = “no latch-up próximo”, 1 = “latch-up en próximos k s”}
  ```
* Entrenar un modelo de clasificación (Random Forest, XGBoost)
* Evaluación con curva ROC, precisión, recall
* Interpretación con SHAP (Importancia de variables predictoras)

 

## 8. Plan de Acción: Siguientes Pasos y Conexiones

*(Cómo se interconectan cada bloque de análisis, y qué entregables esperamos)*

### 8.1. Consolidar verDAQ (Voltaje)

1. **Entrega Parcial**: Notebook con

   * Limpieza de datos verDAQ
   * CWT paso a paso con gráficos de scalogram
   * FFT con espectrogramas
   * Informe breve de hallazgos (principales frecuencias, anomalías detectadas)

### 8.2. Consolidar DMM\_Trenz (Corriente FPGA Trenz)

1. **Entrega Parcial**: Notebook con

   * Limpieza de datos DMM\_Trenz
   * Histogramas de IDC por intervalos de dosis
   * Serie temporal de IDC e IAC
   * Identificación inicial de eventos de latch-up
   * Tabla preliminar de eventos con timestamps y dosis

### 8.3. Integrar Beam ↔ Trenz

1. **Merge asof** → `df_all_trenz`
2. **Gráficos de correlación**:

   * `IDC_Trenz` vs `TID`
   * `IAC_Trenz` vs `HEH`/`N1MeV`
3. **Entrega Parcial**: Notebook

   * Código de merge\_asof
   * Scatter y series temporal con eje dosis
   * Interpretación de correlaciones (¿a qué dosis se producen los primeros latch-up?)

### 8.4. Incorporar DMM\_CPLD (Corriente CPLD)

1. **Limpieza de datos DMM\_CPLD**
2. **Merge asof** con `df_beam` → `df_all_cpld`
3. **Comparativa**:

   * `IDC_Trenz` vs `IDC_CPLD` para mismos instantes
   * Identificar si CPLD y Trenz se comportan distinto ante la misma dosis
4. **Entrega Parcial**: Notebook

   * Hitos de fusión y comparativa gráfica
   * Conclusiones preliminares sobre robustez relativa

### 8.5. Incorporar Bitﬂips en CPLD

1. **Limpieza de logs de bitflips** → `df_bitflips`
2. **Merge asof** con `df_beam` y con `df_all_cpld`
3. **Análisis**:

   * Dosis al primer bitflip
   * Tasa de bitflips por Gy
   * Relación entre picos de `IAC_CPLD` y frecuencia de bitflips
4. **Entrega Parcial**: Notebook

   * Tablas estadísticas y gráficas de bitflips
   * Sección de interpretación de impacto en la placa

### 8.6. Finalmente: Unir verDAQ + Corriente + Beam + Bitﬂips

1. **Merge final**:

   * Unir `df_vb` (verDAQ+Beam) con `df_all_trenz` (Trenz+Beam) y `df_all_cpld` (CPLD+Beam)
   * Alinear todo a un índice temporal común (resampleo a 1 s o 4 s)
   * Incluir `df_bitflips` como “marca” puntual en ese timeline
2. **Visualizaciones globales**:

   * Panel con 4 subplots:

     1. **Voltaje verDAQ** (línea)
     2. **IDC\_Trenz** (línea con marcadores de latch-up)
     3. **IDC\_CPLD** (línea con marcadores de bitflips)
     4. **TID acumulada** (línea)
   * Heatmap de potencia (V×I) vs dosis y tiempo
   * Dashboard interactivo final
3. **Entrega Final**:

   * Notebook maestro con todas las etapas encadenadas
   * Informe escrito (PDF/Markdown) que resuma metodología, resultados clave y recomendaciones

 


## 10. Apéndices

### 10.1. Descripción de comandos del DMM (DMM.py)

* Resumen de cada comando SCPI enviado:

  * `ADC` → activa medición DC
  * `AAC2` → activa medición AC RMS (canal 2)
  * `range 3` → rango de corriente (ej. 10 A)
  * `rate s` → velocidad “slow” (\~4 lecturas/s)
  * `format 2` → formato de salida en notación científica
* Lógica de rollover de ficheros (MAXFSIZE y fidx)

### 10.2. Descripción de mp730424.c (Interfaz OSD)

* Cómo se abre `/dev/ttyS0` a 115200:8n1
* Lectura y parseo de respuestas SCPI del multímetro
* Estructura de bucle principal y refresco de pantalla (OSD)

### 10.3. Ejemplos de Snippets de Código

* Preprocesamiento de timestamps y conversión a `datetime64[ns]`
* Funciones de merge\_asof para fusiones temporales
* Scripts para detección automática de cambios (`ruptures`, CUSUM)

### 10.4. Glosario de Términos

* **CWT**: Transformada Wavelet Continua
* **FFT**: Transformada Rápida de Fourier
* **IDC**: Corriente continua (DC) medida por DMM
* **IAC**: Corriente alterna RMS medida por DMM
* **TID**: Dosis Ionizante Total acumulada (en Gy)
* **HEH**: Contador de Hadrones de alta energía
* **N1MeV**: Contador de neutrones de energía > 1 MeV
* **Latch-Up**: Estado de falla en circuitos CMOS causado por radiación
* **Bitﬂip**: Cambio accidental de un bit en memoria o registro inducido por radiación

 

> **Nota final:**
> Este índice está pensado como un “mapa de ruta” para guiar cada etapa de nuestro análisis. Cada sección (1, 2, 3, …) corresponderá a un notebook o entrega parcial que iremos revisando y validando antes de avanzar a la siguiente capa. De ese modo, nos aseguramos de no perdernos entre tantos ficheros y pasos, y construimos un flujo de trabajo incremental y coherente.