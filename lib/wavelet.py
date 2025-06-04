import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FuncFormatter

import pywt
import matplotlib.dates as mdates
from scipy.fft import rfft, rfftfreq


def cwt(df, channel = 'ch0', time_axis = 'timestamp', scale_max = 256):
    x = df[channel].values
    times = df[time_axis].values

    # 4) CWT
    scales = np.arange(1, scale_max)
    coeffs, freqs = pywt.cwt(x, scales, 'morl', sampling_period=coef)

    # 5) Gráfica señal vs tiempo y scalogram
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

    # Señal vs timestamp
    ax1.plot(df[time_axis], x, '.', markersize=2)
    ax1.set_title(f'{channel} vs {time_axis}')
    ax1.set_ylabel('ADC Code')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

    # Scalogram
    extent = [times[0], times[-1], freqs[-1], freqs[0]]  # Y de f_min a f_max
    im = ax2.imshow(
        np.abs(coeffs),
        extent=extent,
        aspect='auto'
    )
    ax2.set_yscale('log')
    ax2.set_title('CWT Scalogram (ch0)')
    ax2.set_ylabel('Frecuencia [Hz]')
    ax2.set_xlabel('Sample Index')

    # Convertir eje Y a MHz
    # ax2.yaxis.set_major_formatter(
    #     ticker.FuncFormatter(lambda val, pos: f"{val:.3e}")
    # )
    ax2.set_ylabel('Frequency [Hz]')

    plt.tight_layout()
    plt.show()


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


def analyze_frequencies(df, channel='ch0', coef=0.00129798, intercept=-0.030460957185257993):
    """
    Dado un DataFrame con muestras y el sampling period (coef),
    genera:
     1) Un scalogram CWT con el eje de frecuencia (Hz).
     2) Un espectro FFT para identificar los picos de frecuencia.
    """
    for ch in [f'ch{x}' for x in range(8)]:
        df[ch] = df[ch].apply(lambda x: int(str(x), 16))

    x = df[channel].values
    n = len(x)
    fs = 1.0 / coef               # frecuencia de muestreo en Hz

    # generar los time stamps en base a coef
    n = len(df)
    k = np.arange(n)
    # Tiempo relativo en segundos
    pred_secs = intercept + coef * k
    t0 = df['timestamp'].iloc[0]
    df['predicted_timestamp'] = t0 + pd.to_timedelta(pred_secs, unit='s')
    t0 = df['predicted_timestamp'].iloc[0]

    # ——— 1) CWT Scales → Frecuencias ———
    scales = np.arange(1, 128)
    # freqs en Hz: pywt.scale2frequency devuelve frecuencia relativa (1/dt)
    frequencies = pywt.scale2frequency('morl', scales) * fs
    coeffs, _ = pywt.cwt(x, scales, 'morl', sampling_period=coef)

    # Plot scalogram con eje de frecuencia
    fig, ax = plt.subplots(figsize=(8,4))
    im = ax.imshow(np.abs(coeffs), 
                   extent=[0, n, frequencies[-1], frequencies[0]],
                   aspect='auto',
                   cmap='jet')
    ax.set_ylabel('Frecuencia (Hz)')
    ax.set_yscale('log')
    ax.set_xlabel('Índice de muestra k')
    ax.set_title(f'CWT Scalogram ({channel})')
    fig.colorbar(im, ax=ax, label='|coef|')
    plt.tight_layout()
    plt.show()

    # ——— 2) FFT para espectro ———
    # Restar la media para centrar
    x_detrended = x - np.mean(x)
    # Transformada rápida de Fourier
    X = rfft(x_detrended)
    freqs = rfftfreq(n, d=coef)   # eje de frecuencia
    power = np.abs(X)

    # Plot espectro
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(freqs, power)
    ax.set_xlim(0, fs/2)
    ax.set_xlabel('Frecuencia (Hz)')
    ax.set_ylabel('Magnitud FFT')
    ax.set_title(f'Espectro FFT ({channel})')
    plt.tight_layout()
    plt.show()
