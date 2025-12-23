import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- CONFIGURATION ---
L = 20.0            # Length of the universe
N = 1000            # Resolution (Number of points)
k_true = 5.0        # The True "Winding Density" (Momentum) of the Helix
radius = 1.0        # Amplitude

# --- 1. GENERATE THE HYPERSTATE ---
x = np.linspace(0, L, N)
# The 3D Helix: A * exp(i * k * x)
# We use a complex number representation where Real=y, Imag=z
helix_complex = radius * np.exp(1j * k_true * x) 
y = np.real(helix_complex)
z = np.imag(helix_complex)

# --- 2. PROJECT TO 2D (THE WAVEFUNCTION) ---
# The Observer sees only the "Shadow" (Real part)
psi = y 

# --- 3. THE MATHEMATICAL PROOF (FFT) ---
# We calculate the Fourier Transform to find the "Momentum" content
fft_vals = np.fft.fft(psi)
fft_freqs = np.fft.fftfreq(N, d=(L/N)) * 2 * np.pi # Convert to angular wavenumber k

# Get the Power Spectrum (Magnitude squared)
power_spectrum = np.abs(fft_vals)**2

# We only need the positive half of the spectrum for visualization
pos_mask = fft_freqs > 0
k_vals = fft_freqs[pos_mask]
power = power_spectrum[pos_mask]

# --- 4. VISUALIZATION ---
fig = plt.figure(figsize=(14, 8))

# PLOT A: The 3D Reality
ax1 = fig.add_subplot(2, 2, 1, projection='3d')
ax1.plot(x, y, z, color='cyan', lw=2, label=f'Hyperstate (k={k_true})')
ax1.set_title("1. The Reality (3D Helix)")
ax1.set_xlabel('Space (x)')
ax1.set_ylabel('Real')
ax1.set_zlabel('Imag')
ax1.legend()

# PLOT B: The 2D Projection
ax2 = fig.add_subplot(2, 2, 2)
ax2.plot(x, psi, color='red', lw=2, label='Projected Wave')
ax2.set_title("2. The Observation (2D Shadow)")
ax2.set_xlabel('Space (x)')
ax2.set_ylabel('Amplitude')
ax2.grid(True, alpha=0.3)
ax2.legend()

# PLOT C: The Fourier Transform (The Proof)
ax3 = fig.add_subplot(2, 1, 2)
ax3.plot(k_vals, power, color='purple', lw=2)
ax3.set_title("3. The Mathematical Proof (Fourier Transform)")
ax3.set_xlabel('Winding Density / Momentum (k)')
ax3.set_ylabel('Spectral Power')
ax3.set_xlim(0, 10) # Zoom in on the relevant range
ax3.axvline(x=k_true, color='black', linestyle='--', label=f'True Helix Pitch ({k_true})')
ax3.fill_between(k_vals, power, color='purple', alpha=0.3)
ax3.text(k_true + 0.2, np.max(power)*0.8, "Momentum Spike matches Helix Pitch!", fontsize=12)
ax3.grid(True, alpha=0.3)
ax3.legend()

plt.tight_layout()
plt.show()