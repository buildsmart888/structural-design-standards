"""
ACI 318M-25 Diaphragm Design
===========================

Implementation of diaphragm design according to ACI 318M-25.
Includes concrete diaphragms, precast diaphragms, and chord design.

การออกแบบแผ่นรับแรงในระนาบตามมาตรฐาน ACI 318M-25
รวมแผ่นคอนกรีต แผ่นหล่อสำเร็จ และการออกแบบคอร์ด
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


class DiaphragmType(Enum):
    """Diaphragm type classification"""
    CAST_IN_PLACE = "cast_in_place"  # Cast-in-place concrete
    PRECAST = "precast"              # Precast concrete panels
    COMPOSITE = "composite"          # Composite diaphragm
    TOPPED = "topped"                # Topped precast


class DiaphragmBehavior(Enum):
    """Diaphragm behavior classification"""
    FLEXIBLE = "flexible"  # Flexible diaphragm
    RIGID = "rigid"        # Rigid diaphragm
    SEMI_RIGID = "semi_rigid"  # Semi-rigid diaphragm


class LoadingType(Enum):
    """Loading type for diaphragm"""
    WIND = "wind"          # Wind loading
    SEISMIC = "seismic"    # Seismic loading
    COMBINED = "combined"  # Combined loading


@dataclass
class DiaphragmGeometry:
    """Diaphragm geometry parameters"""
    length: float  # mm (plan dimension in primary direction)
    width: float   # mm (plan dimension in secondary direction)
    thickness: float  # mm (diaphragm thickness)
    span: float    # mm (maximum span between supports)
    opening_area: float = 0.0  # mm² (total opening area)
    cover: float = 20.0  # mm (cover for reinforcement)
    
    @property
    def gross_area(self) -> float:
        """Gross diaphragm area"""
        return self.length * self.width
    
    @property
    def net_area(self) -> float:
        """Net diaphragm area accounting for openings"""
        return self.gross_area - self.opening_area
    
    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio (length/width)"""
        return self.length / self.width if self.width > 0 else 0.0


@dataclass
class DiaphragmLoads:
    """Diaphragm loading conditions"""
    # In-plane shear forces
    shear_force: float = 0.0  # kN (total in-plane shear)
    moment: float = 0.0       # kN⋅m (in-plane moment)
    
    # Distributed loads
    wind_pressure: float = 0.0     # kPa (wind pressure)
    seismic_acceleration: float = 0.0  # g (seismic acceleration)
    
    # Load distribution
    tributary_width: float = 0.0   # mm (tributary width)
    load_height: float = 0.0       # mm (height of lateral load application)
    
    @property
    def unit_shear(self) -> float:
        """Unit shear force per unit length"""
        return self.shear_force  # Simplified


@dataclass
class DiaphragmReinforcement:
    """Diaphragm reinforcement layout"""
    # Primary reinforcement (parallel to span)
    primary_bars: Optional[List[str]] = None
    primary_spacing: float = 300.0  # mm
    
    # Secondary reinforcement (perpendicular to span)
    secondary_bars: Optional[List[str]] = None
    secondary_spacing: float = 300.0  # mm
    
    # Chord reinforcement
    chord_bars: Optional[List[str]] = None
    
    # Collector reinforcement
    collector_bars: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.primary_bars is None:
            self.primary_bars = []
        if self.secondary_bars is None:
            self.secondary_bars = []
        if self.chord_bars is None:
            self.chord_bars = []
        if self.collector_bars is None:
            self.collector_bars = []


class ACI318M25DiaphragmDesign(MemberDesign):
    """
    ACI 318M-25 Diaphragm Design Implementation
    
    การออกแบบแผ่นรับแรงในระนาบตาม ACI 318M-25
    """
    
    def __init__(self, 
                 concrete: ACI318M25Concrete,
                 reinforcement: ACI318M25ReinforcementSteel):
        """Initialize diaphragm designer"""
        super().__init__(concrete, reinforcement, "ACI 318M-25")
        self.concrete = concrete
        self.reinforcement = reinforcement
        self.validator = StructuralValidator()
        
        # Design parameters from ACI 318M-25
        self.phi_shear = 0.75       # Shear
        self.phi_flexure = 0.9      # Flexure (for chord design)
        self.phi_compression = 0.65 # Compression strut
        
        # Material properties
        self.fc = concrete.fc_prime
        self.fy = reinforcement.fy
        self.Es = reinforcement.elastic_modulus()
        self.Ec = concrete.elastic_modulus()
    
    def design(self, *args, **kwargs) -> DesignResult:
        """Fail closed: no complete diaphragm design can be certified."""
        return DesignResult(
            member_type="diaphragm",
            design_method="ACI 318M-25 NOT VERIFIED",
            overall_status=DesignStatus.NOT_CHECKED,
            utilization_ratio=float("inf"),
            warnings=["diaphragm analysis, reinforcement, anchorage, "
                      "detailing, stability and serviceability are NOT VERIFIED. "
                      "Do not treat preliminary formulas as design checks."],
        )

    def check_strength(self, *args, **kwargs) -> List[DesignCheck]:
        raise NotImplementedError("diaphragm strength model NOT VERIFIED")

    def check_serviceability(self, *args, **kwargs) -> List[DesignCheck]:
        raise NotImplementedError("diaphragm serviceability model NOT VERIFIED")

    def _design_cast_in_place_diaphragm(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads, 
                                      behavior: DiaphragmBehavior, result: DesignResult) -> None:
        """Design cast-in-place concrete diaphragm"""
        
        # Calculate design forces
        Vu = loads.shear_force * 1000  # kN to N
        Mu = loads.moment * 1e6        # kN⋅m to N⋅mm
        
        # Design for in-plane shear
        Acv = geometry.net_area  # mm²
        
        # Shear reinforcement required
        Vn_concrete = 0.17 * math.sqrt(self.fc) * Acv  # N
        Vn_required = Vu / self.phi_shear  # N
        
        if Vn_required > Vn_concrete:
            # Additional shear reinforcement needed
            Vs_required = Vn_required - Vn_concrete  # N
            Av_required = Vs_required / (self.fy * geometry.thickness)  # mm²/mm
        else:
            Av_required = 0.0
        
        # Minimum reinforcement
        Av_min = max(0.0020 * geometry.thickness, 200)  # mm²/m
        Av_design = max(Av_required * 1000, Av_min)  # mm²/m
        
        # Chord reinforcement
        chord_force = self._calculate_chord_force(geometry, loads)
        As_chord = self._calculate_chord_reinforcement(chord_force)
        
        # Collector reinforcement
        collector_force = self._calculate_collector_force(geometry, loads)
        As_collector = self._calculate_collector_reinforcement(collector_force)
        
        # Store design results
        result.required_reinforcement = {
            'shear_reinforcement': Av_design,  # mm²/m
            'minimum_shear_reinforcement': Av_min,  # mm²/m
            'chord_reinforcement': As_chord,  # mm²
            'collector_reinforcement': As_collector,  # mm²
            'minimum_thickness': self._minimum_diaphragm_thickness(geometry.span),
            'reinforcement_spacing': min(3 * geometry.thickness, 450)  # mm
        }
        
        result.design_forces = {
            'design_shear': Vu,  # N
            'design_moment': Mu,  # N⋅mm
            'chord_force': chord_force,  # N
            'collector_force': collector_force  # N
        }
    
    def _design_precast_diaphragm(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads, 
                                behavior: DiaphragmBehavior, result: DesignResult) -> None:
        """Design precast concrete diaphragm"""
        
        # Reduced capacity for precast connections
        capacity_reduction = 0.75  # Typical reduction for precast connections
        
        # Calculate design forces with increased demand
        Vu = loads.shear_force * 1000 / capacity_reduction  # N
        
        # Connection design
        connection_force = self._calculate_connection_force(geometry, loads)
        connection_capacity = self._calculate_connection_capacity(geometry)
        
        # Panel reinforcement
        panel_reinforcement = max(0.0015 * geometry.thickness * 1000, 150)  # mm²/m
        
        # Chord and collector design (same as cast-in-place)
        chord_force = self._calculate_chord_force(geometry, loads)
        As_chord = self._calculate_chord_reinforcement(chord_force)
        
        collector_force = self._calculate_collector_force(geometry, loads)
        As_collector = self._calculate_collector_reinforcement(collector_force)
        
        result.required_reinforcement = {
            'panel_reinforcement': panel_reinforcement,  # mm²/m
            'connection_force': connection_force,  # N
            'connection_capacity': connection_capacity,  # N
            'chord_reinforcement': As_chord,  # mm²
            'collector_reinforcement': As_collector,  # mm²
            'capacity_reduction_factor': capacity_reduction
        }
        
        result.design_forces = {
            'design_shear': Vu,
            'connection_force': connection_force,
            'chord_force': chord_force,
            'collector_force': collector_force
        }
    
    def _design_composite_diaphragm(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads, 
                                  behavior: DiaphragmBehavior, result: DesignResult) -> None:
        """Design composite diaphragm (precast + topping)"""
        
        # Assume 50mm topping slab minimum
        topping_thickness = max(50, geometry.thickness * 0.3)  # mm
        precast_thickness = geometry.thickness - topping_thickness  # mm
        
        # Design topping slab for primary shear resistance
        Vu = loads.shear_force * 1000  # N
        
        # Topping reinforcement
        Acv_topping = geometry.net_area * (topping_thickness / geometry.thickness)
        Vn_topping = 0.17 * math.sqrt(self.fc) * Acv_topping
        
        if Vu > self.phi_shear * Vn_topping:
            # Additional reinforcement in topping
            Av_topping = (Vu / self.phi_shear - Vn_topping) / (self.fy * topping_thickness)
        else:
            Av_topping = 0.0
        
        # Minimum topping reinforcement
        Av_min = 0.0018 * topping_thickness * 1000  # mm²/m
        Av_topping = max(Av_topping * 1000, Av_min)
        
        # Interface shear transfer
        interface_shear = self._calculate_interface_shear(geometry, loads)
        interface_reinforcement = self._calculate_interface_reinforcement(interface_shear)
        
        # Chord and collector (in topping)
        chord_force = self._calculate_chord_force(geometry, loads)
        As_chord = self._calculate_chord_reinforcement(chord_force)
        
        result.required_reinforcement = {
            'topping_thickness': topping_thickness,  # mm
            'topping_reinforcement': Av_topping,  # mm²/m
            'interface_reinforcement': interface_reinforcement,  # mm²/m
            'chord_reinforcement': As_chord,  # mm²
            'minimum_topping_reinforcement': Av_min  # mm²/m
        }
        
        result.design_forces = {
            'design_shear': Vu,
            'interface_shear': interface_shear,
            'chord_force': chord_force
        }
    
    def _calculate_chord_force(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> float:
        """Calculate chord force in diaphragm"""
        
        # Simplified calculation based on moment and depth
        M = loads.moment * 1e6  # N⋅mm
        depth = geometry.width  # mm (diaphragm depth)
        
        # Chord force = M / depth
        chord_force = abs(M) / depth if depth > 0 else 0.0  # N
        
        return chord_force
    
    def _calculate_collector_force(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> float:
        """Calculate collector force"""
        
        # Simplified - based on shear force distribution
        V = loads.shear_force * 1000  # N
        
        # Collector force (simplified)
        collector_force = V * 0.3  # Assume 30% of shear goes through collectors
        
        return collector_force
    
    def _calculate_chord_reinforcement(self, chord_force: float) -> float:
        """Calculate required chord reinforcement area"""
        
        if chord_force <= 0:
            return 0.0
        
        # Tension reinforcement
        As = chord_force / (self.phi_flexure * self.fy)  # mm²
        
        # Minimum reinforcement
        As_min = 200  # mm² (minimum)
        
        return max(As, As_min)
    
    def _calculate_collector_reinforcement(self, collector_force: float) -> float:
        """Calculate required collector reinforcement area"""
        
        if collector_force <= 0:
            return 0.0
        
        # Tension reinforcement
        As = collector_force / (self.phi_flexure * self.fy)  # mm²
        
        # Minimum reinforcement
        As_min = 150  # mm²
        
        return max(As, As_min)
    
    def _calculate_connection_force(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> float:
        """Calculate connection force for precast panels"""
        
        # Unit shear force at connections
        V = loads.shear_force * 1000  # N
        connection_length = geometry.width  # mm (typical connection length)
        
        # Connection force per unit length
        connection_force = V / connection_length if connection_length > 0 else 0.0  # N/mm
        
        return connection_force * 1000  # N/m
    
    def _calculate_connection_capacity(self, geometry: DiaphragmGeometry) -> float:
        """Calculate connection capacity for precast panels"""
        
        # Simplified connection capacity
        # Assume welded wire fabric or dowel connections
        capacity_per_meter = 50000  # N/m (typical capacity)
        
        return capacity_per_meter
    
    def _calculate_interface_shear(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> float:
        """Calculate interface shear for composite diaphragm"""
        
        V = loads.shear_force * 1000  # N
        interface_area = geometry.gross_area  # mm²
        
        # Interface shear stress
        interface_shear = V / interface_area if interface_area > 0 else 0.0  # N/mm²
        
        return interface_shear * geometry.length  # N/m
    
    def _calculate_interface_reinforcement(self, interface_shear: float) -> float:
        """Calculate interface reinforcement for composite diaphragm"""
        
        # Minimum interface reinforcement
        Av_min = 0.15  # mm²/mm (per ACI 318M-25)
        
        # Required reinforcement based on shear
        if interface_shear > 0:
            Av_req = interface_shear / (self.fy * 0.75)  # mm²/mm
        else:
            Av_req = 0.0
        
        return max(Av_req * 1000, Av_min * 1000)  # mm²/m
    
    def _minimum_diaphragm_thickness(self, span: float) -> float:
        """Minimum diaphragm thickness based on span"""
        
        # ACI 318M-25 minimum thickness requirements
        min_thickness = max(100, span / 30)  # mm
        
        return min_thickness
    
    def _check_in_plane_shear_strength(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads, 
                                     diaphragm_type: DiaphragmType) -> DesignCheck:
        """Check in-plane shear strength"""
        
        Vu = loads.shear_force * 1000  # N
        Acv = geometry.net_area  # mm²
        
        # Nominal shear capacity
        if diaphragm_type == DiaphragmType.CAST_IN_PLACE:
            Vn = 0.17 * math.sqrt(self.fc) * Acv  # N
        else:
            # Reduced capacity for precast
            Vn = 0.12 * math.sqrt(self.fc) * Acv  # N
        
        phi_Vn = self.phi_shear * Vn  # N
        
        ratio = Vu / phi_Vn if phi_Vn > 0 else float('inf')
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="In-Plane Shear Strength",
            status=status,
            value=Vu,
            limit=phi_Vn,
            ratio=ratio,
            units="N",
            description=f"In-plane shear strength check",
            code_reference="ACI 318M-25 Section 12"
        )
    
    def _check_chord_force_capacity(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> DesignCheck:
        """Check chord force capacity"""
        
        chord_force = self._calculate_chord_force(geometry, loads)
        
        # Simplified capacity (assume minimum reinforcement)
        As_min = 0.002 * geometry.thickness * 200  # mm²
        chord_capacity = self.phi_flexure * As_min * self.fy  # N
        
        ratio = chord_force / chord_capacity if chord_capacity > 0 else float('inf')
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Chord Force Capacity",
            status=status,
            value=chord_force,
            limit=chord_capacity,
            ratio=ratio,
            units="N",
            description=f"Chord force capacity check",
            code_reference="ACI 318M-25 Section 12"
        )
    
    def _check_collector_force_capacity(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> DesignCheck:
        """Check collector force capacity"""
        
        collector_force = self._calculate_collector_force(geometry, loads)
        
        # Simplified capacity
        As_min = 0.001 * geometry.thickness * 150  # mm²
        collector_capacity = self.phi_flexure * As_min * self.fy  # N
        
        ratio = collector_force / collector_capacity if collector_capacity > 0 else float('inf')
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Collector Force Capacity",
            status=status,
            value=collector_force,
            limit=collector_capacity,
            ratio=ratio,
            units="N",
            description=f"Collector force capacity check",
            code_reference="ACI 318M-25 Section 12"
        )
    
    def _check_connection_strength(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> DesignCheck:
        """Check connection strength for precast diaphragms"""
        
        connection_force = self._calculate_connection_force(geometry, loads)
        connection_capacity = self._calculate_connection_capacity(geometry)
        
        ratio = connection_force / connection_capacity if connection_capacity > 0 else float('inf')
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        return DesignCheck(
            name="Connection Strength",
            status=status,
            value=connection_force,
            limit=connection_capacity,
            ratio=ratio,
            units="N/m",
            description=f"Precast panel connection strength",
            code_reference="ACI 318M-25 Section 16"
        )
    
    def _check_diaphragm_deflection(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads, 
                                  behavior: DiaphragmBehavior) -> DesignCheck:
        """Check diaphragm deflection"""
        
        # Simplified deflection calculation
        L = geometry.span  # mm
        q = loads.unit_shear / 1000  # N/mm
        
        # Elastic modulus and moment of inertia
        E = self.Ec  # MPa
        I = geometry.width * geometry.thickness**3 / 12  # mm⁴
        
        # Deflection (simplified beam analogy)
        if behavior == DiaphragmBehavior.FLEXIBLE:
            delta = 5 * q * L**4 / (384 * E * I)  # mm
        else:
            delta = q * L**4 / (384 * E * I)  # mm
        
        # Deflection limit
        delta_limit = L / 360  # mm (typical limit)
        
        ratio = delta / delta_limit
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.WARNING
        
        return DesignCheck(
            name="Diaphragm Deflection",
            status=status,
            value=delta,
            limit=delta_limit,
            ratio=ratio,
            units="mm",
            description=f"In-plane deflection check",
            code_reference="Serviceability requirements"
        )
    
    def _check_aspect_ratio(self, geometry: DiaphragmGeometry) -> DesignCheck:
        """Check diaphragm aspect ratio"""
        
        aspect_ratio = geometry.aspect_ratio
        aspect_limit = 3.0  # Typical limit for rigid diaphragm behavior
        
        ratio = aspect_ratio / aspect_limit
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.WARNING
        
        return DesignCheck(
            name="Aspect Ratio",
            status=status,
            value=aspect_ratio,
            limit=aspect_limit,
            ratio=ratio,
            units="",
            description=f"Diaphragm aspect ratio check",
            code_reference="ACI 318M-25 recommendations"
        )
    
    def _check_detailing_requirements(self, geometry: DiaphragmGeometry, 
                                    diaphragm_type: DiaphragmType) -> List[DesignCheck]:
        """Check detailing requirements"""
        
        checks = []
        
        # Minimum thickness check
        min_thickness = self._minimum_diaphragm_thickness(geometry.span)
        ratio = min_thickness / geometry.thickness
        status = DesignStatus.PASS if ratio <= 1.0 else DesignStatus.FAIL
        
        thickness_check = DesignCheck(
            name="Minimum Thickness",
            status=status,
            value=geometry.thickness,
            limit=min_thickness,
            ratio=ratio,
            units="mm",
            description=f"Minimum diaphragm thickness",
            code_reference="ACI 318M-25 Section 7.7"
        )
        checks.append(thickness_check)
        
        # Cover requirement
        min_cover = 20.0  # mm for slabs
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
    
    def _validate_inputs(self, geometry: DiaphragmGeometry, loads: DiaphragmLoads) -> None:
        """Validate input parameters"""
        
        validate_positive(geometry.length, "Diaphragm length")
        validate_positive(geometry.width, "Diaphragm width")
        validate_positive(geometry.thickness, "Diaphragm thickness")
        validate_positive(geometry.span, "Diaphragm span")
        
        if loads.shear_force < 0:
            raise ValueError("Negative shear force not supported")