"""
ACI 318M-25 Footing Design
=========================

Implementation of footing design according to ACI 318M-25.
Includes isolated footings, combined footings, and mat foundations.

การออกแบบฐานรากตามมาตรฐาน ACI 318M-25
รวมฐานรากเดี่ยว ฐานรากรวม และฐานรากแผ่น
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


class FootingType(Enum):
    """Footing type classification"""
    ISOLATED = "isolated"  # Isolated spread footing
    COMBINED = "combined"  # Combined footing
    STRAP = "strap"       # Strap footing
    MAT = "mat"           # Mat foundation


class SoilCondition(Enum):
    """Soil bearing condition"""
    ALLOWABLE_STRESS = "allowable_stress"
    ULTIMATE_BEARING = "ultimate_bearing"


@dataclass
class FootingGeometry:
    """Footing geometry parameters"""
    length: float  # mm (L direction)
    width: float   # mm (B direction)
    thickness: float  # mm
    cover_bottom: float = 75.0  # mm (bottom cover)
    cover_top: float = 40.0     # mm (top cover)
    
    @property
    def area(self) -> float:
        return self.length * self.width
    
    @property
    def volume(self) -> float:
        return self.area * self.thickness
    
    @property
    def effective_depth_length(self) -> float:
        return self.thickness - self.cover_bottom - 12.0
    
    @property
    def effective_depth_width(self) -> float:
        return self.thickness - self.cover_bottom - 12.0 - 12.0


@dataclass
class ColumnLoads:
    """Column loads on footing"""
    axial_dead: float = 0.0     # kN
    axial_live: float = 0.0     # kN
    moment_x_dead: float = 0.0  # kN⋅m
    moment_y_dead: float = 0.0  # kN⋅m
    moment_x_live: float = 0.0  # kN⋅m
    moment_y_live: float = 0.0  # kN⋅m
    shear_x: float = 0.0        # kN
    shear_y: float = 0.0        # kN
    
    @property
    def total_axial(self) -> float:
        return self.axial_dead + self.axial_live
    
    @property
    def total_moment_x(self) -> float:
        return self.moment_x_dead + self.moment_x_live
    
    @property
    def total_moment_y(self) -> float:
        return self.moment_y_dead + self.moment_y_live


@dataclass
class SoilProperties:
    """Soil properties for footing design"""
    bearing_capacity: float  # kPa (allowable or ultimate)
    unit_weight: float = 18.0   # kN/m³
    friction_angle: float = 30.0  # degrees
    cohesion: float = 0.0       # kPa
    condition: SoilCondition = SoilCondition.ALLOWABLE_STRESS
    
    @property
    def design_bearing_pressure(self) -> float:
        if self.condition == SoilCondition.ALLOWABLE_STRESS:
            return self.bearing_capacity
        else:
            return self.bearing_capacity / 3.0


@dataclass
class FootingReinforcement:
    """Footing reinforcement layout"""
    bottom_bars_length: Optional[List[str]] = None
    bottom_bars_width: Optional[List[str]] = None
    top_bars_length: Optional[List[str]] = None
    top_bars_width: Optional[List[str]] = None
    spacing_length: float = 200.0  # mm
    spacing_width: float = 200.0   # mm
    
    def __post_init__(self):
        if self.bottom_bars_length is None:
            self.bottom_bars_length = []
        if self.bottom_bars_width is None:
            self.bottom_bars_width = []
        if self.top_bars_length is None:
            self.top_bars_length = []
        if self.top_bars_width is None:
            self.top_bars_width = []


class ACI318M25FootingDesign(MemberDesign):
    """
    ACI 318M-25 Footing Design Implementation
    
    การออกแบบฐานรากตาม ACI 318M-25
    """
    
    def __init__(self, 
                 concrete: ACI318M25Concrete,
                 reinforcement: ACI318M25ReinforcementSteel):
        """Initialize footing designer"""
        super().__init__(concrete, reinforcement, "ACI 318M-25")
        self.concrete = concrete
        self.reinforcement = reinforcement
        self.validator = StructuralValidator()
        
        # Design parameters from ACI 318M-25
        self.phi_flexure = 0.9      # Flexure
        self.phi_shear = 0.75       # Shear
        self.phi_bearing = 0.65     # Bearing on concrete
        
        # Material properties
        self.fc = concrete.fc_prime
        self.fy = reinforcement.fy
        self.Es = reinforcement.elastic_modulus()
        self.Ec = concrete.elastic_modulus()
        
        # Constants
        self.concrete_unit_weight = 24.0  # kN/m³
    
    def design(self, loads: ColumnLoads, soil: SoilProperties,
               footing_type: FootingType = FootingType.ISOLATED,
               target_geometry: Optional[FootingGeometry] = None) -> DesignResult:
        """Fail-closed footprint; NEVER certify structural footing with guessed inputs."""
        result = DesignResult(
            member_type="footing", design_method="Partial service soil bearing ONLY",
            overall_status=DesignStatus.NOT_CHECKED, utilization_ratio=float("inf"),
        )
        result.warnings.append(
            "NOT VERIFIED: full footing flexure, punching, one-way shear, settlement, "
            "stability and detailing require column dimensions, actual bar layout, "
            "factored load envelopes and geotechnical measurements."
        )
        if footing_type != FootingType.ISOLATED or target_geometry is None:
            result.warnings.append(
                "Provide explicit rectangular isolated footing geometry; auto-size disabled."
            )
            return result
        try:
            check = self.check_service_bearing_pressure(target_geometry, loads, soil)
            result.serviceability_checks.append(check)
            result.utilization_ratio = check.ratio
            result.design_forces["q_service_max_kPa"] = check.value
            result.design_capacities["q_allowable_kPa"] = check.limit
        except (ValueError, NotImplementedError) as error:
            result.warnings.append(str(error))
        return result

    def check_service_bearing_pressure(self, geometry: FootingGeometry,
                                       loads: ColumnLoads, soil: SoilProperties) -> DesignCheck:
        """Full-contact rigid footing elastic contact, service loads only.

        qmax/min = P/A +/- 6Mx/(L B^2) +/- 6My/(B L^2);
        L=X, B=Y (m), Mx about X; My about Y (kNm). Uniform base pressure
        and allowable capacity from a real geotechnical report, NOT ACI.
        """
        if soil.condition != SoilCondition.ALLOWABLE_STRESS:
            raise NotImplementedError(
                "Cannot divide ultimate soil bearing by arbitrary FS=3; "
                "supply geotechnical allowable bearing pressure."
            )
        for name, value in (
            ("length", geometry.length), ("width", geometry.width),
            ("thickness", geometry.thickness),
            ("allowable bearing", soil.bearing_capacity)
        ):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        L, B, H = (geometry.length / 1000, geometry.width / 1000,
                   geometry.thickness / 1000)
        P = loads.total_axial + L*B*H*self.concrete_unit_weight
        Mx, My = loads.total_moment_x, loads.total_moment_y
        if any(not math.isfinite(x) for x in (P, Mx, My)) or P <= 0:
            raise ValueError("Total service vertical force must be positive finite")
        avg = P/(L*B)
        dx = 6*abs(Mx)/(L*B**2)
        dy = 6*abs(My)/(B*L**2)
        qmin = avg-dx-dy
        if qmin < -1e-9:
            raise NotImplementedError(
                "Partial soil contact/uplift: elastic full-contact q formula not valid."
            )
        qmax = avg+dx+dy
        ratio = qmax/soil.bearing_capacity
        return DesignCheck(
            name="Service soil bearing (full contact)",
            status=DesignStatus.PASS if ratio <= 1 else DesignStatus.FAIL,
            value=qmax, limit=soil.bearing_capacity, ratio=ratio, units="kPa",
            description=f"qmin={max(qmin,0):.3f}kPa; settlement NOT VERIFIED",
            code_reference="Geotechnical elastic full-contact bearing; not structural ACI check",
        )

    def check_strength(self, geometry: FootingGeometry, loads: ColumnLoads,
                       soil: SoilProperties) -> List[DesignCheck]:
        raise NotImplementedError(
            "Footing structural ACI checks require explicit column size, layout, "
            "governing factored load combinations and critical sections."
        )

    def check_serviceability(self, geometry: FootingGeometry, loads: ColumnLoads,
                             soil: SoilProperties) -> List[DesignCheck]:
        return [self.check_service_bearing_pressure(geometry, loads, soil)]

    def _size_footing(self, loads: ColumnLoads, soil: SoilProperties, footing_type: FootingType) -> FootingGeometry:
        """Size footing based on bearing pressure"""
        
        P_service = loads.total_axial  # kN
        Mx_service = loads.total_moment_x  # kN⋅m
        My_service = loads.total_moment_y  # kN⋅m
        
        # Estimate footing weight
        footing_weight_estimate = 0.1 * P_service  # kN
        total_load = P_service + footing_weight_estimate
        
        # Required area
        qa = soil.design_bearing_pressure  # kPa
        A_required = total_load / qa  # m²
        A_required *= 1000000  # Convert to mm²
        
        # For square footing initially
        side_length = math.sqrt(A_required)  # mm
        
        # Check for moments and adjust if needed
        if abs(Mx_service) > 0.01 or abs(My_service) > 0.01:
            side_length *= 1.2
        
        # Minimum dimensions
        min_dimension = 600  # mm
        side_length = max(side_length, min_dimension)
        
        # Round up to nearest 50mm
        side_length = math.ceil(side_length / 50) * 50
        
        # Determine thickness
        thickness = max(150, side_length / 10)  # mm
        thickness = math.ceil(thickness / 25) * 25
        
        return FootingGeometry(
            length=side_length,
            width=side_length,
            thickness=thickness
        )
    
    def _design_reinforcement(self, geometry: FootingGeometry, loads: ColumnLoads, 
                            soil: SoilProperties, result: DesignResult) -> None:
        """Design footing reinforcement"""
        
        # Calculate design moments
        Mu_x, Mu_y = self._calculate_design_moments(geometry, loads, soil)
        
        # Design reinforcement in both directions
        As_x = self._calculate_required_steel_area(geometry, Mu_x, geometry.effective_depth_length)
        As_y = self._calculate_required_steel_area(geometry, Mu_y, geometry.effective_depth_width)
        
        # Minimum reinforcement
        As_min_x = self._minimum_reinforcement_area(geometry.width, geometry.effective_depth_length)
        As_min_y = self._minimum_reinforcement_area(geometry.length, geometry.effective_depth_width)
        
        # Required areas
        As_req_x = max(As_x, As_min_x)
        As_req_y = max(As_y, As_min_y)
        
        # Calculate spacing
        bar_area = math.pi * (12/2)**2  # Assume #4 bars (12mm diameter)
        spacing_x = (bar_area * geometry.width) / As_req_x
        spacing_y = (bar_area * geometry.length) / As_req_y
        
        # Maximum spacing limits
        max_spacing = min(3 * geometry.thickness, 450)  # mm
        spacing_x = min(spacing_x, max_spacing)
        spacing_y = min(spacing_y, max_spacing)
        
        # Store reinforcement design
        result.required_reinforcement.update({
            'steel_area_x': As_req_x,
            'steel_area_y': As_req_y,
            'minimum_steel_x': As_min_x,
            'minimum_steel_y': As_min_y,
            'spacing_x': spacing_x,
            'spacing_y': spacing_y,
            'bar_size_recommended': 'DB12',
            'design_moment_x': Mu_x,
            'design_moment_y': Mu_y
        })
        
        result.design_forces = {
            'design_moment_x': Mu_x,
            'design_moment_y': Mu_y,
            'bearing_pressure': self._calculate_bearing_pressure(geometry, loads, soil)
        }
    
    def _calculate_design_moments(self, geometry: FootingGeometry, loads: ColumnLoads, 
                                soil: SoilProperties) -> Tuple[float, float]:
        """Calculate design moments in both directions"""
        
        qu = self._calculate_ultimate_bearing_pressure(geometry, loads, soil)
        
        # Critical sections for moment (at face of column)
        column_size = 400  # mm (assumed)
        
        # Distance from face of column to edge of footing
        cantilever_x = (geometry.length - column_size) / 2
        cantilever_y = (geometry.width - column_size) / 2
        
        # Moments per unit width
        Mu_x = qu * cantilever_x**2 / 2 / 1000000  # kN⋅m/m
        Mu_y = qu * cantilever_y**2 / 2 / 1000000  # kN⋅m/m
        
        # Total moments
        Mu_x_total = Mu_x * geometry.width / 1000  # kN⋅m
        Mu_y_total = Mu_y * geometry.length / 1000  # kN⋅m
        
        return Mu_x_total, Mu_y_total
    
    def _calculate_required_steel_area(self, geometry: FootingGeometry, 
                                     moment: float, effective_depth: float) -> float:
        """Calculate required steel area for flexure"""
        
        Mu = moment * 1e6  # kN⋅m to N⋅mm
        b = 1000  # mm (per meter width)
        d = effective_depth  # mm
        
        # Required moment strength
        Mn_required = Mu / self.phi_flexure
        
        # Solve for required steel area (simplified)
        a_coeff = 0.5 * self.fy / (0.85 * self.fc * b)
        b_coeff = -self.fy * d
        c_coeff = Mn_required
        
        discriminant = b_coeff**2 - 4 * a_coeff * c_coeff
        
        if discriminant < 0:
            raise ValueError('Bending demand exceeds singly reinforced capacity')
        
        As = (-b_coeff - math.sqrt(discriminant)) / (2 * a_coeff)
        
        return max(As, 0.0)
    
    def _minimum_reinforcement_area(self, width: float, effective_depth: float) -> float:
        """Calculate minimum reinforcement area"""
        
        rho_min = max(0.0018, 0.25 * math.sqrt(self.fc) / self.fy)
        As_min = rho_min * width * effective_depth
        
        return As_min
    
    def _calculate_bearing_pressure(self, geometry: FootingGeometry, loads: ColumnLoads, 
                                  soil: SoilProperties) -> float:
        """Calculate bearing pressure under service loads"""
        
        P = loads.total_axial
        footing_weight = geometry.volume * self.concrete_unit_weight / 1e9
        P_total = P + footing_weight
        
        A = geometry.area / 1e6  # m²
        q_avg = P_total / A
        
        return q_avg
    
    def _calculate_ultimate_bearing_pressure(self, geometry: FootingGeometry, loads: ColumnLoads, 
                                           soil: SoilProperties) -> float:
        """Calculate ultimate bearing pressure for design"""
        
        Pu = 1.2 * loads.axial_dead + 1.6 * loads.axial_live
        footing_weight = geometry.volume * self.concrete_unit_weight / 1e9 * 1.2
        Pu_total = Pu + footing_weight
        
        A = geometry.area / 1e6
        qu = Pu_total / A
        
        return qu
    
    def _check_bearing_pressure(self, geometry, loads, soil):
        return self.check_service_bearing_pressure(geometry, loads, soil)

    def _check_flexural_strength_x(self, *args, **kwargs):
        raise NotImplementedError("_check_flexural_strength_x: calculation NOT VERIFIED")

    def _check_flexural_strength_y(self, *args, **kwargs):
        raise NotImplementedError("_check_flexural_strength_y: calculation NOT VERIFIED")

    def _check_one_way_shear_x(self, *args, **kwargs):
        raise NotImplementedError("_check_one_way_shear_x: calculation NOT VERIFIED")

    def _check_one_way_shear_y(self, *args, **kwargs):
        raise NotImplementedError("_check_one_way_shear_y: calculation NOT VERIFIED")

    def _check_punching_shear(self, *args, **kwargs):
        raise NotImplementedError("_check_punching_shear: calculation NOT VERIFIED")

    def _check_settlement(self, *args, **kwargs):
        raise NotImplementedError("_check_settlement: calculation NOT VERIFIED")

    def _check_stability(self, *args, **kwargs):
        raise NotImplementedError("_check_stability: calculation NOT VERIFIED")

    def _check_detailing_requirements(self, geometry: FootingGeometry) -> List[DesignCheck]:
        """Check detailing requirements"""
        
        checks = []
        
        # Minimum thickness check
        min_thickness = 150  # mm
        ratio = min_thickness / geometry.thickness
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        thickness_check = DesignCheck(
            name="Minimum Thickness",
            status=status,
            value=geometry.thickness,
            limit=min_thickness,
            ratio=ratio,
            units="mm",
            description=f"Minimum footing thickness requirement",
            code_reference="ACI 318M-25 Section 13.2"
        )
        checks.append(thickness_check)
        
        # Cover requirement check
        min_cover = 75.0  # mm for footings
        ratio = min_cover / geometry.cover_bottom
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        cover_check = DesignCheck(
            name="Concrete Cover",
            status=status,
            value=geometry.cover_bottom,
            limit=min_cover,
            ratio=ratio,
            units="mm",
            description=f"Minimum cover requirement for footings",
            code_reference="ACI 318M-25 Section 20.5"
        )
        checks.append(cover_check)
        
        return checks
    
    def _validate_inputs(self, loads: ColumnLoads, soil: SoilProperties) -> None:
        """Validate input parameters"""
        
        validate_positive(loads.total_axial, "Total axial load")
        validate_positive(soil.bearing_capacity, "Soil bearing capacity")
        
        if soil.unit_weight <= 0:
            raise ValueError("Soil unit weight must be positive")