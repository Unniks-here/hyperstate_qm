# Pulse-Level Hamiltonian Engineering for Qubit Resurrection

**A Software-Defined Approach to Hardware Resilience in Superconducting Processors**

## Scientific Abstract
This project investigates non-linear stability mechanisms in open quantum systems, specifically deploying **Continuous Hamiltonian Engineering** to simulate topological protection on noisy intermediate-scale quantum (NISQ) hardware.

We successfully demonstrate that spectrally defective qubits (e.g., those coupled to Two-Level System defects) can be "resurrected" by applying off-resonant AC Stark drives, dynamically decoupling the qubit from its environment. Furthermore, we realize a 1D spin chain encoding a topological domain wall, observing a distinct **Solitonic Stability Plateau** (SSE ≈ 0.0008) against correlated noise, in contrast to standard exponential decay.

## Technical Novelty: Instruction-Level Calibration Override
A core contribution of this work is the development of the **Instruction-Level Calibration Override** technique. As cloud-based quantum providers (like IBM Quantum) move towards abstract primitives (Sampler/Estimator V2), direct pulse-level control is often restricted.

This technique bypasses ISA constraints by legally injecting arbitrary continuous waveforms (GaussianSquare) into the compiler pipeline via the `calibrations` attribute, allowing for advanced Floquet engineering without requiring low-level hardware access privileges.

## Hardware Requirements
- **Platform**: IBM Quantum
- **Processors**: Validated on **Eagle** (e.g., `ibm_kyoto`) and **Heron** (e.g., `ibm_torino`) processors.
- **Qiskit Support**: Designed for `qiskit-ibm-runtime` (Primitives V2) with legacy Pulse support (< 2.0).

## Repository Structure
```
/root
├── analysis/       # Data processing and verification tools
├── assets/         # Experimental results and figures
├── experiments/    # Pulse-level control scripts
├── paper/          # LaTeX manuscript
└── stark_env/      # Virtual environment (ignored in git)
```

## Quick Start

### 1. Environment Setup
The project requires a specific environment to handle legacy Pulse definitions alongside modern Runtime Primitives.

```bash
# Create virtual environment
python3 -m venv stark_env
source stark_env/bin/activate

# Install dependencies (ensure Qiskit < 2.0)
pip install -r requirements.txt
```

### 2. Running Experiments

**Experiment I: Defective Qubit Baseline**
Establish the T2* decay of a defective qubit.
```bash
python experiments/01_baseline_defective.py
```

**Experiment II: Phase Resurrections (Stark)**
Apply the rescue drive.
```bash
python experiments/09_hyperstate_stark_rescue.py
```

**Experiment III: Solitonic Stability**
Verify topological protection on a spin chain.
```bash
python experiments/11_hyperstate_verification.py
```

### 3. Verification
Analyze the results using the provided toolset (handles multiple experiment types):
```bash
python analysis/12_verify_results.py
```

## Sample Results (Validated on Hardware)
The following Job IDs correspond to the data presented in the manuscript (run on `ibm_torino`):

- **Stark Rescue Sweep**: `d558ctpsmlfc739ggh9g`
- **Solitonic Chain**: `d558cu0nsj9s73b2iflg`
- **Baseline One-Body Decay**: `d558jq9smlfc739ggnj0`

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
