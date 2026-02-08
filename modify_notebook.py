import json
import os
import pandas as pd

nb_path = r'c:\Users\Asus\Documents\code\xlab_radiationPaper\radiationXlabs_notebooks\1127_Rad_bits.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Helper to create a code cell
def create_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True)
    }

# Helper to create a markdown cell
def create_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True)
    }

new_cells = []

# 1. User's Time-based Plot (Keep as is)
new_cells.append(create_markdown_cell("""## 6. Time-based Analysis Visualization
Visualizing Failure Rate and Cross-section over time with moving average smoothing."""))

new_cells.append(create_code_cell("""
# Prepare data for plotting
# Assuming 'results_df' from previous analysis contains the time-series data
df_clean = results_df.copy()

# Definir ventana de suavizado (ej. 50 puntos de datos, ajusta según tu frecuencia de muestreo)
window_size = 50 

fig, ax1 = plt.subplots(figsize=(12, 6))

# Eje 1: Failure Rate (Suavizado + Datos tenues de fondo)
alpha_value = 0.15
ax1.plot(df_clean['time'], df_clean['lambda'], 'b.-', alpha=alpha_value) # Ruido de fondo
ax1.plot(df_clean['time'], df_clean['lambda'].rolling(window=window_size).mean(), 
         color='blue', linewidth=2, label=f'Failure Rate (Media Móvil {window_size})')
ax1.set_xlabel('Time')
ax1.set_ylabel('Failure Rate (Hz)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')

# Eje 2: Cross Section
ax2 = ax1.twinx()
ax2.plot(df_clean['time'], df_clean['sigma'], 'r.-', alpha=alpha_value) # Ruido de fondo
ax2.plot(df_clean['time'], df_clean['sigma'].rolling(window=window_size).mean(), 
         color='red', linewidth=2, linestyle='--', label=f'Cross Section (Media Móvil {window_size})')
ax2.set_ylabel('Cross Section ($cm^2$)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# Leyenda unificada
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

plt.title(f'Tendencia Suavizada: Failure Rate y Cross Section (Ventana: {window_size})')
plt.grid(True, alpha=0.3)
plt.show()
"""))

# 2. Fluence-based Analysis with Wilson Score CI
new_cells.append(create_markdown_cell("""## 7. Fluence-based Analysis with Robust Confidence Intervals
Calculating Cross-section as a function of Accumulated Fluence, including 95% Confidence Intervals using the Wilson Score method for the binomial proportion $\phi$."""))

new_cells.append(create_code_cell("""
def analyze_fluence_based(df, fluence_window=1e9, reset_interval=None):
    if reset_interval is None:
        print("Error: reset_interval must be provided for correct N_t estimation.")
        return pd.DataFrame()

    print(f"Analysis Fluence Window: {fluence_window:.2e} particles/cm^2")
    
    results = []
    
    current_fluence_acc = 0
    current_fails_acc = 0
    total_fluence_acc = 0
    
    # Pre-calculate fluence step
    df['fluence_step'] = df['HEH_dose_rate'] * df['dt']
    
    # Reconstruct cumulative fails
    vals = df['fails_inst'].values
    reconstructed_fails = []
    cum_val = 0
    for i in range(len(vals)):
        if i > 0:
            d = vals[i] - vals[i-1]
            if d < 0: # Reset
                cum_val += vals[i]
            else:
                cum_val += d
        else:
            cum_val = vals[0]
        reconstructed_fails.append(cum_val)
        
    df['fails_cumulative'] = reconstructed_fails
    
    # Iterate
    start_fails = df['fails_cumulative'].iloc[0]
    
    temp_fluence = 0
    temp_duration = 0
    temp_start_fails = start_fails
    
    for index, row in df.iterrows():
        step_fluence = row['fluence_step']
        temp_fluence += step_fluence
        temp_duration += row['dt']
        total_fluence_acc += step_fluence
        
        if temp_fluence >= fluence_window:
            # End of window
            current_fails = row['fails_cumulative']
            fails_in_window = current_fails - temp_start_fails # N_l
            
            # Estimate N_t (Total Intervals)
            N_t = temp_duration / reset_interval
            N_l = fails_in_window
            
            # Occupancy
            if N_t > 0:
                phi = N_l / N_t
                phi_int = temp_fluence / N_t # Fluence per interval
            else:
                phi = 0
                phi_int = 0
                
            # Central Estimate (MLE)
            if phi < 1 and phi_int > 0:
                sigma = - (1 / phi_int) * np.log(1 - phi)
            else:
                sigma = 0 # Or inf if phi >= 1
                
            # --- Wilson Score Interval for phi ---
            # alpha = 0.05 (95% CI) -> Z = 1.96
            Z = 1.96
            n = N_t
            p_hat = phi
            
            if n > 0:
                denominator = 1 + Z**2/n
                center_adjusted_probability = p_hat + Z**2 / (2*n)
                adjusted_standard_deviation = np.sqrt((p_hat*(1 - p_hat)/n) + (Z**2 / (4*n**2)))
                
                phi_low = (center_adjusted_probability - Z * adjusted_standard_deviation) / denominator
                phi_high = (center_adjusted_probability + Z * adjusted_standard_deviation) / denominator
                
                # Clamp phi to [0, 1) to avoid log errors
                phi_low = max(0, min(phi_low, 0.999999))
                phi_high = max(0, min(phi_high, 0.999999))
                
                # Map to Sigma
                # sigma_low corresponds to phi_low? No.
                # sigma = -C * ln(1 - phi) is monotonically increasing with phi.
                # So phi_low -> sigma_low, phi_high -> sigma_high.
                
                if phi_int > 0:
                    sigma_low = - (1 / phi_int) * np.log(1 - phi_low)
                    sigma_high = - (1 / phi_int) * np.log(1 - phi_high)
                else:
                    sigma_low = 0
                    sigma_high = 0
            else:
                sigma_low = 0
                sigma_high = 0

            results.append({
                'accumulated_fluence': total_fluence_acc,
                'sigma': sigma,
                'sigma_low_95': sigma_low,
                'sigma_high_95': sigma_high,
                'window_fluence': temp_fluence,
                'window_fails': fails_in_window,
                'N_t': N_t,
                'phi': phi
            })
            
            # Reset window
            temp_fluence = 0
            temp_duration = 0
            temp_start_fails = current_fails
            
    return pd.DataFrame(results)

# Run Fluence Analysis
fluence_window_size = 5e9 
# We need reset_interval from previous cells. Assuming it is available as 'reset_interval'
fluence_results = analyze_fluence_based(fails_on, fluence_window=fluence_window_size, reset_interval=reset_interval)

print(f"Generated {len(fluence_results)} data points.")
"""))

# 3. Fluence-based Plot with Confidence Bands
new_cells.append(create_code_cell("""
# Plot Cross Section vs Fluence with 95% Confidence Band
if len(fluence_results) > 0:
    window_size_fl = 10 
    
    plt.figure(figsize=(12, 6))
    
    # Raw data (binned) - Central Estimate
    plt.plot(fluence_results['accumulated_fluence'], fluence_results['sigma'], 
             'g.-', alpha=0.5, label='Corrected Cross Section (MLE)')
    
    # Confidence Band (Wilson Score 95%)
    plt.fill_between(fluence_results['accumulated_fluence'], 
                     fluence_results['sigma_low_95'], 
                     fluence_results['sigma_high_95'], 
                     color='green', alpha=0.2, label='95% Confidence Interval (Wilson)')
    
    # Smoothed Trend
    if len(fluence_results) >= window_size_fl:
        plt.plot(fluence_results['accumulated_fluence'], 
                 fluence_results['sigma'].rolling(window=window_size_fl).mean(), 
                 'k--', linewidth=2, label=f'Smoothed Trend (Window: {window_size_fl})')
        
    plt.xlabel('Accumulated Fluence ($particles/cm^2$)')
    plt.ylabel('Cross Section ($cm^2$)')
    plt.title(f'Cross Section vs Accumulated Fluence (Bin: {fluence_window_size:.1e})')
    plt.grid(True, alpha=0.3)
    plt.legend()
    # Use log scale if range is large
    # plt.yscale('log') 
    plt.show()
else:
    print("Not enough data to plot Fluence-based analysis.")
"""))

# Remove the last 3 cells (previous implementation) and append new ones
# Actually, modify_notebook.py logic was to append. 
# To avoid duplication, we should ideally remove the old ones or just append these as new versions.
# Since I cannot easily delete specific cells by index without knowing them, I will just append these.
# The user can ignore the previous ones or I can try to replace them if I knew the structure.
# But wait, the previous `modify_notebook.py` appended cells. If I run this, it will append AGAIN.
# I should try to remove the previously added cells if possible.
# The previous script added 3 cells.
# Let's try to remove the last 3 cells before appending.

if len(nb['cells']) > 3:
    # Check if the last cell is the one we added previously
    last_source = "".join(nb['cells'][-1]['source'])
    if "Plot Cross Section vs Fluence" in last_source:
        print("Removing previous fluence analysis cells...")
        nb['cells'] = nb['cells'][:-3]

nb['cells'].extend(new_cells)

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4)

print("Notebook modified successfully.")
