# Architecture & Progress Overview

**For Contributors**: This document explains the new enterprise architecture and the progress made in Week 1.

## The New Architecture (Day 1)
We moved away from the flat script structure of the original demo to a modular, scalable Python package.

### Directory Structure
- **`src/`**: The production code.
    - **`domain_models.py`**: Defines the "Language" of our system. We use `Pydantic` models (`Item`, `Bin`) to ensure strict data validation. This is critical for the API layer later.
    - **`solver.py`**: The "Brain". This contains the `EnterpriseSolver` class which wraps the D-Wave CQM (Constrained Quadratic Model).
- **`examples/legacy/`**: The original D-Wave 3D bin packing script. Kept for reference but not used in production.
- **`tests/`**: Automated verification tests.

## Core Features (Day 2)
We have implemented the first "Hard Constraint" for real-world logistics: **Weight Limits**.

### The Weight Constraint
In the original toy problem, items had dimensions but no mass. We added:
1.  **`weight` attribute** to the `Item` model.
2.  **`max_weight` attribute** to the `Bin` model.
3.  **CQM Constraint**:
    $$ \sum_{i \in Bin_j} (x_{i,j} \cdot weight_i) \le MaxWeight_j $$
    *Where $x_{i,j}$ is the binary variable "Item i is in Bin j".*

### Verification
We created `tests/test_weight.py` which attempts to pack two 100kg items into a bin with 150kg capacity.
- **Expected Result**: The solver must use 2 bins (or fail if only 1 is allowed).
- **Status**: Implemented and ready for testing (requires D-Wave API token).

## Next Steps (Day 3+)
- **Stackability**: Ensuring heavy items don't crush fragile ones.
- **Orientation**: allowing items to rotate.
