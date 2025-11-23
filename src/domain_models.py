from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from enum import Enum

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Dimensions(BaseModel):
    length: float = Field(..., gt=0, description="Length in meters")
    width: float = Field(..., gt=0, description="Width in meters")
    height: float = Field(..., gt=0, description="Height in meters")

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height

class Item(BaseModel):
    """
    Represents a cargo item to be packed.
    """
    id: str
    dims: Dimensions
    weight: float = Field(..., gt=0, description="Weight in kg")
    
    # Constraints
    max_stack_weight: Optional[float] = Field(None, description="Max weight that can be placed on top of this item")
    is_fragile: bool = Field(False, description="If True, nothing heavy can be stacked on it")
    priority: Priority = Priority.MEDIUM
    
    # Orientation: (can_rotate_xy, can_rotate_yz, can_rotate_xz) - simplified for now
    allowed_orientations: List[Tuple[int, int, int]] = Field(default_factory=lambda: [(0,0,0)])

class Bin(BaseModel):
    """
    Represents a container or truck.
    """
    id: str
    dims: Dimensions
    max_weight: float = Field(..., gt=0, description="Max payload capacity in kg")
    
    # Advanced Logistics (Day 4)
    axle_max_weight: Optional[float] = Field(None, description="Max weight per axle (Front/Rear)")
    wheelbase: Optional[float] = Field(None, description="Distance between front and rear axles")
    center_of_gravity_target: Optional[Tuple[float, float]] = Field(None, description="Target (x, y) CoG")
    cog_tolerance: Optional[float] = Field(None, description="Allowed deviation from CoG target")
    
    # Future: Axle constraints
    # axle_weights: Optional[List[float]] = None

class PackingRequest(BaseModel):
    items: List[Item]
    bins: List[Bin]
    time_limit_seconds: int = 20
