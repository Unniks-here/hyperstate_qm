# Hyperstate-QM: A Deterministic Geometric Interpretation of Quantum Mechanics

**Hyperstate-QM** is an open-source physics engine and educational toy model that simulates a "Psi-Epistemic" interpretation of Quantum Mechanics.

It challenges the standard view of the wavefunction as a fundamental mathematical abstraction by proposing a concrete geometric origin: **The wavefunction is the 2D projection (shadow) of a higher-dimensional 3D Helix (Hyperstate).**

## 🌌 The Philosophy

This project draws inspiration from several historical and philosophical ideas:

*   **Plato's Cave:** Just as the prisoners in Plato's cave mistake shadows for reality, standard QM might be mistaking the 2D "shadow" (the wavefunction) for the full 3D reality (the Hyperstate).
*   **David Bohm's Implicate Order:** The idea that there is a deeper, hidden order to the universe that we cannot directly perceive.
*   **Kaluza-Klein Theory:** The notion that higher spatial dimensions can explain fundamental forces.

In this model:
*   **Superposition** is simply the geometry of a helix. It looks like a wave from the side, but it's a solid object in 3D.
*   **Collapse** is the geometric act of slicing this cylinder at a specific, random phase angle.
*   **Uncertainty** arises because you cannot simultaneously define the winding density (momentum) and a specific slice point (position) without losing information about the other.

## 📐 The Math

The core mathematical definition of the **Hyperstate** ($\Phi$) is a complex helix winding around a cylinder:

$$
\Phi(x) = A \cdot e^{i(kx - \omega t + \theta)}
$$

Where:
*   $x$: Spatial coordinate
*   $A$: Radius of the cylinder (Amplitude)
*   $k$: Momentum (Winding density)
*   $\omega$: Frequency
*   $\theta$: The hidden variable (Phase orientation)

The **Observed Reality** ($\Psi$), which we call the wavefunction in standard QM, is merely the projection of this Hyperstate onto our observable plane (the Real axis):

$$
\Psi(x) = \text{Re}(\Phi(x)) = A \cdot \cos(kx - \omega t + \theta)
$$

## 📦 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Unniks-here/hyperstate_qm.git
    cd hyperstate_qm
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

The project comes with three experiments to visualize the theory:

### 1. Superposition (The Helix)
Visualizes the 3D Hyperstate and its 2D Shadow side-by-side.
```bash
python experiments/01_superposition.py
```

### 2. Collapse (The Slice)
Simulates the "measurement" process as taking a random phase slice of the cylinder. Shows how different hidden variables ($\theta$) lead to different observed outcomes.
```bash
python experiments/02_collapse.py
```

### 3. Interference (Double Slit)
Simulates interference by adding two helices together. The 3D addition creates a complex geometric shape, which projects down to the familiar "beat" or interference pattern.
```bash
python experiments/03_double_slit.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Disclaimer: This is a "Geometric Toy Model" intended for educational visualization and philosophical exploration. It is not a replacement for standard Quantum Mechanics.*
