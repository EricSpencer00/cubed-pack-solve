"""
geometry.py - T-Tetracube Definition and 3D Rotations

Mathematical Foundation:
========================
The T-tetracube consists of 4 unit cubes arranged in a T-shape.
In 3D, we need to generate all unique orientations of this piece.

The rotation group of 3D space that preserves a cube has 24 elements:
- 6 face choices × 4 rotations around the face normal = 24

We represent each rotation as a 3×3 orthogonal matrix with determinant +1.
We exclude reflections (determinant -1) as the T-tetracube is achiral.

Normalization:
Each rotated piece is normalized so that min(x,y,z) = (0,0,0).
This ensures consistent placement calculations.
"""

import numpy as np
from typing import List, Tuple, FrozenSet, Set

# Type aliases for clarity
Point3D = Tuple[int, int, int]
Orientation = FrozenSet[Point3D]


# =============================================================================
# T-TETRACUBE DEFINITION
# =============================================================================

# The canonical T-tetracube centered at origin
# Shape:   X
#         XXX
# In 3D with coordinates:
#   (0,1,0)
#      |
# (-1,0,0) -- (0,0,0) -- (1,0,0)
T_PIECE_CANONICAL: List[Point3D] = [
    (0, 0, 0),   # Center
    (1, 0, 0),   # Right
    (-1, 0, 0),  # Left  
    (0, 1, 0),   # Top (the stem of the T)
]


# =============================================================================
# 3D ROTATION MATRICES
# =============================================================================

def generate_rotation_matrices() -> List[np.ndarray]:
    """
    Generate all 24 rotation matrices of the cube rotation group.
    
    Mathematical correctness:
    - The rotation group of a cube is isomorphic to S4 (symmetric group on 4 elements)
    - It has exactly 24 elements
    - We generate them by composing 90° rotations around x, y, z axes
    
    Returns:
        List of 24 unique 3×3 rotation matrices with integer entries and det=+1
    """
    # Basic 90° rotation matrices around each axis
    # Rx: rotation around x-axis by 90°
    Rx = np.array([
        [1, 0, 0],
        [0, 0, -1],
        [0, 1, 0]
    ], dtype=int)
    
    # Ry: rotation around y-axis by 90°
    Ry = np.array([
        [0, 0, 1],
        [0, 1, 0],
        [-1, 0, 0]
    ], dtype=int)
    
    # Rz: rotation around z-axis by 90°
    Rz = np.array([
        [0, -1, 0],
        [1, 0, 0],
        [0, 0, 1]
    ], dtype=int)
    
    # Generate all 24 rotations by composing powers of Rx, Ry, Rz
    # We use a set to collect unique matrices
    rotation_set: Set[bytes] = set()
    rotations: List[np.ndarray] = []
    
    identity = np.eye(3, dtype=int)
    
    # Generate Rx^i for i in 0..3
    Rx_powers = [np.linalg.matrix_power(Rx, i).astype(int) for i in range(4)]
    Ry_powers = [np.linalg.matrix_power(Ry, i).astype(int) for i in range(4)]
    Rz_powers = [np.linalg.matrix_power(Rz, i).astype(int) for i in range(4)]
    
    # Compose all combinations - this will give us all 24 rotations
    for rx in Rx_powers:
        for ry in Ry_powers:
            for rz in Rz_powers:
                R = rx @ ry @ rz
                R = R.astype(int)
                
                # Convert to bytes for hashing
                key = R.tobytes()
                if key not in rotation_set:
                    # Verify it's a proper rotation (det = +1)
                    det = int(round(np.linalg.det(R)))
                    assert det == 1, f"Invalid rotation matrix with det={det}"
                    rotation_set.add(key)
                    rotations.append(R)
    
    # Verify we have exactly 24 rotations
    assert len(rotations) == 24, f"Expected 24 rotations, got {len(rotations)}"
    
    return rotations


# =============================================================================
# PIECE ROTATION AND NORMALIZATION
# =============================================================================

def rotate_piece(piece: List[Point3D], rotation: np.ndarray) -> List[Point3D]:
    """
    Apply a rotation matrix to a piece.
    
    Args:
        piece: List of 3D coordinates
        rotation: 3×3 rotation matrix
    
    Returns:
        Rotated piece as list of tuples
    """
    rotated = []
    for point in piece:
        # Apply rotation: R @ v
        new_point = rotation @ np.array(point, dtype=int)
        rotated.append(tuple(new_point.tolist()))
    return rotated


def normalize_piece(piece: List[Point3D]) -> List[Point3D]:
    """
    Normalize a piece so that min(x), min(y), min(z) = (0, 0, 0).
    
    This translation ensures all pieces can be compared and placed consistently.
    
    Args:
        piece: List of 3D coordinates
    
    Returns:
        Normalized piece with minimum corner at origin
    """
    if not piece:
        return piece
    
    min_x = min(p[0] for p in piece)
    min_y = min(p[1] for p in piece)
    min_z = min(p[2] for p in piece)
    
    return [(x - min_x, y - min_y, z - min_z) for x, y, z in piece]


def piece_to_frozenset(piece: List[Point3D]) -> Orientation:
    """Convert piece to frozenset for hashing and comparison."""
    return frozenset(piece)


# =============================================================================
# GENERATE ALL UNIQUE ORIENTATIONS
# =============================================================================

def generate_unique_orientations() -> List[List[Point3D]]:
    """
    Generate all unique orientations of the T-tetracube.
    
    Mathematical correctness:
    - Apply all 24 cube rotations to the T-piece
    - Normalize each result
    - Deduplicate using frozenset comparison
    
    The T-tetracube has some rotational symmetry, so we expect fewer than 24
    unique orientations. The T-tetracube in 3D has 12 unique orientations
    (it has a 2-fold rotational symmetry around the stem axis).
    
    Returns:
        List of unique orientations, each as a list of normalized coordinates
    """
    rotations = generate_rotation_matrices()
    
    seen: Set[Orientation] = set()
    unique_orientations: List[List[Point3D]] = []
    
    for R in rotations:
        rotated = rotate_piece(T_PIECE_CANONICAL, R)
        normalized = normalize_piece(rotated)
        key = piece_to_frozenset(normalized)
        
        if key not in seen:
            seen.add(key)
            # Sort for consistent ordering
            sorted_orientation = sorted(normalized)
            unique_orientations.append(sorted_orientation)
    
    return unique_orientations


# =============================================================================
# MODULE-LEVEL CACHED DATA
# =============================================================================

# Cache the rotation matrices and orientations at module load time
ROTATION_MATRICES: List[np.ndarray] = generate_rotation_matrices()
T_ORIENTATIONS: List[List[Point3D]] = generate_unique_orientations()


def get_orientations() -> List[List[Point3D]]:
    """Get all unique orientations of the T-tetracube."""
    return T_ORIENTATIONS


def get_rotation_matrices() -> List[np.ndarray]:
    """Get all 24 cube rotation matrices."""
    return ROTATION_MATRICES


# =============================================================================
# VERIFICATION / TESTING
# =============================================================================

def verify_geometry() -> None:
    """
    Verify mathematical correctness of the geometry module.
    
    Checks:
    1. T-piece has exactly 4 cells
    2. All 24 rotation matrices generated
    3. Each orientation has exactly 4 cells
    4. Number of unique orientations is reasonable (≤24)
    """
    print("Verifying geometry module...")
    
    # Check T-piece
    assert len(T_PIECE_CANONICAL) == 4, "T-piece must have 4 cells"
    print(f"✓ T-piece has {len(T_PIECE_CANONICAL)} cells")
    
    # Check rotations
    assert len(ROTATION_MATRICES) == 24, f"Expected 24 rotations, got {len(ROTATION_MATRICES)}"
    print(f"✓ Generated {len(ROTATION_MATRICES)} rotation matrices")
    
    # Verify all matrices are orthogonal with det=+1
    for i, R in enumerate(ROTATION_MATRICES):
        det = int(round(np.linalg.det(R)))
        assert det == 1, f"Rotation {i} has det={det}"
        # R @ R.T should be identity
        product = R @ R.T
        assert np.allclose(product, np.eye(3)), f"Rotation {i} is not orthogonal"
    print("✓ All rotation matrices are proper rotations (det=+1, orthogonal)")
    
    # Check orientations
    num_orientations = len(T_ORIENTATIONS)
    assert 1 <= num_orientations <= 24, f"Unexpected number of orientations: {num_orientations}"
    print(f"✓ Generated {num_orientations} unique T-piece orientations")
    
    # Each orientation should have 4 cells
    for i, orient in enumerate(T_ORIENTATIONS):
        assert len(orient) == 4, f"Orientation {i} has {len(orient)} cells, expected 4"
    print("✓ All orientations have exactly 4 cells")
    
    # Print the orientations for inspection
    print("\nUnique orientations (normalized):")
    for i, orient in enumerate(T_ORIENTATIONS):
        print(f"  {i}: {orient}")
    
    print("\n✓ Geometry verification complete!")


if __name__ == "__main__":
    verify_geometry()
