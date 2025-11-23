import unittest
from src.domain_models import Item, Bin, PackingRequest, Dimensions
from src.solver import EnterpriseSolver

class TestBalance(unittest.TestCase):
    def test_center_of_gravity(self):
        """
        Test that items are balanced around the target CoG.
        """
        # Bin: 20x10x10. Target CoG at x=10 (Center). Tolerance=2.
        bin1 = Bin(
            id="truck-1", 
            dims=Dimensions(length=20, width=10, height=10),
            max_weight=100.0,
            center_of_gravity_target=(10.0, 5.0), # Center of floor
            cog_tolerance=2.0
        )
        
        # Item 1: Heavy (50kg)
        item_heavy = Item(
            id="heavy-box", 
            dims=Dimensions(length=2, width=2, height=2), 
            weight=50.0
        )
        
        # Item 2: Light (5kg)
        item_light = Item(
            id="light-box", 
            dims=Dimensions(length=2, width=2, height=2), 
            weight=5.0
        )
        
        request = PackingRequest(items=[item_heavy, item_light], bins=[bin1])
        
        solver = EnterpriseSolver(time_limit=10)
        solver.build_model(request)
        result = solver.solve()
        
        if result['solution']:
            sol = result['solution']
            x_heavy = sol.get("x_0")
            
            print(f"Heavy Item X: {x_heavy}")
            
            # The heavy item dominates the CoG. 
            # If it were at x=0, CoG would be ~0.9. Target is 10 +/- 2.
            # So Heavy item MUST be near the center (8 to 12).
            # Center of item is x + 1.
            # CoG approx = (50*(x+1) + 5*(x_light+1)) / 55
            # We just check if it's reasonably centered.
            self.assertGreater(x_heavy, 5.0, "Heavy item should be near center to satisfy CoG")
            self.assertLess(x_heavy, 15.0, "Heavy item should be near center to satisfy CoG")

    def test_axle_weights(self):
        """
        Test that axle limits force load distribution.
        """
        # Bin: Wheelbase 10. Max Axle 40. Total Capacity 100.
        # If we load 60kg, it MUST be balanced 30/30 to pass (since max is 40).
        # If we put it all at front (x=0), Front Axle = 60 > 40. Fail.
        bin1 = Bin(
            id="truck-2", 
            dims=Dimensions(length=10, width=10, height=10),
            max_weight=100.0,
            wheelbase=10.0,
            axle_max_weight=40.0
        )
        
        # Item: 60kg
        item_heavy = Item(
            id="heavy-load", 
            dims=Dimensions(length=2, width=2, height=2), 
            weight=60.0
        )
        
        request = PackingRequest(items=[item_heavy], bins=[bin1])
        
        solver = EnterpriseSolver(time_limit=10)
        solver.build_model(request)
        result = solver.solve()
        
        if result['solution']:
            sol = result['solution']
            x_heavy = sol.get("x_0")
            print(f"Heavy Item X: {x_heavy}")
            
            # Center of item = x + 1.
            # Rear Load = 60 * (x+1)/10.
            # Front Load = 60 - Rear.
            # Both must be <= 40.
            # 20 <= Rear <= 40
            # 20 <= 6 * (x+1) <= 40
            # 3.33 <= x+1 <= 6.66
            # 2.33 <= x <= 5.66
            
            self.assertGreater(x_heavy, 2.0, "Item must be centered to balance axles")
            self.assertLess(x_heavy, 6.0, "Item must be centered to balance axles")

if __name__ == "__main__":
    unittest.main()
