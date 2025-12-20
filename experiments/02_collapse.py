import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import HyperstateHelix
from src.observer import Slicer

def run_experiment():
    print("Running Experiment 02: Collapse (Random Phase Slicing)...")
    
    # 1. Define the Space
    x_positions = np.linspace(0, 4 * np.pi, 50) # Discrete measurement points
    
    # 2. Create the Hyperstate
    helix = HyperstateHelix(k=1.0, amplitude=1.0)
    
    # 3. Simulate Measurement (Collapse)
    # We measure at each position, but for each measurement, the hidden variable (phase)
    # might be different if we consider them independent events, or we can simulate
    # a single slice across the whole domain.
    # The prompt implies "slicing this cylinder at a specific, random phase angle".
    # Let's visualize multiple "runs" to show how the same helix produces different shadows.
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the "Ideal" Shadow (Phase = 0)
    x_smooth = np.linspace(0, 4 * np.pi, 500)
    _, ideal_shadow, _ = helix.get_coordinates(x_smooth)
    ax.plot(x_smooth, ideal_shadow, label='Ideal Shadow (Phase=0)', color='black', alpha=0.3, linestyle='--')
    
    # Run 1: Random Slice A
    # We'll manually simulate this using the Slicer logic but applied to the whole wave for visualization
    slice_angle_1 = np.random.uniform(0, 2 * np.pi)
    helix_run_1 = HyperstateHelix(k=1.0, amplitude=1.0, phase=slice_angle_1)
    _, shadow_1, _ = helix_run_1.get_coordinates(x_smooth)
    ax.plot(x_smooth, shadow_1, label=f'Observation 1 (Slice {slice_angle_1:.2f})', color='red')
    
    # Run 2: Random Slice B
    slice_angle_2 = np.random.uniform(0, 2 * np.pi)
    helix_run_2 = HyperstateHelix(k=1.0, amplitude=1.0, phase=slice_angle_2)
    _, shadow_2, _ = helix_run_2.get_coordinates(x_smooth)
    ax.plot(x_smooth, shadow_2, label=f'Observation 2 (Slice {slice_angle_2:.2f})', color='blue')
    
    # Demonstrate "Particle-like" detection at specific points
    # Let's say we measure at x=2.0 multiple times
    measure_x = 2.0
    measurements = []
    for _ in range(20):
        val = Slicer.measure_at(helix, measure_x)
        measurements.append(val)
        
    ax.scatter([measure_x]*20, measurements, color='green', alpha=0.6, label='Repeated Measurements at x=2.0')

    ax.set_title("Exp 02: The Effect of Random Slicing (Collapse)")
    ax.set_xlabel("Space (x)")
    ax.set_ylabel("Observed Value")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_experiment()
