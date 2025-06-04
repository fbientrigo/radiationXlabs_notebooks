import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FuncFormatter

def hz_formatter(x, pos):
    """Formatea x en Hz/kHz/MHz para el eje X"""
    if x >= 1e6:
        return f"{x*1e-6:.1f} MHz"
    elif x >= 1e3:
        return f"{x*1e-3:.1f} kHz"
    else:
        return f"{x:.0f} Hz"

def plot_fft_heatmap(
    fft_dict, dt, 
    x_min=None, x_max=None, 
    vmin=None, vmax=None, 
    title="Spectro FFT por grupo (heatmap, eje X log)",
    figsize=(10, 6), show=True,
    vline_freq=None,     # Frecuencia para línea vertical roja (Hz)
    vline_kwargs=None    # Diccionario de kwargs para personalizar la línea
):
    """
    Grafica un heatmap logarítmico de los espectros FFT por grupo.

    Parámetros
    ----------
    fft_dict : dict
        Diccionario {group_id: coeficientes FFT (array complejo)}.
    dt : float
        Intervalo de muestreo en segundos.
    x_min, x_max : float, opcional
        Límites de frecuencia en Hz para recortar el eje X.
    vmin, vmax : float, opcional
        Límites mínimo y máximo de la escala de color (magnitud).
    title : str
        Título de la figura.
    figsize : tuple, opcional
        Tamaño de la figura (ancho, alto).
    show : bool, opcional
        Si True, llama a plt.show().
    vline_freq : float, opcional
        Frecuencia en Hz donde trazar una línea vertical roja.
    vline_kwargs : dict, opcional
        Parámetros adicionales para ax.axvline (color, linestyle, alpha, etc.).

    Retorna
    -------
    fig, ax : matplotlib.figure.Figure, matplotlib.axes.Axes
        Objeto figura y ejes del plot.
    """
    # 1) Determinar N y frecuencias
    N = max(len(coeffs) for coeffs in fft_dict.values())
    freqs = np.fft.fftfreq(N, d=dt)
    freqs_pos = freqs[1:N//2]  # descartamos DC y parte negativa

    # 2) Máscara de recorte de eje X
    mask = np.ones_like(freqs_pos, dtype=bool)
    if x_min is not None:
        mask &= freqs_pos >= x_min
    if x_max is not None:
        mask &= freqs_pos <= x_max
    freqs_plot = freqs_pos[mask]

    # 3) Construir la matriz de magnitudes
    mag_list = []
    group_ids = sorted(fft_dict.keys())
    for gid in group_ids:
        mag = np.abs(fft_dict[gid])[1:N//2]
        if mag.size < freqs_pos.size:
            pad = freqs_pos.size - mag.size
            fill_val = np.min(mag[mag>0]) if np.any(mag>0) else 0
            mag = np.pad(mag, (0, pad), mode='constant', constant_values=fill_val)
        mag_list.append(mag[mask])
    mag_matrix = np.vstack(mag_list)
    groups = np.arange(1, len(group_ids) + 1)

    # 4) Plot
    fig, ax = plt.subplots(figsize=figsize)
    if vmin is None:
        vmin = mag_matrix[mag_matrix>0].min()
    if vmax is None:
        vmax = mag_matrix.max()

    X, Y = np.meshgrid(freqs_plot, groups)
    pcm = ax.pcolormesh(
        X, Y, mag_matrix,
        norm=LogNorm(vmin=vmin, vmax=vmax),
        shading='auto'
    )
    ax.set_xscale('log')
    ax.xaxis.set_major_formatter(FuncFormatter(hz_formatter))
    ax.set_xlabel("Frecuencia")
    ax.set_ylabel("Grupo")
    ax.set_title(title)

    # 5) Línea vertical opcional
    if vline_freq is not None and (mask & (freqs_pos == freqs_pos)).any():
        if x_min is not None and vline_freq < x_min:
            pass
        elif x_max is not None and vline_freq > x_max:
            pass
        else:
            # Personalizar kwargs
            lw = {'color': 'red', 'linestyle': '--', 'linewidth': 1.5, 'alpha': 0.8, 'zorder': 10}
            if vline_kwargs:
                lw.update(vline_kwargs)
            ax.axvline(vline_freq, **lw)

    fig.colorbar(pcm, ax=ax, label="Magnitud (log)")

    plt.tight_layout()
    if show:
        plt.show()

    return fig, ax
