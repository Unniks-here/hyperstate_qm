import numpy as np
import sys
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

# --- CONFIGURATION ---
QUBIT_TARGET = 26
# Simple Ramsey experiment: sweeping from 0 to 100 microseconds
DELAY_TIMES_US = np.linspace(0, 100, 21) 
BACKEND_NAME = "ibm_kyoto" 

print(f"--- Establishing 'Dead' Baseline for Qubit {QUBIT_TARGET} ---")

# 1. CONNECT TO IBM QUANTUM
try:
    service = QiskitRuntimeService()
    try:
        backend = service.backend(BACKEND_NAME)
        print(f"Connected to: {backend.name}")
    except Exception as e:
        print(f"Warning: {BACKEND_NAME} not found or error: {e}")
        print("Finding least busy alternative for baseline...")
        backend = service.least_busy(simulator=False, operational=True)
        print(f"Fallback connected to: {backend.name}")

except Exception as e:
    print(f"Connection Error: {e}")
    sys.exit(1)

# dt Detection
dt = backend.target.dt if hasattr(backend.target, 'dt') else 4.5e-9

# 2. GENERATE BASELINE CIRCUITS (No Stark Drive)
circuits = []
for delay_us in DELAY_TIMES_US:
    qc = QuantumCircuit(backend.num_qubits, 1)
    
    # Standard Ramsey Sequence: X90 -> Delay -> X90
    qc.sx(QUBIT_TARGET)
    
    # Standard delay without any protection field
    delay_dt = int((delay_us * 1e-6) / dt)
    if delay_dt > 0:
        qc.delay(delay_dt, QUBIT_TARGET, unit='dt')
    
    qc.sx(QUBIT_TARGET)
    qc.measure(QUBIT_TARGET, 0)
    circuits.append(qc)

print(f"Created {len(circuits)} baseline circuits.")

# 3. TRANSPILE & SUBMIT
config = backend.configuration()
# Using Optimization level 0 to prevent the compiler from altering the circuit structure
isa_circuits = transpile(
    circuits, 
    backend=backend,
    optimization_level=0,
    initial_layout=list(range(backend.num_qubits))
)

sampler = Sampler(mode=backend)
job = sampler.run([(c,) for c in isa_circuits], shots=4096)

print(f"\nBaseline Job ID: {job.job_id()}")
print("Once this experiment completes, P(1) is expected to decay rapidly toward 0.5.")
print("This will confirm that the qubit is 'defective' or spectrally compromised.")