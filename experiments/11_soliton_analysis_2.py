import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from qiskit_ibm_runtime import QiskitRuntimeService

# --- CONFIGURATION ---
# PASTE YOUR SOLITON TEST JOB ID HERE (Inside the quotes!)
JOB_ID = "d554a10nsj9s73b2ee10" 

# Must match the sweep in Experiment 13
RADION_AMPS = np.linspace(0, 3.0, 15)
CHAIN_LENGTH = 5

def sigmoid(x, L, x0, k, b):
    """Model for Solitonic Critical Collapse (Phase Transition)"""
    return L / (1 + np.exp(k * (x - x0))) + b

def exponential(x, a, b, c):
    """Model for Standard Linear Decoherence"""
    return a * np.exp(-b * x) + c

def analyze_solitons():
    if JOB_ID == "INSERT_JOB_ID_HERE" or not JOB_ID:
        print("ERROR: Please update 'JOB_ID' (Line 8) with the ID from Experiment 13.")
        return

    print(f"--- FETCHING SOLITON DATA: {JOB_ID} ---")
    
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
    
    # We measure "Boundary Integrity".
    # A topological soliton (Domain Wall) in our setup has Q0=|0> and Q4=|1>.
    # We check the fraction of shots where this boundary condition holds.
    # Qiskit Bitstrings are Little-Endian: "Q4 Q3 Q2 Q1 Q0"
    
    integrity_scores = []
    
    for i, pub_result in enumerate(result):
        try:
            counts = pub_result.data.c.get_counts() 
        except AttributeError:
            counts = pub_result.data.meas.get_counts()
            
        total_shots = sum(counts.values())
        valid_solitons = 0
        
        for bitstring, count in counts.items():
            # Pad bitstring if necessary
            bits = bitstring.zfill(CHAIN_LENGTH)
            
            # Check Boundary Condition: Q4='1' (First char) AND Q0='0' (Last char)
            # This works because our soliton goes from 0 -> 1 spatially.
            q4_state = bits[0] # Leftmost in string is highest index
            q0_state = bits[-1] # Rightmost in string is lowest index
            
            if q4_state == '1' and q0_state == '0':
                valid_solitons += count
                
        score = valid_solitons / total_shots
        integrity_scores.append(score)

    # 4. Analyze Shape (The "Smoking Gun")
    print("\n--- ANALYZING DECAY TOPOLOGY ---")
    
    # Fit Sigmoid (Soliton Theory)
    try:
        p0_sig = [0.5, 1.5, 5, 0] # Guess for sigmoid
        popt_sig, _ = curve_fit(sigmoid, RADION_AMPS, integrity_scores, p0=p0_sig, maxfev=5000)
        residuals_sig = np.sum((integrity_scores - sigmoid(RADION_AMPS, *popt_sig))**2)
    except:
        residuals_sig = float('inf')

    # Fit Exponential (Standard QM)
    try:
        p0_exp = [0.5, 1, 0]
        popt_exp, _ = curve_fit(exponential, RADION_AMPS, integrity_scores, p0=p0_exp, maxfev=5000)
        residuals_exp = np.sum((integrity_scores - exponential(RADION_AMPS, *popt_exp))**2)
    except:
        residuals_exp = float('inf')
        
    print(f"Sigmoid Fit Error (Soliton): {residuals_sig:.4f}")
    print(f"Exponential Fit Error (Standard): {residuals_exp:.4f}")

    # Verdict
    print("\n" + "="*40)
    if residuals_sig < residuals_exp:
        print("VERDICT: DATA FAVORS SOLITONIC MODEL")
        print("Observation: Decay exhibits a critical threshold (Sigmoidal).")
        print("Implication: Topological protection persisted against noise.")
    else:
        print("VERDICT: DATA FAVORS STANDARD QM")
        print("Observation: Decay is smooth and immediate (Exponential).")
        print("Implication: No topological protection observed.")
    print("="*40 + "\n")

    # 5. Visualize
    plt.figure(figsize=(10, 6))
    
    # Plot Data
    plt.plot(RADION_AMPS, integrity_scores, 'ko', label='IBM Hardware Data', markersize=8)
    
    # Plot Fits
    x_smooth = np.linspace(0, 3.0, 100)
    if residuals_sig != float('inf'):
        plt.plot(x_smooth, sigmoid(x_smooth, *popt_sig), '-', color='#dc267f', linewidth=2, label='Soliton Theory (Sigmoid)')
    if residuals_exp != float('inf'):
        plt.plot(x_smooth, exponential(x_smooth, *popt_exp), '--', color='#648fff', linewidth=2, label='Standard QM (Exponential)')

    plt.title(f"Soliton Stability Test (Job: {JOB_ID})")
    plt.xlabel("Radion Noise Strength (a.u.)")
    plt.ylabel("Domain Wall Integrity (P(1...0))")
    plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    filename = "soliton_test_result.png"
    plt.savefig(filename)
    print(f"Plot saved to: {filename}")
    plt.show()

if __name__ == "__main__":
    analyze_solitons()