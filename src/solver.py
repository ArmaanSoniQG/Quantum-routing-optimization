from dimod import ConstrainedQuadraticModel, Binary, Real, quicksum
from dwave.system import LeapHybridCQMSampler
from typing import List, Tuple, Dict, Optional
from itertools import combinations
from .domain_models import Item, Bin, PackingRequest

class EnterpriseSolver:
    """
    CQM Solver for 3D Bin Packing with Enterprise Constraints.
    Includes: Weight, Geometry (Non-overlap), Stackability (Fragility/Load Bearing).
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
        
        # Pre-calculate large constant M for Big-M constraints
        # M should be larger than any possible dimension
        max_bin_dim = max(max(b.dims.length, b.dims.width, b.dims.height) for b in bins)
        M = max_bin_dim * 2

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
        self.x = {i: Real(f"x_{i}", lower_bound=0, upper_bound=max_bin_dim) for i in range(num_items)}
        self.y = {i: Real(f"y_{i}", lower_bound=0, upper_bound=max_bin_dim) for i in range(num_items)}
        self.z = {i: Real(f"z_{i}", lower_bound=0, upper_bound=max_bin_dim) for i in range(num_items)}
        
        # 4. Relative Position Selectors (for Non-Overlap)
        # b[i, k, d] = 1 if item i is relative to k in direction d
        # d=0: i left of k, 1: i right of k, 2: i behind k, 3: i front of k, 4: i below k, 5: i above k
        self.selector = {}
        for i, k in combinations(range(num_items), 2):
            for d in range(6):
                self.selector[(i, k, d)] = Binary(f"sel_{i}_{k}_{d}")

        # --- Constraints ---
        
        # C1. Every item must be in exactly one bin
        for i in range(num_items):
            self.cqm.add_constraint(
                quicksum(self.bin_loc[i, j] for j in range(num_bins)) == 1,
                label=f"item_{i}_assigned_once"
            )
            
        # C2. Bin Usage Link
        for i in range(num_items):
            for j in range(num_bins):
                self.cqm.add_constraint(
                    self.bin_loc[i, j] - self.bin_on[j] <= 0,
                    label=f"link_item_{i}_bin_{j}"
                )

        # C3. Geometric Boundaries (Containment)
        for i in range(num_items):
            for j in range(num_bins):
                # If item i is in bin j, it must fit
                # x_i + len_i <= bin_len_j + M(1 - bin_loc[i,j])
                self.cqm.add_constraint(
                    self.x[i] + items[i].dims.length - bins[j].dims.length <= M * (1 - self.bin_loc[i, j]),
                    label=f"contain_x_{i}_{j}"
                )
                self.cqm.add_constraint(
                    self.y[i] + items[i].dims.width - bins[j].dims.width <= M * (1 - self.bin_loc[i, j]),
                    label=f"contain_y_{i}_{j}"
                )
                self.cqm.add_constraint(
                    self.z[i] + items[i].dims.height - bins[j].dims.height <= M * (1 - self.bin_loc[i, j]),
                    label=f"contain_z_{i}_{j}"
                )

        # C4. Non-Overlap (The 3D Puzzle)
        for i, k in combinations(range(num_items), 2):
            # 1. Must be separated in at least one direction IF they are in the same bin
            # We check if they are in the same bin: sum(bin_loc[i,j] * bin_loc[k,j])
            # But that's quadratic. Simplified: Just enforce separation always? 
            # No, if they are in different bins, they don't need to separate.
            # Actually, if they are in different bins, coordinates don't matter relative to each other.
            # So we can just enforce: sum(selector) >= 1 - M * (items_in_diff_bins)
            # But simpler: sum(selector) >= 1. If they are in different bins, we can just pick "i left of k" arbitrarily.
            self.cqm.add_constraint(
                quicksum(self.selector[(i, k, d)] for d in range(6)) >= 1,
                label=f"separation_required_{i}_{k}"
            )
            
            # 2. Enforce the logic for each selector
            # d=0: i left of k => x_i + len_i <= x_k
            self.cqm.add_constraint(
                self.x[i] + items[i].dims.length - self.x[k] <= M * (1 - self.selector[(i, k, 0)]),
                label=f"sep_left_{i}_{k}"
            )
            # d=1: i right of k => x_k + len_k <= x_i
            self.cqm.add_constraint(
                self.x[k] + items[k].dims.length - self.x[i] <= M * (1 - self.selector[(i, k, 1)]),
                label=f"sep_right_{i}_{k}"
            )
            # d=2: i behind k => y_i + wid_i <= y_k
            self.cqm.add_constraint(
                self.y[i] + items[i].dims.width - self.y[k] <= M * (1 - self.selector[(i, k, 2)]),
                label=f"sep_behind_{i}_{k}"
            )
            # d=3: i front of k => y_k + wid_k <= y_i
            self.cqm.add_constraint(
                self.y[k] + items[k].dims.width - self.y[i] <= M * (1 - self.selector[(i, k, 3)]),
                label=f"sep_front_{i}_{k}"
            )
            # d=4: i below k => z_i + hgt_i <= z_k
            self.cqm.add_constraint(
                self.z[i] + items[i].dims.height - self.z[k] <= M * (1 - self.selector[(i, k, 4)]),
                label=f"sep_below_{i}_{k}"
            )
            # d=5: i above k => z_k + hgt_k <= z_i
            self.cqm.add_constraint(
                self.z[k] + items[k].dims.height - self.z[i] <= M * (1 - self.selector[(i, k, 5)]),
                label=f"sep_above_{i}_{k}"
            )

        # C5. Weight Constraint (From Day 2)
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

        # C6. STACKABILITY (Day 3 Feature)
        for i, k in combinations(range(num_items), 2):
            # Case A: Fragility
            # If item i is fragile, NOTHING can be above it.
            # "Above" means selector[(i, k, 4)] (i below k) is 1.
            if items[i].is_fragile:
                self.cqm.add_constraint(
                    self.selector[(i, k, 4)] == 0,
                    label=f"fragile_{i}_cannot_support_{k}"
                )
            if items[k].is_fragile:
                self.cqm.add_constraint(
                    self.selector[(i, k, 5)] == 0, # i above k
                    label=f"fragile_{k}_cannot_support_{i}"
                )
                
            # Case B: Load Bearing
            # If i is below k, weight of k <= load_bearing of i
            if items[i].max_stack_weight is not None:
                # If i below k (sel=1), then weight_k <= limit
                # weight_k * sel <= limit
                self.cqm.add_constraint(
                    items[k].weight * self.selector[(i, k, 4)] <= items[i].max_stack_weight,
                    label=f"load_bearing_{i}_supports_{k}"
                )
            if items[k].max_stack_weight is not None:
                # If k below i (sel=1 for i above k), then weight_i <= limit
                self.cqm.add_constraint(
                    items[i].weight * self.selector[(i, k, 5)] <= items[k].max_stack_weight,
                    label=f"load_bearing_{k}_supports_{i}"
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
