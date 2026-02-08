import time
import sys
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.console import Console

from src.utils.config import SimulationConfig
from src.physics.beam import ParticleBeam
from src.stats.sliding_window import SlidingWindowStats
from src.core.tmr_system import TMRSystem
from src.core.engine import SimulationEngine

def generate_table(engine_data, metrics, config) -> Table:
    table = Table(title="RadAnalysis: TMR Simulation Real-Time Monitor")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    # Time & Fluence
    time_val = engine_data['time']
    table.add_row("Sim Time", f"{time_val:6.2f} s")
    table.add_row("Fluence", f"{engine_data['fluence']:.2e} p/cm²")
    
    # State Counts
    table.add_row("System Failures", f"[red]{engine_data['sys_failures']}[/red]")
    table.add_row("Masked Errors", f"[yellow]{engine_data['masked_errors']}[/yellow]")
    
    # Statistics
    lambda_th = metrics['lambda_theory']
    lambda_obs = metrics['lambda_obs']
    
    # Cumulative Average Calculation
    # Lambda Avg = Total Events / Total Time
    total_events = metrics.get('total_events', 0)
    lambda_cum = total_events / time_val if time_val > 0 else 0.0

    err = metrics['error_rel'] * 100
    
    table.add_section()
    table.add_row("Lambda Theory", f"{lambda_th:.2e}")
    table.add_row("Lambda Obs (Window)", f"{lambda_obs:.2e}")
    table.add_row("Lambda Avg (Cumul)", f"{lambda_cum:.2e}")
    
    table.add_section()
    table.add_row("Rel Error (Obs)", f"{err:.2f} %")
    table.add_row("Convergence (1/√N)", f"{metrics['convergence']:.4f}")
    table.add_row("Total Events", str(total_events))
    
    if engine_data.get('did_scrub'):
        table.add_row("Status", "[bold green]SCRUBBING[/bold green]")
    else:
        table.add_row("Status", "Running")

    return table

import argparse

def parse_arguments():
    """
    Parse command line arguments for the simulation.
    """
    parser = argparse.ArgumentParser(
        description="RadAnalysis: Stochastic Simulation of TMR Logic under Mixed-Field Radiation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Physics Parameters
    parser.add_argument("--flux", type=float, default=1e7, help="Particle Flux in particles/cm^2/s.")
    parser.add_argument("--sigma", type=float, default=1e-12, help="Cross Section (Sigma) in cm^2/device.")
    
    # System Parameters
    parser.add_argument("--triads", type=int, default=10000, help="Number of TMR Triads in the system geometry.")
    
    # Scrubbing Parameters
    parser.add_argument("--scrub-mean", type=float, default=0.5, help="Mean Scrubbing Interval in seconds.")
    parser.add_argument("--scrub-std", type=float, default=0.05, help="Standard Deviation of Scrubbing Interval (Jitter).")
    
    # Simulation Control
    parser.add_argument("--duration", type=float, default=30.0, help="Total simulation duration in seconds.")
    parser.add_argument("--dt", type=float, default=0.01, help="Time step size in seconds.")
    parser.add_argument("--window", type=float, default=2.0, help="Sliding window size for statistics in seconds.")

    return parser.parse_args()

def run_simulation():
    """
    Main entry point for the simulation.
    Initializes the engine with parsed configuration and runs the loop.
    """
    args = parse_arguments()
    
    # Configuration
    config = SimulationConfig(
        flux=args.flux,
        sigma=args.sigma,
        scrubbing_interval=(args.scrub_mean, args.scrub_std),
        triad_count=args.triads
    )
    
    print(f"Initializing Simulation with:")
    print(f"  Flux: {config.flux:.2e} p/cm²/s")
    print(f"  Sigma: {config.sigma:.2e} cm²")
    print(f"  Triads: {config.triad_count}")
    print(f"  Scrubbing: {args.scrub_mean}s (±{args.scrub_std}s)")
    print(f"  Duration: {args.duration}s")
    
    # If flux_active is set, it overrides 'flux' for the BurstBeam
    nominal_flux = config.flux_active if config.flux_active > 0 else config.flux
    
    from src.physics.beam import BurstBeam
    beam = BurstBeam(
        flux_active=nominal_flux,
        duty_cycle=config.duty_cycle,
        spill_duration=config.spill_duration,
        flux_background=config.flux_background
    )
    tmr = TMRSystem(config)
    stats = SlidingWindowStats(config, window_size=args.window)
    engine = SimulationEngine(config, beam, tmr, stats)
    
    console = Console()
    
    dt = args.dt
    
    try:
        # Initial empty data
        metrics = stats.get_metrics(0)
        data = {"time": 0, "fluence": 0, "sys_failures": 0, "masked_errors": 0}
        
        with Live(generate_table(data, metrics, config), 
                  refresh_per_second=10) as live:
            
            while engine.current_time < args.duration:
                data = engine.step(dt)
                metrics = engine.get_metrics()
                
                live.update(generate_table(data, metrics, config))
                time.sleep(0.05) # Visual delay (could be optional flag too)
                
    except KeyboardInterrupt:
        console.print("[bold red]Simulation Aborted by User[/bold red]")

if __name__ == "__main__":
    run_simulation()
