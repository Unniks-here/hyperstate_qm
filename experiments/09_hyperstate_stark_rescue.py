import sys
import numpy as np
import warnings

# --- 0. SUPPRESS NOISY WARNINGS ---
warnings.filterwarnings("ignore", category=DeprecationWarning, module="qiskit.pulse")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*add_calibration.*")

# --- 1. STRICT ENVIRONMENT CHECK ---
import qiskit
from packaging import version

current_ver = version.parse(qiskit.__version__)
required_max = version.parse("2.0.0")

print(f"Detected Qiskit Version: {current_ver}")

if current_ver >= required_max:
    print("CRITICAL ERROR: QISKIT VERSION INCOMPATIBLE. PLEASE DOWNGRADE TO <2.0")
    sys.exit(1)

# --- IMPORTS ---
try:
    import qiskit.pulse as pulse
    from qiskit.pulse import DriveChannel, GaussianSquare, Drag
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit import Gate, Parameter
    from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Session, Options
except ImportError as e:
    print(f"Missing Dependency: {e}")
    sys.exit(1)

# --- CONFIGURATION ---
QUBIT_TARGET = 26
STARK_FREQ_OFFSET = 20e6
AMP_SWEEP = np.linspace(0, 0.4, 11)
DELAY_TIME = 80e-6
BACKEND_NAME = "ibm_kyoto" 

print(f"\n--- PREPARING HARDWARE EXPERIMENT (Qubit {QUBIT_TARGET}) ---")
print("Mode: REAL HARDWARE ONLY")

# --- 2. CONNECT TO SERVICE ---
try:
    service = QiskitRuntimeService()
    try:
        backend = service.backend(BACKEND_NAME)
    except:
        print(f"Backend {BACKEND_NAME} not found. Finding least busy...")
        backend = service.least_busy(operational=True, simulator=False)
    print(f"Connected to backend: {backend.name}")
except Exception as e:
    print(f"Error connecting to IBM Quantum: {e}")
    sys.exit(1)

# --- 3. HARDWARE CAPABILITIES CHECK ---
if hasattr(backend, "num_qubits"):
    N_QUBITS = backend.num_qubits
else:
    N_QUBITS = 127
print(f"System Size: {N_QUBITS} Qubits")

# dt Detection
dt = None
if hasattr(backend, "target") and backend.target.dt is not None:
    dt = backend.target.dt
elif hasattr(backend, "configuration"):
    config = backend.configuration()
    if hasattr(config, "dt"):
        dt = config.dt

if dt is None:
    print("Warning: Could not fetch 'dt'. Assuming 4.5ns.")
    dt = 4.5e-9

print(f"System dt: {dt*1e9:.2f} ns")


def build_stark_delay_schedule(backend, qubit, duration_dt, stark_amp, stark_freq_offset):
    """
    Builds the Pulse Schedule for the Stark Shift.
    """
    with pulse.build(backend=backend, name=f"Stark_Delay_{stark_amp:.2f}") as sched:
        d_chan = DriveChannel(qubit)
        
        if stark_amp > 0:
            # 1. Shift Frequency
            pulse.set_frequency(stark_freq_offset, d_chan)
            
            # 2. Play Tone
            width = duration_dt - 64 
            if width < 0: width = 0
            
            stark_pulse = GaussianSquare(
                duration=duration_dt,
                amp=stark_amp,
                sigma=16,
                width=width
            )
            pulse.play(stark_pulse, d_chan)
            
            # 3. Reset Frequency
            pulse.set_frequency(0, d_chan)
        else:
            # Explicitly play delay instruction on channel for consistency
            pulse.delay(duration_dt, d_chan)
            
    return sched

# --- 4. GENERATE CIRCUITS ---
circuits = []
print("Generating Pulse-Calibrated Circuits...")

# Calculate Delay in dt once
delay_dt = int(DELAY_TIME / dt)
delay_dt = delay_dt - (delay_dt % 16) # Align to 16

for amp in AMP_SWEEP:
    qc = QuantumCircuit(N_QUBITS, 1) 
    
    # Sequence: X90 -> Delay(with Stark) -> X90 -> Measure
    qc.sx(QUBIT_TARGET)
    
    # FIX: Use standard 'delay' instruction to pass validation
    qc.delay(delay_dt, QUBIT_TARGET, unit='dt')
    
    qc.sx(QUBIT_TARGET)
    qc.measure(QUBIT_TARGET, 0)
    
    # Attach Calibration to the standard 'delay' instruction
    sched = build_stark_delay_schedule(backend, QUBIT_TARGET, delay_dt, amp, STARK_FREQ_OFFSET)
    
    # Note: 'delay' instruction params are [duration]
    qc.add_calibration("delay", [QUBIT_TARGET], sched, [delay_dt])
    
    circuits.append(qc)

print(f"Created {len(circuits)} circuits.")

# --- 5. SUBMIT TO HARDWARE ---
print("\n--- SUBMITTING JOB TO IBM QUANTUM ---")

try:
    from qiskit_ibm_runtime import SamplerV2
    print("Using SamplerV2 (Job Mode)...")
    
    # FIX: Manually pass coupling_map and basis_gates instead of 'backend=backend'
    # This prevents the 'ibm_dynamic_circuits' plugin error.
    config = backend.configuration()
    isa_circuits = transpile(
        circuits, 
        basis_gates=config.basis_gates,
        coupling_map=config.coupling_map,
        optimization_level=0, 
        initial_layout=[i for i in range(N_QUBITS)]
    )

    sampler = SamplerV2(mode=backend)
    job = sampler.run([(c,) for c in isa_circuits]) 
except ImportError:
    print("Using SamplerV1 (Job Mode)...")
    sampler = Sampler(backend=backend)
    job = sampler.run(circuits)

print(f"Job Submitted! ID: {job.job_id()}")
print(f"Track here: https://quantum.ibm.com/jobs/{job.job_id()}")
print("\n>>> NEXT STEP: Copy the ID above and paste it into 'experiments/10_stark_results_analysis.py'")