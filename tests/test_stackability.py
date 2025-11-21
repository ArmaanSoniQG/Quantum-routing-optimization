import unittest
from src.domain_models import Item, Bin, PackingRequest, Dimensions
from src.solver import EnterpriseSolver

class TestStackability(unittest.TestCase):
    def test_fragility_constraint(self):
        """
        Test that a fragile item cannot have anything stacked on top of it.
        """
        # Bin: 1x1 base, height 20. Forces stacking if we have 2 items.
        bin1 = Bin(
            id="tower-1", 
            dims=Dimensions(length=10, width=10, height=20),
            max_weight=100.0
        )
        
        # Item 1: Fragile (Must be on top)
        item_fragile = Item(
            id="fragile-box", 
            dims=Dimensions(length=10, width=10, height=10), 
            weight=10.0,
            is_fragile=True
        )
        
        # Item 2: Normal
        item_normal = Item(
            id="normal-box", 
            dims=Dimensions(length=10, width=10, height=10), 
            weight=10.0
        )
        
        request = PackingRequest(items=[item_fragile, item_normal], bins=[bin1])
        
        solver = EnterpriseSolver(time_limit=10)
        solver.build_model(request)
        result = solver.solve()
        
        if result['solution']:
            sol = result['solution']
            # Check z coordinates
            # We expect z_fragile > z_normal (fragile on top)
            # Note: This assumes z=0 is bottom.
            z_fragile = sol.get("z_0") # item 0 is fragile
            z_normal = sol.get("z_1")  # item 1 is normal
            
            print(f"Fragile Z: {z_fragile}, Normal Z: {z_normal}")
            
            # If they are stacked (same x,y), fragile must be higher
            self.assertGreater(z_fragile, z_normal, "Fragile item should be on top!")

    def test_load_bearing(self):
        """
        Test that a weak box cannot support a heavy box.
        """
        bin1 = Bin(id="tower-2", dims=Dimensions(length=10, width=10, height=20), max_weight=100.0)
        
        # Item 1: Weak (Max stack 5kg)
        item_weak = Item(
            id="weak-box", 
            dims=Dimensions(length=10, width=10, height=10), 
            weight=10.0,
            max_stack_weight=5.0
        )
        
        # Item 2: Heavy (20kg)
        item_heavy = Item(
            id="heavy-box", 
            dims=Dimensions(length=10, width=10, height=10), 
            weight=20.0
        )
        
        request = PackingRequest(items=[item_weak, item_heavy], bins=[bin1])
        
        solver = EnterpriseSolver(time_limit=10)
        solver.build_model(request)
        result = solver.solve()
        
        if result['solution']:
            sol = result['solution']
            z_weak = sol.get("z_0")
            z_heavy = sol.get("z_1")
            
            print(f"Weak Z: {z_weak}, Heavy Z: {z_heavy}")
            
            # Heavy item (20kg) cannot be on top of Weak item (limit 5kg)
            # So Weak must be on top of Heavy
            self.assertGreater(z_weak, z_heavy, "Weak item should be on top of heavy item!")

if __name__ == "__main__":
    unittest.main()
