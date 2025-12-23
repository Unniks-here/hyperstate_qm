from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_experiments.library import T2Ramsey
# UPDATED: Use BatchExperiment (Sequential) instead of ParallelExperiment (Simultaneous)
# This fixes the "Zero Results" unpacking error while still using a single job.
from qiskit_experiments.framework import BatchExperiment
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
import numpy as np
import sys

# --- 1. CONNECT ---
print("Connecting to IBM Quantum...")
backend = None

try:
    # Load the saved account automatically
    service = QiskitRuntimeService()
    
    # Find the least busy real hardware
    print("Searching for available quantum computers...")
    # operational=True means it's working, simulator=False means real atoms
    # min_num_qubits=5 ensures we have enough room for the test
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f">>> SUCCESS: Using Real Hardware: {backend.name}")
    print(f"    Qubits available: {backend.num_qubits}")
    print(f"    Pending jobs in queue: {backend.status().pending_jobs}")
    
except Exception as e:
    print(f"Warning: Could not connect to real hardware ({e})")
    print(">>> FALLBACK: Using AerSimulator (Local Simulation)")
    backend = AerSimulator()

# --- 2. CONFIGURATION ---
n_qubits = backend.num_qubits
# Limit to 5 qubits max for the test to keep it fast/manageable
qubits_to_test = list(range(min(5, n_qubits)))
print(f"Running Experiment on Qubits: {qubits_to_test}")

# Experiment Parameters
# T2* Ramsey delays
delays = np.linspace(0, 50e-6, 40) # 0 to 50 microseconds
osc_freq = 100e3                   # 100 kHz oscillation

# --- 3. BUILD EXPERIMENTS ---
experiments = []
for q in qubits_to_test:
    # Create T2* Ramsey experiment for each qubit
    exp = T2Ramsey(physical_qubits=[q], delays=delays, osc_freq=osc_freq)
    experiments.append(exp)

# UPDATED: Bundle using BatchExperiment for robust data retrieval
print("Bundling experiments into a Batch (Single Job)...")
combined_exp = BatchExperiment(experiments)

# --- 4. EXECUTE ---
print("Starting execution... (If using real hardware, this enters the queue)")
# Set shots=1000 for decent statistics
# Note: For real hardware, this blocks until the job is done.
try:
    exp_data = combined_exp.run(backend=backend, shots=1000)
    
    # Check if we have job IDs (ExperimentData uses 'job_ids' property, which is a list)
    # Wait briefly to ensure submission if async
    try:
        current_job_ids = exp_data.job_ids
        print(f"Job submitted! IDs: {current_job_ids}")
    except AttributeError:
        # Fallback for different library versions
        print("Job submitted (ID retrieval skipped).")

    print("Waiting for results (this may take minutes to hours depending on the queue)...")
    exp_data.block_for_results()
except Exception as e:
    print(f"Execution failed: {e}")
    sys.exit(1)

# --- 5. ANALYZE ---
print("Analyzing data...")

# --- DEBUGGING / ERROR CHECKING ---
status = exp_data.status()
print(f"Experiment Status: {status}")

# Check for backend errors
if status.name in ['ERROR', 'CANCELLED']:
    print("!!! Job Failed on Server. Error messages:")
    for error in exp_data.errors():
        print(f"  - {error}")
    # If using real hardware, sometimes specific gates aren't supported
    print("\nTroubleshooting Tip: If error is 'Instruction not supported', try a different backend.")
    sys.exit(1)

# Safely retrieve child data
try:
    child_data_list = exp_data.child_data()
    print(f"Number of sub-experiments returned: {len(child_data_list)}")
except Exception as e:
    print(f"Could not retrieve child data list: {e}")
    child_data_list = []

t2_results = []
freq_shifts = []

if not child_data_list:
    print("CRITICAL ERROR: The experiment completed but returned ZERO results.")
    print("This often happens if the 'ParallelExperiment' wrapper failed to unpack data.")
else:
    for i, q in enumerate(qubits_to_test):
        if i >= len(child_data_list):
            print(f"Qubit {q}: No data returned.")
            continue

        try:
            # Access the child experiment data from the list
            child_result = child_data_list[i]
            
            # Check fit status
            t2_fit = child_result.analysis_results("T2star")
            freq_fit = child_result.analysis_results("Frequency")
            
            if t2_fit and freq_fit:
                t2_val = t2_fit.value.n
                freq_val = freq_fit.value.n
                
                t2_results.append(t2_val)
                freq_shifts.append(freq_val)
                print(f"Qubit {q}: T2* = {t2_val*1e6:.2f} µs | Freq Shift = {freq_val/1e3:.2f} kHz")
            else:
                print(f"Qubit {q}: Fit failed (bad data).")
                
        except Exception as e:
            print(f"Error analyzing Qubit {q}: {e}")

# --- 6. PLOT ---
if len(t2_results) > 1:
    try:
        plt.figure(figsize=(10, 6))
        plt.scatter(freq_shifts, t2_results, c='red', s=120, edgecolors='black', label='Qubit Data')
        
        plt.xlabel("Frequency Shift (Gradient Proxy) [Hz]", fontsize=12)
        plt.ylabel("Coherence Time T2* [s]", fontsize=12)
        plt.title(f"Gradient Test on {backend.name}", fontsize=14)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        filename = "gradient_test_results.png"
        plt.savefig(filename)
        print(f"Plot saved as {filename}")
    except Exception as e:
        print(f"Plotting failed: {e}")
else:
    print("Not enough successful data points to plot.")