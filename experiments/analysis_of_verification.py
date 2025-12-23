import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from qiskit_ibm_runtime import QiskitRuntimeService

# --- CONFIGURATION ---
# PASTE YOUR VERIFICATION JOB ID HERE
JOB_ID = "d553pl0nsj9s73b2dukg" 
QUBIT_TARGET = 26
BASELINE_T2 = 30.0 # The "Dead" T2 lifetime in microseconds

# Must match the sweep in experiments/11_hyperstate_verification.py
DELAYS_US = np.linspace(0, 300, 15) 

def exponential_decay(t, a, t2, c):
    return a * np.exp(-t / t2) + c

def analyze_verification():
    if JOB_ID == "INSERT_NEW_JOB_ID_HERE" or not JOB_ID:
        print("ERROR: Please update 'JOB_ID' with the ID from experiment 11.")
        return

    print(f"--- FETCHING VERIFICATION JOB: {JOB_ID} ---")
    
    # 1. Retrieve Job
    try:
        service = QiskitRuntimeService()
        job = service.job(JOB_ID)
    except Exception as e:
        print(f"Error connecting to service: {e}")
        return

    # 2. Check Status
    status = job.status()
    status_name = status if isinstance(status, str) else status.name
    print(f"Job Status: {status_name}")
    
    if status_name not in ["DONE", "COMPLETED"]:
        print("Job not finished. Please wait.")
        return

    # 3. Get Data
    print("Downloading results...")
    result = job.result()
    
    # Calculate Probabilities
    probabilities = []
    for i, pub_result in enumerate(result):
        try:
            counts = pub_result.data.c.get_counts() 
        except AttributeError:
            counts = pub_result.data.meas.get_counts()
            
        total_shots = sum(counts.values())
        # For T2 Echo, we measure |1> population decay
        p1 = counts.get('1', 0) / total_shots
        probabilities.append(p1)

    # 4. Fit Data
    print("\n--- FITTING T2 DECAY ---")
    t2_fit = 0
    try:
        # Initial guess: Amp=0.5, T2=50us, Offset=0.5
        p0 = [0.5, 50, 0.5] 
        popt, pcov = curve_fit(exponential_decay, DELAYS_US, probabilities, p0=p0, maxfev=5000)
        
        t2_fit = popt[1]
        print(f"Calculated T2: {t2_fit:.2f} µs")
        
        # Generate fit line for plotting
        x_fit = np.linspace(0, 300, 100)
        y_fit = exponential_decay(x_fit, *popt)
        fit_label = f"Fit: T2 = {t2_fit:.1f} µs"
    except Exception as e:
        print(f"Fitting failed: {e}")
        x_fit, y_fit = [], []
        fit_label = "Fit Failed"

    # 5. FINAL VERDICT LOGIC
    print("\n" + "="*40)
    print("FINAL EXPERIMENT VERDICT")
    print("="*40)
    
    if t2_fit > (BASELINE_T2 * 1.3): # Threshold: 30% improvement
        print("RESULT: SUCCESS (Hyperstate Confirmed)")
        print(f"Logic: New T2 ({t2_fit:.1f}us) is significantly better than baseline ({BASELINE_T2}us).")
        print("Conclusion: The Stark Shift successfully rescued the qubit from the defect.")
    elif t2_fit > BASELINE_T2:
        print("RESULT: MARGINAL IMPROVEMENT")
        print(f"Logic: New T2 ({t2_fit:.1f}us) is slightly better than baseline ({BASELINE_T2}us).")
        print("Conclusion: The effect exists but might need amplitude optimization.")
    else:
        print("RESULT: FAILURE (No Protection)")
        print(f"Logic: New T2 ({t2_fit:.1f}us) is effectively the same or worse than baseline.")
        print("Conclusion: The Stark Shift did not decouple the qubit from the noise.")
    print("="*40 + "\n")

    # 6. Visualize
    plt.figure(figsize=(10, 6))
    
    # Plot Data
    plt.plot(DELAYS_US, probabilities, 'o', color='#648fff', label='Experimental Data', markersize=8)
    
    # Plot Fit
    if len(x_fit) > 0:
        plt.plot(x_fit, y_fit, '-', color='#dc267f', linewidth=2, label=fit_label)
    
    # Add Baseline reference (Original Dead Qubit T2 ~ 30us)
    y_baseline = exponential_decay(x_fit, 0.5, BASELINE_T2, 0.5)
    plt.plot(x_fit, y_baseline, '--', color='gray', alpha=0.5, label=f'Original Baseline (T2~{BASELINE_T2}us)')

    plt.title(f"Hyperstate Verification (Q{QUBIT_TARGET})\nJob: {JOB_ID}")
    plt.xlabel("Delay Time (µs)")
    plt.ylabel("Survival Probability P(1)")
    plt.ylim(0, 1.1)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    filename = "hyperstate_t2_result.png"
    plt.savefig(filename)
    print(f"Plot saved to: {filename}")
    plt.show()

if __name__ == "__main__":
    analyze_verification()