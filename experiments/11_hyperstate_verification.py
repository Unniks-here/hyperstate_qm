import sys
import numpy as np
import warnings
from packaging import version
import qiskit

# --- VERSION CHECK ---
current_ver = version.parse(qiskit.__version__)
required_max = version.parse("2.0.0")

if current_ver >= required_max:
    print(f"CRITICAL ERROR: Qiskit Version {current_ver} detected.")
    print("This experiment requires Qiskit Pulse, which was removed or altered in Qiskit 2.0.")
    print("Please use an environment with Qiskit < 2.0 (e.g., 'pip install qiskit<2.0').")
    sys.exit(1)

from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
import qiskit.pulse as pulse
from qiskit.pulse import DriveChannel, GaussianSquare

# --- CONFIGURATION ---
BACKEND_NAME = "ibm_kyoto" 
TARGET_QUBIT = 26
CHAIN_QUBITS = [24, 25, 26, 27, 28] # 5-qubit chain
STARK_AMPS = np.linspace(0, 0.4, 11)
SOLITON_LAMBDAS = np.linspace(0, np.pi, 15)
DELAY_DURATION_DT = 4504 # ~1us at 4.5ns dt, aligned to 16 samples

def get_stark_schedule(backend, qubit_index, amp, duration_dt, freq_shift=20e6):
    """
    Creates the pulse schedule for the Stark Rescue.
    Uses 'qubit_index' to define the channel.
    IMPORTANT: When attaching to a logic circuit that will be transpiled, 
    'qubit_index' MUST be the PHYSICAL qubit index (e.g. TARGET_QUBIT)
    because basic transpilation does NOT remap pulse channels in schedules.
    """
    with pulse.build(backend=backend, name=f"stark_pulse_{amp:.2f}") as stark_sched:
        # FIX: Use DriveChannel class directly to avoid NotImplementedError 
        # on some backend objects that don't expose .drive_channel()
        chan = DriveChannel(qubit_index)
        
        if amp > 0:
            # Apply the frequency shift (The "Rescue" mechanism)
            pulse.set_frequency(freq_shift, chan)
            
            # GaussianSquare to minimize leakage
            # Width must be >= 0
            sigma = 64
            width = duration_dt - (4 * sigma)
            if width < 0: width = 0
            
            pulse.play(GaussianSquare(
                duration=duration_dt,
                amp=amp,
                sigma=sigma,
                width=width
            ), chan)
            
            # Reset frequency
            pulse.set_frequency(0, chan)
        else:
            pulse.delay(duration_dt, chan)
            
    return stark_sched

def build_retest_circuits(backend):
    """
    Builds transpiled (ISA) circuits for both experiments.
    """
    print("Building and Transpiling Circuits...")
    
    # --- EXPERIMENT I: STARK RESCUE SWEEP ---
    stark_circuits = []
    
    # We use a 1-qubit logical circuit, mapped to TARGET_QUBIT
    for a in STARK_AMPS:
        qc = QuantumCircuit(1)
        qc.h(0) 
        
        # We use 'delay' as the instruction to attach calibration to
        # NOTE: In V2/ISA, we generally attach to a custom gate or standard gate.
        # Attaching to 'delay' requires careful handling.
        qc.delay(DELAY_DURATION_DT, 0, unit='dt')
        
        qc.h(0) 
        qc.measure_all()
        
        # Helper: Build schedule for PHYSICAL channel (TARGET_QUBIT)
        # We attach this schedule (which plays on physical wire 26) to logical instruction on qubit 0.
        # When transpiled 0->26, the instruction is now on 26, matching the physical schedule.
        sched = get_stark_schedule(backend, TARGET_QUBIT, a, DELAY_DURATION_DT)
        
        # Attach to logical qubit 0
        qc.add_calibration("delay", [0], sched, [DELAY_DURATION_DT])
        
        stark_circuits.append(qc)

    # --- EXPERIMENT II: SOLITONIC STABILITY ---
    soliton_circuits = []
    
    for l in SOLITON_LAMBDAS:
        qc = QuantumCircuit(len(CHAIN_QUBITS)) # Logical 0..4
        
        # 1. State Prep: Domain Wall Gradient
        for i in range(len(CHAIN_QUBITS)):
            qc.ry(i * np.pi/4, i)
            
        # 2. Correlated ZZ Noise Injection
        for i in range(len(CHAIN_QUBITS)-1):
            qc.rzz(l, i, i+1)
        
        qc.measure_all()
        soliton_circuits.append(qc)
        
    print("Fetching backend configuration for manual transpilation...")
    # FIX: Avoid 'ibm_dynamic_circuits' plugin error by passing config manually
    # instead of 'backend=backend'.
    try:
        config = backend.configuration()
        bg = config.basis_gates
        cm = config.coupling_map
    except AttributeError:
        # Fallback for V2 or other backends if configuration() is missing
        print("Warning: backend.configuration() missing, using backend.target...")
        bg = backend.target.operation_names
        cm = backend.coupling_map

    # Transpile Stark Circuits
    stark_isa = transpile(
        stark_circuits,
        basis_gates=bg,
        coupling_map=cm,
        initial_layout=[TARGET_QUBIT],
        optimization_level=0 # Preserve timing/structure
    )
    
    # Transpile Soliton Circuits
    soliton_isa = transpile(
        soliton_circuits,
        basis_gates=bg,
        coupling_map=cm,
        initial_layout=CHAIN_QUBITS, # Map logical 0..4 -> 24..28
        optimization_level=1
    )
    
    return stark_isa, soliton_isa

# --- EXECUTION ---
if __name__ == "__main__":
    service = QiskitRuntimeService()
    
    try:
        backend = service.backend(BACKEND_NAME)
        print(f"Connected to: {BACKEND_NAME}")
    except Exception as e:
        print(f"Warning: {BACKEND_NAME} not found or error: {e}")
        print("Using least busy...")
        backend = service.least_busy(simulator=False, operational=True)
        print(f"Fallback: {backend.name}")

    if TARGET_QUBIT >= backend.num_qubits:
        print(f"CRITICAL: Target {TARGET_QUBIT} out of range for {backend.name} ({backend.num_qubits}).")
        # Fallback logic if needed, or exit
        sys.exit(1)

    stark_isa, soliton_isa = build_retest_circuits(backend)
    
    sampler = SamplerV2(mode=backend)
    
    print(f"\nSubmitting Retest Jobs to {backend.name}...")
    
    # Submit Stark Sweep
    # V2 run takes a list of (circuit, parameter_values, shots) tuples or just list of pubs
    # Pub = (circuit, [shots])
    try:
        job_stark = sampler.run([(c, ) for c in stark_isa], shots=4096)
        print(f"Stark Rescue Job ID: {job_stark.job_id()}")
    except Exception as e:
        print(f"Stark Job Failed: {e}")

    # Submit Soliton Chain
    try:
        job_soliton = sampler.run([(c, ) for c in soliton_isa], shots=8192)
        print(f"Solitonic Stability Job ID: {job_soliton.job_id()}")
    except Exception as e:
        print(f"Soliton Job Failed: {e}")
        
    print("\nRetest submitted. Track jobs online.")