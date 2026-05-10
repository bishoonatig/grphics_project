# Computer Graphics Project

VectorLab Studio is a Python-based computer graphics application built with `pygame` and `PyOpenGL`. It provides interactive drawing, line and circle algorithms, curve rendering, geometric transformations, clipping, animation, save/load support, and a benchmark view for comparing drawing routines.

## Project Overview

This project lets you:

- Draw lines using DDA and Bresenham
- Draw circles using midpoint and Bresenham circle algorithms
- Create polygons, Bezier curves, and B-splines
- Clip lines and polygons against a clipping window
- Apply transformations such as translate, rotate, scale, reflect, and shear
- Animate selected shapes
- Save and load drawings from `drawing.json`
- Compare algorithm performance inside the app
- Switch between dark and light themes

## Project Structure

- `main.py` - application entry point and UI
- `shapes.py` - basic point and shape helpers
- `algorithms/` - drawing, transformation, clipping, animation, and save/load logic
- `drawing.json` - saved drawing data

## Requirements

- Python 3.12 or newer recommended
- `pygame`
- `PyOpenGL`

The repository also contains `package.json` because the workspace was set up with the Codex CLI tooling, but the graphics application itself runs from Python.

## Installation

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install the Python dependencies:

   ```powershell
   pip install pygame PyOpenGL
   ```

## Compilation and Execution

This project does not require a separate compilation step. It is a Python application, so you run it directly.

To start the program:

```powershell
python main.py
```

## Controls

### Drawing Tools

- `1` - DDA Line
- `2` - Bresenham Line
- `3` - Midpoint Circle
- `4` - Bresenham Circle
- `5` - Clip Line
- `6` - Clip Polygon
- `7` - Bezier Curve
- `8` - B-Spline
- `P` - Polygon

### File and View Actions

- `K` - Save drawing to `drawing.json`
- `L` - Load drawing and inspect JSON
- `M` - Compare algorithms
- `D` - Toggle theme
- `C` - Clear canvas

### Shape Operations

- Arrow keys - move selected shape
- `Q` / `E` - rotate counterclockwise / clockwise
- `-` / `+` - scale down / scale up
- `X` / `Y` - reflect across X or Y axis
- `H` / `J` - shear on X axis
- `U` / `I` - shear on Y axis
- `Delete` or `Backspace` - delete selected shape
- `A` - animate selected shape

### Mouse

- Left click on the canvas to place drawing points
- Right click on a shape to select it

## Save and Load

The application stores drawings in `drawing.json`. When you load a file, the app opens a JSON inspector so you can review the saved structure.

## Submission Guidelines

- Submit the source code in a compressed ZIP file.
- Include this README file with compilation and execution instructions.
- Submit the report in PDF format.

## Notes

- The project uses `pygame` for the interface and event loop.
- The app window size is fixed in `main.py`.
- If you change dependencies, update your local environment before running the project again.
