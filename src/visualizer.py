import matplotlib.pyplot as plt
import numpy as np

def plot_reality_vs_shadow(helix, x_range, t=0, title="Hyperstate Helix vs. Observed Reality"):
    """
    Subplot 1 (3D): Wireframe cylinder with the Helix winding through it.
    Subplot 2 (2D): The projected Cosine wave.
    """
    x, real_part, imag_part = helix.get_coordinates(x_range, t)
    
    fig = plt.figure(figsize=(12, 6))
    fig.suptitle(title, fontsize=16)

    # --- Subplot 1: 3D Helix ---
    ax3d = fig.add_subplot(121, projection='3d')
    
    # Plot the helix
    ax3d.plot(x, real_part, imag_part, label='Hyperstate (Φ)', color='blue', linewidth=2)
    
    # Draw a wireframe cylinder for context
    # Cylinder radius is the amplitude
    radius = 1.0 # Default/Normalized
    if hasattr(helix, 'amplitude'):
        radius = helix.amplitude
    elif hasattr(helix, 'helices'): # Composite
         # Estimate radius for composite (just for visual context, use max amplitude sum)
         radius = sum(h.amplitude for h in helix.helices)

    # Create cylinder mesh
    x_cyl = np.linspace(x_range.min(), x_range.max(), 50)
    theta_cyl = np.linspace(0, 2*np.pi, 20)
    X_cyl, Theta_cyl = np.meshgrid(x_cyl, theta_cyl)
    Y_cyl = radius * np.cos(Theta_cyl)
    Z_cyl = radius * np.sin(Theta_cyl)
    
    # Plot cylinder as faint wireframe
    ax3d.plot_wireframe(X_cyl, Y_cyl, Z_cyl, color='gray', alpha=0.2)
    
    # Labels
    ax3d.set_xlabel('Space (x)')
    ax3d.set_ylabel('Real Part')
    ax3d.set_zlabel('Imaginary Part')
    ax3d.set_title('Higher-Dimensional Reality (3D)')
    ax3d.legend()

    # --- Subplot 2: 2D Shadow ---
    ax2d = fig.add_subplot(122)
    
    # The Observed Reality (Psi) is the projection: Ψ(x) = Real(Φ(x))
    ax2d.plot(x, real_part, label='Observed Reality (Ψ)', color='red', linewidth=2)
    
    # Visual guide connecting the two
    ax2d.set_xlabel('Space (x)')
    ax2d.set_ylabel('Amplitude')
    ax2d.set_title('Projected Shadow (2D)')
    ax2d.grid(True, linestyle='--', alpha=0.6)
    ax2d.legend()
    
    # Set y-limits to match the 3D plot's radius/amplitude
    ax2d.set_ylim(-radius * 1.2, radius * 1.2)

    plt.tight_layout()
    plt.show()
