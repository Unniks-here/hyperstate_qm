import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

# --- CONFIGURATION ---
# We need a linear chain of 5 qubits. 
# On ibm_kyoto/torino, typically 0-1-2-3-4 are connected.
CHAIN = [0, 1, 2, 3, 4] 
# The "Radion" Noise Strength (Sweep)
RADION_AMPS = np.linspace(0, 3.0, 15)
BACKEND_NAME = "ibm_kyoto"

# --- 1. SETUP ---
service = QiskitRuntimeService()
try:
    backend = service.backend(BACKEND_NAME)
except:
    backend = service.least_busy(operational=True, simulator=False)

print(f"--- SOLITONIC PROBABILITY TEST ---")
print(f"Targeting Soliton Chain: {CHAIN}")
print("Hypothesis: Solitons resist noise until a critical 'Radion' threshold.")

# --- 2. THE SOLITON CIRCUIT ---
def build_soliton_circuit(radion_strength):
    # FIX: Create circuit with exact number of qubits (5), not 127.
    # This prevents InvalidLayoutError during transpilation.
    n_qubits = len(CHAIN)
    qc = QuantumCircuit(n_qubits, n_qubits)
    
    # A. CREATE THE SOLITON (The "Kink")
    # A topological soliton in a spin chain is a Domain Wall.
    # Left side |0>, Right side |1>. The "Kink" is in the middle.
    # We create a "soft" kink using rotations to mimic a continuous field.
    
    # We operate on logical qubits 0..4. Transpiler maps these to CHAIN physical qubits.
    qc.ry(0, 0)          # 0
    qc.ry(np.pi/4, 1)    # 45 deg
    qc.ry(np.pi/2, 2)    # 90 deg (The singularity/Kink)
    qc.ry(3*np.pi/4, 3)  # 135 deg
    qc.ry(np.pi, 4)      # 180 deg
    
    # B. INJECT RADION FLUCTUATIONS (Synthetic 5D Noise)
    # Standard decoherence is random. Radion fluctuations are Correlated.
    # We apply a ZZ interaction between neighbors that scales with 'radion_strength'.
    # This simulates the "warping" of the metric between lattice sites.
    
    for i in range(n_qubits-1):
        # RZZ mimics the stress on the brane metric
        qc.rzz(radion_strength, i, i+1)
        
        # Add a transverse kick (The "Breather" mode)
        qc.rx(radion_strength * 0.5, i)

    # C. MEASURE DOMAIN WALL INTEGRITY
    # We measure the parity of the chain.
    for i in range(n_qubits):
        qc.measure(i, i)
        
    return qc

# --- 3. GENERATE CIRCUITS ---
circuits = []
for amp in RADION_AMPS:
    qc = build_soliton_circuit(amp)
    circuits.append(qc)

print(f"Generated {len(circuits)} soliton stress-test circuits.")

# --- 4. SUBMIT ---
print("Submitting to Braneworld Simulation (IBM Hardware)...")
config = backend.configuration()

# Manual transpile to keep our chain structure intact
# We extract constraints manually to avoid 'ibm_dynamic_circuits' plugin error
isa_circuits = transpile(
    circuits, 
    basis_gates=config.basis_gates,
    coupling_map=config.coupling_map,
    optimization_level=1, # Light optimization allowed
    initial_layout=CHAIN  # Map strictly to our chain
)

sampler = Sampler(mode=backend)
job = sampler.run([(c,) for c in isa_circuits])

print(f"Job ID: {job.job_id()}")
print("Analyze this job to see if the Soliton decays linearly (Standard QM) or critically (Solitonic Theory).")