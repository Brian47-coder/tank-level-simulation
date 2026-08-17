# tank-level-simulation
Python/Tkinter GUI tool for 3D visualization and variable-geometry level-volume calculations in horizontal cylindrical tanks using Newton-Raphson.

# Horizontal Tank Level & Volume Simulator

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-informational)
![Matplotlib](https://img.shields.io/badge/Visualization-Matplotlib-orange)
![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-red)

An interactive Python application designed for 3D visualization, variable geometry adjustments, and precise liquid level/volume calculations in horizontal cylindrical tanks.

---

## Key Features

* **Numerical Engine:** Fast and robust root-finding via the Newton-Raphson method applied to the circular segment area equation.
* **Graphical User Interface:** Built using Tkinter following a clean Model-View-Controller (MVC) architecture (`TanqueModel`).
* **3D Interactive Rendering:** Real-time orthographic/isometric 3D projection powered by Matplotlib.
* **Dynamic Geometry Scaling:** On-the-fly adjustment of diameter, length, and volume parameters while preserving fill percentage states.

---

## Tech Stack

* **Language:** Python 3
* **GUI Framework:** Tkinter / CustomTkinter
* **Data Processing & Plotting:** Matplotlib, NumPy

---

## Installation & Running

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Brian47-coder/tank-level-simulation.git](https://github.com/Brian47-coder/tank-level-simulation.git)
   cd tank-level-simulation
