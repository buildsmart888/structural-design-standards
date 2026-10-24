"""
ACI 318M-25 Wall Design
======================

Implementation of wall design according to ACI 318M-25.
Includes bearing walls, shear walls, and out-of-plane flexure.

การออกแบบกำแพงตามมาตรฐาน ACI 318M-25
รวมกำแพงรับน้ำหนัก กำแพงรับแรงเฉือน และการดัดนอกระนาบ
"""

import math
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from ....base.design_base import MemberDesign, DesignResult, DesignCheck, DesignStatus
from ....base.material_base import ConcreteMaterial, ReinforcementSteel
from ..materials.concrete import ACI318M25Concrete
from ..materials.steel import ACI318M25ReinforcementSteel
from ....utils.validation import StructuralValidator, validate_positive, validate_range


class WallType(Enum):
    """Wall type classification"""
    BEARING = "bearing"  # Load-bearing wall
    SHEAR = "shear"      # Shear wall  
    NON_BEARING = "non_bearing"  # Non-load bearing partition


class WallBoundaryCondition(Enum):
    """Wall boundary conditions"""
    PINNED_TOP_BOTTOM = "pinned_top_bottom"
    FIXED_TOP_BOTTOM = "fixed_top_bottom"
    CANTILEVER = "cantilever"


@dataclass
class WallGeometry:
    """Wall geometry parameters"""
    length: float  # mm (plan length)
    height: float  # mm (story height)
    thickness: float  # mm
    cover: float = 40.0  # mm
    opening_area: float = 0.0  # mm² (total opening area)
    
    @property
    def gross_area(self) -> float:
        return self.length * self.thickness
    
    @property
    def net_area(self) -> float:
        return self.gross_area - self.opening_area


@dataclass
class WallLoads:
    """Wall loading conditions"""
    axial_dead: float = 0.0  # kN/m
    axial_live: float = 0.0  # kN/m
    wind_pressure: float = 0.0  # kPa
    seismic_pressure: float = 0.0  # kPa
    shear_force: float = 0.0  # kN
    overturning_moment: float = 0.0  # kN⋅m
    
    @property
    def total_axial(self) -> float:
        return self.axial_dead + self.axial_live
    
    @property
    def total_lateral_pressure(self) -> float:
        return abs(self.wind_pressure) + abs(self.seismic_pressure)


@dataclass
class WallReinforcement:
    """Wall reinforcement layout"""
    vertical_bars: Optional[List[str]] = None
    vertical_spacing: float = 400.0  # mm
    horizontal_bars: Optional[List[str]] = None
    horizontal_spacing: float = 400.0  # mm
    boundary_element_bars: Optional[List[str]] = None
    tie_size: str = "DB10"
    tie_spacing: float = 200.0  # mm
    
    def __post_init__(self):
        if self.vertical_bars is None:
            self.vertical_bars = []
        if self.horizontal_bars is None:
            self.horizontal_bars = []
        if self.boundary_element_bars is None:
            self.boundary_element_bars = []


class ACI318M25WallDesign(MemberDesign):
    """
    ACI 318M-25 Wall Design Implementation
    
    การออกแบบกำแพงตาม ACI 318M-25
    """
    
    def __init__(self, 
                 concrete: ACI318M25Concrete,
                 reinforcement: ACI318M25ReinforcementSteel):
        """Initialize wall designer"""
        super().__init__(concrete, reinforcement, "ACI 318M-25")
        self.concrete = concrete
        self.reinforcement = reinforcement
        self.validator = StructuralValidator()
        
        # Design parameters from ACI 318M-25
        self.phi_compression = 0.65
        self.phi_tension = 0.9
        self.phi_shear = 0.75
        
        # Material properties
        self.fc = concrete.fc_prime
        self.fy = reinforcement.fy
        self.Es = reinforcement.elastic_modulus()
        self.Ec = concrete.elastic_modulus()
        
        # Strain limits
        self.epsilon_cu = 0.003
        self.epsilon_ty = self.fy / self.Es
    
    def design(self,
               geometry: WallGeometry,
               loads: WallLoads,
               wall_type: WallType,
               boundary_condition: WallBoundaryCondition = WallBoundaryCondition.PINNED_TOP_BOTTOM) -> DesignResult:
        """Complete wall design according to ACI 318M-25"""
        
        result = DesignResult(
            member_type="wall",
            design_method="ACI 318M-25",
            overall_status=DesignStatus.NOT_CHECKED,
            utilization_ratio=0.0
        )
        
        try:
            # Validate inputs
            self._validate_inputs(geometry, loads)
            
            # Design based on wall type
            if wall_type == WallType.BEARING:
                self._design_bearing_wall(geometry, loads, boundary_condition, result)
            elif wall_type == WallType.SHEAR:
                self._design_shear_wall(geometry, loads, boundary_condition, result)
            else:
                self._design_non_bearing_wall(geometry, loads, boundary_condition, result)
            
            # Perform checks
            strength_checks = self.check_strength(geometry, loads, wall_type, boundary_condition)
            for check in strength_checks:
                result.add_strength_check(check)
            
            serviceability_checks = self.check_serviceability(geometry, loads, boundary_condition)
            for check in serviceability_checks:
                result.add_serviceability_check(check)
            
            detailing_checks = self._check_detailing_requirements(geometry, wall_type)
            for check in detailing_checks:
                result.add_detailing_check(check)
            
            # Determine overall status
            result.utilization_ratio = result.get_critical_ratio()
            result.overall_status = DesignStatus.PASS if result.is_adequate() else DesignStatus.FAIL
            
        except Exception as e:
            result.overall_status = DesignStatus.FAIL
            result.warnings.append(f"Design error: {str(e)}")
        
        return result
    
    def check_strength(self,
                      geometry: WallGeometry,
                      loads: WallLoads,
                      wall_type: WallType,
                      boundary_condition: WallBoundaryCondition) -> List[DesignCheck]:
        """Check strength requirements according to ACI 318M-25"""
        
        checks = []
        
        # Axial strength check (for bearing and shear walls)
        if wall_type in [WallType.BEARING, WallType.SHEAR]:
            check = self._check_axial_strength(geometry, loads)
            checks.append(check)
        
        # Flexural strength check
        check = self._check_flexural_strength(geometry, loads, boundary_condition)
        checks.append(check)
        
        # Shear strength check (for shear walls)
        if wall_type == WallType.SHEAR:
            check = self._check_shear_strength(geometry, loads)
            checks.append(check)
        
        # Slenderness check
        check = self._check_slenderness_limits(geometry, wall_type)
        checks.append(check)
        
        return checks
    
    def check_serviceability(self,
                           geometry: WallGeometry,
                           loads: WallLoads,
                           boundary_condition: WallBoundaryCondition) -> List[DesignCheck]:
        """Check serviceability requirements"""
        
        checks = []
        
        # Deflection check
        check = self._check_deflection_limits(geometry, loads, boundary_condition)
        checks.append(check)
        
        # Crack control check
        check = self._check_crack_control(geometry, loads)
        checks.append(check)
        
        return checks
    
    def _design_bearing_wall(self, geometry, loads, boundary_condition, result):
        """Design bearing wall for axial load and out-of-plane moment"""
        
        Pu = loads.total_axial * geometry.length  # N  ((kN/m)·(mm) ≡ N)
        q = loads.total_lateral_pressure * 1e-6  # kPa -> N/mm²
        
        # Calculate moment based on boundary conditions
        if boundary_condition == WallBoundaryCondition.PINNED_TOP_BOTTOM:
            Mu = q * geometry.length * geometry.height**2 / 8
        elif boundary_condition == WallBoundaryCondition.FIXED_TOP_BOTTOM:
            Mu = q * geometry.length * geometry.height**2 / 12
        elif boundary_condition == WallBoundaryCondition.CANTILEVER:
            Mu = q * geometry.length * geometry.height**2 / 2
        else:
            Mu = q * geometry.length * geometry.height**2 / 10
        
        # Design reinforcement
        rho_vertical = self._calculate_required_vertical_reinforcement(geometry, Pu, Mu)
        rho_horizontal = max(0.0012, 0.0020)  # Minimum horizontal reinforcement
        
        result.required_reinforcement = {
            'vertical_reinforcement_ratio': rho_vertical,
            'horizontal_reinforcement_ratio': rho_horizontal,
            'minimum_thickness': max(100, geometry.height / 25),
            'required_vertical_area': rho_vertical * geometry.thickness * 1000,
            'required_horizontal_area': rho_horizontal * geometry.thickness * 1000
        }
        
        result.design_forces = {
            'axial_force': Pu,
            'moment_per_meter': Mu,
            'lateral_pressure': q
        }
    
    def _design_shear_wall(self, geometry, loads, boundary_condition, result):
        """Design shear wall for in-plane forces"""
        
        Pu = loads.total_axial * geometry.length  # N  ((kN/m)·(mm) ≡ N)
        Vu = loads.shear_force * 1000  # N
        Mu = loads.overturning_moment * 1e6  # N⋅mm
        
        # Simplified design calculations
        As_flexural = max(0.0025 * geometry.gross_area, 1000)  # mm²
        As_shear = max(0.0020 * geometry.thickness * 1000, 200)  # mm²/m
        spacing = min(400, geometry.thickness * 3)  # mm
        
        boundary_required = (Mu / (Pu * geometry.length)) > (geometry.length / 6)
        As_boundary = 0.01 * geometry.thickness * 500 if boundary_required else 0.0
        
        result.required_reinforcement = {
            'flexural_reinforcement': As_flexural,
            'shear_reinforcement_area': As_shear,
            'shear_reinforcement_spacing': spacing,
            'boundary_elements_required': boundary_required,
            'boundary_element_area': As_boundary,
            'minimum_thickness': max(150, geometry.height / 20)
        }
        
        result.design_forces = {
            'axial_force': Pu,
            'shear_force': Vu,
            'overturning_moment': Mu
        }
    
    def _design_non_bearing_wall(self, geometry, loads, boundary_condition, result):
        """Design non-bearing wall for out-of-plane loads only"""
        
        q = loads.total_lateral_pressure * 1e-6  # kPa -> N/mm²
        
        # Calculate moment based on boundary conditions
        if boundary_condition == WallBoundaryCondition.PINNED_TOP_BOTTOM:
            Mu = q * geometry.height**2 / 8
        elif boundary_condition == WallBoundaryCondition.FIXED_TOP_BOTTOM:
            Mu = q * geometry.height**2 / 12
        elif boundary_condition == WallBoundaryCondition.CANTILEVER:
            Mu = q * geometry.height**2 / 2
        else:
            Mu = q * geometry.height**2 / 10
        
        # Design reinforcement
        As_required = max(0.0018 * geometry.thickness * 1000, 200)  # mm²/m
        As_min = 0.0018 * geometry.thickness * 1000
        As_design = max(As_required, As_min)
        
        result.required_reinforcement = {
            'required_reinforcement': As_design,
            'minimum_reinforcement': As_min,
            'reinforcement_direction': 'both_ways',
            'minimum_thickness': max(75, geometry.height / 30)
        }
        
        result.design_forces = {
            'moment_per_meter': Mu * geometry.length,
            'lateral_pressure': q
        }
    
    def _calculate_required_vertical_reinforcement(self, geometry, Pu, Mu):
        """Calculate required vertical reinforcement ratio"""
        
        t = geometry.thickness
        Ag = geometry.gross_area
        
        # Eccentricity
        e = Mu / max(Pu, 1.0)
        
        # Load eccentricity factor
        if e / t <= 1/6:
            # Small eccentricity - primarily compression
            rho_required = max(0.0012, Pu / (0.85 * self.fc * Ag * self.phi_compression))
        else:
            # Large eccentricity - combined bending and compression
            rho_required = 0.005
        
        # Apply limits
        return max(0.0012, min(rho_required, 0.04))
    
    def _check_axial_strength(self, geometry, loads):
        """Check axial strength capacity"""
        
        Pu = loads.total_axial * geometry.length  # N  ((kN/m)·(mm) ≡ N)
        Ag = geometry.gross_area
        
        # Assume 1% reinforcement for preliminary check
        rho = 0.01
        As = rho * Ag
        
        # Axial capacity (simplified)
        Pn = 0.85 * self.fc * (Ag - As) + self.fy * As
        phi_Pn = self.phi_compression * Pn
        
        ratio = Pu / phi_Pn if phi_Pn > 0 else float('inf')
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Axial Strength",
            status=status,
            value=Pu,
            limit=phi_Pn,
            ratio=ratio,
            units="N",
            description=f"Axial load demand vs capacity",
            code_reference="ACI 318M-25 Section 14.5"
        )
    
    def _check_flexural_strength(self, geometry, loads, boundary_condition):
        """Check flexural strength capacity"""
        
        q = loads.total_lateral_pressure * 1e-6  # kPa -> N/mm²
        
        # Calculate moment based on boundary conditions
        if boundary_condition == WallBoundaryCondition.PINNED_TOP_BOTTOM:
            Mu = q * geometry.height**2 / 8
        elif boundary_condition == WallBoundaryCondition.FIXED_TOP_BOTTOM:
            Mu = q * geometry.height**2 / 12
        elif boundary_condition == WallBoundaryCondition.CANTILEVER:
            Mu = q * geometry.height**2 / 2
        else:
            Mu = q * geometry.height**2 / 10
        
        Mu_total = Mu * geometry.length
        
        # Simplified flexural capacity
        rho_min = 0.0018
        As = rho_min * geometry.thickness * geometry.length
        d = geometry.thickness - geometry.cover - 8
        
        a = As * self.fy / (0.85 * self.fc * geometry.length)
        Mn = As * self.fy * (d - a/2)
        phi_Mn = self.phi_tension * Mn
        
        ratio = Mu_total / phi_Mn if phi_Mn > 0 else float('inf')
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Flexural Strength",
            status=status,
            value=Mu_total,
            limit=phi_Mn,
            ratio=ratio,
            units="N⋅mm",
            description=f"Out-of-plane moment demand vs capacity",
            code_reference="ACI 318M-25 Section 14.6"
        )
    
    def _check_shear_strength(self, geometry, loads):
        """Check shear strength capacity for shear walls"""
        
        Vu = loads.shear_force * 1000  # N
        Acv = geometry.net_area
        
        # Simplified shear capacity
        Vc = 0.17 * math.sqrt(self.fc) * Acv
        phi_Vc = self.phi_shear * Vc
        
        ratio = Vu / phi_Vc if phi_Vc > 0 else float('inf')
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Shear Strength",
            status=status,
            value=Vu,
            limit=phi_Vc,
            ratio=ratio,
            units="N",
            description=f"In-plane shear demand vs capacity",
            code_reference="ACI 318M-25 Section 14.9"
        )
    
    def _check_slenderness_limits(self, geometry, wall_type):
        """Check slenderness ratio limits"""
        
        slenderness = geometry.height / geometry.thickness
        
        # Slenderness limits from ACI 318M-25
        if wall_type == WallType.BEARING:
            limit = 25
        elif wall_type == WallType.SHEAR:
            limit = 30
        else:
            limit = 35
        
        ratio = slenderness / limit
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Slenderness Ratio",
            status=status,
            value=slenderness,
            limit=limit,
            ratio=ratio,
            units="",
            description=f"Height-to-thickness ratio check",
            code_reference="ACI 318M-25 Section 14.2"
        )
    
    def _check_deflection_limits(self, geometry, loads, boundary_condition):
        """Check deflection limits under service loads"""
        
        q = loads.total_lateral_pressure * 1e-6  # kPa -> N/mm²
        L = geometry.height
        E = self.Ec
        I = geometry.length * geometry.thickness**3 / 12
        
        if boundary_condition == WallBoundaryCondition.PINNED_TOP_BOTTOM:
            delta_max = 5 * q * L**4 / (384 * E * I)
        elif boundary_condition == WallBoundaryCondition.FIXED_TOP_BOTTOM:
            delta_max = q * L**4 / (384 * E * I)
        elif boundary_condition == WallBoundaryCondition.CANTILEVER:
            delta_max = 8 * q * L**4 / (384 * E * I)
        else:
            delta_max = 3 * q * L**4 / (384 * E * I)
        
        delta_limit = L / 240
        
        ratio = delta_max / delta_limit
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Deflection Control",
            status=status,
            value=delta_max,
            limit=delta_limit,
            ratio=ratio,
            units="mm",
            description=f"Out-of-plane deflection check",
            code_reference="ACI 318M-25 Section 24.2"
        )
    
    def _check_crack_control(self, geometry, loads):
        """Check crack control requirements"""
        
        max_spacing_vertical = min(3 * geometry.thickness, 450)
        max_spacing_horizontal = min(5 * geometry.thickness, 450)
        
        typical_spacing = 400  # mm
        limit = min(max_spacing_vertical, max_spacing_horizontal)
        ratio = typical_spacing / limit
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Crack Control",
            status=status,
            value=typical_spacing,
            limit=limit,
            ratio=ratio,
            units="mm",
            description=f"Reinforcement spacing for crack control",
            code_reference="ACI 318M-25 Section 14.3"
        )
    
    def _check_detailing_requirements(self, geometry, wall_type):
        """Check detailing requirements"""
        
        checks = []
        
        # Minimum thickness check
        if wall_type == WallType.BEARING:
            min_thickness = max(100, geometry.height / 25)
        elif wall_type == WallType.SHEAR:
            min_thickness = max(150, geometry.height / 20)
        else:
            min_thickness = max(75, geometry.height / 30)
        
        ratio = min_thickness / geometry.thickness
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        thickness_check = DesignCheck(
            name="Minimum Thickness",
            status=status,
            value=geometry.thickness,
            limit=min_thickness,
            ratio=ratio,
            units="mm",
            description=f"Minimum thickness requirement",
            code_reference="ACI 318M-25 Section 14.2"
        )
        checks.append(thickness_check)
        
        # Cover requirement check
        min_cover = 40.0
        ratio = min_cover / geometry.cover
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        cover_check = DesignCheck(
            name="Concrete Cover",
            status=status,
            value=geometry.cover,
            limit=min_cover,
            ratio=ratio,
            units="mm",
            description=f"Minimum cover requirement",
            code_reference="ACI 318M-25 Section 20.5"
        )
        checks.append(cover_check)
        
        return checks
    
    def _validate_inputs(self, geometry, loads):
        """Validate input parameters"""
        
        validate_positive(geometry.length, "Wall length")
        validate_positive(geometry.height, "Wall height")
        validate_positive(geometry.thickness, "Wall thickness")
        
        if loads.total_axial < 0:
            raise ValueError("Negative axial load not supported")