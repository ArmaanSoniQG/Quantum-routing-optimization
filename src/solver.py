from dimod import ConstrainedQuadraticModel, Binary, Real, quicksum
from dwave.system import LeapHybridCQMSampler
from typing import List, Tuple, Dict, Optional
from .domain_models import Item, Bin, PackingRequest

class EnterpriseSolver:
    """
    CQM Solver for 3D Bin Packing with Enterprise Constraints.
    """
    def __init__(self, time_limit: int = 20):
        self.time_limit = time_limit
        self.cqm = ConstrainedQuadraticModel()
        self.sampler = LeapHybridCQMSampler()

    def build_model(self, request: PackingRequest):
        """
        Builds the CQM model from the request.
        """
        items = request.items
        bins = request.bins
        num_items = len(items)
        num_bins = len(bins)
        
        # --- Variables ---
        
        # 1. Assignment: bin_loc[i, j] = 1 if item i is in bin j
        self.bin_loc = {
            (i, j): Binary(f"item_{i}_in_bin_{j}")
            for i in range(num_items)
            for j in range(num_bins)
        }
        
        # 2. Bin Usage: bin_on[j] = 1 if bin j is used
        self.bin_on = {
            j: Binary(f"bin_{j}_used")
            for j in range(num_bins)
        }
        
        # 3. Coordinates: x, y, z for each item
        # We use continuous variables for positions
        max_dim = max(b.dims.length + b.dims.width + b.dims.height for b in bins)
        self.x = {i: Real(f"x_{i}", lower_bound=0, upper_bound=max_dim) for i in range(num_items)}
        self.y = {i: Real(f"y_{i}", lower_bound=0, upper_bound=max_dim) for i in range(num_items)}
        self.z = {i: Real(f"z_{i}", lower_bound=0, upper_bound=max_dim) for i in range(num_items)}
        
        # 4. Orientation: o[i, k] (6 possible rotations)
        # For now, we assume fixed orientation to start simple, or add rotation later.
        # Let's stick to fixed orientation for Day 2 to ensure Weight works first.
        
        # --- Constraints ---
        
        # C1. Every item must be in exactly one bin
        for i in range(num_items):
            self.cqm.add_constraint(
                quicksum(self.bin_loc[i, j] for j in range(num_bins)) == 1,
                label=f"item_{i}_assigned_once"
            )
            
        # C2. Bin Usage Link: If item i is in bin j, bin j must be ON
        for i in range(num_items):
            for j in range(num_bins):
                self.cqm.add_constraint(
                    self.bin_loc[i, j] - self.bin_on[j] <= 0,
                    label=f"link_item_{i}_bin_{j}"
                )
                
        # C3. Geometric Boundaries (Simplified for fixed orientation)
        for i in range(num_items):
            for j in range(num_bins):
                # If item i is in bin j, x_i + len_i <= bin_len_j
                # M-trick: x_i + len_i - M(1 - bin_loc) <= bin_len
                # We'll implement the full geometric non-overlap in Day 3.
                # For Day 2, we focus on WEIGHT.
                pass

        # C4. WEIGHT CONSTRAINT (The Day 2 Goal)
        # Sum of weights of items in bin j <= Max Weight of bin j
        for j in range(num_bins):
            bin_capacity = bins[j].max_weight
            current_weight = quicksum(
                self.bin_loc[i, j] * items[i].weight 
                for i in range(num_items)
            )
            self.cqm.add_constraint(
                current_weight <= bin_capacity,
                label=f"bin_{j}_weight_limit"
            )

        # --- Objective ---
        # Minimize number of bins used
        self.cqm.set_objective(quicksum(self.bin_on[j] for j in range(num_bins)))
        
    def solve(self) -> Dict:
        """
        Submits to D-Wave Leap.
        """
        print("Submitting to D-Wave Leap...")
        sampleset = self.sampler.sample_cqm(self.cqm, time_limit=self.time_limit)
        feasible = sampleset.filter(lambda d: d.is_feasible)
        
        if len(feasible) == 0:
            return {"status": "Infeasible", "solution": None}
            
        best = feasible.first.sample
        return {"status": "Optimal", "solution": best}
