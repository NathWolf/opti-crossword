# CrossSolver

CrossSolver is a daily crossword generator powered by optimization and constraint-solving techniques. Designed to create one fresh crossword every day, it uses mathematical modeling to generate compact and challenging crossword grids. The project supports both Mixed-Integer Linear Programming (MILP) and Constraint Programming (CP) approaches.

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Gurobi license (free academic license available) - for MILP approach
- OR-Tools (open source) - for CP approach

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/crosssolver.git
   cd CrossSolver
   ```

2. **Set up the environment:**
   ```bash
   ./setup_env.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Test the optimization models:**
   ```bash
   cd server && python test_comparison.py
   ```

### Manual Installation

If you prefer to set up manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Two Solver Approaches

### 1. Gurobi (MILP) Approach
- **File**: `server/generator.py`
- **Method**: Mixed-Integer Linear Programming
- **License**: Commercial-grade solver with academic license
- **Best for**: Small grids (3x3, 4x4), limited word sets
- **Advantages**: 
  - Proven optimization techniques
  - Faster for small problems
  - Advanced MILP features
  - Commercial support available

### 2. CP-SAT (Constraint Programming) Approach
- **File**: `server/cp_sat_generator.py`
- **Method**: Google OR-Tools CP-SAT solver
- **License**: Open source
- **Best for**: Large grids (5x5+), large word sets (40+ words)
- **Advantages**:
  - No licensing costs
  - Better scalability
  - More intuitive constraint modeling
  - Consistent success rates
  - Easier to extend

## Configuration and Usage

### Using the Settings File

The main configuration file is `server/settings_crossword.py`. You can:

1. **Set Default Solver Method**:
   ```python
   DEFAULT_SOLVER_METHOD = "auto"  # Options: "gurobi", "cp_sat", "auto"
   ```

2. **Configure Individual Puzzles**:
   ```python
   CROSSWORD_CONFIGS = [
       {
           "name": "Daily Mini Crossword",
           "solver_method": "cp_sat",  # Force CP-SAT
           "R": 5, "C": 5,
           # ... other settings
       }
   ]
   ```

3. **Auto-Selection Rules**:
   ```python
   AUTO_SELECTION_RULES = {
       "small_grid_threshold": 5,  # Use Gurobi for grids < 5x5
       "large_word_threshold": 40,  # Use CP-SAT for word sets >= 40
   }
   ```

### Running Crosswords

```bash
# Generate all configured crosswords
python settings_crossword.py

# Generate specific crossword
python -c "from settings_crossword import generate_specific_crossword; generate_specific_crossword('Daily Mini Crossword')"

# Generate with specific solver method
python -c "from settings_crossword import generate_crossword_with_method; generate_crossword_with_method('Daily Mini Crossword', 'cp_sat')"
```

### Direct API Usage

#### Gurobi Approach
```python
from generator import generate_fixed_crossword

grid, valid_words, invalid_words, non_words = generate_fixed_crossword(
    R=5, C=5,
    min_word_length=3,
    max_word_length=5,
    max_words=50,
    time_limit=180
)
```

#### CP-SAT Approach
```python
from cp_sat_generator import generate_crossword_cp_sat

grid, valid_words, invalid_words, non_words = generate_crossword_cp_sat(
    R=5, C=5,
    min_word_length=3,
    max_word_length=5,
    max_words=50,
    time_limit=180
)
```

## Performance Comparison

Based on comprehensive testing with multiple grid sizes:

| Grid Size | CP-SAT Time | Gurobi Time | Speedup | Recommended |
|-----------|-------------|-------------|---------|-------------|
| 3x3 Small | 0.05s | 0.03s | 0.60x | Gurobi |
| 3x3 Large | 0.04s | 0.05s | 1.17x | CP-SAT |
| 4x4 Small | 1.36s | 0.73s | 0.54x | Gurobi |
| 4x4 Large | 3.58s | 1.92s | 0.54x | Gurobi |
| 5x5 Small | 9.66s | 45.19s | 4.68x | CP-SAT |
| 5x5 Large | 14.35s | 180.10s | 12.55x | CP-SAT |

### Key Findings

1. **Size-Dependent Performance**:
   - Small grids (3x3, 4x4): Gurobi is faster
   - Large grids (5x5+): CP-SAT is significantly faster
   - Crossover point: Around 4x4 to 5x5 grid size

2. **Reliability**:
   - CP-SAT: 100% success rate across all configurations
   - Gurobi: 100% success for smaller problems, 0% for 5x5 large

3. **Scalability**:
   - CP-SAT: Scales much better with problem size
   - Gurobi: Performance degrades rapidly with larger problems

## Testing and Comparison Tools

### Basic Comparison
```bash
python test_comparison.py
```

### Comprehensive Testing
```bash
python comprehensive_test.py
```

### Demo Scripts
```bash
python demo_cp_sat.py
```

## Roadmap

- [x] Initial prototype with Gurobi MIP model
- [x] CP-SAT implementation with OR-Tools
- [x] Solver method selection in settings
- [ ] Add visualization page for displaying crossword puzzles
- [ ] Use an LLM to generate hints with different dificulties
- [ ] Build API to serve daily puzzles (Flask or FastAPI)
- [ ] Schedule daily puzzle generation (cron or task queue)
- [ ] Add support for difficulty levels
- [ ] Export puzzles to image/PDF formats
- [ ] Launch simple front-end app for daily users

## Features

- Optimization-based crossword generation using both MILP and CP
- Multiple objective options:
  - Maximize number of words
  - Maximize letters filled
  - Minimize empty space
  - Encourage grid symmetry
- Easily pluggable into a daily puzzle workflow
- Comparison tools to evaluate different approaches
- Automatic solver selection based on problem size
- Configurable crossword settings

## How It Works

The generator solves a mathematical model that:

1. Takes a list of candidate words
2. Places them on a grid, obeying crossword rules
3. Optimizes the layout based on your chosen objective

It returns a 2D grid representing the filled crossword.

## Tech Stack

- Python
- Gurobi (`gurobipy`) - for MILP approach
- Google OR-Tools (`ortools`) - for CP approach
- Planned: Flask or FastAPI for serving puzzles
- Planned: HTML/CSS/JS for visualization

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `ortools` is installed
   ```bash
   pip install ortools>=9.0.0
   ```

2. **No Solution Found**: Try increasing `time_limit` or reducing `max_words`

3. **Memory Issues**: Reduce grid size or word count for very large problems

4. **Gurobi License**: Ensure you have a valid Gurobi license for MILP approach

### Performance Tips

1. **Start Small**: Begin with 3x3 or 4x4 grids
2. **Limit Words**: Use fewer words initially (20-30)
3. **Adjust Time Limits**: CP-SAT may need different time limits than Gurobi
4. **Word Selection**: Try `random_selection=True` for different results
5. **Solver Selection**: Use auto-selection or choose based on grid size

## Recommendations

### When to Use CP-SAT
1. Grid sizes 5x5 and larger
2. Large word sets (40+ words)
3. When reliability is critical
4. Open-source requirements
5. Rapid prototyping

### When to Use Gurobi
1. Small grids (3x3, 4x4)
2. Limited word sets (15-30 words)
3. When you have a commercial license
4. When you need advanced MILP features

### Hybrid Approach
Consider using both approaches:
- Use Gurobi for small problems (faster)
- Use CP-SAT for large problems (more reliable)
- Implement automatic switching based on problem size

## License

MIT License.

## Author

Developed by Nathalia Wolf. Built for fun and to prove a point. Mainly to procastinate working on my thesis. 
 
## Contributions

Feel free to open issues, suggest improvements, or submit pull requests.

## References

- [Google OR-Tools Documentation](https://developers.google.com/optimization)
- [CP-SAT Solver Guide](https://developers.google.com/optimization/cp/cp_solver)
- [Constraint Programming Tutorial](https://developers.google.com/optimization/cp/cp_tutorial)
- [Gurobi Documentation](https://www.gurobi.com/documentation/)
