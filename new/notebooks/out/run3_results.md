# Results of run 3
After going thought the file "0826_bathub_poisson_lib.ipynb"

Every bean its constructed by deciding an equivalent time that its calculated via an accumulated flux

For the run3:
Its tested against a Generalized Linear Model, where the model of baiss its a Poisson, as using as basis the number of fails $N$ in an interval of $T$ flux exposure (equivalent time)

$$
\log \mathbb{E}[N_i] = \beta_0 + \beta_1 t_i + \log(T_i)
$$

* $N_i$: number of fails at bin $i$
* $T_i$: exposure as fluence
* $t_i$: equivalent time (counting as hour since start of run)

