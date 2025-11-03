
**Acta de Reunión**
**Fecha:** 5 de junio de 2025
**Objetivo:** Revisión de avances en el sistema de adquisición de datos (DRS4, VerDAQ y DMM) y planificación de los siguientes pasos.

---

### 1. Muestreo en DRS4 / VerDAQ

**1.1 Modo de operación**

* El módulo DRS4 se configuró en **modo cascada de alta velocidad**, lo que produce un intervalo de muestreo temporal

  $$
    \delta t \approx 0{,}5\text{–}1\,\mathrm{ns}.
  $$
* Para facilitar la comunicación, definimos los picos de frecuencia en términos de **primer, segundo, … enésimo armónico**, dado que variar $\delta t$ solo escala el eje temporal sin alterar la forma del espectro.

**1.2 Correcciones a los gráficos**

* **Eje horizontal:** renombrar de `grupo` a **`evento`**.
* **Gráfico de FFT:** eje vertical → “Coeficiente de amplitud”; eje horizontal → “Número de evento”.

---

### 2. Estado del Beam

**2.1 Verificación ON/OFF**

* Monitorizar el estado del beam: cuando está **apagado**, las variables de tipo acumulación (p. ej. TID) permanecen en un valle sin variaciones.
* **Sólo** procesar análisis de tiempos de vida, dosis y otros parámetros durante los periodos en que el beam esté **encendido**.

**2.2 Sincronización con DMM y VerDAQ**

* Realizar **cruces de datos** entre VerDAQ y DMM para detectar inconsistencias.
* Documentar cualquier fallo indicando el rango de tiempo, el estado del beam y la relación entre señales de ambos sistemas.

---

### 3. Descripción de los “Runs”

| Run       | Hardware involucrado          | Observaciones                                                               |
| --------- | ----------------------------- | --------------------------------------------------------------------------- |
| **Run 1** | Mezzanine + Trenz (Zynq 7000) | Ambos módulos operativos y sincronizados.                                   |
| **Run 2** | Solo Trenz                    | La mezzanine dejó de responder; procedemos únicamente con la tarjeta Trenz. |
| **Run 3** | Sólo CPLD                     | Se aísla la etapa de CPLD para caracterización independiente.               |

---

### 4. Próximos Pasos y Responsables

| Tarea                                                  | Fecha límite  |
| ------------------------------------------------------ | ------------- |
| Ajustar y validar eje de eventos en los gráficos FFT   | 10 junio 2025 |
| Implementar lógica de filtrado beam OFF en el análisis | 12 junio 2025 |
| Desarrollar script de cruce DMM–VerDAQ                 | 15 junio 2025 |
| Preparar informe de caracterización del CPLD           | 17 junio 2025 |

