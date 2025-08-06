# CrossSolver

CrossSolver is a daily crossword generator powered by optimization and constraint-solving techniques. Designed to create one fresh crossword every day, it uses mathematical modeling to generate compact and challenging crossword grids. The project is planned for future integration into a web or mobile app, with a goal to eventually switch to an open-source solver.

The Daily Solver is the webpage. 

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Gurobi license (free academic license available)

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

4. **Test the optimization model:**
   ```bash
   cd server && python test.py
   ```

### Manual Installation

If you prefer to set up manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Roadmap

- [x] Initial prototype with Gurobi MIP model
- [ ] Refactor model to use an open-source solver (e.g., CBC, OR-Tools)
- [ ] Add visualization page for displaying crossword puzzles
- [ ] Build API to serve daily puzzles (Flask or FastAPI)
- [ ] Schedule daily puzzle generation (cron or task queue)
- [ ] Add support for difficulty levels
- [ ] Export puzzles to image/PDF formats
- [ ] Launch simple front-end app for daily users

## Features

- Optimization-based crossword generation using MIP
- Multiple objective options:
  - Maximize number of words
  - Maximize letters filled
  - Minimize empty space
  - Encourage grid symmetry
- Easily pluggable into a daily puzzle workflow

## How It Works

The generator solves a mathematical model that:

1. Takes a list of candidate words
2. Places them on a grid, obeying crossword rules
3. Optimizes the layout based on your chosen objective

It returns a 2D grid representing the filled crossword.

## Tech Stack

- Python
- Gurobi (`gurobipy`)
- Planned: Flask or FastAPI for serving puzzles
- Planned: HTML/CSS/JS for visualization

## Installation

```bash
git clone https://github.com/yourusername/CrossSolver.git
cd CrossSolver
pip install gurobipy
# Ensure Gurobi license is active
```

## Running the Solver

```bash
python crossword_solver.py
```

You can change the objective by editing the call:

```python
grid = solve_crossword(words, R=5, C=5, objective="max_letters")
```

Supported objectives:
- "max_words"
- "max_letters"
- "min_blanks"
- "symmetry"

## License

MIT License.

## Author

Developed by Nathalia Wolf. Built for fun and to prove a point. Mainly to procastinate working on my thesis. 
 
## Contributions

Feel free to open issues, suggest improvements, or submit pull requests.
