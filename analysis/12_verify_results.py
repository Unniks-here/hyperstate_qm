import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from qiskit_ibm_runtime import QiskitRuntimeService

# --- CONFIGURATION ---
# Job IDs from the recent run
JOB_IDS = [
    # "d558dgjht8fs73a0kj90", # Stark Rescue (failed)
    "d558dgrht8fs73a0kj9g",  # Solitonic Stability
    "d558jq9smlfc739ggnj0"   # Baseline (Defective Qubit 26)
]

def sigmoid(x, L, x0, k, b):
    """Models the critical stability threshold (Soliton)."""
    return L / (1 + np.exp(k * (x - x0))) + b

def exponential(x, a, b, c):
    """Models standard linear decoherence."""
    return a * np.exp(-b * x) + c

def verify_results():
    service = QiskitRuntimeService()
    
    for job_id in JOB_IDS:
        print(f"\n{'='*40}")
        print(f"Processing Job ID: {job_id}")
        print(f"{'='*40}")
        
        try:
            job = service.job(job_id)
        except Exception as e:
            print(f"Error fetching job {job_id}: {e}")
            continue

        # Wait for completion
        print("Checking status...")
        status = job.status()
        status_name = status.name if hasattr(status, "name") else str(status)
        print(f"Job Status: {status_name}")
        
        if status_name not in ["DONE", "COMPLETED", "JobStatus.DONE"]:
            print(f"Job is {status_name}. Waiting for completion...")
            try:
                job.wait_for_final_state()
            except Exception as e:
                print(f"Wait failed: {e}")
                continue
        
        # Get Results
        try:
            result = job.result()
        except Exception as e:
            print(f"Failed to retrieve results: {e}")
            continue
            
        num_circuits = len(result)
        print(f"Retrieved {num_circuits} circuits.")

        # Stark: 11 circuits (0.0 to 0.4 sweep)
        # Soliton: 15 circuits (0 to pi sweep)
        # Baseline Defective: 21 circuits (0 to 100us)
        if num_circuits == 11:
            analyze_stark_rescue(result)
        elif num_circuits == 15:
            analyze_soliton_stability(result)
        elif num_circuits == 21:
            analyze_baseline_defective(result)
        else:
            print(f"Unknown experiment format ({num_circuits} circuits). Skipping specific analysis.")
            # analyze_generic(result)

def analyze_baseline_defective(result):
    print("\n--- ANALYZING BASELINE (DEFECTIVE QUBIT) ---")
    delays = np.linspace(0, 100, 21)
    probs = []
    
    for pub_result in result:
        try:
            counts = pub_result.data.meas.get_counts()
        except AttributeError:
             keys = list(pub_result.data.keys())
             counts = getattr(pub_result.data, keys[0]).get_counts()

        total = sum(counts.values())
        probs.append(counts.get('1', 0) / total)

    # Simple Exponential Fit to find T2*
    try:
        popt, _ = curve_fit(exponential, delays, probs, p0=[0.5, 0.1, 0.5], maxfev=5000)
        t2_star = 1/popt[1] if popt[1] > 0 else 0
        print(f"Estimated T2*: {t2_star:.2f} microseconds")
        
        if t2_star < 20:
            print("VERDICT: CONFIRMED DEFECTIVE. Coherence time is critically low.")
        else:
            print("VERDICT: OPERATIONAL. Qubit shows standard coherence.")
    except:
        print("Fitting failed.")

    plt.figure(figsize=(8, 5))
    plt.plot(delays, probs, 'o-', color='gray', label='Baseline Decay')
    if 'popt' in locals():
        x_smooth = np.linspace(0, 100, 100)
        plt.plot(x_smooth, exponential(x_smooth, *popt), 'k--', label=f'Fit (T2*={t2_star:.1f}us)')
    
    plt.axhline(0.5, color='red', linestyle='--', label='Mixed State (0.5)')
    plt.title(f"Baseline: Qubit 26 Free Decay")
    plt.xlabel("Delay (us)")
    plt.ylabel("P(1)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    try:
        plt.savefig("baseline_defective_result.png")
        print("Saved plot to 'baseline_defective_result.png'")
    except:
        pass

def analyze_stark_rescue(result):
    print("\n--- ANALYZING STARK RESCUE ---")
    amps = np.linspace(0, 0.4, 11)
    probs = []
    
    for pub_result in result:
        # SamplerV2: data.<register_name>.get_counts()
        # We assume register is 'meas' (default for measure_all)
        try:
            counts = pub_result.data.meas.get_counts()
        except AttributeError:
             # Fallback if register name differs (e.g. 'c' or 'clbits')
             # Try first available attribute that looks like a BitArray
             keys = list(pub_result.data.keys())
             counts = getattr(pub_result.data, keys[0]).get_counts()

        total = sum(counts.values())
        probs.append(counts.get('1', 0) / total)

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(amps, probs, 'o-', color='#648fff', label='Q26 Stark Sweep')
    plt.axhline(0.5, color='red', linestyle='--', label='Decoherence Limit')
    plt.title("Verification: Stark Shift Phase Recovery")
    plt.xlabel("Drive Amplitude (a.u.)")
    plt.ylabel("P(1)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save instead of show (headless env) or show if interactive
    try:
        plt.savefig("stark_rescue_results.png")
        print("Saved plot to 'stark_rescue_results.png'")
    except:
        pass
    # plt.show() # Optional
    
    peak_visibility = max(probs) - min(probs)
    print(f"Maximum Fringe Visibility: {peak_visibility:.4f}")
    if peak_visibility > 0.2:
        print("VERDICT: SUCCESS. Stark drive successfully restored coherence.")
    else:
        print("VERDICT: FAILURE. Qubit remained in decohered state (or visibility low).")

def analyze_soliton_stability(result):
    print("\n--- ANALYZING SOLITONIC STABILITY ---")
    lambdas = np.linspace(0, np.pi, 15)
    integrity = []
    
    for pub_result in result:
        try:
            counts = pub_result.data.meas.get_counts()
        except AttributeError:
             keys = list(pub_result.data.keys())
             counts = getattr(pub_result.data, keys[0]).get_counts()

        total = sum(counts.values())
        
        # Domain wall integrity: Fraction of shots where Q4=1 and Q0=0
        # Bitstrings are Little-Endian in Qiskit (q4...q0)
        # We want q4='1' and q0='0'.
        # String: "1xxxx0"
        valid = 0
        for bitstr, count in counts.items():
            if bitstr.startswith('1') and bitstr.endswith('0'):
                valid += count
        integrity.append(valid / total)

    # Statistical Fitting
    popt_sig, popt_exp = None, None
    try:
        popt_sig, _ = curve_fit(sigmoid, lambdas, integrity, p0=[0.5, 1.5, 5, 0], maxfev=5000)
        sse_sig = np.sum((integrity - sigmoid(lambdas, *popt_sig))**2)
        
        popt_exp, _ = curve_fit(exponential, lambdas, integrity, p0=[0.5, 1, 0], maxfev=5000)
        sse_exp = np.sum((integrity - exponential(lambdas, *popt_exp))**2)
        
        print(f"Sigmoidal SSE: {sse_sig:.6f}")
        print(f"Exponential SSE: {sse_exp:.6f}")
        
        if sse_sig < sse_exp:
            print("VERDICT: SOLITONIC MODEL VERIFIED. The data shows a critical stability plateau.")
        else:
            print("VERDICT: STANDARD DECAY. No evidence of topological protection.")
            
    except Exception as e:
        print(f"Fitting failed (noise or data shape): {e}")

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(lambdas, integrity, 'ko', label='Hardware Data')
    
    x_smooth = np.linspace(0, np.pi, 100)
    if popt_sig is not None:
        plt.plot(x_smooth, sigmoid(x_smooth, *popt_sig), 'r-', label='Sigmoidal Fit')
    if popt_exp is not None:
        plt.plot(x_smooth, exponential(x_smooth, *popt_exp), 'b--', label='Exponential Fit', alpha=0.5)

    plt.title("Verification: Solitonic Critical Threshold")
    plt.xlabel("Noise Strength (Lambda)")
    plt.ylabel("Domain Wall Integrity")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    try:
        plt.savefig("soliton_test_result.png")
        print("Saved plot to 'soliton_test_result.png'")
    except:
        pass

if __name__ == "__main__":
    verify_results()