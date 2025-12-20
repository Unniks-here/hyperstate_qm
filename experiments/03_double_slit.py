import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import HyperstateHelix
from src.visualizer import plot_reality_vs_shadow

def run_experiment():
    print("Running Experiment 03: Double Slit (Interference)...")
    
    # 1. Define the Space
    x = np.linspace(0, 6 * np.pi, 500)
    
    # 2. Create two Hyperstates with slightly different momenta (k)
    # This creates a "beat" pattern, similar to interference
    helix_1 = HyperstateHelix(k=1.0, amplitude=1.0)
    helix_2 = HyperstateHelix(k=1.2, amplitude=1.0) # Slightly different k
    
    # 3. Add them (Vector Addition in 3D)
    interference_helix = helix_1 + helix_2
    
    # 4. Visualize
    # The 3D plot will show a complex winding shape
    # The 2D plot will show the interference pattern (beats)
    plot_reality_vs_shadow(interference_helix, x, title="Exp 03: Interference (Adding Two Helices)")

if __name__ == "__main__":
    run_experiment()
