# Learning Guide: Mapping Logistics to QUBO

This guide maps the real-world "Ecosystem of Load Consolidation" to the mathematical world of Quantum Annealing (QUBO/CQM).

## The Ecosystem Map

### 1. The Entities
| Real World | Code (`domain_models.py`) | Math (CQM Variables) |
|------------|---------------------------|----------------------|
| **Cargo Item** | `Item` class | $x_i, y_i, z_i$ (Coordinates), $bin_{i,j}$ (Assignment) |
| **Truck/Container** | `Bin` class | $u_j$ (Bin used indicator) |
| **Rotation** | `allowed_orientations` | $o_{i,k}$ (Orientation selector) |

### 2. The Constraints (Hard Rules)
These *must* be met. In CQM, we add them as `cqm.add_constraint(...)`.

#### A. Geometric (The Basics)
- **No Overlap**: Two items cannot occupy the same space.
  - *Math*: If item $i$ and $k$ are in the same bin, their coordinates must differ by at least their dimension.
- **Containment**: Items must fit inside the bin dimensions.
  - *Math*: $x_i + length_i \le BinLength$

#### B. Weight (The New Frontier)
- **Bin Capacity**: Total weight of items in a bin $\le$ Max Payload.
  - *Math*: $\sum_{i \in Bin_j} weight_i \le MaxWeight_j$
  - *Implementation*: This is a simple linear constraint! Very efficient for CQM.

#### C. Stackability (Vertical Logic)
- **Load Bearing**: Item $i$ cannot support more than $X$ kg on top.
  - *Math*: If item $k$ is on top of item $i$, then $weight_k \le load\_bearing_i$.
  - *Complexity*: This requires knowing "what is on top of what", which is tricky. We often approximate this by checking vertical overlap ($z$ coordinates).

### 3. The Objectives (Soft Goals)
These are what we want to minimize.
- **Minimize Bins**: Use fewer trucks.
- **Minimize Height**: Pack tighter.
- **Balance Load**: Distribute weight evenly (Phase 2).

## How to Read the Code
1. Start with `src/domain_models.py`: Understand the data.
2. Look at `src/solver.py` (coming soon): See how data turns into Math.
3. Look at `examples/legacy/packing3d.py`: See the raw D-Wave implementation.
