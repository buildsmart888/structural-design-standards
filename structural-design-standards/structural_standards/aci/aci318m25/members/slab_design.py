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
    
    def calculate_minimum_thickness(self, geometry: SlabGeometry) -> float:
        """
        Calculate minimum slab thickness per ACI 318M-25 Table 7.3.1.1
        """
        longer_span = max(geometry.length_x, geometry.length_y)
        
        if geometry.slab_type == SlabType.ONE_WAY:
            support_type = list(geometry.support_conditions.values())[0]
            if support_type == SupportCondition.SIMPLY_SUPPORTED:
                ratio = 20
            elif support_type == SupportCondition.FIXED:
                ratio = 28
            elif support_type == SupportCondition.CONTINUOUS:
                ratio = 24
            else:  # Cantilever
                ratio = 10
                
            h_min = longer_span / ratio
            
        else:  # Two-way slabs
            # Two-way slab without beams - ACI 318M-25 Section 8.3.1.1
            ln = longer_span - 200  # Assume 200mm support width
            h_min = ln * (0.8 + self.steel.fy / 1400) / 36
            h_min = max(h_min, 125)  # 125mm minimum
            
        return h_min
    
    def calculate_slab_moments_two_way(self, geometry: SlabGeometry,
                                     loads: SlabLoads) -> SlabMoments:
        """
        Calculate moments for two-way slabs using Direct Design Method
        Enhanced from original aci318m25_slab.py with unit fix
        """
        # Total factored load
        wu = ((loads.dead_load + loads.superimposed_dead) * loads.load_factors['D'] + 
              loads.live_load * loads.load_factors['L'])
        
        # Convert dimensions to meters (FIXED unit conversion issue)
        lx = min(geometry.length_x, geometry.length_y) / 1000  # mm to m
        ly = max(geometry.length_x, geometry.length_y) / 1000  # mm to m
        
        # Total static moments - ACI 318M-25 Direct Design Method
        Mo_x = wu * lx * ly**2 / 8  # kN⋅m
        Mo_y = wu * ly * lx**2 / 8  # kN⋅m
        
        # Moment distribution (simplified)
        return SlabMoments(
            moment_x_positive=0.35 * Mo_x,
            moment_x_negative=0.65 * Mo_x, 
            moment_y_positive=0.35 * Mo_y,
            moment_y_negative=0.65 * Mo_y,
            shear_x=wu * ly / 2,
            shear_y=wu * lx / 2
        )
    
    def design_flexural_reinforcement(self, 
                                    moment: float,
                                    width: float,
                                    effective_depth: float) -> Dict[str, float]:
        """
        Design flexural reinforcement per ACI 318M-25 Chapter 9
        """
        if moment <= 0:
            return self._design_minimum_reinforcement(width, effective_depth)
        
        # Material properties
        fc = self.concrete.fc_prime
        fy = self.steel.fy
        phi = self.phi_factors['flexure']
        
        # Convert moment to N⋅mm
        Mu = moment * 1e6
        
        # Calculate required reinforcement using Whitney stress block
        Ru = Mu / (phi * width * effective_depth**2)
        
        # Reinforcement ratio
        rho = (0.85 * fc / fy) * (1 - math.sqrt(1 - 2 * Ru / (0.85 * fc)))
        
        # Check limits
        rho_min = max(1.4 / fy, 0.0020)  # ACI minimum 
        rho_max = 0.025  # Practical maximum
        
        rho = max(rho, rho_min)
        if rho > rho_max:
            raise ValueError("Required reinforcement exceeds maximum")
        
        # Required area
        As_required = rho * width * effective_depth
        
        # Select reinforcement
        return self._select_reinforcement(As_required, width)
    
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
    
    def design_one_way_slab(self, 
                          moment_ultimate: float,
                          slab_thickness: float, 
                          slab_width: float = 1000.0) -> Dict[str, float]:
        """Design one-way slab per ACI 318M-25"""
        effective_depth = slab_thickness - self.concrete.get_minimum_cover_requirements()['slab']
        
        return self.design_flexural_reinforcement(
            moment_ultimate, slab_width, effective_depth
        )
    
    def design_two_way_slab(self,
                          moment_x: float,
                          moment_y: float,
                          slab_thickness: float) -> Dict[str, Dict[str, float]]:
        """Design two-way slab reinforcement"""
        effective_depth = slab_thickness - self.concrete.get_minimum_cover_requirements()['slab']
        
        return {
            'x_direction': self.design_flexural_reinforcement(moment_x, 1000.0, effective_depth),
            'y_direction': self.design_flexural_reinforcement(moment_y, 1000.0, effective_depth - 20)  # Layer spacing
        }
    
    def check_punching_shear(self,
                           punching_force: float,
                           column_width: float,
                           column_depth: float, 
                           slab_thickness: float) -> DesignCheck:
        """Check punching shear per ACI 318M-25 Chapter 22"""
        effective_depth = slab_thickness - self.concrete.get_minimum_cover_requirements()['slab']
        
        # Critical perimeter
        bo = 2 * (column_width + column_depth + 2 * effective_depth)
        
        # Concrete punching shear strength
        fc = self.concrete.fc_prime
        lambda_factor = self.concrete.shear_strength_factor()
        vc = 0.17 * lambda_factor * math.sqrt(fc) * bo * effective_depth / 1000  # kN
        
        phi_Vc = self.phi_factors['shear'] * vc
        
        return self.create_design_check(
            name="Punching Shear",
            actual_value=punching_force,
            limit_value=phi_Vc,
            units="kN",
            description="Punching shear check at column",
            code_reference="ACI 318M-25 Section 22.6"
        )
    
    def check_minimum_thickness(self,
                              span_length: float,
                              support_conditions: str,
                              provided_thickness: float) -> DesignCheck:
        """Check minimum thickness per ACI 318M-25"""
        ratios = {
            'simply_supported': 20,
            'fixed': 28, 
            'continuous': 24,
            'cantilever': 10
        }
        
        ratio = ratios.get(support_conditions, 20)
        min_thickness = span_length / ratio
        # 7.3.1.1.1: for fy other than 420 MPa multiply by (0.4 + fy/700)
        min_thickness *= (0.4 + self.steel.fy / 700.0)
        
        return self.create_design_check(
            name="Minimum Thickness",
            actual_value=provided_thickness,
            limit_value=min_thickness,
            units="mm",
            description="Minimum thickness requirement",
            code_reference="ACI 318M-25 Table 7.3.1.1",
            is_lower_bound=True
        )
    
    def design(self, geometry: SlabGeometry, loads: SlabLoads) -> DesignResult:
        """Complete slab design"""
        result = DesignResult(
            member_type="slab",
            design_method="ACI 318M-25", 
            overall_status=DesignStatus.NOT_CHECKED,
            utilization_ratio=0.0
        )
        
        try:
            # Calculate moments
            if geometry.slab_type == SlabType.ONE_WAY:
                # One-way slab design
                wu = loads.dead_load * loads.load_factors['D'] + loads.live_load * loads.load_factors['L']
                span = max(geometry.length_x, geometry.length_y) / 1000
                moment = wu * span**2 / 8  # Simply supported
                
                reinforcement = self.design_one_way_slab(moment, geometry.thickness)
                
            else:
                # Two-way slab design  
                moments = self.calculate_slab_moments_two_way(geometry, loads)
                reinforcement = self.design_two_way_slab(
                    moments.moment_x_positive,
                    moments.moment_y_positive,
                    geometry.thickness
                )
            
            result.required_reinforcement = reinforcement
            result.overall_status = DesignStatus.PASS
            
            # Add design checks
            thickness_check = self.check_minimum_thickness(
                max(geometry.length_x, geometry.length_y),
                'continuous',
                geometry.thickness
            )
            result.add_strength_check(thickness_check)
            
        except Exception as e:
            result.overall_status = DesignStatus.FAIL
            result.notes.append(f"Design error: {str(e)}")
        
        return result