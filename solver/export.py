"""
export.py - JSON Export for Web Viewer

Exports solutions in a format suitable for the Three.js web viewer.

Output Format:
{
    "metadata": {
        "problem": "6x6x6 cube with T-tetracubes",
        "total_cells": 216,
        "pieces_per_solution": 54,
        "piece_type": "T-tetracube",
        "cells_per_piece": 4,
        "symmetry_group": "cube rotations (24 elements)",
        "generated_at": "2024-..."
    },
    "solutions": [
        {
            "id": 0,
            "pieces": [
                [[x,y,z], [x,y,z], [x,y,z], [x,y,z]],
                ...
            ]
        },
        ...
    ]
}
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from .placements import NUM_CELLS, NUM_PIECES, CUBE_SIZE


def solution_to_json(solution: List[List[tuple]], solution_id: int) -> Dict[str, Any]:
    """
    Convert a single solution to JSON-serializable format.
    
    Args:
        solution: List of pieces (each piece is list of (x,y,z) tuples)
        solution_id: Unique identifier for this solution
    
    Returns:
        Dictionary ready for JSON serialization
    """
    pieces = []
    for piece in solution:
        # Convert tuples to lists for JSON
        piece_coords = [[x, y, z] for x, y, z in piece]
        pieces.append(piece_coords)
    
    return {
        "id": solution_id,
        "pieces": pieces
    }


def export_solutions(solutions: List[List[List[tuple]]], 
                     output_path: str,
                     pretty: bool = True) -> None:
    """
    Export all solutions to a JSON file.
    
    Args:
        solutions: List of solutions
        output_path: Path to output JSON file
        pretty: Whether to format JSON for readability
    """
    data = {
        "metadata": {
            "problem": f"{CUBE_SIZE}x{CUBE_SIZE}x{CUBE_SIZE} cube with T-tetracubes",
            "cube_size": CUBE_SIZE,
            "total_cells": NUM_CELLS,
            "pieces_per_solution": NUM_PIECES,
            "piece_type": "T-tetracube",
            "cells_per_piece": 4,
            "symmetry_group": "cube rotations (24 elements)",
            "total_solutions": len(solutions),
            "generated_at": datetime.now().isoformat()
        },
        "solutions": [
            solution_to_json(sol, i) for i, sol in enumerate(solutions)
        ]
    }
    
    with open(output_path, 'w') as f:
        if pretty:
            json.dump(data, f, indent=2)
        else:
            json.dump(data, f)
    
    print(f"Exported {len(solutions)} solutions to {output_path}")


def export_solutions_compact(solutions: List[List[List[tuple]]], 
                             output_path: str) -> None:
    """
    Export solutions in a compact format (pieces only, no metadata).
    
    This is useful for very large solution sets where space matters.
    
    Args:
        solutions: List of solutions
        output_path: Path to output JSON file
    """
    # Just output array of solutions, each solution is array of pieces
    data = []
    for solution in solutions:
        sol_data = []
        for piece in solution:
            piece_coords = [[x, y, z] for x, y, z in piece]
            sol_data.append(piece_coords)
        data.append(sol_data)
    
    with open(output_path, 'w') as f:
        json.dump(data, f)
    
    print(f"Exported {len(solutions)} solutions (compact) to {output_path}")


# =============================================================================
# STATISTICS EXPORT
# =============================================================================

def export_statistics(solutions: List[List[List[tuple]]], 
                      output_path: str) -> None:
    """
    Export statistics about the solutions.
    
    Args:
        solutions: List of solutions
        output_path: Path to output JSON file
    """
    from collections import Counter
    
    stats = {
        "total_solutions": len(solutions),
        "piece_type": "T-tetracube",
        "cube_size": CUBE_SIZE,
    }
    
    # Analyze piece distribution (which cells are most commonly covered together)
    if solutions:
        # Count how often each cell is covered by each piece position
        cell_coverage = Counter()
        for solution in solutions:
            for piece in solution:
                for cell in piece:
                    cell_coverage[tuple(cell)] += 1
        
        stats["cell_coverage_min"] = min(cell_coverage.values())
        stats["cell_coverage_max"] = max(cell_coverage.values())
        stats["cell_coverage_avg"] = sum(cell_coverage.values()) / len(cell_coverage)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Exported statistics to {output_path}")


if __name__ == "__main__":
    # Test export with a dummy solution
    print("Testing export module...")
    
    # Create a fake solution (just for testing serialization)
    fake_piece = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]
    fake_solution = [fake_piece] * 54  # 54 pieces (won't be valid, just for testing)
    
    json_data = solution_to_json(fake_solution, 0)
    print(f"  - Converted solution to JSON: {len(json_data['pieces'])} pieces")
    
    # Verify JSON serialization works
    json_str = json.dumps(json_data)
    print(f"  - JSON string length: {len(json_str)} bytes")
    
    print("\n✓ Export module verification complete!")
