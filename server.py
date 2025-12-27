"""
server.py - Local development server with live solution generation

Run this instead of the simple http.server to get:
- Static file serving for the web viewer
- API endpoint to generate more solutions on-demand

Usage:
    cd cubed-pack-solve
    source venv/bin/activate
    python server.py

Then open http://localhost:8000
"""

import http.server
import socketserver
import json
import os
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add solver to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from solver.placements import get_placements, NUM_CELLS
from solver.exact_cover import build_dlx_matrix
from solver.symmetry import SolutionSet, placements_to_pieces

PORT = 8000
WEB_DIR = Path(__file__).parent / "web"

# Global solver state
solver_lock = threading.Lock()
all_placements = None
solution_set = None
dlx_generator = None
is_solving = False


def init_solver():
    """Initialize the solver state."""
    global all_placements, solution_set, dlx_generator
    
    print("Initializing solver...")
    all_placements = get_placements()
    solution_set = SolutionSet()
    
    # Build DLX matrix
    dlx = build_dlx_matrix(NUM_CELLS, [list(p) for p in all_placements])
    dlx_generator = dlx.solve()
    
    print(f"Solver ready. {len(all_placements)} placements loaded.")


def generate_solutions(count: int) -> list:
    """Generate up to `count` new unique solutions."""
    global dlx_generator, is_solving
    
    if dlx_generator is None:
        init_solver()
    
    new_solutions = []
    
    with solver_lock:
        is_solving = True
        try:
            found = 0
            for solution_rows in dlx_generator:
                pieces = placements_to_pieces(solution_rows, all_placements)
                
                if solution_set.add(pieces):
                    # Convert to JSON-serializable format
                    solution_data = {
                        "id": len(solution_set) - 1,
                        "pieces": [[[x, y, z] for x, y, z in piece] for piece in pieces]
                    }
                    new_solutions.append(solution_data)
                    found += 1
                    
                    if found >= count:
                        break
        except StopIteration:
            pass
        finally:
            is_solving = False
    
    return new_solutions


class SolverHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with API endpoints for solution generation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/generate":
            self.handle_generate(parsed)
        elif parsed.path == "/api/status":
            self.handle_status()
        elif parsed.path == "/api/solutions":
            self.handle_get_solutions()
        else:
            # Serve static files
            super().do_GET()
    
    def handle_generate(self, parsed):
        """Generate more solutions on demand."""
        params = parse_qs(parsed.query)
        count = int(params.get("count", [10])[0])
        count = min(count, 100)  # Limit per request
        
        new_solutions = generate_solutions(count)
        
        response = {
            "success": True,
            "generated": len(new_solutions),
            "total": len(solution_set) if solution_set else 0,
            "solutions": new_solutions
        }
        
        self.send_json(response)
    
    def handle_status(self):
        """Get solver status."""
        response = {
            "ready": dlx_generator is not None,
            "solving": is_solving,
            "total_solutions": len(solution_set) if solution_set else 0
        }
        self.send_json(response)
    
    def handle_get_solutions(self):
        """Get all current solutions."""
        if solution_set is None:
            solutions = []
        else:
            solutions = [
                {
                    "id": i,
                    "pieces": [[[x, y, z] for x, y, z in piece] for piece in sol]
                }
                for i, sol in enumerate(solution_set.solutions)
            ]
        
        response = {
            "metadata": {
                "problem": "6x6x6 cube with T-tetracubes",
                "cube_size": 6,
                "total_cells": 216,
                "pieces_per_solution": 54,
                "piece_type": "T-tetracube",
                "cells_per_piece": 4,
                "symmetry_group": "cube rotations (24 elements)",
                "total_solutions": len(solutions),
                "live_generation": True
            },
            "solutions": solutions
        }
        
        self.send_json(response)
    
    def send_json(self, data):
        """Send JSON response."""
        content = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(content))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content)
    
    def log_message(self, format, *args):
        """Custom logging."""
        if '/api/' in args[0]:
            print(f"[API] {args[0]}")


def main():
    print(f"Starting T-Tetracube solver server on http://localhost:{PORT}")
    print(f"Serving files from: {WEB_DIR}")
    print()
    print("API Endpoints:")
    print(f"  GET /api/status     - Get solver status")
    print(f"  GET /api/solutions  - Get all current solutions")
    print(f"  GET /api/generate?count=N - Generate N more solutions")
    print()
    
    # Initialize solver in background
    init_thread = threading.Thread(target=init_solver)
    init_thread.start()
    
    with socketserver.TCPServer(("", PORT), SolverHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == "__main__":
    main()
