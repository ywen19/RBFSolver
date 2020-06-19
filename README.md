# RBF Solver in Maya 2019
---

## Synopsis
---

<img src="images/inUse.gif" width="1080">
A python Radial Basis Function solver plugin in Maya with UI for shape registration;  
Scripted for a university project.  

---

## Key Features
---

1. Radial Basis Function solver;  
   Pass (or connect) in vectors and output solved weight matrix;  
   
2. Shape registration deformer;  
   Take weight matrix from RBF solver and apply registration on input mesh;  
   Can be automatically connected by the tool UI;
   
3. Register tool;  
   A tool with GUI to manage inputs, connecting with plug-in nodes, and generates registration results;  
   After click **`register`** button the first time, changes can be made in real-time.  
   
---

## Usage
---

1. To Download/Clone
   - You can download the folder or clone with https://github.com/ywen19/RBFSolver.git .
2. Setup
   - Open Maya; Make sure numpy can be imported into Maya (**`import numpy`**).
   - Go to Preferences -> Plugin Manager.
   - Load in **`RBF_Solver.py`** and **`register_deformer.py`** as plugin.
   - Run **`register_tool.py`** in script editor to open GUI.
3. Manual Instruction on tool prototype
   - See from **`Synopsis`** video.
   
---

## Motivation & Background
---

Inspired by RBF algorithm described in ‘Expression Cloning’ [Noh and Neumann, 2001]. 

---


