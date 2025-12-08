# CLAUDE.md - AI Assistant Guide for Sopromat

## Project Overview

**Sopromat** (Сопротивление материалов - Strength of Materials) is a desktop GUI application for structural analysis and diagram visualization. It solves classic engineering mechanics problems and generates force, stress, and deformation diagrams.

### Purpose
Educational tool for solving variant-based problems in structural mechanics courses:
- **Task 2**: Simply supported beam analysis - Shear force Q(x) and bending moment M(x) diagrams
- **Task 3**: Stepped rod under axial loading - Normal force N(x), stress σ(x), and elongation Δl(x) diagrams

## Technology Stack

- **Language**: Python 3.8+
- **GUI Framework**: PyQt5
- **Plotting**: Matplotlib (embedded in Qt via FigureCanvasQTAgg)
- **Numerical Computing**: NumPy
- **Data Structures**: Python dataclasses

## Project Structure

```
sopromat/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── gui/
│   ├── __init__.py        # Exports MainWindow
│   ├── main_window.py     # Main application window with controls
│   └── plot_canvas.py     # Matplotlib canvas for diagrams
└── solvers/
    ├── __init__.py        # Exports Task2Solver, Task3Solver
    ├── task2.py           # Beam solver (Q, M diagrams)
    └── task3.py           # Stepped rod solver (N, σ, Δl diagrams)
```

## Architecture

### Solver Pattern
Each task has a dedicated solver class following this pattern:

```python
class TaskNSolver:
    def __init__(self, N: int):       # N = variant number (1-35)
        self.params = self._calculate_params()
        self.results = None

    def solve(self) -> TaskNResults:  # Performs calculations
    def get_X_data(self) -> Tuple:    # Returns plotting data
    def get_key_points_X(self) -> List:  # Returns annotation points
```

### Data Flow
1. User selects variant number (1-35) and task type in GUI
2. Solver calculates parameters from variant using lookup tables
3. `solve()` computes reactions, forces, stresses
4. `get_*_data()` methods provide arrays for matplotlib
5. `PlotCanvas` renders diagrams with annotations

## Key Classes

### Task2Solver (task2.py)
Solves simply supported beam problems:
- **Input**: Variant N → derives L (length), a (force position), q (distributed load), F (point force)
- **Output**: Reactions RA, RB; max moment location and value
- **Methods**: `Q(x)`, `M(x)` - evaluate functions at any point

### Task3Solver (task3.py)
Solves stepped axial rod problems:
- **Input**: Variant N → derives geometry (L1, L2, L3), areas (A1, A2, A3), forces (F1, F2, F3), modulus E
- **Output**: Reaction RA; forces N1-N3; stresses σ1-σ3; total elongation; zero-crossing point
- **Methods**: `N(x)`, `sigma(x)`, `delta_l(x)` - evaluate at any point

### PlotCanvas (plot_canvas.py)
Matplotlib-based widget for rendering:
- Structural scheme (beam/rod with supports, loads, reactions)
- Force diagrams with hatching and sign annotations
- Key value labels at critical points

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Or use as module
python -m main
```

## Coding Conventions

### Language
- **Code**: English identifiers, English docstrings
- **UI/Comments**: Russian (Cyrillic) for user-facing text and detailed comments
- **Units in comments**: SI units (м, кН, МПа, ГПа)

### Style
- Use dataclasses for parameter/result containers
- Type hints on public methods
- Private methods prefixed with `_`
- Constants as class attributes (e.g., `ALPHA_R`, `XI_S`)

### Units Convention
| Quantity | Code Unit | Display Unit |
|----------|-----------|--------------|
| Length | meters (m) | м |
| Force | kilonewtons (kN) | кН |
| Distributed load | kN/m | кН/м |
| Moment | kN·m | кН·м |
| Area | cm² | см² |
| Stress | MPa | МПа |
| Modulus | GPa | ГПа |
| Elongation | mm | мм |

### Conversion Factors (in task3.py)
```python
# Stress: σ = N/A * 10 (kN/cm² → MPa)
# Elongation coefficient: k = 10 * N / (E * A) gives mm/m
```

## Variant System

Both tasks use a variant number N (1-35) to derive parameters:
```python
R = 1 + ((N - 1) % 7)   # R index: 1-7
K = 1 + ((N - 1) // 7)  # K index: 1-5
S = 1 + ((N - 1) % 5)   # S index: 1-5
```

Parameters are then computed using lookup tables (`ALPHA_R`, `XI_S`, etc.) and formulas specific to each task.

## Adding New Features

### Adding a New Task (Task 4, etc.)
1. Create `solvers/task4.py` with:
   - `Task4Params` dataclass
   - `Task4Results` dataclass
   - `Task4Solver` class with `solve()` and data getter methods
2. Export from `solvers/__init__.py`
3. Add plotting method `plot_task4()` in `PlotCanvas`
4. Add UI option in `MainWindow._create_control_panel()`
5. Add handler in `MainWindow._on_build_clicked()`

### Modifying Diagrams
- Edit `_draw_*_diagram()` methods in `plot_canvas.py`
- Key points come from solver's `get_key_points_*()` methods
- Color conventions: Blue (Q, N), Red (M, F2), Green (σ, reactions), Purple (Δl)

## Testing

Currently no automated tests. To verify calculations:
1. Run app with known variant
2. Compare results with manual calculations
3. Check equilibrium: ΣY = 0 for beams, ΣX = 0 for rods

## Common Issues

### Import Error for matplotlib.pyplot
`plot_canvas.py` imports `plt` at the end of file - this is intentional for `plt.Circle` usage.

### UI Scaling
Minimum window size is 1000x800. Plot canvas has minimum size 700x800 for readability.

## Git Workflow

- Main development on feature branches
- Commit messages in English
- Keep commits focused on single changes
