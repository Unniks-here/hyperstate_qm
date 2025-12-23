import numpy as np
import matplotlib.pyplot as plt
from qiskit_ibm_runtime import QiskitRuntimeService

# --- CONFIGURATION ---
# PASTE YOUR NEW JOB ID HERE (From Experiment 09 output)
JOB_ID = "d553n9bht8fs73a0fvf0"  
QUBIT_TARGET = 26
AMP_SWEEP = np.linspace(0, 0.4, 11) # Must match the experiment script

def analyze_results():
    if JOB_ID == "INSERT_NEW_JOB_ID_HERE" or not JOB_ID:
        print("ERROR: Please update the 'JOB_ID' variable in the script with your new Job ID.")
        return

    print(f"--- FETCHING JOB: {JOB_ID} ---")
    
    # 1. Retrieve Job
    try:
        service = QiskitRuntimeService()
        job = service.job(JOB_ID)
    except Exception as e:
        print(f"Error connecting to service: {e}")
        return

    # 2. Check Status
    try:
        status = job.status()
        # Robustly handle status (can be Enum or String depending on Qiskit version)
        status_name = status if isinstance(status, str) else status.name
        print(f"Job Status: {status_name}")
        
        if status_name == "ERROR":
            print("\n!!! JOB FAILED !!!")
            try:
                print(f"Error Message: {job.error_message()}")
            except:
                print("Check IBM Quantum Dashboard for error details.")
            return

        if status_name not in ["DONE", "COMPLETED"]:
            print("Job is not finished yet. Please wait and try again later.")
            try:
                print(f"Queue Position: {job.metrics().get('position_in_queue', 'Unknown')}")
            except:
                pass
            return
            
    except Exception as e:
        print(f"Could not fetch job status. The ID might be wrong or the job doesn't exist. Error: {e}")
        return

    # 3. Get Data
    print("Downloading results...")
    result = job.result()
    
    # Handle SamplerV2 Result Structure
    probabilities = []
    
    # Iterate through each result item (each point in the sweep)
    for i, pub_result in enumerate(result):
        try:
            # Try to get counts dictionary
            counts = pub_result.data.c.get_counts() 
        except AttributeError:
            # Fallback for standard measure name
            counts = pub_result.data.meas.get_counts()
            
        # Calculate Probability of |1>
        total_shots = sum(counts.values())
        p1 = counts.get('1', 0) / total_shots
        probabilities.append(p1)

    # 4. Visualize
    print("\n--- ANALYZING HYPERSTATE PROTECTION ---")
    print("If Qubit 26 is 'Dead' (T2 ~ 30us), the signal should be flat (0.5) at 80us delay.")
    print("If Stark Shift works, we expect high-contrast oscillations (Ramsey Fringes).")
    
    plt.figure(figsize=(10, 6))
    plt.plot(AMP_SWEEP, probabilities, 'o-', color='#648fff', linewidth=2, label=f'Q{QUBIT_TARGET} (80us Delay)')
    
    # Add theoretical "Dead" baseline
    plt.axhline(0.5, color='gray', linestyle='--', label='Dead/Decayed Baseline')
    
    plt.title(f"Stark Shift Rescue Experiment (Job: {JOB_ID})")
    plt.xlabel("Stark Drive Amplitude (a.u.)")
    plt.ylabel("Probability |1>")
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    filename = "stark_rescue_results.png"
    plt.savefig(filename)
    print(f"\nPlot saved to: {filename}")
    plt.show()

if __name__ == "__main__":
    analyze_results()