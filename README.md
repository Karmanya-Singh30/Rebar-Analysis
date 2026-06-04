# Rebar Analysis

AI-powered structural rebar measurement and verification tool using computer vision and Generative AI.

## Overview

Rebar Analyzer Pro is a desktop application designed to automate the quality assurance process for structural engineering and construction. It analyzes high-resolution photographs of physical rebar layouts, calculates precise spatial measurements, and verifies them against original architectural designs.

The system uses an interactive computer vision pipeline to let users tag rebar rods and reference objects. It then calculates pixel-to-millimeter ratios and average radii using dynamic color sampling and ray-casting. Finally, it leverages Google Gemini 2.5 Pro to generate a strict, automated compliance report comparing the physical build to the CAD design.

## Key Features

* **Modern Desktop Interface:** Sleek, dark-mode GUI with threaded execution to prevent UI freezing.
* **Interactive Computer Vision:** Resizable, high-resolution OpenCV window with on-screen "Undo" and "Confirm" controls.
* **Automated Spatial Math:** Calculates real-world distances, sorts rods radially, and determines average rod radii using custom ray-casting.
* **Dynamic UI Scaling:** Graphics, text, and targeting reticles automatically scale to remain legible regardless of camera megapixel count.
* **AI Architectural Verification:** Automated table generation evaluating parameters (Number of rods, Radius, Distances) and determining "Acceptance" based on unit matching and tolerances.
* **Global Encoding Support:** Custom subprocess handling to ensure cross-platform terminal compatibility for complex UI symbols.

## Tech Stack

* Python
* OpenCV (`cv2`)
* CustomTkinter
* Google Generative AI (Gemini 2.5 Pro Vision)
* NumPy
* Pillow (PIL)
* Python-dotenv

## System Capabilities

| Parameter Verified | Analysis Method | AI Acceptance Criteria |
| :--- | :--- | :--- |
| **Rod Count** | Interactive CV tagging | Strict match required |
| **Average Radius** | Adaptive HSV masking & ray-casting | Unit-matched threshold |
| **Rod Distances** | Center-of-mass radial sorting & distance mapping | Unit-matched threshold |
