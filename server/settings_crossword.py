#!/usr/bin/env python3
"""
Crossword Generator - Configuration and Generation Tool
This script allows you to easily configure and generate different types of crosswords.
Modify the configurations below to generate the crosswords you want.
"""

from generator import generate_fixed_crossword
from cp_sat_generator import generate_crossword_cp_sat
import time

# =============================================================================
# SOLVER METHOD CONFIGURATION
# =============================================================================
# Choose your preferred solver method:
# - "gurobi": Uses Gurobi MILP solver (faster for small grids, requires license)
# - "cp_sat": Uses Google OR-Tools CP-SAT solver (faster for large grids, open source)
# - "auto": Automatically selects the best method based on grid size

DEFAULT_SOLVER_METHOD = "auto"  # Options: "gurobi", "cp_sat", "auto"

# Auto-selection rules (used when method is "auto")
AUTO_SELECTION_RULES = {
    "small_grid_threshold": 5,  # Grid size below which Gurobi is preferred
    "large_word_threshold": 40,  # Word count above which CP-SAT is preferred
}

# =============================================================================
# CROSSWORD CONFIGURATIONS
# =============================================================================
# Modify these configurations to generate different types of crosswords

CROSSWORD_CONFIGS = [
    {
        "name": "Easier Challenge",
        "description": "5x5 crossword",
        "R": 5,
        "C": 5,
        "min_word_length": 4,
        "max_word_length": 5,
        "min_freq": 1e-5,
        "max_words": 60,
        "time_limit": 100,
        "n_limit": 1,
        "random_selection": True,
        "seed": None,  
        "solver_method": "cp_sat"
    },
    {
        "name": "Challenge Crossword",
        "description": "Large 9x9 crossword for challenges",
        "R": 9,
        "C": 9,
        "min_word_length": 4,
        "max_word_length": 8,
        "min_freq": 1e-5,
        "max_words": 1000,
        "time_limit": 100,
        "n_limit": 2,
        "random_selection": False,
        "seed": None,
        "solver_method": "cp_sat"  
    }
]

# =============================================================================
# SOLVER SELECTION FUNCTIONS
# =============================================================================

def select_solver_method(config):
    """Select the best solver method based on configuration and auto-rules."""
    method = config.get("solver_method", DEFAULT_SOLVER_METHOD)
    
    if method == "auto":
        # Auto-select based on grid size and word count
        grid_size = max(config["R"], config["C"])
        word_count = config["max_words"]
        
        if (grid_size < AUTO_SELECTION_RULES["small_grid_threshold"] or 
            word_count < AUTO_SELECTION_RULES["large_word_threshold"]):
            return "gurobi"
        else:
            return "cp_sat"
    
    return method

def get_solver_recommendation(config):
    """Get a recommendation for which solver to use."""
    grid_size = max(config["R"], config["C"])
    word_count = config["max_words"]
    
    if grid_size <= 4:
        return "gurobi", "Gurobi is typically faster for small grids (≤4x4)"
    elif grid_size >= 7 or word_count >= 50:
        return "cp_sat", "CP-SAT is typically faster for large grids (≥7x7) or many words (≥50)"
    else:
        return "auto", "Auto-selection will choose the best method based on problem size"

# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def generate_crossword(config):
    """Generate a crossword with the given configuration."""
    print(f"\n🧩 GENERATING: {config['name']}")
    print(f"📝 {config['description']}")
    print("=" * 60)
    
    # Determine solver method
    solver_method = select_solver_method(config)
    recommendation_method, recommendation_reason = get_solver_recommendation(config)
    
    print(f"🔧 Solver method: {solver_method.upper()}")
    if solver_method == "auto":
        print(f"💡 Recommendation: {recommendation_method.upper()} - {recommendation_reason}")
    
    start_time = time.time()
    
    # Generate crossword using selected method
    if solver_method == "cp_sat":
        grid, valid_words, invalid_words, non_word_combinations = generate_crossword_cp_sat(
            R=config["R"],
            C=config["C"],
            min_word_length=config["min_word_length"],
            max_word_length=config["max_word_length"],
            min_freq=config["min_freq"],
            max_words=config["max_words"],
            time_limit=config["time_limit"],
            random_selection=config.get("random_selection", False),
            seed=config.get("seed", None)
        )
    else:  # gurobi or auto (defaults to gurobi)
        grid, valid_words, invalid_words, non_word_combinations = generate_fixed_crossword(
            R=config["R"],
            C=config["C"],
            min_word_length=config["min_word_length"],
            max_word_length=config["max_word_length"],
            min_freq=config["min_freq"],
            max_words=config["max_words"],
            n_limit=config["n_limit"],
            time_limit=config["time_limit"],
            random_selection=config.get("random_selection", False),
            seed=config.get("seed", None)
        )
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    if grid:
        print(f"✅ SUCCESS! Generated in {generation_time:.2f} seconds using {solver_method.upper()}")
        print(f"📊 Grid size: {config['R']}x{config['C']}")
        print(f"📝 Valid words: {len(valid_words)}")
        print(f"⚠️  Invalid words: {len(invalid_words)}")
        print(f"🔢 Non-word combinations: {len(non_word_combinations)}")
        print(f"⬛ Black squares: {sum(1 for row in grid for cell in row if cell == '#')}")
        
        # Show word selection method
        if config.get("random_selection", False):
            seed_info = f" (seed: {config.get('seed', 'random')})" if config.get('seed') is not None else " (random seed)"
            print(f"🎲 Word selection: Random{seed_info}")
        else:
            print(f"📊 Word selection: Frequency-based (most common first)")
        
        # Display the crossword
        print(f"\n📋 GENERATED CROSSWORD:")
        print("-" * (config["C"] * 2 + 1))
        for row in grid:
            print(f"{' '.join(row)}")
        print("-" * (config["C"] * 2 + 1))
        
        # Show word lists
        print(f"\n📝 WORDS FOUND: {', '.join(valid_words)}")
        
        if invalid_words:
            print(f"\n⚠️  INVALID WORDS: {', '.join(invalid_words)}")
        
        return {
            "success": True,
            "grid": grid,
            "valid_words": valid_words,
            "invalid_words": invalid_words,
            "generation_time": generation_time,
            "solver_method": solver_method,
            "config": config
        }
    else:
        print(f"❌ FAILED! No solution found in {generation_time:.2f} seconds using {solver_method.upper()}")
        print(f"💡 Try adjusting the configuration parameters or switching solver method")
        
        # Suggest alternative solver
        if solver_method == "gurobi":
            print(f"💡 Suggestion: Try CP-SAT method for this problem size")
        elif solver_method == "cp_sat":
            print(f"💡 Suggestion: Try Gurobi method for this problem size")
        
        return {"success": False, "solver_method": solver_method, "config": config}

def generate_all_crosswords():
    """Generate all configured crosswords."""
    print("🧩 CROSSWORD GENERATOR")
    print("=" * 60)
    print(f"📋 Generating {len(CROSSWORD_CONFIGS)} different crosswords...")
    print(f"🔧 Default solver method: {DEFAULT_SOLVER_METHOD.upper()}")
    
    results = []
    
    for i, config in enumerate(CROSSWORD_CONFIGS, 1):
        print(f"\n🔧 [{i}/{len(CROSSWORD_CONFIGS)}] Generating {config['name']}...")
        result = generate_crossword(config)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {config['name']} completed successfully!")
        else:
            print(f"❌ {config['name']} failed to generate")
    
    # Summary
    print(f"\n📊 GENERATION SUMMARY:")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    print(f"✅ Successful: {successful}/{len(CROSSWORD_CONFIGS)}")
    
    # Group by solver method
    solver_stats = {}
    for result in results:
        if result["success"]:
            solver = result["solver_method"]
            if solver not in solver_stats:
                solver_stats[solver] = {"count": 0, "total_time": 0}
            solver_stats[solver]["count"] += 1
            solver_stats[solver]["total_time"] += result["generation_time"]
    
    for solver, stats in solver_stats.items():
        avg_time = stats["total_time"] / stats["count"]
        print(f"   • {solver.upper()}: {stats['count']} puzzles, avg {avg_time:.1f}s")
    
    for result in results:
        if result["success"]:
            config = result["config"]
            print(f"   • {config['name']}: {config['R']}x{config['C']}, {len(result['valid_words'])} words, {result['generation_time']:.1f}s ({result['solver_method'].upper()})")
    
    return results

def generate_specific_crossword(config_name):
    """Generate a specific crossword by name."""
    config = next((c for c in CROSSWORD_CONFIGS if c["name"] == config_name), None)
    
    if config:
        return generate_crossword(config)
    else:
        print(f"❌ Configuration '{config_name}' not found")
        print(f"Available configurations: {[c['name'] for c in CROSSWORD_CONFIGS]}")
        return {"success": False}

def generate_crossword_with_method(config_name, solver_method):
    """Generate a specific crossword with a specified solver method."""
    config = next((c for c in CROSSWORD_CONFIGS if c["name"] == config_name), None)
    
    if config:
        # Override the solver method
        config = config.copy()
        config["solver_method"] = solver_method
        return generate_crossword(config)
    else:
        print(f"❌ Configuration '{config_name}' not found")
        print(f"Available configurations: {[c['name'] for c in CROSSWORD_CONFIGS]}")
        return {"success": False}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function - generates all configured crosswords."""
    # You can modify this to generate specific crosswords
    # For example: generate_specific_crossword("Daily Mini Crossword")
    
    results = generate_all_crosswords()
    
    # Example of how to access results
    if results:
        print(f"\n🎯 USAGE EXAMPLES:")
        print("=" * 60)
        print("• To generate a specific crossword:")
        print("  generate_specific_crossword('Daily Mini Crossword')")
        print("• To generate with specific solver method:")
        print("  generate_crossword_with_method('Daily Mini Crossword', 'cp_sat')")
        print("• To modify configurations: Edit the CROSSWORD_CONFIGS list above")
        print("• To change default solver: Modify DEFAULT_SOLVER_METHOD")
        print("• Available solver methods: 'gurobi', 'cp_sat', 'auto'")

if __name__ == "__main__":
    main() 