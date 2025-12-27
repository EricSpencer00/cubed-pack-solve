"""
solve.py - Main T-Tetracube Cube Packing Solver

This module orchestrates the complete solution process:
1. Generate all legal placements
2. Build the exact cover matrix
3. Solve using Algorithm X (DLX)
4. Apply symmetry reduction to get unique solutions

Mathematical Correctness:
=========================
- The exact cover formulation guarantees that every cell is covered exactly once
- Algorithm X is complete: it finds ALL solutions
- Symmetry reduction via canonical forms ensures we count distinct tilings
  only once (modulo the 24 cube rotations)

Usage:
    python -m solver.solve [--max N] [--output FILE]
"""

import argparse
import time
import sys
from typing import List, Optional, Generator

from .placements import (
    get_placements, 
    NUM_CELLS, 
    NUM_PIECES,
    index_to_point,
    Placement
)
from .exact_cover import build_dlx_matrix, DancingLinks
from .symmetry import (
    SolutionSet, 
    placements_to_pieces,
    get_symmetry_breaking_placements
)


# =============================================================================
# SOLVER
# =============================================================================

class CubeSolver:
    """
    Complete solver for the T-tetracube 6×6×6 packing problem.
    
    Attributes:
        placements: All legal placements
        dlx: The Dancing Links matrix
        solution_set: Set of unique (canonical) solutions
    """
    
    def __init__(self, use_symmetry_breaking: bool = True):
        """
        Initialize the solver.
        
        Args:
            use_symmetry_breaking: If True, use symmetry-breaking constraints
                                  to speed up search (still guarantees completeness
                                  when combined with canonical form checking)
        """
        print("Initializing solver...")
        
        # Get all placements
        self.placements: List[Placement] = get_placements()
        print(f"  - {len(self.placements)} legal placements")
        
        # Get symmetry-breaking placements (those covering origin)
        self.origin_placements = get_symmetry_breaking_placements(self.placements)
        print(f"  - {len(self.origin_placements)} placements cover origin (0,0,0)")
        
        self.use_symmetry_breaking = use_symmetry_breaking
        
        # Solution storage
        self.solution_set = SolutionSet()
        
        # Statistics
        self.solutions_found = 0
        self.solutions_unique = 0
        self.start_time = None
        
        print("  - Solver initialized")
    
    def build_matrix(self) -> DancingLinks:
        """
        Build the DLX matrix for the exact cover problem.
        
        Returns:
            Configured DancingLinks instance
        """
        print("Building exact cover matrix...")
        
        dlx = DancingLinks(NUM_CELLS)
        
        # Add each placement as a row
        for row_id, placement in enumerate(self.placements):
            dlx.add_row(row_id, list(placement))
        
        print(f"  - Matrix: {len(self.placements)} rows × {NUM_CELLS} columns")
        return dlx
    
    def solve(self, max_solutions: Optional[int] = None, 
              report_interval: int = 1000,
              verbose: bool = True) -> Generator[List[List[tuple]], None, None]:
        """
        Solve the packing problem and yield unique solutions.
        
        Args:
            max_solutions: Maximum number of unique solutions to find (None for all)
            report_interval: How often to print progress (in raw solutions)
            verbose: Whether to print progress
        
        Yields:
            Unique solutions as lists of pieces (each piece is list of coordinates)
        """
        self.start_time = time.time()
        self.solutions_found = 0
        self.solutions_unique = 0
        
        dlx = self.build_matrix()
        
        if verbose:
            print("\nSolving exact cover problem...")
            print(f"  - Need to select {NUM_PIECES} pieces to cover {NUM_CELLS} cells")
            print(f"  - Using symmetry reduction: canonical forms under 24 cube rotations")
            print()
        
        # Solve and process solutions
        for solution_rows in dlx.solve():
            self.solutions_found += 1
            
            # Convert to piece coordinates
            pieces = placements_to_pieces(solution_rows, self.placements)
            
            # Add to solution set (handles deduplication)
            if self.solution_set.add(pieces):
                self.solutions_unique += 1
                
                if verbose:
                    elapsed = time.time() - self.start_time
                    print(f"  Found unique solution #{self.solutions_unique} "
                          f"(raw: {self.solutions_found}, time: {elapsed:.1f}s)")
                
                yield pieces
                
                if max_solutions is not None and self.solutions_unique >= max_solutions:
                    break
            
            # Progress report
            if verbose and self.solutions_found % report_interval == 0:
                elapsed = time.time() - self.start_time
                print(f"  Progress: {self.solutions_found} raw solutions, "
                      f"{self.solutions_unique} unique, {elapsed:.1f}s")
        
        if verbose:
            self._print_summary()
    
    def solve_all(self, max_solutions: Optional[int] = None) -> List[List[List[tuple]]]:
        """
        Solve and return all unique solutions as a list.
        
        Args:
            max_solutions: Maximum number of solutions to find
        
        Returns:
            List of all unique solutions
        """
        return list(self.solve(max_solutions=max_solutions))
    
    def _print_summary(self):
        """Print final summary statistics."""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("SOLUTION SUMMARY")
        print("="*60)
        print(f"  Total raw solutions found:    {self.solutions_found}")
        print(f"  Unique solutions (mod symmetry): {self.solutions_unique}")
        print(f"  Symmetry reduction ratio:     {self.solutions_found / max(1, self.solutions_unique):.1f}x")
        print(f"  Total time:                   {elapsed:.2f}s")
        print(f"  Solutions per second:         {self.solutions_found / max(0.001, elapsed):.1f}")
        print("="*60)


# =============================================================================
# VERIFICATION
# =============================================================================

def verify_solution(pieces: List[List[tuple]]) -> bool:
    """
    Verify that a solution is valid.
    
    Checks:
    1. Exactly 54 pieces
    2. Each piece has exactly 4 cells
    3. No overlapping cells
    4. All 216 cells covered
    
    Args:
        pieces: List of pieces (each piece is list of coordinates)
    
    Returns:
        True if valid, raises AssertionError otherwise
    """
    # Check piece count
    assert len(pieces) == NUM_PIECES, f"Expected {NUM_PIECES} pieces, got {len(pieces)}"
    
    # Collect all cells
    all_cells = []
    for piece in pieces:
        assert len(piece) == 4, f"Piece should have 4 cells, got {len(piece)}"
        for cell in piece:
            assert len(cell) == 3, f"Cell should be 3D coordinate, got {cell}"
            x, y, z = cell
            assert 0 <= x < 6 and 0 <= y < 6 and 0 <= z < 6, f"Cell out of bounds: {cell}"
            all_cells.append(cell)
    
    # Check no overlap
    assert len(all_cells) == len(set(all_cells)), "Overlapping cells found"
    
    # Check all cells covered
    assert len(all_cells) == NUM_CELLS, f"Expected {NUM_CELLS} cells, got {len(all_cells)}"
    
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Solve the T-tetracube 6×6×6 cube packing problem"
    )
    parser.add_argument(
        "--max", "-m",
        type=int,
        default=None,
        help="Maximum number of solutions to find (default: all)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output JSON file (default: print summary only)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify each solution (slower)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("T-TETRACUBE 6×6×6 CUBE PACKING SOLVER")
    print("="*60)
    print(f"  Board:   6×6×6 = {NUM_CELLS} cells")
    print(f"  Pieces:  {NUM_PIECES} T-tetracubes (4 cells each)")
    print(f"  Goal:    Find all distinct tilings (mod cube rotation)")
    print("="*60)
    print()
    
    solver = CubeSolver()
    
    solutions = []
    for solution in solver.solve(max_solutions=args.max, verbose=not args.quiet):
        if args.verify:
            verify_solution(solution)
        solutions.append(solution)
    
    if args.output:
        from .export import export_solutions
        export_solutions(solutions, args.output)
        print(f"\nSolutions saved to {args.output}")
    
    return len(solutions)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
