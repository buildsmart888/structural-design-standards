"""
ACI 318M-25 Slab Design Implementation
=====================================

Enhanced slab design implementation based on ACI 318M-25 Building Code
for Structural Concrete. Migrated and improved from twoWaySlab project.

Based on:
- ACI 318M-25 Chapter 8: Two-Way Slab Systems  
- ACI 318M-25 Chapter 9: Flexural Design
- ACI 318M-25 Chapter 24: Deflection Control

การออกแบบพื้นตาม ACI 318M-25 ที่ปรับปรุงแล้ว
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from structural_standards.base.design_base import SlabDesign, DesignResult, DesignCheck, DesignStatus
from structural_standards.aci.aci318m25.materials.concrete import ACI318M25Concrete
from structural_standards.aci.aci318m25.materials.steel import ACI318M25ReinforcementSteel
from structural_standards.utils.validation import validate_positive, validate_range

class SlabType(Enum):
    """Types of slab systems"""
    ONE_WAY = "one_way"
    TWO_WAY_FLAT = "two_way_flat"
    FLAT_PLATE = "flat_plate"
    FLAT_SLAB = "flat_slab"

class SupportCondition(Enum):
    """Support conditions"""
    SIMPLY_SUPPORTED = "simply_supported"
    FIXED = "fixed"
    CONTINUOUS = "continuous"
    CANTILEVER = "cantilever"

@dataclass
class SlabGeometry:
    """Slab geometry properties"""
    length_x: float           # mm
    length_y: float           # mm  
    thickness: float          # mm
    cover: float              # mm
    effective_depth_x: float  # mm
    effective_depth_y: float  # mm
    slab_type: SlabType
    support_conditions: Dict[str, SupportCondition]

@dataclass
class SlabLoads:
    """Slab loading"""
    dead_load: float          # kN/m²
    live_load: float          # kN/m²
    superimposed_dead: float  # kN/m²
    load_factors: Dict[str, float] = None
    
    def __post_init__(self):
        if self.load_factors is None:
            self.load_factors = {'D': 1.4, 'L': 1.6}

@dataclass 
class SlabMoments:
    """Slab moment results"""
    moment_x_positive: float  # kN⋅m/m
    moment_x_negative: float  # kN⋅m/m
    moment_y_positive: float  # kN⋅m/m
    moment_y_negative: float  # kN⋅m/m
    shear_x: float            # kN/m
    shear_y: float            # kN/m

@dataclass
class SlabReinforcement:
    """Slab reinforcement layout"""
    bottom_bars_x: List[str]  # Bottom reinforcement in x-direction
    bottom_bars_y: List[str]  # Bottom reinforcement in y-direction
    top_bars_x: List[str]     # Top reinforcement in x-direction
    top_bars_y: List[str]     # Top reinforcement in y-direction
    spacing_x: float          # Spacing in x-direction (mm)
    spacing_y: float          # Spacing in y-direction (mm)
    
    def __post_init__(self):
        if not self.bottom_bars_x:
            self.bottom_bars_x = []
        if not self.bottom_bars_y:
            self.bottom_bars_y = []
        if not self.top_bars_x:
            self.top_bars_x = []
        if not self.top_bars_y:
            self.top_bars_y = []

class ACI318M25SlabDesign(SlabDesign):
    """
    ACI 318M-25 Slab Design Implementation
    
    Comprehensive slab design per ACI 318M-25:
    - One-way and two-way systems
    - Flexural reinforcement design
    - Deflection control
    - Minimum thickness requirements
    """
    
    def __init__(self, 
                 concrete: ACI318M25Concrete,
                 steel: ACI318M25ReinforcementSteel):
        """Initialize slab designer"""
        super().__init__(concrete, steel, "ACI 318M-25")
        
        # Strength reduction factors - ACI 318M-25 Chapter 21
        self.phi_factors = {
            'flexure': 0.90,
            'shear': 0.75, 
            'bearing': 0.65
        }
        
        # Standard bar database
        self.bar_areas = {
            '10M': 100,   # mm²
            '15M': 200,
            '20M': 300, 
            '25M': 500,
            '30M': 700
        }
    
    def calculate_minimum_thickness(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI slab calculate_minimum_thickness NOT VERIFIED: span/support geometry, "
            "code method eligibility, bar layout and complete limit states required"
        )

    def calculate_slab_moments_two_way(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI slab calculate_slab_moments_two_way NOT VERIFIED: span/support geometry, "
            "code method eligibility, bar layout and complete limit states required"
        )

    def design_flexural_reinforcement(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI slab design_flexural_reinforcement NOT VERIFIED: span/support geometry, "
            "code method eligibility, bar layout and complete limit states required"
        )

    def _design_minimum_reinforcement(self, width: float, depth: float) -> Dict[str, float]:
        """Design minimum reinforcement for temperature/shrinkage.

        ACI 318M-25 7.6.1.1 requires As,min = 0.0018·Ag, with 0.0020 permitted
        for fy <= 420 MPa and (0.0018)(420/fy) for fy > 520 MPa.
        `depth` must be the total slab thickness (gross area), not d.
        """
        if self.steel.fy <= 420:
            rho_min = 0.0020
        elif self.steel.fy <= 520:
            rho_min = 0.0018
        else:
            rho_min = 0.0018 * 420 / self.steel.fy
            
        As_min = rho_min * width * depth
        return self._select_reinforcement(As_min, width)
    
    def _select_reinforcement(self, As_required: float, width: float) -> Dict[str, float]:
        """Select bar size and spacing"""
        for bar_size in ['15M', '20M', '25M']:
            bar_area = self.bar_areas[bar_size]
            spacing = bar_area * width / As_required
            
            # Check spacing limits
            if 100 <= spacing <= 500:  # Practical range
                return {
                    'bar_size': bar_size,
                    'spacing': spacing,
                    'area_provided': bar_area * width / spacing,
                    'area_required': As_required
                }
        
        raise ValueError("Cannot find suitable reinforcement")
    
    def design_one_way_slab(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI slab design_one_way_slab NOT VERIFIED: span/support geometry, "
            "code method eligibility, bar layout and complete limit states required"
        )

    def design_two_way_slab(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI slab design_two_way_slab NOT VERIFIED: span/support geometry, "
            "code method eligibility, bar layout and complete limit states required"
        )

    def check_punching_shear(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI slab check_punching_shear NOT VERIFIED: span/support geometry, "
            "code method eligibility, bar layout and complete limit states required"
        )

    def check_minimum_thickness(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI slab check_minimum_thickness NOT VERIFIED: span/support geometry, "
            "code method eligibility, bar layout and complete limit states required"
        )

    def design(self, *args, **kwargs) -> DesignResult:
        """Never return PASS after the invalid one-way or Direct Design shortcuts."""
        return DesignResult(
            member_type="slab", design_method="ACI 318M-25 NOT VERIFIED",
            overall_status=DesignStatus.NOT_CHECKED,
            utilization_ratio=float("inf"),
            warnings=["Slab flexure/deflection/one- and two-way shear, valid "
                      "support conditions, Direct Design Method eligibility, "
                      "actual bar sizes/layers and detailing NOT VERIFIED."],
        )

    def check_strength(self, *args, **kwargs) -> List[DesignCheck]:
        raise NotImplementedError("Full ACI 318-25 slab strength NOT VERIFIED")

    def check_serviceability(self, *args, **kwargs) -> List[DesignCheck]:
        raise NotImplementedError("Full slab deflection and crack control NOT VERIFIED")

    @staticmethod
    def simply_supported_strip_actions(
            uniform_factored_load_kN_per_m2: float,
            clear_span_m: float, strip_width_m: float = 1.0) -> Dict[str, float]:
        """Pure statics for a KNOWN one-way, simply supported uniform-load strip.

        Mu=wL^2/8 and Vu=wL/2. Does not check ACI design, supports, SLS.
        """
        for name,v in (("w",uniform_factored_load_kN_per_m2),
                       ("span",clear_span_m),("strip width",strip_width_m)):
            if not math.isfinite(v) or v <= 0:
                raise ValueError(f"{name} must be positive finite")
        line_load = uniform_factored_load_kN_per_m2*strip_width_m
        return {"Mu_kNm":line_load*clear_span_m**2/8,
                "Vu_kN":line_load*clear_span_m/2,
                "scope":"simply supported uniform strip statics only"}
