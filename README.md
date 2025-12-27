# T-Tetracube 6×6×6 Cube Packing Solver

A mathematically rigorous solver that enumerates **all distinct tilings** of a 6×6×6 cube using 54 identical T-tetracubes, up to rotational symmetry.

## Demo

Run the static demo with precompiled solutions here online: https://ericspencer00.github.io/cubed-pack-solve/

## Problem Definition

- **Board**: 6×6×6 cube = 216 unit cells
- **Piece**: T-tetracube (4 unit cubes in a T-shape)
- **Goal**: Pack exactly 54 T-tetracubes to fill the cube completely
- **Uniqueness**: Solutions are counted modulo the 24 rotational symmetries of the cube

## Mathematical Foundation

This is an **Exact Cover Problem** solved using:

1. **Algorithm X** (Knuth's Dancing Links / DLX) - guarantees finding ALL solutions
2. **Symmetry Reduction** - canonical form computation under the cube rotation group

### Key Properties

- **Completeness**: The solver finds every valid tiling (no heuristics that break completeness)
- **Correctness**: Each solution covers all 216 cells exactly once
- **Uniqueness**: Equivalent solutions under cube rotations are identified and deduplicated

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Find Solutions

```bash
# Find first 10 unique solutions
python -m solver.solve --max 10 --output web/solutions.json

# Find ALL solutions (may take a long time!)
python -m solver.solve --output web/solutions.json

# Verify solutions are valid
python -m solver.solve --max 5 --verify
```

### View Solutions (Static)

1. Start a simple web server:
   ```bash
   cd web
   python3 -m http.server 8000
   ```

2. Open http://localhost:8000 in your browser

### View Solutions (Live Generation)

For real-time solution generation, use the live server:

```bash
source venv/bin/activate
python server.py
```

Then open http://localhost:8000 - you'll see a "Live" indicator and can generate more solutions on-demand with the "Generate More" buttons.

### Controls

- **Navigate**: Arrow keys or Prev/Next buttons
- **Rotate view**: Click and drag
- **Explode view**: See individual T-pieces separated
- **Opacity**: Adjust transparency
- **Wireframe**: Toggle wireframe rendering

## Project Structure

```
/solver
 ├── __init__.py      # Package initialization
 ├── geometry.py      # T-piece definition & 3D rotations (12 unique orientations)
 ├── placements.py    # Generate all legal placements (1440 in 6×6×6 cube)
 ├── exact_cover.py   # Dancing Links (DLX) Algorithm X implementation
 ├── symmetry.py      # Cube rotation canonicalization (24 rotations)
 ├── solve.py         # Main solver orchestration
 └── export.py        # JSON output for web viewer

/web
 ├── index.html       # Three.js viewer interface
 ├── viewer.js        # 3D rendering code
 └── solutions.json   # Pre-generated solutions

server.py             # Live solution generation server
 ├── viewer.js        # 3D rendering code
 └── solutions.json   # Generated solutions (after running solver)
```

## Technical Details

### T-Tetracube Orientations

The T-tetracube has **12 unique orientations** in 3D space (from the 24 cube rotations, half produce the same shape due to the T's symmetry).

### Placement Count

There are **1440 legal placements** of T-tetracubes within the 6×6×6 cube (all positions where the piece fits within bounds).

### Algorithm Complexity

- DLX matrix: 1440 rows × 216 columns
- Solution requires selecting 54 rows that cover all columns exactly once
- Search space is vast but DLX with pruning makes it tractable

### Symmetry Reduction

For each solution found, we:
1. Apply all 24 cube rotations
2. Compute canonical form (lexicographically smallest)
3. Store only canonical forms to eliminate duplicates

## Verification

Each module includes self-verification:

```bash
python -m solver.geometry     # Verify T-piece rotations
python -m solver.placements   # Verify placement generation
python -m solver.exact_cover  # Verify DLX with test case
python -m solver.symmetry     # Verify symmetry operations
```

## Output Format

Solutions are exported as JSON:

```json
{
  "metadata": {
    "problem": "6x6x6 cube with T-tetracubes",
    "total_solutions": 50,
    ...
  },
  "solutions": [
    {
      "id": 0,
      "pieces": [
        [[x,y,z], [x,y,z], [x,y,z], [x,y,z]],
        ...  // 54 pieces per solution
      ]
    }
  ]
}
```

## Performance

On a modern machine:
- ~40 solutions/second for enumeration
- Symmetry checking adds overhead but ensures uniqueness
- Full enumeration may take hours to days depending on total solution count

## References

- Knuth, D. E. (2000). "Dancing Links" - The DLX algorithm
- The rotation group of a cube (order 24)
- Exact cover and polycube packing problems

## License

MIT License
