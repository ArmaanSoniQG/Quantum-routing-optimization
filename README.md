# Quantum Routing Optimization Middleware

**Mission**: Build an enterprise-grade integration middleware that allows 3PL brokers and movers to optimize load consolidation using D-Wave's Quantum Annealing technology.

## Overview
This repository contains the source code for the "One-Click" optimization solution. It bridges the gap between complex logistics constraints (weight, axles, stackability) and QUBO formulations.

## Structure
- `src/`: Core application logic and solvers.
    - `domain_models.py`: Pydantic models defining the logistics ecosystem.
    - `solver.py`: The CQM (Constrained Quadratic Model) formulations.
- `docs/`: Documentation and learning guides.
- `examples/`: Example scripts and the legacy demo.
    - `legacy/`: The original 3D bin packing demo (reference).

## Getting Started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the tests:
   ```bash
   pytest
   ```

## Roadmap
- **Phase 1**: Domain Modeling & Core Formulation (Current)
- **Phase 2**: Middleware & API Layer
- **Phase 3**: Pilot Interface & Deployment