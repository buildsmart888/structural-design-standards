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

from ....base.design_base import ColumnDesign, DesignResult, DesignCheck, DesignStatus
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
    transverse_reinforcement: str = "ties"  # "ties" or "spiral"

    def __post_init__(self):
        for name, v in (("width", self.width), ("depth", self.depth),
                        ("length", self.length)):
            if not math.isfinite(v) or v <= 0:
                raise ValueError(f"{name} must be positive finite")
        if self.cross_section not in ("rectangular", "circular"):
            raise ValueError("Unknown cross-section; no silent rectangular default")
        if self.cross_section == "circular" and self.width != self.depth:
            raise ValueError("Circular cross-section width/depth must match")
        if self.transverse_reinforcement not in ("ties", "spiral"):
            raise ValueError("Explicit ties or spiral transverse reinforcement required")

    
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
        super().__init__(concrete, reinforcement, "ACI 318M-25")
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
    
    def calculate_concentric_axial_upper_bound(
            self, geometry: ColumnGeometry, provided_As_mm2: float) -> Dict[str, float]:
        """Uniaxial CONCENTRIC upper bound per ACI 22.4; not a P-M check.

        P0 = 0.85 fc'(Ag-As) + fy*As, with tied limit 0.80*phi*P0
        and spiral limit 0.85*phi*P0. The reinforcement MUST be real,
        not a requested/suggested ratio. Pu must come from factored combos.
        """
        Ag = geometry.area
        As = provided_As_mm2
        if not math.isfinite(As) or not (0.01*Ag <= As <= 0.08*Ag):
            raise ValueError("Provided column longitudinal steel must be 1-8% Ag")
        transverse = geometry.transverse_reinforcement
        phi = 0.75 if transverse == "spiral" else 0.65
        cap = 0.85 if transverse == "spiral" else 0.80
        P0 = 0.85 * self.fc*(Ag-As) + min(self.fy,550.0)*As
        return {
            "P0_kN": P0/1000.0,
            "phi_Pn_max_kN": phi*cap*P0/1000.0,
            "phi_compression": phi,
            "max_axial_factor": cap,
            "provided_As_mm2": As,
            "verified_scope": "concentric upper bound only; not an interaction check",
        }

    def design(self, **kwargs) -> DesignResult:
        """Fail closed; do not treat pure axial upper bound as full P-M design."""
        return DesignResult(
            member_type="column", design_method="ACI 318M-25 (NOT VERIFIED)",
            overall_status=DesignStatus.NOT_CHECKED,
            utilization_ratio=float("inf"),
            warnings=["Column P-M biaxial interaction, slenderness, moment "
                      "magnification, transverse confinement and details "
                      "NOT VERIFIED. Factored load cases and bar positions required."],
        )

    def design_axial_reinforcement(self, geometry: ColumnGeometry,
                                 loads: ColumnLoads,
                                 reinforcement_ratio: float = 0.02) -> DesignResult:
        """Preliminary sizing ONLY; no load comparison without factored Pu."""
        validate_range(reinforcement_ratio, 0.01, 0.08, "Reinforcement ratio")
        area = geometry.area * reinforcement_ratio
        limits = self.calculate_concentric_axial_upper_bound(geometry, area)
        return DesignResult(
            member_type="column", design_method="ACI 318M-25 trial axial sizing",
            overall_status=DesignStatus.NOT_CHECKED,
            utilization_ratio=float("inf"),
            required_reinforcement={"trial_As_mm2": area,
                                    "trial_reinforcement_ratio": reinforcement_ratio},
            design_capacities={"theoretical_phi_Pn_max_kN": limits["phi_Pn_max_kN"]},
            warnings=["Trial As is not a provided bar layout. Input loads are not "
                      "factored Pu; no P-M interaction or slenderness check. "
                      "DO NOT use this result to approve a column."],
        )

    def design_reinforcement(self, *args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Column reinforcement design requires verified P-M and bar layout")

    def check_strength(self, *args, **kwargs) -> List[DesignCheck]:
        raise NotImplementedError("Full factored P-M interaction and second-order design NOT VERIFIED")

    def check_serviceability(self, *args, **kwargs) -> List[DesignCheck]:
        raise NotImplementedError("Column serviceability and drift NOT VERIFIED")

    def check_slenderness(self, *args, **kwargs) -> DesignCheck:
        raise NotImplementedError("Sway, end restraint, K-factor and second-order effects required")

    def interaction_diagram(self, *args, **kwargs) -> Dict[str, List[float]]:
        raise NotImplementedError("Full strain-compatible P-M diagram with real bar coordinates required")

    def design_tie_reinforcement(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI 318M-25 design_tie_reinforcement NOT VERIFIED: real geometry and code checks required"
        )

    def check_biaxial_bending(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI 318M-25 check_biaxial_bending NOT VERIFIED: real geometry and code checks required"
        )

    def classify_column_slenderness(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI 318M-25 classify_column_slenderness NOT VERIFIED: real geometry and code checks required"
        )

    def calculate_moment_magnification(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI 318M-25 calculate_moment_magnification NOT VERIFIED: real geometry and code checks required"
        )

    def axial_moment_interaction(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI 318M-25 axial_moment_interaction NOT VERIFIED: real geometry and code checks required"
        )

    def uniaxial_moment_capacity(self, *args, **kwargs):
        raise NotImplementedError(
            "ACI 318M-25 uniaxial_moment_capacity NOT VERIFIED: real geometry and code checks required"
        )

    def check_lateral_support(self, *args, **kwargs):
        raise NotImplementedError("Lateral bar support detailing NOT VERIFIED")
