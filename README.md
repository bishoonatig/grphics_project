# VectorLab Studio

VectorLab Studio is an interactive computer graphics application implemented in Python with `pygame`. The project demonstrates classical raster graphics algorithms, geometric transformations, clipping techniques, curve generation, shape persistence, and algorithm visualization inside a single desktop interface.

## Overview

The application was built as a computer graphics coursework project. Its main purpose is to let the user construct and inspect graphical primitives while comparing how different drawing algorithms behave.

Core capabilities:

- draw line segments using the Digital Differential Analyzer (DDA) algorithm
- draw line segments using Bresenham's line algorithm
- draw circles using the Midpoint Circle algorithm
- draw circles using Bresenham's circle algorithm
- create polygons from user-selected vertices
- generate Bezier curves from control points
- generate B-spline curves from control points
- clip lines using the Cohen-Sutherland algorithm
- clip polygons using the Sutherland-Hodgman algorithm
- apply translation, rotation, scaling, reflection, and shearing
- animate the selected shape through translation preview
- save drawings to `drawing.json`
- load saved drawings and inspect the JSON structure
- compare algorithm execution time on an off-screen surface
- preview algorithm equations, step tables, and pixel-by-pixel construction before committing a new shape

## Project Structure

- `main.py`: application entry point, event loop, UI, drawing workflow, algorithm preview panel, and shape management
- `shapes.py`: point helper class and legacy shape helpers
- `algorithms/dda.py`: DDA line rasterization
- `algorithms/bresenham.py`: Bresenham line rasterization
- `algorithms/circle.py`: midpoint and Bresenham circle rasterization
- `algorithms/bezier.py`: Bezier curve generation and drawing
- `algorithms/bspline.py`: B-spline basis evaluation and drawing
- `algorithms/clipping.py`: Cohen-Sutherland line clipping and Sutherland-Hodgman polygon clipping
- `algorithms/transformations.py`: geometric transformations on point sets
- `algorithms/animation.py`: translation-based animation preview
- `algorithms/performance.py`: timing helper for benchmark mode
- `algorithms/save_load.py`: shape serialization and deserialization
- `drawing.json`: sample saved drawing data

## Requirements

- Python 3.12 or newer recommended
- `pygame`

Optional dependency:

- `matplotlib`

`matplotlib` is only needed if you want the equation panel to render mathematical formulas with typeset math text. Without it, the program still runs and falls back to standard text rendering.

## Installation

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install pygame
```

To enable mathematical equation rendering in the preview panel:

```powershell
pip install matplotlib
```

## Running the Program

Start the application with:

```powershell
python main.py
```

No separate compilation step is required.

## User Interface Summary

The window is divided into three main areas:

- left sidebar: drawing tools and file actions
- center: canvas, clipping window, and shape preview area
- right sidebar: transformations, clipping window resize controls, selection information, and animation actions

When a shape receives the required number of input points, the application opens an algorithm preview panel before the shape is added to the canvas. This panel shows:

- mathematical equations related to the selected algorithm
- the rendering method used for line or curve construction
- a step table with vertical and horizontal scrolling
- an animated pixel-by-pixel preview in a square viewport

Press `Esc` to close the preview and commit the shape.

## Controls

Drawing modes:

- `1`: DDA line
- `2`: Bresenham line
- `3`: Midpoint circle
- `4`: Bresenham circle
- `5`: Clip line
- `6`: Clip polygon
- `7`: Bezier curve
- `8`: B-spline curve
- `P`: Polygon

File and display actions:

- `K`: save drawing
- `L`: load drawing and open JSON inspector
- `M`: open benchmark comparison
- `D`: toggle dark and light theme
- `C`: clear canvas

Selection and transformation:

- right click on a shape: select shape
- arrow keys: translate selected shape
- `Q` / `E`: rotate
- `-` / `+`: scale down or scale up
- `X` / `Y`: reflect
- `H` / `J`: shear in x direction
- `U` / `I`: shear in y direction
- `Delete` or `Backspace`: delete selected shape
- `A`: animate selected shape

Preview panel:

- `Esc`: accept preview and draw the shape
- mouse wheel or `Up` / `Down`: vertical step scrolling
- `Shift` + mouse wheel or `Left` / `Right`: horizontal step scrolling

## Data Format

Shapes are stored in `drawing.json` as dictionaries. Depending on the shape type, entries contain endpoint coordinates, circle center and radius, or lists of point coordinates.

Example shape kinds:

- `dda`
- `bresenham`
- `midpoint_circle`
- `bresenham_circle`
- `polygon`
- `bezier`
- `bspline`

## Notes

- The current implementation uses `pygame` for the UI and canvas rendering.
- `shapes.py` still contains legacy OpenGL helpers, but the main application flow is `pygame`-based.
- The application window size is fixed in `main.py`.
- Benchmark results are relative to the current machine and runtime state.

## Included Documentation

- `README.md`: setup, execution, controls, and feature summary
- `REPORT.md`: professional project report suitable as the basis for a formal submission document

