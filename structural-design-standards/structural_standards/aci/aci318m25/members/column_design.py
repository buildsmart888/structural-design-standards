"""
ACI 318M-25 Column Design
========================

Implementation of column design according to ACI 318M-25.
Includes axial-moment interaction, slenderness effects, and detailing.

การออกแบบเสาตามมาตรฐาน ACI 318M-25
รวมการตรวจสอบปฏิสัมพันธ์แรงอัด-โมเมนต์ ผลของความเรียว และรายละเอียด
"""

import math
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from ....base.design_base import ColumnDesign, DesignResult, DesignCheck
from ....base.material_base import ConcreteMaterial, ReinforcementSteel
from ..materials.concrete import ACI318M25Concrete
from ..materials.steel import ACI318M25ReinforcementSteel
from ....utils.validation import StructuralValidator, validate_positive, validate_range


class ColumnType(Enum):
    """Column type classification"""
    SHORT = "short"
    INTERMEDIATE = "intermediate"
    SLENDER = "slender"


class ReinforcementPattern(Enum):
    """Reinforcement arrangement pattern"""
    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"
    BUNDLED = "bundled"


@dataclass
class ColumnGeometry:
    """Column geometry parameters"""
    width: float  # mm (b for rectangular, diameter for circular)
    depth: float  # mm (h for rectangular, same as width for circular)
    length: float  # mm (unsupported length)
    cross_section: str = "rectangular"  # "rectangular" or "circular"
    cover: float = 40.0  # mm
    
    @property
    def area(self) -> float:
        """Cross-sectional area"""
        if self.cross_section == "circular":
            return math.pi * (self.width/2)**2
        else:
            return self.width * self.depth
    
    @property
    def moment_of_inertia(self) -> float:
        """Moment of inertia about major axis"""
        if self.cross_section == "circular":
            return math.pi * self.width**4 / 64
        else:
            return self.width * self.depth**3 / 12


@dataclass
class ColumnLoads:
    """Column loading conditions"""
    axial_dead: float = 0.0  # kN
    axial_live: float = 0.0  # kN
    moment_x_dead: float = 0.0  # kN⋅m (about x-axis)
    moment_y_dead: float = 0.0  # kN⋅m (about y-axis)
    moment_x_live: float = 0.0  # kN⋅m
    moment_y_live: float = 0.0  # kN⋅m
    
    @property
    def axial_total(self) -> float:
        """Total axial load"""
        return self.axial_dead + self.axial_live
    
    @property
    def moment_x_total(self) -> float:
        """Total moment about x-axis"""
        return self.moment_x_dead + self.moment_x_live
    
    @property
    def moment_y_total(self) -> float:
        """Total moment about y-axis"""
        return self.moment_y_dead + self.moment_y_live


@dataclass
class ColumnReinforcement:
    """Column reinforcement layout"""
    longitudinal_bars: List[str]  # Bar designations
    tie_size: str = "DB10"  # Tie bar size
    tie_spacing: float = 200.0  # mm
    reinforcement_pattern: ReinforcementPattern = ReinforcementPattern.RECTANGULAR
    
    def __post_init__(self):
        if not self.longitudinal_bars:
            self.longitudinal_bars = []


class ACI318M25ColumnDesign(ColumnDesign):
    """
    ACI 318M-25 Column Design Implementation
    
    การออกแบบเสาตาม ACI 318M-25
    """
    
    def __init__(self, 
                 concrete: ACI318M25Concrete,
                 reinforcement: ACI318M25ReinforcementSteel):
        """
        Initialize column designer
        
        Parameters:
        -----------
        concrete : ACI318M25Concrete
            Concrete material
        reinforcement : ACI318M25ReinforcementSteel
            Reinforcement steel material
        """
        super().__init__()
        self.concrete = concrete
        self.reinforcement = reinforcement
        self.validator = StructuralValidator()
        
        # Design parameters from ACI 318M-25
        self.phi_compression = 0.65  # Tied columns
        self.phi_compression_spiral = 0.75  # Spiral columns
        self.phi_flexure = 0.9  # Flexure-controlled
        
        # Material properties
        self.fc = concrete.fc_prime
        self.fy = reinforcement.fy
        self.Es = reinforcement.elastic_modulus()
        self.Ec = concrete.elastic_modulus()
        
        # Strain limits
        self.epsilon_cu = 0.003  # Ultimate concrete strain
        self.epsilon_ty = self.fy / self.Es  # Yield strain of steel
    
    def design_axial_reinforcement(self,
                                 geometry: ColumnGeometry,
                                 loads: ColumnLoads,
                                 reinforcement_ratio: float = 0.02) -> DesignResult:
        """
        Design reinforcement for axial load with optional moment
        
        Parameters:
        -----------
        geometry : ColumnGeometry
            Column geometry
        loads : ColumnLoads
            Applied loads
        reinforcement_ratio : float
            Target reinforcement ratio (0.01 to 0.08)
            
        Returns:
        --------
        DesignResult
            Design results with required reinforcement
        """
        # Convert loads to consistent units
        Pu = loads.axial_total * 1000  # kN to N
        Mux = loads.moment_x_total * 1e6  # kN⋅m to N⋅mm
        Muy = loads.moment_y_total * 1e6  # kN⋅m to N⋅mm
        
        Ag = geometry.area  # mm²
        
        # Validate inputs
        validate_positive(Pu, "Axial load")
        validate_range(reinforcement_ratio, 0.01, 0.08, "Reinforcement ratio")
        
        # Determine if column is short or slender
        column_type = self.classify_column_slenderness(geometry)
        
        # Calculate slenderness effects if needed
        if column_type != ColumnType.SHORT:
            moment_magnifier = self.calculate_moment_magnification(geometry, loads)
            Mux *= moment_magnifier
            Muy *= moment_magnifier
        
        # Required steel area
        As_target = reinforcement_ratio * Ag  # mm²
        
        # Check reinforcement limits
        As_min = 0.01 * Ag  # 1% minimum
        As_max = 0.08 * Ag  # 8% maximum
        
        As_required = max(As_min, min(As_target, As_max))
        
        # Calculate axial capacity. ACI 318M-25 selects both φ and Pn,max from the
        # type of transverse reinforcement (Table 21.2.2 and Table 22.4.2.1), not
        # from the shape of the cross-section, so the spiral case must be requested
        # explicitly via ColumnGeometry.transverse_reinforcement.
        transverse = getattr(geometry, 'transverse_reinforcement', 'ties')
        spiral = transverse in ('spiral', 'spirals')
        phi = self.phi_compression_spiral if spiral else self.phi_compression
        
        # Pure axial capacity (ACI 318M-25 Eq. 22.4.2.2), fy limited to 550 MPa
        Po = 0.85 * self.fc * (Ag - As_required) + min(self.fy, 550.0) * As_required  # N
        # Table 22.4.2.1: Pn,max = 0.80Po (tied) or 0.85Po (spirally reinforced)
        phi_Pn_max = phi * (0.85 if spiral else 0.80) * Po
        
        # Check if axial load is within limits
        if math.sqrt(Mux**2 + Muy**2) < 0.1 * phi_Pn_max:
            # Primarily axial load
            phi_Pn = phi_Pn_max
            governing_mode = "Axial Compression"
        else:
            # Combined axial and moment - use interaction
            phi_Pn = self.axial_moment_interaction(geometry, As_required, Pu, 
                                                  math.sqrt(Mux**2 + Muy**2))
            governing_mode = "Combined Loading"
        
        # Calculate actual reinforcement ratio
        rho_provided = As_required / Ag
        
        # Design checks
        checks = [
            DesignCheck("Axial Strength", phi_Pn >= Pu,
                       f"φPn = {phi_Pn/1000:.0f} kN ≥ Pu = {Pu/1000:.0f} kN"),
            DesignCheck("Minimum Reinforcement", rho_provided >= 0.01,
                       f"ρ = {rho_provided:.3f} ≥ 0.01"),
            DesignCheck("Maximum Reinforcement", rho_provided <= 0.08,
                       f"ρ = {rho_provided:.3f} ≤ 0.08"),
            DesignCheck("Slenderness", column_type != ColumnType.SLENDER,
                       f"Column type: {column_type.value}")
        ]
        
        feasible = all(check.passes for check in checks)
        capacity_ratio = phi_Pn / Pu if Pu > 0 else float('inf')
        
        # Calculate minimum number of bars
        bar_area = self.reinforcement.bar_area()  # mm² per bar
        num_bars_required = math.ceil(As_required / bar_area)
        
        # Minimum bars for different sections
        if geometry.cross_section == "circular":
            min_bars = 6
        else:
            min_bars = 4
        
        num_bars = max(num_bars_required, min_bars)
        As_provided = num_bars * bar_area
        
        results = {
            'As_required_mm2': As_required,
            'As_provided_mm2': As_provided,
            'reinforcement_ratio': As_provided / Ag,
            'num_longitudinal_bars': num_bars,
            'bar_designation': self.reinforcement.bar_designation,
            'axial_capacity_kN': phi_Pn / 1000,
            'capacity_ratio': capacity_ratio,
            'column_type': column_type.value,
            'governing_mode': governing_mode,
            'strength_reduction_factor': phi
        }
        
        return DesignResult(
            is_adequate=feasible,
            capacity_ratio=capacity_ratio,
            governing_check="Axial Strength",
            design_details=results,
            checks=checks
        )
    
    def design_tie_reinforcement(self,
                               geometry: ColumnGeometry,
                               longitudinal_bars: int,
                               bar_size: str) -> DesignResult:
        """
        Design tie reinforcement according to ACI 318M-25
        
        Parameters:
        -----------
        geometry : ColumnGeometry
            Column geometry
        longitudinal_bars : int
            Number of longitudinal bars
        bar_size : str
            Longitudinal bar designation
            
        Returns:
        --------
        DesignResult
            Tie design results
        """
        # Tie size requirements (ACI 318M-25 Section 25.7.2)
        longitudinal_db = self.reinforcement.bar_diameter()  # mm
        
        # Minimum tie size
        if longitudinal_db <= 32:  # #10 bars or smaller
            tie_size_min = 10  # DB10 (10mm)
        else:
            tie_size_min = 13  # DB13 (13mm)
        
        # Tie spacing requirements (ACI 318M-25 Section 25.7.2)
        # s ≤ minimum of:
        # 1. 16 × longitudinal bar diameter
        # 2. 48 × tie diameter  
        # 3. Least dimension of column
        
        tie_diameter = max(tie_size_min, 10)  # Assume DB10 minimum
        
        s1 = 16 * longitudinal_db  # mm
        s2 = 48 * tie_diameter  # mm
        s3 = min(geometry.width, geometry.depth)  # mm
        s4 = 300  # mm (practical limit)
        
        tie_spacing = min(s1, s2, s3, s4)
        
        # Check tie arrangement
        if geometry.cross_section == "rectangular":
            # Rectangular ties
            if longitudinal_bars <= 4:
                tie_legs = 1  # Single rectangular tie
            elif longitudinal_bars <= 6:
                tie_legs = 1  # Single tie with intermediate legs possible
            else:
                tie_legs = 2  # Multiple ties may be needed
        else:
            # Circular section - spiral or circular ties
            tie_legs = 1
        
        # Tie area calculation (if needed for design)
        tie_area = math.pi * (tie_diameter/2)**2  # mm² per leg
        
        # Design checks
        checks = [
            DesignCheck("Tie Size", tie_diameter >= tie_size_min,
                       f"Tie diameter = {tie_diameter} mm ≥ {tie_size_min} mm"),
            DesignCheck("Tie Spacing", tie_spacing <= min(s1, s2, s3),
                       f"s = {tie_spacing:.0f} mm ≤ {min(s1, s2, s3):.0f} mm"),
            DesignCheck("Longitudinal Support", self.check_lateral_support(geometry, longitudinal_bars),
                       "All longitudinal bars adequately supported")
        ]
        
        feasible = all(check.passes for check in checks)
        
        results = {
            'tie_diameter_mm': tie_diameter,
            'tie_spacing_mm': tie_spacing,
            'tie_designation': f"DB{tie_diameter}",
            'tie_legs': tie_legs,
            'tie_area_mm2': tie_area,
            'spacing_controls': {
                '16db': s1,
                '48dt': s2,
                'least_dimension': s3
            }
        }
        
        return DesignResult(
            is_adequate=feasible,
            capacity_ratio=1.0,  # Not applicable for tie design
            governing_check="Tie Spacing",
            design_details=results,
            checks=checks
        )
    
    def check_biaxial_bending(self,
                            geometry: ColumnGeometry,
                            reinforcement: ColumnReinforcement,
                            loads: ColumnLoads) -> DesignResult:
        """
        Check biaxial bending using reciprocal load method
        
        Parameters:
        -----------
        geometry : ColumnGeometry
            Column geometry
        reinforcement : ColumnReinforcement
            Provided reinforcement
        loads : ColumnLoads
            Applied loads
            
        Returns:
        --------
        DesignResult
            Biaxial bending check results
        """
        # Convert loads
        Pu = loads.axial_total * 1000  # N
        Mux = loads.moment_x_total * 1e6  # N⋅mm
        Muy = loads.moment_y_total * 1e6  # N⋅mm
        
        # Calculate uniaxial capacities
        # Assuming reinforcement is known
        As_total = len(reinforcement.longitudinal_bars) * self.reinforcement.bar_area()
        
        # Uniaxial moment capacities at given axial load
        phi_Mnx = self.uniaxial_moment_capacity(geometry, As_total, Pu, "x")  # N⋅mm
        phi_Mny = self.uniaxial_moment_capacity(geometry, As_total, Pu, "y")  # N⋅mm
        
        # Biaxial interaction check using reciprocal load method
        # (ACI 318M-25 Section 22.4.2)
        if Pu >= 0.1 * self.fc * geometry.area:
            # High axial load
            alpha = 1.0
        else:
            # Low axial load
            alpha = 0.5
        
        # Interaction equation: (Mux/Mnx)^α + (Muy/Mny)^α ≤ 1.0
        if phi_Mnx > 0 and phi_Mny > 0:
            interaction_ratio = (abs(Mux)/phi_Mnx)**alpha + (abs(Muy)/phi_Mny)**alpha
        else:
            interaction_ratio = float('inf')
        
        # Design checks
        checks = [
            DesignCheck("Biaxial Interaction", interaction_ratio <= 1.0,
                       f"({abs(Mux)/1e6:.1f}/{phi_Mnx/1e6:.1f})^{alpha:.1f} + "
                       f"({abs(Muy)/1e6:.1f}/{phi_Mny/1e6:.1f})^{alpha:.1f} = {interaction_ratio:.3f} ≤ 1.0"),
            DesignCheck("X-axis Moment", abs(Mux) <= phi_Mnx,
                       f"|Mux| = {abs(Mux)/1e6:.1f} kN⋅m ≤ φMnx = {phi_Mnx/1e6:.1f} kN⋅m"),
            DesignCheck("Y-axis Moment", abs(Muy) <= phi_Mny,
                       f"|Muy| = {abs(Muy)/1e6:.1f} kN⋅m ≤ φMny = {phi_Mny/1e6:.1f} kN⋅m")
        ]
        
        feasible = interaction_ratio <= 1.0
        capacity_ratio = 1.0 / interaction_ratio if interaction_ratio > 0 else float('inf')
        
        results = {
            'interaction_ratio': interaction_ratio,
            'moment_capacity_x_kNm': phi_Mnx / 1e6,
            'moment_capacity_y_kNm': phi_Mny / 1e6,
            'applied_moment_x_kNm': Mux / 1e6,
            'applied_moment_y_kNm': Muy / 1e6,
            'axial_load_kN': Pu / 1000,
            'alpha_exponent': alpha
        }
        
        return DesignResult(
            is_adequate=feasible,
            capacity_ratio=capacity_ratio,
            governing_check="Biaxial Interaction",
            design_details=results,
            checks=checks
        )
    
    def classify_column_slenderness(self, geometry: ColumnGeometry) -> ColumnType:
        """
        Classify column based on slenderness ratio
        """
        # Slenderness ratio
        if geometry.cross_section == "circular":
            r = geometry.width / 4  # Radius of gyration
        else:
            r = min(geometry.width, geometry.depth) / math.sqrt(12)
        
        slenderness_ratio = geometry.length / r
        
        # Classification based on ACI 318M-25
        if slenderness_ratio <= 12:
            return ColumnType.SHORT
        elif slenderness_ratio <= 40:
            return ColumnType.INTERMEDIATE
        else:
            return ColumnType.SLENDER
    
    def calculate_moment_magnification(self, 
                                     geometry: ColumnGeometry, 
                                     loads: ColumnLoads) -> float:
        """
        Calculate moment magnification factor for slender columns
        """
        # Simplified approach - typically requires more detailed analysis
        # This is a placeholder for the complete P-δ analysis
        
        slenderness_ratio = geometry.length / (min(geometry.width, geometry.depth) / math.sqrt(12))
        
        if slenderness_ratio <= 22:
            return 1.0  # No magnification needed
        else:
            # Simplified magnification factor
            return 1.0 + 0.005 * (slenderness_ratio - 22)
    
    def axial_moment_interaction(self, 
                               geometry: ColumnGeometry,
                               As: float,
                               Pu: float,
                               Mu: float) -> float:
        """
        Calculate interaction capacity (simplified approach)
        """
        # This is a simplified interaction - full implementation would require
        # strain compatibility analysis
        
        Ag = geometry.area
        Po = 0.85 * self.fc * (Ag - As) + self.fy * As
        
        # Simplified interaction approximation
        phi = self.phi_compression
        e = Mu / Pu if Pu > 0 else 0  # Eccentricity
        
        # Whitney's approximation for tied columns
        if e < 0.1 * min(geometry.width, geometry.depth):
            # Small eccentricity
            Pn = 0.85 * Po
        else:
            # Large eccentricity - reduced capacity
            Pn = 0.85 * Po * (1 - e / (0.5 * min(geometry.width, geometry.depth)))
        
        return phi * max(Pn, 0)
    
    def uniaxial_moment_capacity(self, 
                                geometry: ColumnGeometry,
                                As: float,
                                Pu: float,
                                axis: str) -> float:
        """
        Calculate uniaxial moment capacity about specified axis
        """
        # Simplified calculation - full implementation requires strain compatibility
        
        if axis == "x":
            h = geometry.depth
            b = geometry.width
        else:
            h = geometry.width
            b = geometry.depth
        
        # Balanced condition approximation
        d = h - geometry.cover - 15  # Approximate effective depth
        
        # Simplified moment capacity
        Mn = As * self.fy * (d - 0.1 * h)  # Approximate internal moment arm
        
        return self.phi_flexure * Mn
    
    def check_lateral_support(self, geometry: ColumnGeometry, num_bars: int) -> bool:
        """
        Check if lateral support is adequate for longitudinal bars
        """
        # ACI 318M-25 Section 25.7.2
        # Every corner and alternate bar should be supported
        # Maximum distance between supported bars = 150mm
        
        if geometry.cross_section == "rectangular":
            # For rectangular sections
            bars_per_face = num_bars / 4  # Approximate
            if bars_per_face <= 2:
                return True  # Corner bars only
            else:
                # Check spacing between supported bars
                clear_span = max(geometry.width, geometry.depth) - 2 * geometry.cover
                max_unsupported_length = clear_span / (bars_per_face - 1)
                return max_unsupported_length <= 150  # mm
        else:
            # Circular sections generally acceptable with spiral or circular ties
            return True