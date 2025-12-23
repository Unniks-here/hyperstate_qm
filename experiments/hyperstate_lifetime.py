import numpy as np
import warnings
import sys
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Gate
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

# --- CONFIGURATION (UPDATE THIS!) ---
QUBIT = 26
OPTIMAL_STARK_AMP = 0.25   # <--- REPLACE with the best Amp from your previous plot!
STARK_FREQ_OFFSET = 20e6   # Keep same as before
BACKEND_NAME = "ibm_kyoto"

# T2 Echo Sweep: Measure how long it survives
DELAYS_US = np.linspace(0, 300, 15)  # Sweep up to 300us
DELAYS_SEC = DELAYS_US * 1e-6

# --- SETUP ---
warnings.filterwarnings("ignore")
service = QiskitRuntimeService()
try:
    backend = service.backend(BACKEND_NAME)
except:
    backend = service.least_busy(operational=True, simulator=False)
    
print(f"--- VERIFYING HYPERSTATE LIFETIME (Q{QUBIT}) ---")
print(f"Backend: {backend.name}")
print(f"Applying Protection Field: Amp={OPTIMAL_STARK_AMP}, Shift=20MHz")

# Check dt
dt = backend.target.dt if hasattr(backend.target, 'dt') else 4.5e-9

# --- PULSE BUILDER ---
# We need to import Pulse safely again
try:
    import qiskit.pulse as pulse
    from qiskit.pulse import DriveChannel, GaussianSquare
except ImportError:
    print("Error: Qiskit Pulse not found. Ensure you are in the 'stark_env'.")
    sys.exit(1)

def build_protected_delay(backend, qubit, duration_dt, amp, freq_offset):
    with pulse.build(backend=backend, name="Protected_Wait") as sched:
        d_chan = DriveChannel(qubit)
        if amp > 0:
            pulse.set_frequency(freq_offset, d_chan)
            
            # FIX: Ensure width is non-negative. 
            # Sigma=16 implies ~64 samples for rise/fall. 
            width = duration_dt - 64
            if width < 0: width = 0
            
            stark_pulse = GaussianSquare(duration=duration_dt, amp=amp, sigma=16, width=width)
            pulse.play(stark_pulse, d_chan)
            pulse.set_frequency(0, d_chan)
        else:
            pulse.delay(duration_dt, d_chan)
    return sched

# --- CIRCUIT GENERATION ---
circuits = []

for delay_sec in DELAYS_SEC:
    delay_dt = int(delay_sec / dt)
    delay_dt = delay_dt - (delay_dt % 16)
    
    # FIX: Min duration must be 128 (64 per half) to fit pulse edges
    if delay_dt < 128: delay_dt = 128 
    
    qc = QuantumCircuit(127, 1)
    
    # Hahn Echo Sequence: X90 -- Wait/2 -- X180 -- Wait/2 -- X90
    qc.sx(QUBIT)
    
    # 1st Protected Wait
    qc.delay(delay_dt//2, QUBIT, unit='dt')
    
    qc.x(QUBIT) # Echo Pulse
    
    # 2nd Protected Wait
    qc.delay(delay_dt//2, QUBIT, unit='dt')
    
    qc.sx(QUBIT)
    qc.measure(QUBIT, 0)
    
    # Attach Calibrations
    # We apply the Stark tone during BOTH wait periods
    sched_half = build_protected_delay(backend, QUBIT, delay_dt//2, OPTIMAL_STARK_AMP, STARK_FREQ_OFFSET)
    qc.add_calibration("delay", [QUBIT], sched_half, [delay_dt//2])
    
    circuits.append(qc)

print(f"Generated {len(circuits)} verification circuits.")

# --- SUBMIT ---
print("Submitting verification job...")
config = backend.configuration()
isa_circuits = transpile(
    circuits, 
    basis_gates=config.basis_gates,
    coupling_map=config.coupling_map,
    optimization_level=0, 
    initial_layout=[i for i in range(127)]
)

sampler = Sampler(mode=backend)
job = sampler.run([(c,) for c in isa_circuits])

print(f"\nVerification Job ID: {job.job_id()}")
print("When complete, plotting this data will reveal the NEW T2 lifetime.")