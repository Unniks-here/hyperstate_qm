import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import warnings

# Filter out runtime warnings (overflows/invalid values) during optimization exploration
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ==========================================
# 1. ROBUST FITTING LOGIC (The Fix)
# ==========================================
def fit_ramsey_robust(x_times, y_probs):
    """
    Fits Ramsey fringe data with strict physical bounds to prevent 
    OptimizeWarning and unphysical results (like negative T2).
    
    Model: P(t) = A * exp(-t/T2*) * cos(2*pi*delta_f*t + phi) + B
    """
    
    # Define Model
    def model(t, a, t2, f, phi, b):
        return a * np.exp(-t/t2) * np.cos(2*np.pi*f*t + phi) + b

    # --- A. Smart Initial Guesses ---
    # Amplitude: Half the range of data
    amp_guess = (np.max(y_probs) - np.min(y_probs)) / 2
    # Offset: Mean of data
    offset_guess = np.mean(y_probs)
    # T2: Guess 30us (conservative start)
    t2_guess = 30e-6 
    # Freq: Guess 50kHz (typical detuning target)
    freq_guess = 50e3 
    
    p0 = [amp_guess, t2_guess, freq_guess, 0, offset_guess]
    
    # --- B. Physical Bounds [Amp, T2, Freq, Phi, Offset] ---
    # T2 must be positive (1ns to 1ms)
    # Freq allowed between -1MHz and +1MHz
    lower_bounds = [0.0, 1e-9,    -1e6, -2*np.pi, 0.0]
    upper_bounds = [1.0, 1000e-6,  1e6,  2*np.pi, 1.0]
    
    try:
        # maxfev=5000 gives the solver more time to find the true minimum
        popt, pcov = curve_fit(
            model, 
            x_times, 
            y_probs, 
            p0=p0, 
            bounds=(lower_bounds, upper_bounds), 
            maxfev=5000 
        )
        
        t2_fit = popt[1]
        freq_fit = popt[2]
        
        # Calculate fitting error (std dev) for T2
        perr = np.sqrt(np.diag(pcov))
        t2_err = perr[1]
        
        return {
            "success": True,
            "T2": t2_fit,
            "Freq_Shift": freq_fit,
            "T2_Err": t2_err,
            "Params": popt
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "T2": 0, "Freq_Shift": 0}

# ==========================================
# 2. REPORTING LOGIC
# ==========================================
def generate_brutal_report(qubit_data):
    """
    Analyzes the processed data to generate the 'No Sugarcoating' report.
    """
    print("\n" + "="*60)
    print("      CRITICAL RAMSEY DIAGNOSTIC REPORT      ")
    print("="*60)
    print(f"{'Qubit':<6} | {'T2* (us)':<10} | {'Shift (kHz)':<12} | {'Status'}")
    print("-" * 60)
    
    shifts = []
    valid_qubits = 0
    
    # Quality Thresholds
    BAD_T2_THRESH = 50e-6   # Below 50us is unusable
    WARN_T2_THRESH = 100e-6 # Below 100us is risky
    BAD_SHIFT_THRESH = 20e3 # >20kHz is miscalibrated
    
    sorted_ids = sorted(qubit_data.keys())
    
    for q_id in sorted_ids:
        res = qubit_data[q_id]
        
        if not res['success']:
            print(f"{q_id:<6} | {'FAILED':<10} | {'---':<12} | FIT FAILURE")
            continue
            
        t2 = res['T2']
        shift = res['Freq_Shift']
        
        # Color coding status
        status = "OK"
        if t2 < BAD_T2_THRESH:
            status = "BLACKLIST (Dead)"
        elif abs(shift) > BAD_SHIFT_THRESH:
            status = "RECALIBRATE (Detuned)"
        elif t2 < WARN_T2_THRESH:
            status = "POOR (Noisy)"
        
        # Collect stats for global correction only if qubit is generally working
        # Exclude "Detuned" qubits from global shift calculation
        if t2 > BAD_T2_THRESH and abs(shift) <= BAD_SHIFT_THRESH:
            shifts.append(shift)
            valid_qubits += 1

        print(f"{q_id:<6} | {t2*1e6:<10.1f} | {shift/1000:<12.1f} | {status}")

    # --- Global Correction ---
    print("-" * 60)
    if shifts:
        median_shift = np.median(shifts)
        print(f"\nGlobal Systematic Shift (Median): {median_shift/1000:.2f} kHz")
        print(f"(Calculated from {valid_qubits} valid qubits, ignoring outliers)")
        
        correction = -median_shift
        print(f"ACTION REQUIRED: Add {correction/1000:+.2f} kHz to global drive frequency.")
    else:
        print("No valid data to calculate global shift (All qubits dead or detuned).")

# ==========================================
# 3. DATA RETRIEVAL & MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # --- CONFIGURATION ---
    # Replace with the Job ID you want to recover/analyze
    JOB_ID = 'c9s...your_job_id_here...abc' 
    
    # Standard Qiskit Runtime Service retrieval
    # Uncomment and adjust based on your authentication setup
    """
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService()
    job = service.job(JOB_ID)
    result = job.result()
    
    # Assuming standard result structure [pub_result_0, pub_result_1...]
    # or specific memory format. Adjust extraction logic below as needed.
    """
    
    print(f"Analyzing Job: {JOB_ID} (Placeholder Mode)")
    print("... Fetching results ...")
    
    # Dictionary to store analysis results for report
    analysis_results = {}

    # --- MOCK DATA LOOP (Replace with real `for qubit in qubits:` loop) ---
    # This simulates retrieving data for a few qubits to demonstrate the report
    
    # Define simulated time points (x-axis)
    delay_times = np.linspace(0, 100e-6, 15) 

    # Simulate Qubit 1 (Healthy, systematic shift)
    analysis_results[1] = fit_ramsey_robust(
        delay_times, 
        0.5 * np.exp(-delay_times/190e-6) * np.cos(2*np.pi*-5e3*delay_times) + 0.5
    )
    
    # Simulate Qubit 7 (Detuned)
    analysis_results[7] = fit_ramsey_robust(
        delay_times, 
        0.5 * np.exp(-delay_times/312e-6) * np.cos(2*np.pi*57e3*delay_times) + 0.5
    )
    
    # Simulate Qubit 26 (Dead)
    analysis_results[26] = fit_ramsey_robust(
        delay_times, 
        0.5 * np.exp(-delay_times/37e-6) * np.cos(2*np.pi*-16.7e3*delay_times) + 0.5 + np.random.normal(0, 0.05, 15)
    )

    # --- REAL DATA INTEGRATION GUIDE ---
    # 1. Loop through your `result` object
    # 2. Extract `y_probs` for each qubit
    # 3. Call `fit_ramsey_robust(delay_times, y_probs)`
    # 4. Store result: analysis_results[qubit_index] = fit_result

    # Generate the final report
    generate_brutal_report(analysis_results)