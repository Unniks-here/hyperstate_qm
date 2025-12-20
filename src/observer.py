import numpy as np

class Slicer:
    """
    The Measurement logic.
    Simulates the geometric act of slicing the cylinder at a specific, random phase angle.
    """
    @staticmethod
    def measure_at(helix, position, t=0):
        """
        Applies a random phase θ to simulate the "hidden variable" being unknown.
        In this model, 'measurement' means fixing a specific phase slice.
        
        Returns the observed value (Real part) at that specific instance.
        """
        # Random phase slice between 0 and 2pi
        random_phase_slice = np.random.uniform(0, 2 * np.pi)
        
        # We temporarily shift the helix's phase to this random slice
        # effectively "collapsing" it to a specific orientation for this measurement
        
        # Calculate the value at the specific position
        exponent = 1j * (helix.k * position - helix.omega * t + helix.phase + random_phase_slice)
        phi_val = helix.amplitude * np.exp(exponent)
        
        # The observed reality is the projection (Real part)
        return np.real(phi_val)
