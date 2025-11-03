Datos de 2209XX_TGCCMS_radiationResume.pdf
Se utiliza RadMon
Los eventos importantes en cuanto a la CPLD
- 14/9 21hrs se registra el inicio del beam
- 15/9 16hrs CPLD envia mensajes corruptos

Numero de registros
4665 de 10552 44%
Numero de slices 
3271 de 4700 70%
NUmero de LUTs
5698 de 9400 61%

Radiacion estimada
TID [Gy] 84.5/330 

___

Se revisaron referencias oficiales como:
- https://r2e.web.cern.ch/about-radiation/test-facilities/charm
en donde se descrbie las catacteristicas de la radiacion proveniente
5 x 10^11 protones, con 350ms con momentum de 24Gev/c

Dependiendo del target material (Cu, Al, AlH, NT) y el shielding (OOOO, CIOO, CIIC) tenemos el espectro.

# 0721 RadMon y Datos del Beam
Se describe el uso de RadMon para conocer la conocer la composicion de la radiacion
https://ieeexplore.ieee.org/document/6949156 (Revisar RadMon.pdf en notas)

- HEH con hadrones por encima de 20MeV, cuyo flujo ayuda a determinar los Single Event Effects mediante deposicion de carga
    Evento puntual causado por energía depositada por partículas individuales que generan pares e⁻/h⁺.

    Produce “bit-flip” transitorio en nodos sensibles; es un error suave, no permanente, y se recupera al reiniciar

    - https://www.mdpi.com/2674-0729/4/1/12
    - Compendio de la NASA de SEU para iones: https://ntrs.nasa.gov/api/citations/20140017803/downloads/20140017803.pdf

- TID (Total Ionizing Dose)
    Provoca acumulación de carga en óxidos y cambios en parámetros eléctricos (voltage threshold, fugas).

    Efecto gradual, acumulativo, degradando la confiabilidad con el tiempo. De acuerdo a https://secwww.jhuapl.edu/techdigest/Content/techdigest/pdf/V28-N01/28-01-Maurer.pdf

- N1Mev (Neutrones Termales) Hadrones no cargados representados como un flujo equivalente
    Daño por desplazamiento (Displacement Damage, DD)

    Partículas rompen la red cristalina del silicio, generando defectos (vacantes e intersticiales).

    Reduce la movilidad de portadores, su desempeño analógico y la estabilidad, sin producir SEUs directos.



# 0722 Relacion entre Variables
De acuerdo a RadMon.pdf se describe como mediante el uso de FLUKA al ser las variables altamente colineales, dado el entorno especifico es posible tener factores de conversion.
Este factor de conversión se encuentra
    En el contexto de LHC y Silicon
    Del artículo Single Event Effects in High-energy Accelerators de Garcia R. Et al.
$$
    10^9 [\frac{HEH}{cm^2}] ~ 10^10 [\frac{1MeV neq}{cm^2}] ~ 1 [Gy]
$$

de manera que es posible adimensionalizar las variables en el caso de creacion de un indice teniendo en cuenta el daño provocado.
Tal como se conversa en SEU.pdf y RadMon.pdf los efectos de envejecimiento provienen principalmente del daño por ionizacion y desplazamiento (TID y N1MeV).


# 0723 Testing
Se procede a utilizar un modelo mixto para estudiar 
Puede asumirse que el daño ionizante (TID) ya contiene la información del daño en HEH

el indice empirico propuesto
$$
\varepsilon = \frac{TID}{1 [Gy]} + \frac{N1MeV}{10^10 [neq/cm^2]}
$$

mientras que el SEU ocurriria debido a la fluencia $HEH$ instantanea $\phi_H(t)$
pero la probabilidad se verá modulada por el historia de dosis,
esto tal que el modelo propuesto es el siguiente:

La probabilidad de un SEU como proceso Poisson no homogeneo
$$
P(\text{SEU en } [t, t + \Delta t]) \approx \lambda(t) \Delta t
$$

donde 
$$
\lambda(t) = \sigma_{SEU}(\varepsilon(t)) \phi_H(t)
$$

con la seccion eficaz dependiendo de la historia acumulada, siendo multiplicada por la funcion de reliability R(t) de Weibull

$$
\sigma_{SEU}(\varepsilon(t)) = \sigma_0 R(t) =  \sigma_0  \left( 1 - \exp(-(\frac{\varepsilon(t)}{\eta})^\beta )\right)
$$

