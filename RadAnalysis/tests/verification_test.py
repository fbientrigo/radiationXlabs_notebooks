import sys
from pathlib import Path
import time

# Add src to path so we can import modules
# Assuming script is run from RadAnalysis root or tests folder
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root / "src"))

try:
    from utils.config import SimulationConfig
    from stats.sliding_window import SlidingWindowStats
    print("[OK] Imports successful.")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

def run_test():
    print("Running Verification Test...")
    
    # 1. Setup Config
    config = SimulationConfig(
        flux=1e5,             # 10^5 particles/cm2/s
        sigma=1e-10,          # 10^-10 cm2/device
        scrubbing_interval=(1.0, 0.1),
        triad_count=1000
    )
    
    print(f"Config Theory Lambda Device: {config.lambda_theory_device}")
    print(f"Config Theory Lambda Total: {config.lambda_theory_total}")
    
    # 2. Setup Observer
    observer = SlidingWindowStats(config, window_size=10.0)
    
    # 3. Simulate Events
    # Expected rate = 1e5 * 1e-10 * 3 * 1000 = 1e-5 * 3000 = 0.03 fails/sec
    # Let's fake a higher rate to see numbers
    
    current_time = 0.0
    for i in range(10):
        current_time += 1.0
        # Inject an event every second (Lambda ~ 1.0)
        observer.record_event(current_time, "fail")
        
        metrics = observer.get_metrics(current_time)
        print(f"T={current_time:4.1f} | Obs={metrics['lambda_obs']:.3f} | CI={metrics['ci_95'][0]:.3f}-{metrics['ci_95'][1]:.3f} | Conv={metrics['convergence']:.3f}")

    print("\n[OK] Verification Complete.")

if __name__ == "__main__":
    run_test()
