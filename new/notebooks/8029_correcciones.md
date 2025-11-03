# Post Show the Fits of Bathub Poisson

Si bien el test estadistico de los bins da un slop = 0 para run3, !=0 para run2,
el fit que se hizo es un GLM que va a calzar un slop=0@run3 debido a las flucutuaciones, pero no va a ser indincativo de tener error constante, podemos cheuqear el chi2.
$$
\frac{\chi^2}{\text{ndof}}
$$

Claramente va a dar un mal indicador (muy grande) para este modelo.

Se deben considerar otras formas de testear si es constante el error rate $\lambda$