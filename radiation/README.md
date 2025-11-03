# Proyecto CHARM\_TEST

Versioning:
```
root 6.28/04
Python 3.11.2
```

Este repositorio organiza el flujo completo de pruebas de radiación en CHARM\_TEST: adquisición, preprocesamiento, análisis y resultados.

```bash
CHARM_TEST/
├── .vscode/                  # Config del editor VS Code
├── 0_raw/                    # Datos originales y archivos empaquetados
│   ├── data/                 # Datos crudos de corriente (hex) de TCMS y DMM
│   ├── dataC/                # Datos calibrados (corriente en notación científica)
│   ├── TCMS_RadTest/         # Estructura de datos de TCMS (data_run, data_run_trenz, logs)
│   ├── user_data_*/          # Carpeta con datos brutos de usuarios (slots y fechas)
│   ├── charm_data.zip        # Zip de datos brutos CHARM (equivalente a user_data_*)
│   ├── current_data.tar      # Tar con archivos DMM originales
│   ├── data_run.tar          # Tar con DMM_data, VERDAQ8_data y logs
│   ├── data_run_trenz.tar    # Similar a data_run.tar para sistema Trenz
│   └── user_data_*.zip       # Zips históricos de datos de usuario
├── 1_logs/                   # Registros de adquisición y errores
│   ├── daqlogs/              # Logs básicos DMM/VERDAQ ("all devices online")
│   ├── daqlogs_ok/           # Logs extendidos (reinicios, power cycle)
│   └── daqlogs_sep/          # Logs filtrados por septiembre
├── 1_src/                    # Scripts y macros de preprocesamiento y análisis
│   ├── *.py                  # Python: monitor_current.py, monitor_data(.C).py, plot_data.py, testplot.py, verdaq_ana.py
│   ├── *.cxx, *.C            # ROOT macros: process_time.cxx, get_reliability.cxx, makeCPLD_pics_bkup.cxx, cpld_TTF_2.C/3.C
│   └── tr.C, tr.h            # Clases ROOT para cpld_data.root
├── 2_processed/              # Datos transformados para análisis
│   ├── merged/               # CSV combinados (verdaq_data_…_all.csv, dmm_data_…)
│   └── filtered/             # Subconjuntos filtrados (p. ej. testlist.txt)
├── notebooks/                # Notebooks Jupyter organizados por prueba y propósito
│   ├── FirstRunAna/          # Análisis interactivo de FirstRun
│   ├── SecondRunAna/         # Análisis de SecondRun
│   ├── ThirdRunAna/          # Análisis de ThirdRun
│   ├── current_analysis.ipynb
│   ├── CPLD_data_ana.ipynb
│   ├── CPLD_data_ana_Run3.ipynb
│   ├── ploting_charm_data.ipynb
│   ├── ploting_charm_data-nov.ipynb
│   ├── ploting_charm_data-sep.ipynb
│   └── time_analysis.ipynb
├── analysis/                 # Artefactos generados de análisis
│   ├── beam_data_second_run.root
│   ├── beam_data_third_run.root
│   ├── cpld_data_second_run.root
│   ├── cpld_data_third_run.root
│   ├── signals_post.png
│   └── test.root
├── docs/                     # Documentos y presentaciones
│   ├── CHARM_-_technical_meeting_29-03-2022.pptx
│   └── Docs_Reviews_v3.1.docx
├── download/                 # Contiene la carpeta TCMS_RadTest descomprimida de download.tar
│   └── TCMS_RadTest/
└── results/                  # Figuras y tablas finales para el paper
    ├── figures/
    └── tables/
```

---

## Descripción de carpetas 

* **.vscode/**: Ajustes de VS Code (launch.json, settings.json).
* **0\_raw/**: Todos los datos originales sin tocar, incluidos zips/tars históricos.
* **1\_logs/**: Registros detallados de adquisición y errores en DMM/VERDAQ.
* **1\_src/**: Código fuente para extracción, transformaciones y generación de histogramas.
* **2\_processed/**: Datos ya fusionados y filtrados listos para exploración y análisis. (WIP)

* **notebooks/**: Notebooks en Jupyter separados por run y estudios específicos.
* **analysis/**: Archivos ROOT e imágenes generadas tras el análisis.
* **docs/**: Presentaciones y documentos de revisión.
* **download/**: Contenido descomprimido de descarga prevpython --version a (`download.tar`).
* **results/**: Material pulido (figuras, tablas) para inclusión en el paper.

## Posibilidades
- dmm_data_2022_05_25-29.dat: posible `dry run` aunque falta encontrarlo como tal la carpeta
- dmm_data_2022_09_14-20_all_trenz_noM : dmm_data_2022_09_14-20_all_trenz_noMezz (renombrado 0606), posible no Mezzanine
- Posiblemente fechas de Mayo sean correspondientes a `dry run`.