#!/usr/bin/env python3
"""
compile_static_data.py - Generate static patterns and tutorials for GitHub Pages

This script generates solutions and extracts:
- 10 common patterns (3D chunks for learning)
- 5 tutorial solutions (corner-first step-by-step)

Output files:
- web/data/patterns.json
- web/data/tutorials.json
"""

import json
import os
from solver.solve import CubeSolver
from solver.patterns import (
    get_all_patterns,
    order_solution_bfs,
    generate_tutorial_steps,
    analyze_solution_patterns
)


def generate_static_data(num_solutions=50, num_tutorials=5):
    """Generate and save static patterns and tutorials."""
    
    print(f"Generating {num_solutions} solutions...")
    solver = CubeSolver()
    solutions = solver.solve_all(max_solutions=num_solutions)
    print(f"✓ Generated {len(solutions)} solutions\n")
    
    # Extract patterns
    print("Extracting patterns...")
    patterns = get_all_patterns(solutions)
    print(f"✓ Found {len(patterns)} common patterns\n")
    
    # Limit to top 10 patterns
    patterns = patterns[:10]
    
    # Prepare patterns for JSON
    patterns_data = {
        "success": True,
        "patterns": [
            {
                "id": p["id"],
                "name": p["name"],
                "description": p["description"],
                "difficulty": p["difficulty"],
                "tip": p["tip"],
                "pieces": p["pieces"],
                "dimensions": p.get("dimensions", (0, 0, 0)),
                "frequency": p.get("frequency", "n/a")
            }
            for p in patterns
        ]
    }
    
    # Generate tutorials from first N solutions
    print(f"Generating {num_tutorials} tutorials...")
    tutorials_data = {
        "success": True,
        "tutorials": []
    }
    
    for i in range(min(num_tutorials, len(solutions))):
        solution = solutions[i]
        ordered = order_solution_bfs(solution)
        steps = generate_tutorial_steps(ordered)
        stats = analyze_solution_patterns(ordered)
        
        tutorials_data["tutorials"].append({
            "id": i,
            "piece_count": len(solution),
            "stats": {
                "total_pieces": stats["total_pieces"],
                "by_layer": stats["by_layer"],
                "orientations": stats["orientations"]
            },
            "steps": steps
        })
        
        print(f"  Tutorial {i+1}: {len(steps)} steps")
    
    print(f"✓ Generated {len(tutorials_data['tutorials'])} tutorials\n")
    
    # Create data directory
    data_dir = os.path.join("web", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Save patterns
    patterns_file = os.path.join(data_dir, "patterns.json")
    with open(patterns_file, "w") as f:
        json.dump(patterns_data, f, indent=2)
    print(f"✓ Saved patterns to {patterns_file}")
    print(f"  - {len(patterns_data['patterns'])} patterns")
    
    # Save tutorials
    tutorials_file = os.path.join(data_dir, "tutorials.json")
    with open(tutorials_file, "w") as f:
        json.dump(tutorials_data, f, indent=2)
    print(f"✓ Saved tutorials to {tutorials_file}")
    print(f"  - {len(tutorials_data['tutorials'])} tutorials")
    
    print("\n" + "="*60)
    print("STATIC DATA GENERATION COMPLETE")
    print("="*60)
    print("\nPattern Summary:")
    for p in patterns_data["patterns"]:
        dims = p["dimensions"]
        freq = p.get("frequency", "n/a")
        print(f"  {p['name']}: {len(p['pieces'])} pieces, {dims[0]}×{dims[1]}×{dims[2]}, freq={freq}")
    
    print("\nTutorial Summary:")
    for t in tutorials_data["tutorials"]:
        print(f"  Tutorial {t['id']+1}: {len(t['steps'])} steps, {t['stats']['total_pieces']} pieces")
    
    return patterns_data, tutorials_data


if __name__ == "__main__":
    generate_static_data(num_solutions=50, num_tutorials=5)
