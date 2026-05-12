# VectorLab Studio Project Report

## 1. Introduction

VectorLab Studio is a desktop computer graphics application developed in Python as an educational project for demonstrating foundational raster graphics algorithms and interactive geometric operations. The system combines algorithm implementation with a visual interface so that users can draw primitives, transform shapes, clip objects, benchmark methods, and inspect how each algorithm progresses internally.

The project is designed to bridge theory and practice. Instead of treating drawing algorithms as abstract formulas only, the application exposes them through a live graphical workflow where the user can provide input points, preview algorithm equations, inspect intermediate steps, and observe the generated pixels before the shape is committed to the canvas.

## 2. Objectives

The project was developed with the following objectives:

- implement classical computer graphics algorithms manually rather than relying on high-level drawing libraries
- provide an interactive environment for drawing lines, circles, polygons, and curves
- support common geometric transformations for selected objects
- demonstrate clipping of lines and polygons against a rectangular clipping window
- compare drawing algorithm performance experimentally
- support saving and reloading drawing state
- improve educational value through an algorithm preview panel that displays formulas, step-by-step output, and pixel construction

## 3. Technologies Used

- Programming language: Python
- Primary graphics and UI library: `pygame`
- Optional mathematical equation renderer: `matplotlib` mathtext
- Data storage format: JSON

Although `shapes.py` contains OpenGL-related helper code from earlier work, the current application workflow is implemented through `pygame`.

## 4. System Overview

The application window is organized into three major regions:

- a left control panel for selecting drawing tools and file actions
- a central drawing canvas containing the active clipping window
- a right control panel for transformations, clipping window adjustments, and selection actions

The user interacts with the system by selecting a mode and placing points with the mouse. Once the required points are collected, the application constructs a preview of the chosen algorithm. The preview panel includes:

- a mathematical visualization area with equations
- a description of the rendering method used
- a step table showing intermediate values
- a square pixel viewport that animates the generated points

Only after the preview is accepted does the shape get added to the scene.

## 5. Implemented Algorithms

### 5.1 Line Drawing

Two line rasterization algorithms are implemented:

- Digital Differential Analyzer (DDA)
- Bresenham's Line Algorithm

The DDA method computes incremental floating-point steps between the start and end points. Bresenham's algorithm uses integer arithmetic and a decision parameter to determine the next pixel efficiently.

### 5.2 Circle Drawing

Two circle drawing algorithms are implemented:

- Midpoint Circle Algorithm
- Bresenham's Circle Algorithm

Both methods exploit eight-way symmetry to reduce repeated computation and draw circles efficiently from a center point and radius.

### 5.3 Curves

Two curve-generation techniques are supported:

- Bezier curves
- B-spline curves

Bezier curves are produced using Bernstein polynomial blending of control points. B-spline curves are generated using recursive basis function evaluation.

### 5.4 Clipping

Two clipping algorithms are included:

- Cohen-Sutherland line clipping
- Sutherland-Hodgman polygon clipping

These algorithms allow the user to visualize how primitives are trimmed to a rectangular clipping window.

### 5.5 Transformations

The project supports standard 2D transformations:

- translation
- rotation
- scaling
- reflection across x and y directions
- shear in x and y directions

Transformations operate on the currently selected shape. For non-circular shapes, the project applies transformations over point lists. For circles, translation affects the center while scaling updates the radius.

## 6. Functional Features

The completed system provides the following functionality:

- interactive point-based drawing
- shape selection by right-click
- preview-before-commit algorithm visualization
- save/load support through `drawing.json`
- animation preview for selected shapes
- dark/light theme toggle
- timing comparison of major drawing algorithms
- clipping window resizing
- deletion and canvas reset

## 7. Software Architecture

The codebase is intentionally modular and organized around responsibilities.

### 7.1 Main Application Layer

`main.py` contains:

- the main event loop
- application state
- user interface layout
- shape selection and input handling
- preview panel rendering
- dispatch logic for commands and transformations

### 7.2 Algorithm Modules

The `algorithms` directory isolates core graphics logic:

- `dda.py`: DDA line routine
- `bresenham.py`: Bresenham line routine
- `circle.py`: midpoint and Bresenham circle routines
- `bezier.py`: Bezier curve evaluation and rendering
- `bspline.py`: B-spline basis evaluation and rendering
- `clipping.py`: clipping algorithms
- `transformations.py`: geometric transformations
- `animation.py`: translation animation helper
- `performance.py`: execution timing helper
- `save_load.py`: shape serialization and deserialization

This structure separates algorithm implementations from interface management and makes the project easier to maintain and extend.

## 8. Algorithm Preview Panel

One of the strongest educational features of the project is the preview panel shown before a new shape is committed.

This panel was designed to improve clarity in the following ways:

- equations are displayed in a dedicated mathematical header area
- the top-right section explains which rendering method is used for the visible output
- the step table reveals rows progressively to show algorithm flow
- horizontal and vertical scrolling allow large tables to remain usable
- the pixel viewport animates the shape point by point
- the preview remains open until the user presses `Esc`

With the optional `matplotlib` dependency installed, equations can be rendered using math text rather than plain font glyphs, making the interface closer to a professional mathematics or CAD-oriented tool.

## 9. Data Representation

Shapes are represented as Python dictionaries with type-specific fields. Examples include:

- line: endpoints `x1`, `y1`, `x2`, `y2`
- circle: center `xc`, `yc` and radius `r`
- polygon and curves: list of `Point` objects under `points`

For persistence, these shapes are converted to JSON-compatible structures and stored in `drawing.json`.

## 10. User Workflow

A typical interaction sequence is:

1. select a drawing mode from the sidebar or keyboard shortcut
2. place the required points on the canvas
3. inspect the algorithm preview panel
4. press `Esc` to add the generated shape
5. select shapes for transformation or animation
6. save the scene or benchmark algorithms when needed

This workflow supports both practical drawing and algorithm study.

## 11. Testing and Verification

The project was verified through:

- direct execution in the `pygame` window
- shape creation in each supported drawing mode
- transformation operations on selected objects
- save/load testing using `drawing.json`
- clipping tests for lines and polygons
- Python compilation checks such as `python -m py_compile main.py`

Because the application is interactive and graphical, practical runtime testing is especially important in addition to static syntax validation.

## 12. Strengths

The project has several strengths:

- clear separation between UI logic and algorithm modules
- support for multiple classical graphics algorithms
- interactive visualization of intermediate algorithm states
- editable clipping window
- persistent storage through JSON
- educational value through step-by-step preview and pixel animation

## 13. Limitations

Current limitations include:

- fixed application window size
- no undo/redo history
- no arbitrary color picker or line thickness control
- no mouse-driven drag editing of existing shapes
- mathematical typesetting depends on an optional library
- the project is currently focused on 2D graphics only

## 14. Future Improvements

Possible future extensions include:

- undo and redo support
- export to image formats
- editable vertices after shape creation
- richer mathematical typesetting with matrices, derivatives, and integrals
- improved benchmarking views with charts
- additional algorithms such as ellipse drawing, scan-line polygon filling, and line anti-aliasing

## 15. Conclusion

VectorLab Studio successfully demonstrates the implementation and visualization of classical computer graphics algorithms in an interactive environment. The project combines algorithmic correctness, practical user interaction, and educational transparency through its preview system. As a coursework submission, it provides both a working graphics tool and a structured demonstration of key topics in 2D computer graphics.

