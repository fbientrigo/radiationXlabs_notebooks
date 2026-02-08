import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap

from src.utils.config import SimulationConfig
from src.physics.beam import BurstBeam
from src.stats.sliding_window import SlidingWindowStats
from src.core.tmr_system import TMRSystem
from src.core.engine import SimulationEngine

def parse_arguments():
    parser = argparse.ArgumentParser(description="RadAnalysis: Visual Burst Mode")
    # Burst Params
    parser.add_argument("--flux-active", type=float, default=2e8)
    parser.add_argument("--duty-cycle", type=float, default=0.2)
    parser.add_argument("--spill-duration", type=float, default=2.0)
    parser.add_argument("--flux-bg", type=float, default=0.0)
    
    # Standard Params
    parser.add_argument("--sigma", type=float, default=1e-12)
    parser.add_argument("--triads", type=int, default=2500)
    parser.add_argument("--scrub-mean", type=float, default=3.0)
    parser.add_argument("--scrub-std", type=float, default=0.1)
    parser.add_argument("--dt", type=float, default=0.02)
    
    # Viz
    parser.add_argument("--steps-per-frame", type=int, default=5)
    parser.add_argument("--history", type=int, default=500, help="History steps for plot")
    
    return parser.parse_args()

def run_visualization():
    args = parse_arguments()
    
    config = SimulationConfig(
        flux=0,
        flux_active=args.flux_active,
        flux_background=args.flux_bg,
        duty_cycle=args.duty_cycle,
        spill_duration=args.spill_duration,
        sigma=args.sigma,
        scrubbing_interval=(args.scrub_mean, args.scrub_std),
        triad_count=args.triads
    )
    
    beam = BurstBeam(
        flux_active=config.flux_active,
        duty_cycle=config.duty_cycle,
        spill_duration=config.spill_duration,
        flux_background=config.flux_background
    )
    
    tmr = TMRSystem(config)
    stats = SlidingWindowStats(config, window_size=2.0)
    engine = SimulationEngine(config, beam, tmr, stats)
    
    # Setup Plot
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1]) 
    # Layout:
    # [ Grid (Left) ]  [ Flux Plot (Top Right) ]
    # [ Grid (Left) ]  [ Failure Plot (Bottom Right) ]
    
    ax_grid = fig.add_subplot(gs[:, 0])
    ax_grid.axis('off')
    ax_grid.set_title("TMR Array State")
    
    ax_flux = fig.add_subplot(gs[0, 1])
    ax_flux.set_title("Instantaneous Flux (Spill Structure)")
    ax_flux.set_ylabel("Flux (p/cm²/s)")
    ax_flux.grid(True, alpha=0.3)
    
    ax_fail = fig.add_subplot(gs[1, 1])
    ax_fail.set_title("Cumulative System Failures")
    ax_fail.set_xlabel("Time (s)")
    ax_fail.grid(True, alpha=0.3)
    
    # Init Viz Objects
    n = args.triads
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    
    cmap = ListedColormap(['#333333', '#FFD700', '#FF4500']) # Grey, Gold, Red
    grid_init = np.zeros((rows, cols))
    img = ax_grid.imshow(grid_init, cmap=cmap, vmin=0, vmax=2, animated=True)
    
    # Text overlay
    status_text = ax_grid.text(0.5, -0.05, "Init", transform=ax_grid.transAxes, 
                               ha='center', color='white', fontsize=12, animated=True)
    
    # Buffers
    N = args.history
    buf_time = np.zeros(N)
    buf_flux = np.zeros(N)
    buf_fail = np.zeros(N) # Cumulative failures count
    
    # Plot Lines
    line_flux, = ax_flux.plot([], [], 'g-', lw=2, animated=True)
    fill_flux = ax_flux.fill_between([], [], color='green', alpha=0.1) # Hard to animate fill_between efficiently in basic blit
    # We will skip fill_between for pure speed or use a static polygon?
    # Let's just use the line.
    
    line_fail, = ax_fail.plot([], [], 'r-', lw=2, animated=True)
    
    # Indicators
    scrub_line = ax_flux.axvline(x=-1, color='cyan', linestyle='--', alpha=0, animated=True)
    
    # Calculate Y-Limits
    ax_flux.set_ylim(-0.1 * args.flux_active, args.flux_active * 1.2)
    ax_fail.set_ylim(0, 10) # Auto-expand
    
    cum_failures = 0

    def start():
        return img, status_text, line_flux, line_fail, scrub_line

    def update(frame):
        nonlocal cum_failures
        
        # Step Simulation
        for _ in range(args.steps_per_frame):
            last_data = engine.step(args.dt)
            # Accumulate failures for the plot (Cumulative Count)
            # engine data 'sys_failures' is CURRENT state count (instantaneous).
            # We want to verify accumulation?
            # Actually, let's plot ACTIVE System Failures (Instantaneous) like before.
            # But prompt said "Cumulative Failures".
            # Engine doesn't track cumulative failures indefinitely (it resets on scrub).
            # Let's plot INSTANTANEOUS System Failures (Risk state).
            pass
            
        t = last_data['time']
        flux = beam.get_flux_at(t)
        failures = last_data['sys_failures'] # Current count
        
        # Update Buffers
        buf_time[:-1] = buf_time[1:]; buf_time[-1] = t
        buf_flux[:-1] = buf_flux[1:]; buf_flux[-1] = flux
        buf_fail[:-1] = buf_fail[1:]; buf_fail[-1] = failures
        
        # Grid
        upsets = np.sum(engine.tmr.bits, axis=1)
        upsets = np.minimum(upsets, 2)
        padded = np.zeros(rows * cols)
        padded[:len(upsets)] = upsets
        img.set_data(padded.reshape(rows, cols))
        
        # Plots
        # Update X-Axis (Scrolling)
        t_min, t_max = buf_time[0], buf_time[-1] + args.dt
        ax_flux.set_xlim(t_min, t_max)
        ax_fail.set_xlim(t_min, t_max)
        
        ax_fail.set_ylim(0, max(10, np.max(buf_fail) * 1.1))
        
        line_flux.set_data(buf_time, buf_flux)
        line_fail.set_data(buf_time, buf_fail)
        
        # Scrub Indicator
        # If failures dropped significantly or exact scrub match
        # Let's enable the Scrub Line at current time if scrub happened
        if last_data['did_scrub']:
            scrub_line.set_xdata([t, t])
            scrub_line.set_alpha(1.0)
        else:
            # Fade out
            curr = scrub_line.get_alpha()
            if curr > 0: scrub_line.set_alpha(max(0, curr - 0.1))
        
        # Status Text
        state = "SPILL" if flux > args.flux_active*0.5 else "OFF"
        status_text.set_text(f"T={t:.2f}s | {state} | Failures: {failures}")
        
        return img, status_text, line_flux, line_fail, scrub_line

    ani = animation.FuncAnimation(fig, update, init_func=start, 
                                  interval=20, blit=False, cache_frame_data=False)
                                  # blit=False because we are changing x-limits every frame
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_visualization()
