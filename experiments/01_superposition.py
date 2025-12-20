import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import HyperstateHelix
from src.visualizer import plot_reality_vs_shadow

def run_experiment():
    print("Running Experiment 01: Superposition (Helix vs Shadow)...")
    
    # 1. Define the Space
    x = np.linspace(0, 4 * np.pi, 500)
    
    # 2. Create the Hyperstate (The 3D Object)
    # A simple helix with momentum k=1
    helix = HyperstateHelix(k=1.0, amplitude=1.0)
    
    # 3. Visualize
    plot_reality_vs_shadow(helix, x, title="Exp 01: The Hyperstate Helix (Superposition)")

if __name__ == "__main__":
    run_experiment()
