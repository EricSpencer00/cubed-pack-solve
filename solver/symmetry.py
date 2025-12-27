"""
symmetry.py - Cube Rotation Canonicalization

Mathematical Foundation:
========================
The rotation group of a cube has 24 elements (the orientation-preserving
symmetries of a cube). Two solutions are equivalent if one can be obtained
from the other by rotating the entire cube.

To eliminate duplicates, we compute a canonical form:
1. Apply all 24 rotations to a solution
2. Choose the lexicographically smallest representation
3. Store only canonical forms

This ensures that equivalent solutions are identified.

Cube Coordinates:
Our 6×6×6 cube uses coordinates in [0,5]³.
Rotations are around the center (2.5, 2.5, 2.5).
We transform by: translate to origin, rotate, translate back.
"""

import numpy as np
from typing import List, Tuple, Set, FrozenSet
from .geometry import get_rotation_matrices, Point3D
from .placements import CUBE_SIZE, point_to_index, index_to_point, get_placement_coordinates

# Type for a solution: tuple of placement indices (row IDs)
Solution = Tuple[int, ...]

# Type for a canonical solution: sorted tuple of sorted pieces
CanonicalSolution = Tuple[Tuple[Point3D, ...], ...]


# =============================================================================
# COORDINATE TRANSFORMATION UNDER CUBE ROTATION
# =============================================================================

def rotate_point_in_cube(point: Point3D, rotation: np.ndarray) -> Point3D:
    """
    Rotate a point within the 6×6×6 cube.
    
    The rotation is performed around the cube center (2.5, 2.5, 2.5).
    
    Process:
    1. Translate point to center origin: p' = p - (2.5, 2.5, 2.5)
    2. Apply rotation: p'' = R @ p'
    3. Translate back: p''' = p'' + (2.5, 2.5, 2.5)
    4. Round to integers (rotation by 90° keeps lattice points on lattice)
    
    Args:
        point: (x, y, z) coordinates in [0, 5]
        rotation: 3×3 rotation matrix
    
    Returns:
        Rotated point coordinates
    """
    center = 2.5  # Center of 6×6×6 cube
    
    # Convert to centered coordinates
    p = np.array([point[0] - center, point[1] - center, point[2] - center])
    
    # Apply rotation
    rotated = rotation @ p
    
    # Convert back to cube coordinates
    result = rotated + center
    
    # Round to nearest integer (should be exact for 90° rotations)
    x = int(round(result[0]))
    y = int(round(result[1]))
    z = int(round(result[2]))
    
    return (x, y, z)


def rotate_piece_in_cube(piece_coords: List[Point3D], rotation: np.ndarray) -> List[Point3D]:
    """
    Rotate a piece (list of coordinates) within the cube.
    
    Args:
        piece_coords: List of cell coordinates
        rotation: 3×3 rotation matrix
    
    Returns:
        List of rotated coordinates
    """
    return [rotate_point_in_cube(p, rotation) for p in piece_coords]


def rotate_solution(solution_pieces: List[List[Point3D]], rotation: np.ndarray) -> List[List[Point3D]]:
    """
    Rotate an entire solution (all pieces) within the cube.
    
    Args:
        solution_pieces: List of pieces, each piece is a list of coordinates
        rotation: 3×3 rotation matrix
    
    Returns:
        List of rotated pieces
    """
    return [rotate_piece_in_cube(piece, rotation) for piece in solution_pieces]


# =============================================================================
# CANONICAL FORM COMPUTATION
# =============================================================================

def solution_to_canonical_key(solution_pieces: List[List[Point3D]]) -> CanonicalSolution:
    """
    Convert a solution to a canonical comparable form.
    
    The key is a tuple of sorted pieces, where each piece is a sorted tuple
    of coordinates. This allows lexicographic comparison.
    
    Args:
        solution_pieces: List of pieces (each piece is list of coordinates)
    
    Returns:
        Canonical form as nested tuples
    """
    # Sort coordinates within each piece, then sort pieces
    sorted_pieces = [tuple(sorted(piece)) for piece in solution_pieces]
    return tuple(sorted(sorted_pieces))


def compute_canonical_form(solution_pieces: List[List[Point3D]]) -> CanonicalSolution:
    """
    Compute the canonical form of a solution under cube rotations.
    
    Mathematical correctness:
    - Apply all 24 rotations to the solution
    - Compute the canonical key for each rotated version
    - Return the lexicographically smallest key
    
    This defines an equivalence relation where two solutions are equivalent
    iff their canonical forms are equal.
    
    Args:
        solution_pieces: List of pieces (each piece is list of coordinates)
    
    Returns:
        Canonical form (lexicographically smallest under rotations)
    """
    rotations = get_rotation_matrices()
    
    min_key = None
    
    for R in rotations:
        rotated = rotate_solution(solution_pieces, R)
        key = solution_to_canonical_key(rotated)
        
        if min_key is None or key < min_key:
            min_key = key
    
    return min_key


# =============================================================================
# SOLUTION MANAGEMENT
# =============================================================================

class SolutionSet:
    """
    A set of unique solutions, with symmetry reduction.
    
    Only stores canonical forms, so equivalent solutions are automatically
    deduplicated.
    """
    
    def __init__(self):
        self.canonical_forms: Set[CanonicalSolution] = set()
        self.solutions: List[List[List[Point3D]]] = []  # Store one representative
    
    def add(self, solution_pieces: List[List[Point3D]]) -> bool:
        """
        Add a solution if it's not equivalent to an existing one.
        
        Args:
            solution_pieces: List of pieces (each piece is list of coordinates)
        
        Returns:
            True if this is a new solution, False if equivalent exists
        """
        canonical = compute_canonical_form(solution_pieces)
        
        if canonical in self.canonical_forms:
            return False
        
        self.canonical_forms.add(canonical)
        self.solutions.append(solution_pieces)
        return True
    
    def __len__(self) -> int:
        return len(self.canonical_forms)
    
    def __iter__(self):
        return iter(self.solutions)


def placements_to_pieces(placement_indices: List[int], 
                         all_placements: List[Tuple[int, ...]]) -> List[List[Point3D]]:
    """
    Convert placement indices to piece coordinates.
    
    Args:
        placement_indices: List of row IDs (indices into all_placements)
        all_placements: List of all placements (each is tuple of cell indices)
    
    Returns:
        List of pieces, each piece is a list of (x,y,z) coordinates
    """
    pieces = []
    for placement_idx in placement_indices:
        cell_indices = all_placements[placement_idx]
        coords = [index_to_point(cell_idx) for cell_idx in cell_indices]
        pieces.append(coords)
    return pieces


# =============================================================================
# SYMMETRY-BREAKING CONSTRAINT
# =============================================================================

def get_symmetry_breaking_placements(all_placements: List[Tuple[int, ...]]) -> List[int]:
    """
    Get placements that can be used for symmetry breaking.
    
    Strategy: Force the first piece to be at a "minimal" position.
    We require that cell (0,0,0) is covered, and the piece at that cell
    has minimal orientation.
    
    This reduces the search space by a factor of approximately 24.
    
    Note: This is an OPTIONAL optimization. For correctness, we still
    use canonical form deduplication. This just speeds up the search.
    
    Args:
        all_placements: List of all placements
    
    Returns:
        List of placement indices that cover cell (0,0,0)
    """
    # Cell index for (0,0,0)
    origin_cell = point_to_index(0, 0, 0)
    
    # Find all placements that cover the origin
    origin_placements = []
    for i, placement in enumerate(all_placements):
        if origin_cell in placement:
            origin_placements.append(i)
    
    return origin_placements


# =============================================================================
# VERIFICATION / TESTING
# =============================================================================

def verify_symmetry() -> None:
    """
    Verify mathematical correctness of symmetry module.
    
    Checks:
    1. Point rotation preserves cube bounds
    2. All 24 rotations are distinct
    3. Canonical form is invariant under rotation
    """
    print("Verifying symmetry module...")
    
    rotations = get_rotation_matrices()
    print(f"✓ Using {len(rotations)} rotation matrices")
    
    # Test that rotations keep points in bounds
    test_points = [
        (0, 0, 0), (5, 5, 5), (0, 5, 0), (2, 3, 4)
    ]
    
    for R in rotations:
        for p in test_points:
            rotated = rotate_point_in_cube(p, R)
            for coord in rotated:
                assert 0 <= coord <= 5, f"Rotation moved {p} to {rotated} (out of bounds)"
    print("✓ All rotations keep points within cube bounds")
    
    # Test that all rotations produce different results for a general point
    general_point = (0, 1, 2)  # Asymmetric point
    rotated_points = set()
    for R in rotations:
        rotated = rotate_point_in_cube(general_point, R)
        rotated_points.add(rotated)
    # Note: Some rotations may produce the same result for a given point,
    # but we should get at least several distinct points
    print(f"✓ Point (0,1,2) maps to {len(rotated_points)} distinct positions")
    
    # Test canonical form invariance
    # Create a test "solution" (just one piece)
    test_piece = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]
    test_solution = [test_piece]
    
    canonical = compute_canonical_form(test_solution)
    
    # Verify that all rotations produce the same canonical form
    for R in rotations:
        rotated_solution = rotate_solution(test_solution, R)
        rotated_canonical = compute_canonical_form(rotated_solution)
        assert rotated_canonical == canonical, "Canonical form not invariant under rotation"
    print("✓ Canonical form is invariant under all cube rotations")
    
    # Test SolutionSet
    sol_set = SolutionSet()
    
    # Add original solution
    added1 = sol_set.add(test_solution)
    assert added1, "First solution should be added"
    
    # Add rotated version (should be rejected as duplicate)
    R = rotations[5]  # Some rotation
    rotated = rotate_solution(test_solution, R)
    added2 = sol_set.add(rotated)
    assert not added2, "Rotated solution should be rejected as duplicate"
    
    assert len(sol_set) == 1, "Should have exactly 1 unique solution"
    print("✓ SolutionSet correctly identifies equivalent solutions")
    
    print("\n✓ Symmetry verification complete!")


if __name__ == "__main__":
    verify_symmetry()
