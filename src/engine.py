import numpy as np

class HyperstateHelix:
    """
    Represents the higher-dimensional 3D Helix (Hyperstate).
    Φ(x) = A * exp(i(kx - ωt + θ))
    """
    def __init__(self, k=1.0, omega=1.0, amplitude=1.0, phase=0.0):
        self.k = k  # Momentum (Winding density)
        self.omega = omega  # Frequency
        self.amplitude = amplitude  # Radius of the cylinder
        self.phase = phase  # The hidden variable (Phase)

    def get_coordinates(self, x_range, t=0):
        """
        Generates the 3D coordinates of the helix at time t.
        Returns: (x, real_part, imag_part)
        """
        # Calculate the complex value Φ(x)
        # exponent = i(kx - ωt + θ)
        exponent = 1j * (self.k * x_range - self.omega * t + self.phase)
        phi = self.amplitude * np.exp(exponent)
        
        return x_range, np.real(phi), np.imag(phi)

    def __add__(self, other):
        """
        Allows adding two helices to simulate interference.
        Returns a new CompositeHelix object (or similar).
        For simplicity in this toy model, we'll return a CompositeHelix
        that sums the complex values.
        """
        return CompositeHelix(self, other)

class CompositeHelix:
    """
    Represents the superposition of two or more HyperstateHelices.
    """
    def __init__(self, *helices):
        self.helices = helices

    def get_coordinates(self, x_range, t=0):
        total_phi = np.zeros_like(x_range, dtype=np.complex128)
        
        for helix in self.helices:
            # Re-calculate phi for each helix
            exponent = 1j * (helix.k * x_range - helix.omega * t + helix.phase)
            total_phi += helix.amplitude * np.exp(exponent)
            
        return x_range, np.real(total_phi), np.imag(total_phi)
