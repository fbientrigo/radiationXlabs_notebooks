import argparse
import sys
import time
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap

from src.utils.config import SimulationConfig
from src.physics.beam import ParticleBeam
from src.stats.sliding_window import SlidingWindowStats
from src.core.tmr_system import TMRSystem
from src.core.engine import SimulationEngine

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="RadAnalysis: Visual TMR Simulation (Enhanced)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Physics
    parser.add_argument("--flux", type=float, default=2e7, help="Particle Flux")
    parser.add_argument("--sigma", type=float, default=1e-12, help="Cross Section")
    parser.add_argument("--triads", type=int, default=2500, help="Number of Triads")
    parser.add_argument("--scrub-mean", type=float, default=1.0, help="Scrub Interval Mean")
    parser.add_argument("--scrub-std", type=float, default=0.1, help="Scrub Jitter")
    
    # Sim Control
    parser.add_argument("--dt", type=float, default=0.01, help="Simulation time step")
    parser.add_argument("--window", type=float, default=2.0, help="Stats window")
    
    # Optimization & Viz
    parser.add_argument("--steps-per-frame", type=int, default=10, help="Sim steps per render frame")
    parser.add_argument("--history", type=int, default=300, help="Plot history length")
    parser.add_argument("--log", action="store_true", help="Use Logarithmic scale for plots")
    
    return parser.parse_args()

def run_visualization():
    args = parse_arguments()
    
    # 1. Setup Simulation
    config = SimulationConfig(
        flux=args.flux,
        sigma=args.sigma,
        scrubbing_interval=(args.scrub_mean, args.scrub_std),
        triad_count=args.triads
    )
    
    beam = ParticleBeam(flux_nominal=config.flux)
    tmr = TMRSystem(config)
    stats = SlidingWindowStats(config, window_size=args.window)
    engine = SimulationEngine(config, beam, tmr, stats)
    
    # 2. Setup Grid Dimensions
    n = args.triads
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    grid_size = rows * cols
    
    # 3. Setup Matplotlib
    plt.style.use('dark_background')
    
    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1])
    
    # Ax1: Grid View
    ax_grid = fig.add_subplot(gs[0, :])
    ax_grid.axis('off')
    
    # RGBA Grid Initialization for Persistence
    # Colors: 0=Grey, 1=Yellow, 2=Red
    base_colors = np.array([
        [0.2, 0.2, 0.2], # Grey
        [1.0, 0.84, 0.0], # Gold
        [1.0, 0.27, 0.0]  # OrangeRed
    ])
    
    # Check shape correctness (rows, cols)
    # Initialize persistence
    persistence_grid = np.zeros(grid_size) 
    
    # Create valid initial image
    initial_rgba = np.zeros((rows, cols, 4))
    initial_rgba[..., 3] = 1.0 # Alpha 1
    
    img = ax_grid.imshow(initial_rgba, interpolation='nearest', animated=True)
    
    # Info Text (Scientific Notation)
    status_text = ax_grid.text(0.01, 0.99, "", transform=ax_grid.transAxes, 
                               color='white', fontsize=12, va='top', ha='left', 
                               fontfamily='monospace', animated=True)
    
    # Ax2: Error Count
    ax_err = fig.add_subplot(gs[1, 0])
    ax_err.set_title("Active Errors")
    ax_err.set_xlim(0, args.history * args.dt * args.steps_per_frame)
    ax_err.grid(True, alpha=0.3)
    if args.log:
        ax_err.set_yscale('log')
        ax_err.set_ylim(0.8, max(10, args.triads)) # Avoid log(0)
    else:
         ax_err.set_ylim(0, 10)

    line_masked, = ax_err.plot([], [], 'y-', label='Masked', animated=True)
    line_fail, = ax_err.plot([], [], 'r-', label='Failed', animated=True)
    ax_err.legend(loc='upper left', fontsize='small')
    
    # Ax3: Convergence
    ax_conv = fig.add_subplot(gs[1, 1])
    ax_conv.set_title("Lambda Convergence")
    ax_conv.grid(True, alpha=0.3)
    if args.log:
        ax_conv.set_yscale('log')
        min_log = max(1e-9, config.lambda_theory_total * 0.1)
        ax_conv.set_ylim(min_log, config.lambda_theory_total * 10)
    else:
        ax_conv.set_ylim(0, config.lambda_theory_total * 2)

    line_th, = ax_conv.plot([], [], 'w--', alpha=0.5, label='Theory', animated=True)
    line_obs, = ax_conv.plot([], [], 'c-', label='Obs (Window)', animated=True)
    line_cum, = ax_conv.plot([], [], 'm-', label='Avg (Cumul)', animated=True)
    ax_conv.legend(loc='upper right', fontsize='small')
    
    scrub_indicator = ax_grid.text(0.98, 0.95, "SCRUB", transform=ax_grid.transAxes, 
                                   color='cyan', fontsize=16, fontweight='bold', 
                                   ha='right', va='top', alpha=0.0, animated=True)

    # 4. Buffers
    N = args.history
    buf_time = np.zeros(N)
    buf_masked = np.zeros(N)
    buf_fail = np.zeros(N)
    buf_lam_obs = np.zeros(N)
    buf_lam_th = np.zeros(N)
    buf_lam_cum = np.zeros(N) # Cumulative Average
    
    # Avoid log(0) artifacts in buffer init
    if args.log:
        buf_masked.fill(0.1)
        buf_fail.fill(0.1)
        buf_lam_obs.fill(1e-9)
        buf_lam_cum.fill(1e-9)

    def init():
        return img, status_text, line_masked, line_fail, line_th, line_obs, line_cum, scrub_indicator

    def update(frame):
        # Frame Skipping Loop
        for _ in range(args.steps_per_frame):
            last_data = engine.step(args.dt)
        
        last_metrics = engine.get_metrics()
        
        t = last_data['time']
        fluence = last_data['fluence']
        failures = last_data['sys_failures']
        masked = last_data['masked_errors']
        
        # Cumulative Stats Calculation
        # lambda_avg = TotalEvents / TotalTime
        total_events = stats.total_events
        lambda_cum = total_events / t if t > 0 else 0.0
        
        # Buffer Scroll
        buf_time[:-1] = buf_time[1:]; buf_time[-1] = t
        
        # Handle Log Safety
        safe_masked = max(0.1, masked) if args.log else masked
        safe_failures = max(0.1, failures) if args.log else failures
        
        buf_masked[:-1] = buf_masked[1:]; buf_masked[-1] = safe_masked
        buf_fail[:-1] = buf_fail[1:]; buf_fail[-1] = safe_failures
        
        buf_lam_obs[:-1] = buf_lam_obs[1:]; buf_lam_obs[-1] = max(1e-9, last_metrics['lambda_obs']) if args.log else last_metrics['lambda_obs']
        buf_lam_th[:-1] = buf_lam_th[1:]; buf_lam_th[-1] = last_metrics['lambda_theory']
        buf_lam_cum[:-1] = buf_lam_cum[1:]; buf_lam_cum[-1] = max(1e-9, lambda_cum) if args.log else lambda_cum
        
        # 1. Update Grid with Persistence
        upsets = np.sum(engine.tmr.bits, axis=1)
        upsets = np.minimum(upsets, 2)
        if len(upsets) < grid_size:
            upsets = np.concatenate([upsets, np.zeros(grid_size - len(upsets), dtype=int)])
        
        # Persistence Logic:
        # Non-zero state sets persistence to 1.0
        # Zero state decays persistence
        
        # Identify active errors
        is_active = upsets > 0
        
        # Decay global persistence
        nonlocal persistence_grid
        persistence_grid *= 0.90 # Decay factor (tunable)
        
        # Set active pixels to 1.0 (Full visibility)
        persistence_grid[is_active] = 1.0
        
        # Clip
        persistence_grid = np.clip(persistence_grid, 0.05, 1.0) # Min 0.05 to keep grid visible slightly?
        # Actually base grid is Grey. We only want persistence for Yellow/Red.
        # So we use upsets + persistence.
        
        # Construct RGBA
        # If upset[i] == 0: Color is Grey. Beta (Overlay) is 0? 
        # Persistence tracks "Heat".
        # If upset[i] == 0 but persistence[i] > 0.1: We show Fading Color.
        # What color? The last color? 
        # Simplifying assumption: Persistence implies "Yellow" decay for simplicity, or 
        # we need to track "last state". 
        # Enhanced Logic: Persistence of RED vs YELLOW?
        # Let's just use: If currently 0, but persistence high, show Yellow fade.
        # If currently 1 or 2, show real color.
        
        display_indices = upsets.copy()
        # Where upsets are 0 but persistence > 0.1, fake it as 1 (Yellow) to show decay
        # (visual trail of corrected errors)
        mask_decay = (upsets == 0) & (persistence_grid > 0.05)
        display_indices[mask_decay] = 1 # Decay looks yellow
        
        # Map indices to RGB
        rgb_flat = base_colors[display_indices]
        
        # Reshape to (rows, cols, 3)
        rgb_img = rgb_flat.reshape((rows, cols, 3))
        
        # Alpha Logic:
        # If upset > 0: Alpha 1.0
        # If upset == 0: Alpha = persistence (fade out)
        # But we want base Grey always visible?
        # If we use RGBA, lower alpha blends with white/black background.
        # Background is Dark (#000).
        # So low alpha = fade to black.
        # Grey (Index 0) should be persistent or not?
        # Usually inactive chips are visible.
        # Let's say:
        # Index 0 (Grey): Alpha 0.3 (Dim)
        # Index 1/2 (Active/Decay): Alpha 1.0 * persistence? 
        # Let's try:
        
        alpha_flat = np.ones(grid_size)
        # Inactive pixels: Dim
        alpha_flat[upsets == 0] = 0.3 
        # Decaying pixels: Use persistence
        alpha_flat[mask_decay] = persistence_grid[mask_decay]
        
        alpha_img = alpha_flat.reshape((rows, cols, 1))
        
        rgba_img = np.concatenate([rgb_img, alpha_img], axis=2)
        
        img.set_data(rgba_img)
        
        # 2. Update Plots
        ax_err.set_xlim(buf_time[0], buf_time[-1] + args.dt)
        ax_conv.set_xlim(buf_time[0], buf_time[-1] + args.dt)
        
        # Y-Limits - Autoscale occasionally? Manual usually better for performance.
        if not args.log:
             ax_err.set_ylim(0, max(10, np.max(buf_masked) * 1.1))
        
        line_masked.set_data(buf_time, buf_masked)
        line_fail.set_data(buf_time, buf_fail)
        line_th.set_data(buf_time, buf_lam_th)
        line_obs.set_data(buf_time, buf_lam_obs)
        line_cum.set_data(buf_time, buf_lam_cum)
        
        # 3. Status Text (Scientific Notation)
        status_str = (
            f"Time: {t:6.2f} s\n"
            f"Flux: {fluence:.2e} p/cm²\n"
            f"Lambda Th : {last_metrics['lambda_theory']:.2e}\n"
            f"Lambda Obs: {last_metrics['lambda_obs']:.2e}\n"
            f"Lambda Avg: {lambda_cum:.2e}\n"
            f"Active Err: {int(masked)} / {int(failures)}"
        )
        status_text.set_text(status_str)
        
        # 4. Scrub Flash
        # Check if sys_failures count dropped significantly or we need a cleaner signal
        # Just use simple decay flash
        if failures == 0 and buf_fail[-2] > 0:
            scrub_indicator.set_alpha(1.0)
        else:
            curr = scrub_indicator.get_alpha()
            if curr > 0: scrub_indicator.set_alpha(max(0, curr - 0.2))

        return img, status_text, line_masked, line_fail, line_th, line_obs, line_cum, scrub_indicator

    ani = animation.FuncAnimation(fig, update, init_func=init, 
                                  interval=20, blit=True, cache_frame_data=False)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_visualization()
