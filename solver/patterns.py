"""
patterns.py - Common T-Tetracube Patterns and Tutorial Ordering

This module provides:
1. Corner-first BFS ordering for gravity-safe step-by-step assembly
2. Accessibility check (piece must have an opening to be placed)
3. 3D chunk pattern extraction (3+ pieces in compact 3D regions)
"""

from typing import List, Tuple, Set, Dict, Optional
from collections import defaultdict
from .placements import Point3D, CUBE_SIZE

# =============================================================================
# PIECE ANALYSIS
# =============================================================================

def get_piece_min_z(piece: List[Point3D]) -> int:
    """Get the minimum Z coordinate of a piece (height from ground)."""
    return min(p[2] for p in piece)

def get_piece_max_z(piece: List[Point3D]) -> int:
    """Get the maximum Z coordinate of a piece."""
    return max(p[2] for p in piece)

def get_piece_bounding_box(piece: List[Point3D]) -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]:
    """Get (min_corner, max_corner) of piece bounding box."""
    xs = [p[0] for p in piece]
    ys = [p[1] for p in piece]
    zs = [p[2] for p in piece]
    return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))

def is_piece_grounded(piece: List[Point3D]) -> bool:
    """Check if piece touches the ground (z=0)."""
    return get_piece_min_z(piece) == 0

def piece_corner_distance(piece: List[Point3D]) -> float:
    """Calculate distance from piece's closest cell to corner (0,0,0)."""
    return min((p[0]**2 + p[1]**2 + p[2]**2)**0.5 for p in piece)

def piece_min_coords(piece: List[Point3D]) -> Tuple[int, int, int]:
    """Get the minimum x, y, z coordinates of a piece."""
    return (min(p[0] for p in piece), min(p[1] for p in piece), min(p[2] for p in piece))


# =============================================================================
# ACCESSIBILITY CHECK - Can the piece physically be placed?
# =============================================================================

def is_piece_accessible(piece: List[Point3D], placed_cells: Set[Point3D]) -> bool:
    """
    Check if a piece can be physically placed (has an opening).
    
    A piece is accessible if at least one of its cells can be reached from
    outside the cube (from +x, +y, or +z direction without passing through
    placed cells).
    
    This ensures we don't create enclosed spaces that can't be filled.
    """
    piece_set = set(tuple(p) for p in piece)
    
    for x, y, z in piece:
        # Check if this cell is accessible from +z (top)
        accessible_from_top = True
        for check_z in range(z + 1, CUBE_SIZE):
            if (x, y, check_z) in placed_cells:
                accessible_from_top = False
                break
        if accessible_from_top:
            return True
        
        # Check if accessible from +x side
        accessible_from_x = True
        for check_x in range(x + 1, CUBE_SIZE):
            if (check_x, y, z) in placed_cells:
                accessible_from_x = False
                break
        if accessible_from_x:
            return True
        
        # Check if accessible from +y side  
        accessible_from_y = True
        for check_y in range(y + 1, CUBE_SIZE):
            if (x, check_y, z) in placed_cells:
                accessible_from_y = False
                break
        if accessible_from_y:
            return True
    
    return False


def is_piece_supported(piece: List[Point3D], placed_cells: Set[Point3D]) -> bool:
    """
    Check if a piece is fully gravity-supported.
    A piece is supported if:
    - It touches the ground (z=0), OR
    - Every cell at its lowest z-level has support below
    """
    min_z = get_piece_min_z(piece)
    if min_z == 0:
        return True
    
    # Check if all cells at min_z have support below
    for x, y, z in piece:
        if z == min_z:
            if (x, y, z - 1) not in placed_cells:
                return False
    return True


# =============================================================================
# CORNER-FIRST BFS ORDERING FOR TUTORIAL
# =============================================================================

def order_solution_bfs(pieces: List[List[Point3D]]) -> List[List[Point3D]]:
    """
    Reorder pieces using Corner-First BFS for physical assembly.
    
    Strategy:
    1. Start from corner (0,0,0) and expand outward
    2. Prioritize: grounded pieces first, then by corner distance
    3. Only place pieces that are supported AND accessible
    4. Within each "wave", prefer pieces closer to already-placed pieces
    
    This ensures we build from the corner outward, layer by layer.
    """
    remaining = [tuple(tuple(p) for p in piece) for piece in pieces]
    ordered = []
    placed_cells: Set[Point3D] = set()
    
    while remaining:
        # Score each remaining piece
        candidates = []
        for piece in remaining:
            # Must be supported (gravity-safe)
            if not is_piece_supported(piece, placed_cells):
                continue
            
            # Must be accessible (can physically place it)
            if placed_cells and not is_piece_accessible(piece, placed_cells):
                continue
            
            min_z = get_piece_min_z(piece)
            corner_dist = piece_corner_distance(piece)
            min_coords = piece_min_coords(piece)
            
            # Adjacency bonus: prefer pieces that connect to what's already built
            adjacency_score = 0
            if placed_cells:
                for x, y, z in piece:
                    for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                        if (x+dx, y+dy, z+dz) in placed_cells:
                            adjacency_score += 1
            
            # Score: prioritize grounded, close to corner, adjacent to existing
            # Lower score = better
            score = (
                min_z * 1000 +           # Strongly prefer lower z
                corner_dist * 10 -       # Prefer closer to corner
                adjacency_score * 5 +    # Bonus for adjacency (subtract)
                min_coords[0] + min_coords[1]  # Tie-break by x+y
            )
            
            candidates.append((score, piece))
        
        if not candidates:
            # Fallback: take the piece with lowest z and closest to corner
            remaining.sort(key=lambda p: (get_piece_min_z(p), piece_corner_distance(p)))
            next_piece = remaining.pop(0)
        else:
            # Take the best candidate
            candidates.sort(key=lambda x: x[0])
            next_piece = candidates[0][1]
            remaining.remove(next_piece)
        
        ordered.append(list(next_piece))
        
        # Add cells to placed set
        for cell in next_piece:
            placed_cells.add(tuple(cell))
    
    return ordered


# Alias for backward compatibility
order_solution_for_tutorial = order_solution_bfs


# =============================================================================
# 3D CHUNK PATTERN EXTRACTION
# =============================================================================

def get_piece_orientation(piece: List[Point3D]) -> str:
    """Determine the orientation of a T-piece."""
    zs = set(p[2] for p in piece)
    ys = set(p[1] for p in piece)
    xs = set(p[0] for p in piece)
    
    if len(zs) == 1:
        return "flat"     # Lying flat in XY plane
    elif len(ys) == 1:
        return "wall_xz"  # Standing in XZ plane
    elif len(xs) == 1:
        return "wall_yz"  # Standing in YZ plane
    else:
        return "3d"       # True 3D orientation


def are_pieces_adjacent(piece1: List[Point3D], piece2: List[Point3D]) -> bool:
    """Check if two pieces share at least one face."""
    cells1 = set(tuple(c) for c in piece1)
    for x, y, z in piece2:
        for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            if (x+dx, y+dy, z+dz) in cells1:
                return True
    return False


def find_connected_group(start_idx: int, pieces: List[List[Point3D]], 
                         max_size: int = 6) -> List[int]:
    """
    Find a connected group of pieces starting from start_idx.
    Uses BFS to find adjacent pieces up to max_size.
    """
    group = [start_idx]
    queue = [start_idx]
    visited = {start_idx}
    
    while queue and len(group) < max_size:
        current = queue.pop(0)
        current_piece = pieces[current]
        
        for i, piece in enumerate(pieces):
            if i in visited:
                continue
            if are_pieces_adjacent(current_piece, piece):
                visited.add(i)
                group.append(i)
                queue.append(i)
                if len(group) >= max_size:
                    break
    
    return group


def get_chunk_dimensions(pieces: List[List[Point3D]]) -> Tuple[int, int, int]:
    """Get the bounding box dimensions of a group of pieces."""
    all_cells = [cell for piece in pieces for cell in piece]
    if not all_cells:
        return (0, 0, 0)
    
    xs = [c[0] for c in all_cells]
    ys = [c[1] for c in all_cells]
    zs = [c[2] for c in all_cells]
    
    return (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1)


def normalize_chunk(pieces: List[List[Point3D]]) -> Tuple[Tuple[Tuple[int,int,int], ...], ...]:
    """Normalize a chunk to a canonical form for comparison."""
    all_cells = [cell for piece in pieces for cell in piece]
    if not all_cells:
        return tuple()
    
    # Translate to origin
    min_x = min(c[0] for c in all_cells)
    min_y = min(c[1] for c in all_cells)
    min_z = min(c[2] for c in all_cells)
    
    normalized_pieces = []
    for piece in pieces:
        normalized = tuple(sorted((c[0] - min_x, c[1] - min_y, c[2] - min_z) for c in piece))
        normalized_pieces.append(normalized)
    
    return tuple(sorted(normalized_pieces))


def classify_chunk(pieces: List[List[Point3D]], dims: Tuple[int, int, int]) -> Dict:
    """Classify a chunk pattern by its characteristics."""
    dx, dy, dz = dims
    num_pieces = len(pieces)
    
    orientations = [get_piece_orientation(p) for p in pieces]
    flat_count = orientations.count("flat")
    wall_count = orientations.count("wall_xz") + orientations.count("wall_yz")
    threed_count = orientations.count("3d")
    
    # Determine chunk type
    if dz == 1:
        chunk_type = "layer"
        difficulty = "easy"
        tip = f"A flat {dx}×{dy} layer pattern - great for building the base"
    elif dx <= 3 and dy <= 3 and dz <= 3:
        if threed_count > 0 or (flat_count > 0 and wall_count > 0):
            chunk_type = "3d_corner"
            difficulty = "medium"
            tip = f"A compact 3D corner chunk - pieces interlock in all directions"
        else:
            chunk_type = "column"
            difficulty = "easy"
            tip = f"A vertical column pattern - stack these to build height"
    else:
        chunk_type = "region"
        difficulty = "hard" if threed_count > 1 else "medium"
        tip = f"A {dx}×{dy}×{dz} region - visualize how pieces mesh together"
    
    return {
        "type": chunk_type,
        "difficulty": difficulty,
        "tip": tip,
        "dimensions": dims,
        "num_pieces": num_pieces,
        "orientations": {
            "flat": flat_count,
            "wall": wall_count,
            "3d": threed_count
        }
    }


def extract_3d_chunks(solution: List[List[Point3D]], 
                       min_pieces: int = 3, 
                       max_pieces: int = 4) -> List[Dict]:
    """
    Extract interesting 3D chunks from a solution.
    Finds groups of 3-4 connected pieces that form compact 3D patterns.
    Prefers chunks that fit within ~3x3x3 or similar compact regions.
    """
    chunks = []
    used_starts = set()
    
    for start_idx in range(len(solution)):
        if start_idx in used_starts:
            continue
        
        # Try different group sizes, preferring smaller compact groups
        for target_size in range(min_pieces, max_pieces + 1):
            group_indices = find_connected_group(start_idx, solution, target_size)
            
            if len(group_indices) < min_pieces:
                break
            
            group_pieces = [solution[i] for i in group_indices]
            dims = get_chunk_dimensions(group_pieces)
            
            # Prefer compact chunks: max dimension <= 4 for learning
            max_dim = max(dims)
            if max_dim > 4:
                continue
                
            total_cells = len(group_indices) * 4
            volume = dims[0] * dims[1] * dims[2]
            
            # Density check: chunks should fill at least 40% of their bounding box
            density = total_cells / volume
            if density < 0.4:
                continue
            
            # Require 3D structure (not flat)
            if dims[2] > 1 and (dims[0] > 1 or dims[1] > 1):
                classification = classify_chunk(group_pieces, dims)
                
                # Score compactness: prefer smaller, denser chunks
                compactness = density * 10 - max_dim
                
                chunks.append({
                    "indices": group_indices,
                    "pieces": group_pieces,
                    "dimensions": dims,
                    "normalized": normalize_chunk(group_pieces),
                    "compactness": compactness,
                    **classification
                })
                
                # Found a good chunk at this size, stop looking for larger
                break
        
        # Mark as used
        used_starts.add(start_idx)
    
    # Sort by compactness (higher is better)
    chunks.sort(key=lambda x: -x.get("compactness", 0))
    return chunks[:10]  # Return top 10


def extract_corner_chunks(solution: List[List[Point3D]]) -> List[Dict]:
    """
    Extract chunks specifically near the corner (0,0,0).
    These are most useful for learning how to start the puzzle.
    """
    # Find pieces that touch or are near the corner
    corner_pieces = []
    for i, piece in enumerate(solution):
        min_coords = piece_min_coords(piece)
        if min_coords[0] <= 2 and min_coords[1] <= 2 and min_coords[2] <= 1:
            corner_pieces.append(i)
    
    if len(corner_pieces) < 3:
        return []
    
    # Find connected groups within corner pieces
    chunks = []
    used = set()
    
    for start_idx in corner_pieces[:5]:  # Try first 5 corner pieces
        if start_idx in used:
            continue
        
        # Find connected pieces within corner region
        group = [start_idx]
        queue = [start_idx]
        visited = {start_idx}
        
        while queue and len(group) < 4:
            current = queue.pop(0)
            for i in corner_pieces:
                if i in visited:
                    continue
                if are_pieces_adjacent(solution[current], solution[i]):
                    visited.add(i)
                    group.append(i)
                    queue.append(i)
                    if len(group) >= 4:
                        break
        
        if len(group) >= 3:
            group_pieces = [solution[i] for i in group]
            dims = get_chunk_dimensions(group_pieces)
            classification = classify_chunk(group_pieces, dims)
            classification["type"] = "corner_start"
            classification["tip"] = "Start your puzzle with this corner pattern"
            
            chunks.append({
                "indices": group,
                "pieces": group_pieces,
                "dimensions": dims,
                "normalized": normalize_chunk(group_pieces),
                **classification
            })
            
            for idx in group:
                used.add(idx)
    
    return chunks


def extract_3d_chunks_original(solution: List[List[Point3D]], 
                       min_pieces: int = 3, 
                       max_pieces: int = 6) -> List[Dict]:
    """
    Original extract function - kept for backwards compatibility.
    """
    chunks = []
    used_starts = set()
    
    for start_idx in range(len(solution)):
        if start_idx in used_starts:
            continue
        
        group_indices = find_connected_group(start_idx, solution, max_pieces)
        
        if len(group_indices) < min_pieces:
            continue
        
        group_pieces = [solution[i] for i in group_indices]
        dims = get_chunk_dimensions(group_pieces)
        
        max_dim = max(dims)
        total_cells = len(group_indices) * 4
        volume = dims[0] * dims[1] * dims[2]
        
        if volume > total_cells * 3:
            continue
        
        if dims[2] > 1 or (dims[0] > 1 and dims[1] > 1):
            classification = classify_chunk(group_pieces, dims)
            
            chunks.append({
                "indices": group_indices,
                "pieces": group_pieces,
                "dimensions": dims,
                "normalized": normalize_chunk(group_pieces),
                **classification
            })
            
            # Mark these as used to avoid too many overlapping chunks
            for idx in group_indices[:2]:  # Only mark first 2 to allow overlap
                used_starts.add(idx)
    
    return chunks


def extract_common_chunks(solutions: List[List[List[Point3D]]], 
                          min_frequency: int = 2) -> List[Dict]:
    """
    Analyze multiple solutions to find common 3D chunk patterns.
    Includes both general chunks and corner-specific patterns.
    """
    chunk_counts = defaultdict(int)
    chunk_examples = {}
    corner_counts = defaultdict(int)
    corner_examples = {}
    
    for solution in solutions:
        # Regular compact chunks
        chunks = extract_3d_chunks(solution)
        seen_in_solution = set()
        
        for chunk in chunks:
            key = chunk["normalized"]
            if key not in seen_in_solution:
                chunk_counts[key] += 1
                seen_in_solution.add(key)
                if key not in chunk_examples:
                    chunk_examples[key] = chunk
        
        # Corner chunks (for learning to start)
        corner_chunks = extract_corner_chunks(solution)
        corner_seen = set()
        for chunk in corner_chunks:
            key = chunk["normalized"]
            if key not in corner_seen:
                corner_counts[key] += 1
                corner_seen.add(key)
                if key not in corner_examples:
                    corner_examples[key] = chunk
    
    # Build result: corner patterns first (most useful), then general
    common = []
    
    # Add best corner pattern first
    for key, count in sorted(corner_counts.items(), key=lambda x: -x[1]):
        if count >= min_frequency and len(common) < 2:
            example = corner_examples[key]
            dims = example["dimensions"]
            common.append({
                "id": f"corner_{len(common)+1}",
                "name": f"Corner Start ({dims[0]}×{dims[1]}×{dims[2]})",
                "description": f"{example['num_pieces']} pieces at corner, in {count} solutions",
                "pieces": example["pieces"],
                "frequency": count,
                "difficulty": "easy",
                "tip": "Start your puzzle from the corner with these pieces",
                "dimensions": dims
            })
    
    # Add compact 3D chunks
    for key, count in sorted(chunk_counts.items(), key=lambda x: -x[1]):
        if count >= min_frequency and len(common) < 8:
            example = chunk_examples[key]
            dims = example["dimensions"]
            
            common.append({
                "id": f"chunk_{len(common)+1}",
                "name": f"{example['type'].replace('_', ' ').title()} ({dims[0]}×{dims[1]}×{dims[2]})",
                "description": f"{example['num_pieces']} pieces, appears in {count} solutions",
                "pieces": example["pieces"],
                "frequency": count,
                "difficulty": example["difficulty"],
                "tip": example["tip"],
                "dimensions": dims
            })
    
    return common


# =============================================================================
# FALLBACK 3D CHUNK PATTERNS (used when no solutions available)
# =============================================================================

FALLBACK_PATTERNS = [
    {
        "id": "corner_3x3x2",
        "name": "Corner Block (3×3×2)",
        "description": "4 pieces filling a corner region in 3D",
        "pieces": [
            [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]],  # Flat at corner
            [[0, 1, 0], [0, 2, 0], [0, 3, 0], [1, 2, 0]],  # Perpendicular
            [[0, 0, 1], [1, 0, 1], [2, 0, 1], [1, 1, 1]],  # Stacked on first
            [[2, 1, 0], [2, 2, 0], [2, 2, 1], [2, 3, 0]],  # Connecting vertical
        ],
        "difficulty": "medium",
        "tip": "Build from the corner: flat base, then stack and connect",
        "dimensions": (3, 4, 2)
    },
    {
        "id": "layer_3x3",
        "name": "Base Layer (3×3)",
        "description": "3 pieces forming a flat 3×3 layer",
        "pieces": [
            [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]],
            [[0, 1, 0], [0, 2, 0], [1, 2, 0], [0, 3, 0]],
            [[2, 1, 0], [2, 2, 0], [3, 2, 0], [2, 3, 0]],
        ],
        "difficulty": "easy",
        "tip": "Flat layers are the foundation - T-stems can interlock",
        "dimensions": (4, 4, 1)
    },
    {
        "id": "tower_2x2x3",
        "name": "Tower (2×2×3)",
        "description": "3 pieces stacked vertically with interlocking",
        "pieces": [
            [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]],
            [[0, 0, 1], [1, 0, 1], [2, 0, 1], [1, 1, 1]],
            [[0, 0, 2], [1, 0, 2], [2, 0, 2], [1, 1, 2]],
        ],
        "difficulty": "easy",
        "tip": "Identical orientations stack perfectly into towers",
        "dimensions": (3, 2, 3)
    },
    {
        "id": "l_corner_3d",
        "name": "L-Corner 3D",
        "description": "4 pieces forming an L in 3D space",
        "pieces": [
            [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]],
            [[3, 0, 0], [4, 0, 0], [5, 0, 0], [4, 1, 0]],
            [[0, 0, 1], [0, 0, 2], [0, 1, 1], [0, 0, 3]],
            [[1, 0, 1], [2, 0, 1], [2, 0, 2], [3, 0, 1]],
        ],
        "difficulty": "medium",
        "tip": "Mix flat and vertical pieces along an L-edge",
        "dimensions": (6, 2, 4)
    },
    {
        "id": "interlocked_cube",
        "name": "Interlocked Cube (3×3×3)",
        "description": "5 pieces meshing in a cubic region",
        "pieces": [
            [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]],
            [[0, 1, 0], [0, 2, 0], [0, 2, 1], [0, 3, 0]],
            [[1, 2, 0], [2, 2, 0], [2, 1, 0], [2, 2, 1]],
            [[0, 0, 1], [1, 0, 1], [1, 0, 2], [2, 0, 1]],
            [[1, 1, 1], [1, 2, 1], [2, 2, 1], [1, 1, 2]],
        ],
        "difficulty": "hard",
        "tip": "Study how stems interlock across all three dimensions",
        "dimensions": (3, 4, 3)
    },
    {
        "id": "wall_segment",
        "name": "Wall Segment (4×1×3)",
        "description": "3 pieces forming a vertical wall section",
        "pieces": [
            [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 0, 1]],
            [[3, 0, 0], [3, 0, 1], [3, 0, 2], [2, 0, 1]],
            [[0, 0, 1], [0, 0, 2], [1, 0, 2], [0, 0, 3]],
        ],
        "difficulty": "medium",
        "tip": "Walls need pieces with stems pointing outward for stability",
        "dimensions": (4, 1, 4)
    },
]


def get_all_patterns(solutions: List[List[List[Point3D]]] = None) -> List[Dict]:
    """
    Get patterns - either extracted from real solutions or fallback patterns.
    """
    if solutions and len(solutions) >= 3:
        common = extract_common_chunks(solutions, min_frequency=2)
        if len(common) >= 4:
            return common
    
    return FALLBACK_PATTERNS


def get_pattern(pattern_id: str, solutions: List[List[List[Point3D]]] = None) -> Dict:
    """Get a specific pattern by ID."""
    patterns = get_all_patterns(solutions)
    for p in patterns:
        if p["id"] == pattern_id:
            return p
    return None


# =============================================================================
# TUTORIAL STEPS
# =============================================================================

def generate_tutorial_steps(ordered_pieces: List[List[Point3D]]) -> List[Dict]:
    """
    Generate tutorial step data for each piece placement.
    """
    steps = []
    placed_cells: Set[Point3D] = set()
    
    for i, piece in enumerate(ordered_pieces):
        piece_tuples = [tuple(p) for p in piece]
        
        # Analyze this piece
        min_z = get_piece_min_z(piece_tuples)
        is_grounded = min_z == 0
        corner_dist = piece_corner_distance(piece_tuples)
        
        # Find adjacent pieces (which pieces it touches)
        adjacent_pieces = set()
        for x, y, z in piece_tuples:
            for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                neighbor = (x+dx, y+dy, z+dz)
                if neighbor in placed_cells:
                    for j, prev_piece in enumerate(ordered_pieces[:i]):
                        if neighbor in [tuple(p) for p in prev_piece]:
                            adjacent_pieces.add(j + 1)
                            break
        
        # Check accessibility 
        accessible = is_piece_accessible(piece_tuples, placed_cells) if placed_cells else True
        
        # Generate tip based on context
        if i == 0:
            tip = "Start at the corner (0,0,0) with a flat piece for stability."
        elif is_grounded and corner_dist < 3:
            tip = "Expanding from corner - keep building the base outward."
        elif is_grounded:
            tip = "Ground level piece - stable foundation."
        elif len(adjacent_pieces) > 0:
            adj_list = sorted(adjacent_pieces)
            tip = f"Layer z={min_z}: Connects to piece(s) {adj_list}."
        else:
            tip = f"Layer z={min_z}: Place carefully on the layer below."
        
        step = {
            "step": i + 1,
            "total_steps": len(ordered_pieces),
            "piece_index": i,
            "cells": [[x, y, z] for x, y, z in piece_tuples],
            "is_grounded": is_grounded,
            "z_level": min_z,
            "corner_distance": round(corner_dist, 2),
            "adjacent_to": sorted(adjacent_pieces),
            "accessible": accessible,
            "tip": tip,
        }
        steps.append(step)
        
        # Add to placed cells
        for cell in piece_tuples:
            placed_cells.add(cell)
    
    return steps


def analyze_solution_patterns(pieces: List[List[Point3D]]) -> Dict:
    """
    Analyze a solution for statistics.
    """
    by_layer = defaultdict(int)
    orientations = defaultdict(int)
    
    for piece in pieces:
        min_z = get_piece_min_z(piece)
        by_layer[min_z] += 1
        orientations[get_piece_orientation(piece)] += 1
    
    return {
        "total_pieces": len(pieces),
        "by_layer": dict(by_layer),
        "orientations": dict(orientations)
    }


if __name__ == "__main__":
    print("3D Chunk Patterns for T-Tetracube Puzzle:")
    print("=" * 50)
    for pattern in FALLBACK_PATTERNS:
        dims = pattern.get("dimensions", (0,0,0))
        print(f"\n{pattern['name']}")
        print(f"  {pattern['description']}")
        print(f"  Dimensions: {dims[0]}×{dims[1]}×{dims[2]}")
        print(f"  Difficulty: {pattern['difficulty']}")
        print(f"  Tip: {pattern['tip']}")
