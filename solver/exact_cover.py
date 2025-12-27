"""
exact_cover.py - Dancing Links (DLX) Implementation of Algorithm X

Mathematical Foundation:
========================
Algorithm X is a recursive, nondeterministic, depth-first, backtracking algorithm
that finds all solutions to the exact cover problem.

Given a matrix of 0s and 1s, we want to select a subset of rows such that
every column has exactly one 1 in the selected rows.

For our cube packing problem:
- Columns: 216 cells (one per cell in the 6×6×6 cube)
- Rows: 1440 placements (one per legal T-piece placement)
- Each row has 4 ones (the T-piece covers 4 cells)
- We need to select 54 rows (pieces) that cover all 216 cells exactly once

Dancing Links:
Knuth's "Dancing Links" technique uses doubly-linked lists to efficiently
implement the "covering" and "uncovering" operations. Each column and row
can be removed and restored in O(1) time.

Reference: Donald Knuth, "Dancing Links" (2000)
"""

from typing import List, Optional, Generator, Callable


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Node:
    """
    A node in the Dancing Links sparse matrix.
    
    Each node represents a 1 in the binary matrix.
    Nodes are linked in both directions (left/right within a row,
    up/down within a column).
    """
    __slots__ = ['left', 'right', 'up', 'down', 'column', 'row_id']
    
    def __init__(self):
        self.left: 'Node' = None
        self.right: 'Node' = None
        self.up: 'Node' = None
        self.down: 'Node' = None
        self.column: 'ColumnNode' = None
        self.row_id: int = -1  # Which row (placement) this node belongs to


class ColumnNode(Node):
    """
    A column header node.
    
    Contains additional information:
    - size: number of 1s in this column (used for heuristic column selection)
    - name: column identifier (cell index for our problem)
    """
    __slots__ = ['size', 'name']
    
    def __init__(self):
        super().__init__()
        self.size: int = 0
        self.name: int = -1


class DancingLinks:
    """
    Dancing Links matrix implementation.
    
    The matrix is represented as a torus of doubly-linked nodes.
    The header node is the entry point for traversing columns.
    """
    
    def __init__(self, num_columns: int):
        """
        Initialize the DLX matrix with the given number of columns.
        
        Args:
            num_columns: Number of columns (216 for our 6×6×6 cube)
        """
        self.header = ColumnNode()
        self.header.left = self.header
        self.header.right = self.header
        self.header.up = self.header
        self.header.down = self.header
        self.header.column = self.header
        self.header.name = -1
        
        # Create column headers
        self.columns: List[ColumnNode] = []
        prev = self.header
        
        for i in range(num_columns):
            col = ColumnNode()
            col.name = i
            col.size = 0
            col.column = col
            col.up = col
            col.down = col
            
            # Link horizontally
            col.left = prev
            col.right = self.header
            prev.right = col
            self.header.left = col
            
            self.columns.append(col)
            prev = col
        
        self.num_rows = 0
        self.solution_rows: List[int] = []
    
    def add_row(self, row_id: int, column_indices: List[int]) -> None:
        """
        Add a row to the matrix.
        
        Args:
            row_id: Identifier for this row (placement index)
            column_indices: List of column indices where this row has 1s
        """
        if not column_indices:
            return
        
        first_node = None
        prev_node = None
        
        for col_idx in column_indices:
            col = self.columns[col_idx]
            
            # Create new node
            node = Node()
            node.row_id = row_id
            node.column = col
            
            # Link vertically (at bottom of column)
            node.up = col.up
            node.down = col
            col.up.down = node
            col.up = node
            
            # Update column size
            col.size += 1
            
            # Link horizontally (circular list)
            if first_node is None:
                first_node = node
                node.left = node
                node.right = node
            else:
                node.left = prev_node
                node.right = first_node
                prev_node.right = node
                first_node.left = node
            
            prev_node = node
        
        self.num_rows += 1
    
    def choose_column(self) -> Optional[ColumnNode]:
        """
        Choose a column to cover using the "minimum remaining values" heuristic.
        
        This heuristic (also known as "S heuristic" in Knuth's paper) selects
        the column with the fewest 1s, which minimizes branching factor.
        
        Returns:
            Column with minimum size, or None if all columns are covered
        """
        if self.header.right is self.header:
            return None  # All columns covered - solution found!
        
        min_size = float('inf')
        min_col = None
        
        col = self.header.right
        while col is not self.header:
            if col.size < min_size:
                min_size = col.size
                min_col = col
                if min_size == 0:
                    break  # Can't do better than 0 (dead end)
            col = col.right
        
        return min_col
    
    def cover(self, col: ColumnNode) -> None:
        """
        Cover a column (remove it from the header list and remove all rows
        that have a 1 in this column from other columns they're in).
        
        This is the key operation that makes Algorithm X work.
        """
        # Remove column from header list
        col.right.left = col.left
        col.left.right = col.right
        
        # For each row in this column
        row = col.down
        while row is not col:
            # Remove this row from all other columns
            node = row.right
            while node is not row:
                node.down.up = node.up
                node.up.down = node.down
                node.column.size -= 1
                node = node.right
            row = row.down
    
    def uncover(self, col: ColumnNode) -> None:
        """
        Uncover a column (restore it - the "dancing" part of Dancing Links).
        
        This operation reverses cover() exactly, which is possible because
        we never actually delete nodes - we just modify their links.
        """
        # For each row in this column (in reverse order)
        row = col.up
        while row is not col:
            # Restore this row in all other columns
            node = row.left
            while node is not row:
                node.column.size += 1
                node.down.up = node
                node.up.down = node
                node = node.left
            row = row.up
        
        # Restore column in header list
        col.right.left = col
        col.left.right = col
    
    def solve(self, callback: Callable[[List[int]], bool] = None) -> Generator[List[int], None, None]:
        """
        Solve the exact cover problem using Algorithm X.
        
        Yields all solutions as lists of row IDs.
        
        Args:
            callback: Optional callback function that receives each solution.
                     If callback returns True, stop searching.
        
        Yields:
            Lists of row IDs that form complete solutions
        """
        yield from self._solve_recursive(callback)
    
    def _solve_recursive(self, callback: Callable[[List[int]], bool] = None) -> Generator[List[int], None, None]:
        """
        Recursive implementation of Algorithm X.
        
        Mathematical correctness:
        1. If no columns remain, we've found a solution
        2. Otherwise, choose a column c (heuristically, the smallest)
        3. For each row r that has a 1 in column c:
           a. Include r in the partial solution
           b. For each column j that r covers, cover j
           c. Recurse
           d. Uncover all columns covered by r (backtrack)
        """
        # Choose column with minimum size (MRV heuristic)
        col = self.choose_column()
        
        if col is None:
            # All columns covered - found a solution!
            solution = list(self.solution_rows)
            if callback is not None:
                if callback(solution):
                    return  # Stop if callback returns True
            yield solution
            return
        
        if col.size == 0:
            # Dead end - this column can't be covered
            return
        
        # Cover this column
        self.cover(col)
        
        # Try each row in this column
        row = col.down
        while row is not col:
            # Include this row in the solution
            self.solution_rows.append(row.row_id)
            
            # Cover all other columns this row touches
            node = row.right
            while node is not row:
                self.cover(node.column)
                node = node.right
            
            # Recurse
            yield from self._solve_recursive(callback)
            
            # Backtrack: uncover columns (in reverse order)
            node = row.left
            while node is not row:
                self.uncover(node.column)
                node = node.left
            
            # Remove this row from solution
            self.solution_rows.pop()
            
            row = row.down
        
        # Uncover the column
        self.uncover(col)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def build_dlx_matrix(num_columns: int, rows: List[List[int]]) -> DancingLinks:
    """
    Build a DLX matrix from a list of rows.
    
    Args:
        num_columns: Total number of columns
        rows: List of rows, where each row is a list of column indices
    
    Returns:
        Configured DancingLinks instance
    """
    dlx = DancingLinks(num_columns)
    for row_id, column_indices in enumerate(rows):
        dlx.add_row(row_id, list(column_indices))
    return dlx


def solve_exact_cover(num_columns: int, rows: List[List[int]], 
                      max_solutions: int = None) -> Generator[List[int], None, None]:
    """
    Solve an exact cover problem.
    
    Args:
        num_columns: Number of columns (items to cover)
        rows: List of rows (each row is a list of column indices it covers)
        max_solutions: Maximum number of solutions to find (None for all)
    
    Yields:
        Solutions as lists of row indices
    """
    dlx = build_dlx_matrix(num_columns, rows)
    
    solution_count = 0
    
    def callback(solution):
        nonlocal solution_count
        solution_count += 1
        if max_solutions is not None and solution_count >= max_solutions:
            return True  # Stop
        return False
    
    for solution in dlx.solve(callback):
        yield solution
        if max_solutions is not None and solution_count >= max_solutions:
            break


# =============================================================================
# VERIFICATION / TESTING
# =============================================================================

def verify_exact_cover() -> None:
    """
    Verify the DLX implementation with a simple test case.
    
    Test case from Knuth's paper:
    Columns: {A, B, C, D, E, F, G} = {0, 1, 2, 3, 4, 5, 6}
    Rows:
        0: {C, E, F}       = {2, 4, 5}
        1: {A, D, G}       = {0, 3, 6}
        2: {B, C, F}       = {1, 2, 5}
        3: {A, D}          = {0, 3}
        4: {B, G}          = {1, 6}
        5: {D, E, G}       = {3, 4, 6}
    
    The unique solution is rows {0, 3, 4} = {C,E,F} ∪ {A,D} ∪ {B,G}
    """
    print("Verifying exact cover module...")
    
    num_columns = 7
    rows = [
        [2, 4, 5],     # Row 0: C, E, F
        [0, 3, 6],     # Row 1: A, D, G
        [1, 2, 5],     # Row 2: B, C, F
        [0, 3],        # Row 3: A, D
        [1, 6],        # Row 4: B, G
        [3, 4, 6],     # Row 5: D, E, G
    ]
    
    solutions = list(solve_exact_cover(num_columns, rows))
    
    print(f"✓ Found {len(solutions)} solution(s)")
    
    assert len(solutions) == 1, f"Expected 1 solution, got {len(solutions)}"
    
    solution = sorted(solutions[0])
    expected = [0, 3, 4]
    assert solution == expected, f"Expected {expected}, got {solution}"
    print(f"✓ Solution is correct: rows {solution}")
    
    # Verify the solution covers all columns exactly once
    covered = set()
    for row_idx in solution:
        for col in rows[row_idx]:
            assert col not in covered, f"Column {col} covered twice"
            covered.add(col)
    
    assert covered == set(range(num_columns)), "Not all columns covered"
    print("✓ Solution covers all columns exactly once")
    
    print("\n✓ Exact cover verification complete!")


if __name__ == "__main__":
    verify_exact_cover()
