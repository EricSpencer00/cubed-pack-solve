"""
placements.py - Generate All Legal T-Tetracube Placements in 6×6×6 Cube

Mathematical Foundation:
========================
A placement is valid if and only if:
1. All 4 cells of the piece are within bounds [0,5] × [0,5] × [0,5]
2. No overlap with other pieces (handled by exact cover)

We generate placements by:
1. Taking each unique orientation
2. Sliding it across all positions in the cube
3. Checking bounds
4. Recording the cell indices it occupies

Cell Indexing:
We use a linear index: cell_id = x + y*6 + z*36
This maps (x,y,z) ∈ [0,5]³ → [0,215]
"""

from typing import List, Tuple, Set
from .geometry import get_orientations, Point3D

# =============================================================================
# CUBE PARAMETERS
# =============================================================================

CUBE_SIZE = 6  # 6×6×6 cube
NUM_CELLS = CUBE_SIZE ** 3  # 216 cells
NUM_PIECES = NUM_CELLS // 4  # 54 pieces needed


# =============================================================================
# CELL INDEXING
# =============================================================================

def point_to_index(x: int, y: int, z: int) -> int:
    """
    Convert (x, y, z) coordinates to linear cell index.
    
    Index formula: x + y*6 + z*36
    This gives a unique index in [0, 215] for each cell.
    
    Args:
        x, y, z: Coordinates in [0, 5]
    
    Returns:
        Linear index in [0, 215]
    """
    return x + y * CUBE_SIZE + z * CUBE_SIZE * CUBE_SIZE


def index_to_point(index: int) -> Point3D:
    """
    Convert linear cell index to (x, y, z) coordinates.
    
    Inverse of point_to_index.
    
    Args:
        index: Linear index in [0, 215]
    
    Returns:
        Tuple (x, y, z)
    """
    z = index // (CUBE_SIZE * CUBE_SIZE)
    remainder = index % (CUBE_SIZE * CUBE_SIZE)
    y = remainder // CUBE_SIZE
    x = remainder % CUBE_SIZE
    return (x, y, z)


# =============================================================================
# BOUNDS CHECKING
# =============================================================================

def is_in_bounds(x: int, y: int, z: int) -> bool:
    """Check if a point is within the 6×6×6 cube."""
    return 0 <= x < CUBE_SIZE and 0 <= y < CUBE_SIZE and 0 <= z < CUBE_SIZE


def is_placement_valid(cells: List[Point3D]) -> bool:
    """Check if all cells of a placement are within bounds."""
    return all(is_in_bounds(x, y, z) for x, y, z in cells)


# =============================================================================
# PLACEMENT GENERATION
# =============================================================================

# A placement is represented as a tuple of cell indices (sorted)
Placement = Tuple[int, ...]


def translate_piece(piece: List[Point3D], dx: int, dy: int, dz: int) -> List[Point3D]:
    """Translate a piece by (dx, dy, dz)."""
    return [(x + dx, y + dy, z + dz) for x, y, z in piece]


def generate_all_placements() -> List[Placement]:
    """
    Generate all legal placements of T-tetracubes in the 6×6×6 cube.
    
    Algorithm:
    1. For each unique orientation of the T-piece
    2. For each translation (dx, dy, dz) in [0, 5]³
    3. If all cells are in bounds, record the placement
    
    Returns:
        List of placements, where each placement is a tuple of 4 cell indices
    """
    orientations = get_orientations()
    placements: List[Placement] = []
    placement_set: Set[Placement] = set()  # For deduplication (shouldn't be needed but safety)
    
    for orientation in orientations:
        # Compute the bounding box of this orientation
        max_x = max(p[0] for p in orientation)
        max_y = max(p[1] for p in orientation)
        max_z = max(p[2] for p in orientation)
        
        # Valid translation ranges (since orientation is normalized to start at 0)
        for dx in range(CUBE_SIZE - max_x):
            for dy in range(CUBE_SIZE - max_y):
                for dz in range(CUBE_SIZE - max_z):
                    translated = translate_piece(orientation, dx, dy, dz)
                    
                    # Double-check bounds (should always pass given our ranges)
                    if is_placement_valid(translated):
                        # Convert to cell indices
                        indices = tuple(sorted(
                            point_to_index(x, y, z) for x, y, z in translated
                        ))
                        
                        if indices not in placement_set:
                            placement_set.add(indices)
                            placements.append(indices)
    
    return placements


def get_placement_coordinates(placement: Placement) -> List[Point3D]:
    """Convert a placement (tuple of indices) back to coordinates."""
    return [index_to_point(idx) for idx in placement]


# =============================================================================
# MODULE-LEVEL CACHED DATA
# =============================================================================

# Cache all placements at module load time
ALL_PLACEMENTS: List[Placement] = generate_all_placements()


def get_placements() -> List[Placement]:
    """Get all legal placements of T-tetracubes."""
    return ALL_PLACEMENTS


# =============================================================================
# VERIFICATION / TESTING
# =============================================================================

def verify_placements() -> None:
    """
    Verify mathematical correctness of placement generation.
    
    Checks:
    1. All placements have exactly 4 cells
    2. All cell indices are in valid range [0, 215]
    3. No duplicate placements
    4. Reasonable number of placements
    """
    print("Verifying placements module...")
    
    placements = get_placements()
    print(f"✓ Generated {len(placements)} unique placements")
    
    # Check each placement
    for i, placement in enumerate(placements):
        assert len(placement) == 4, f"Placement {i} has {len(placement)} cells, expected 4"
        for idx in placement:
            assert 0 <= idx < NUM_CELLS, f"Placement {i} has invalid index {idx}"
    print("✓ All placements have exactly 4 cells with valid indices")
    
    # Check for duplicates
    unique_placements = set(placements)
    assert len(unique_placements) == len(placements), "Duplicate placements found"
    print("✓ No duplicate placements")
    
    # Verify index conversion
    for idx in range(NUM_CELLS):
        point = index_to_point(idx)
        reconstructed = point_to_index(*point)
        assert reconstructed == idx, f"Index conversion failed for {idx}"
    print("✓ Index conversion is bijective")
    
    # Show some example placements
    print(f"\nExample placements (first 5):")
    for i, placement in enumerate(placements[:5]):
        coords = get_placement_coordinates(placement)
        print(f"  {i}: indices={placement} coords={coords}")
    
    print("\n✓ Placements verification complete!")


if __name__ == "__main__":
    verify_placements()
