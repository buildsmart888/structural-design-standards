"""
ACI 318M-25 Beam Design
======================

Implementation of beam design according to ACI 318M-25.
Includes flexural, shear, deflection, and detailing requirements.

การออกแบบคานตามมาตรฐาน ACI 318M-25
รวมการตรวจสอบโมเมนต์ แรงเฉือน การโก่งตัว และรายละเอียดการเสริม
"""

import math
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from ....base.design_base import BeamDesign, DesignResult, DesignCheck, DesignStatus
from ....base.material_base import ConcreteMaterial, ReinforcementSteel
from ..materials.concrete import ACI318M25Concrete
from ..materials.steel import ACI318M25ReinforcementSteel
from ....utils.validation import StructuralValidator, validate_positive, validate_range


class BeamType(Enum):
    """Beam type classification"""
    SIMPLY_SUPPORTED = "simply_supported"
    CONTINUOUS = "continuous"
    CANTILEVER = "cantilever"


class LoadType(Enum):
    """Load type for deflection calculations"""
    SUSTAINED = "sustained"
    TRANSIENT = "transient"
    TOTAL = "total"


@dataclass
class BeamGeometry:
    """Beam geometry parameters"""
    width: float  # mm
    height: float  # mm
    effective_depth: float  # mm
    span_length: float  # mm
    cover: float = 40.0  # mm
    
    def __post_init__(self):
        """Validate geometry"""
        if self.effective_depth <= 0:
            self.effective_depth = self.height - self.cover - 12.0  # Assume #4 bar + stirrup


@dataclass
class BeamLoads:
    """Beam loading conditions"""
    dead_load: float = 0.0  # kN/m
    live_load: float = 0.0  # kN/m
    concentrated_loads: List[Tuple[float, float]] = None  # [(P, a)] kN, mm from support
    
    def __post_init__(self):
        if self.concentrated_loads is None:
            self.concentrated_loads = []


@dataclass
class BeamReinforcement:
    """Beam reinforcement layout"""
    # Flexural reinforcement
    tension_bars: List[str] = None  # Bar designations
    compression_bars: List[str] = None
    
    # Shear reinforcement
    stirrup_size: str = "DB10"
    stirrup_spacing: float = 200.0  # mm
    stirrup_legs: int = 2
    
    def __post_init__(self):
        if self.tension_bars is None:
            self.tension_bars = []
        if self.compression_bars is None:
            self.compression_bars = []


class ACI318M25BeamDesign(BeamDesign):
    """
    ACI 318M-25 Beam Design Implementation
    
    การออกแบบคานตาม ACI 318M-25
    """
    
    def __init__(self, 
                 concrete: ACI318M25Concrete,
                 reinforcement: ACI318M25ReinforcementSteel):
        """
        Initialize beam designer
        
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
        self.phi_flexure = 0.9  # Strength reduction factor for flexure
        self.phi_shear = 0.75   # Strength reduction factor for shear
        self.phi_compression = 0.65  # For compression-controlled sections
        
        # Material properties
        self.fc = concrete.fc_prime
        self.fy = reinforcement.fy
        self.Es = reinforcement.elastic_modulus()
        self.Ec = concrete.elastic_modulus()
        
        # Strain limits (ACI 318M-25 Section 21.2.2)
        self.epsilon_cu = 0.003  # Ultimate concrete strain
        self.epsilon_ty = self.fy / self.Es  # Yield strain of steel
        
    def design_flexural_reinforcement(self,
                                    geometry: BeamGeometry,
                                    moment_ultimate: float,
                                    moment_service: Optional[float] = None) -> DesignResult:
        """
        Design flexural reinforcement for beam
        
        Parameters:
        -----------
        geometry : BeamGeometry
            Beam geometry
        moment_ultimate : float
            Ultimate moment (kN⋅m)
        moment_service : float, optional
            Service moment for crack control (kN⋅m)
            
        Returns:
        --------
        DesignResult
            Design results with required reinforcement
        """
        # Convert to consistent units (N⋅mm)
        Mu = moment_ultimate * 1e6  # kN⋅m to N⋅mm
        
        b = geometry.width  # mm
        h = geometry.height  # mm
        d = geometry.effective_depth  # mm
        
        # Validate inputs
        validate_positive(Mu, "Ultimate moment")
        validate_positive(b, "Beam width")
        validate_positive(h, "Beam height")
        validate_positive(d, "Effective depth")
        
        # Required moment strength
        Mn_required = Mu / self.phi_flexure  # N⋅mm
        
        # Calculate required reinforcement
        # Using simplified rectangular stress block (ACI 318M-25 Section 22.2)
        
        # Assume tension-controlled section initially
        phi = self.phi_flexure
        
        # Calculate reinforcement ratio limits
        rho_min = self.minimum_flexural_reinforcement_ratio(b, d)
        rho_max = self.maximum_flexural_reinforcement_ratio()
        
        # Solve for required steel area using quadratic formula
        # Mn = As⋅fy⋅(d - a/2) where a = As⋅fy/(0.85⋅fc⋅b)
        beta1 = self.concrete.beta1()
        
        # Quadratic equation coefficients
        # 0.5⋅As²⋅fy/(0.85⋅fc⋅b) - As⋅fy⋅d + Mn = 0
        a_coeff = 0.5 * self.fy / (0.85 * self.fc * b)
        b_coeff = -self.fy * d
        c_coeff = Mn_required
        
        # Solve quadratic equation
        discriminant = b_coeff**2 - 4*a_coeff*c_coeff
        
        if discriminant < 0:
            # Cannot solve with single layer tension reinforcement
            As_required = None
            feasible = False
            warnings = ["Required moment exceeds capacity with single tension reinforcement"]
        else:
            As_required = (-b_coeff - math.sqrt(discriminant)) / (2*a_coeff)  # mm²
            
            # Check if section is tension-controlled
            a = As_required * self.fy / (0.85 * self.fc * b)  # mm
            c = a / beta1  # mm
            
            # Strain in extreme tension steel
            epsilon_t = self.epsilon_cu * (d - c) / c
            
            # Check section behavior (Table 21.2.2: epsilon_ty + 0.003)
            epsilon_t_limit = self.epsilon_ty + 0.003
            if epsilon_t >= epsilon_t_limit:
                # Tension-controlled
                phi_actual = self.phi_flexure
                section_type = "tension-controlled"
            elif epsilon_t <= self.epsilon_ty:
                # Compression-controlled
                phi_actual = self.phi_compression
                section_type = "compression-controlled"
            else:
                # Transition zone
                phi_actual = self.phi_compression + (self.phi_flexure - self.phi_compression) * \
                           (epsilon_t - self.epsilon_ty) / 0.003
                section_type = "transition"
            
            # Check reinforcement ratio limits
            rho_provided = As_required / (b * d)
            
            warnings = []
            if rho_provided < rho_min:
                As_required = max(As_required, rho_min * b * d)
                warnings.append(f"Minimum reinforcement controls: ρ = {rho_min:.4f}")
            
            if rho_provided > rho_max:
                feasible = False
                warnings.append(f"Exceeds maximum reinforcement ratio: ρ = {rho_max:.4f}")
            else:
                feasible = True
        
        # Calculate actual capacity with required steel
        if feasible and As_required:
            Mn_provided = self.flexural_capacity(b, d, As_required, phi_actual)
            capacity_ratio = Mn_provided / Mn_required
        else:
            Mn_provided = 0
            capacity_ratio = 0
        
        # Create design checks
        checks = [
            DesignCheck(
                name="Flexural Strength",
                status=DesignStatus.PASS if Mn_provided >= Mn_required else DesignStatus.FAIL,
                value=Mn_provided/1e6,
                limit=Mn_required/1e6,
                ratio=Mn_provided/Mn_required if Mn_required > 0 else float('inf'),
                units="kN⋅m",
                description=f"φMn = {Mn_provided/1e6:.1f} kN⋅m ≥ Mu = {Mu/1e6:.1f} kN⋅m"
            ),
            DesignCheck(
                name="Minimum Reinforcement",
                status=DesignStatus.PASS if As_required >= rho_min * b * d else DesignStatus.FAIL,
                value=As_required,
                limit=rho_min * b * d,
                ratio=As_required/(rho_min * b * d) if rho_min * b * d > 0 else float('inf'),
                units="mm²",
                description=f"As = {As_required:.0f} mm² ≥ As,min = {rho_min * b * d:.0f} mm²"
            ),
            DesignCheck(
                name="Maximum Reinforcement",
                status=DesignStatus.PASS if rho_provided <= rho_max else DesignStatus.FAIL,
                value=rho_provided,
                limit=rho_max,
                ratio=rho_provided/rho_max if rho_max > 0 else float('inf'),
                units="-",
                description=f"ρ = {rho_provided:.4f} ≤ ρ,max = {rho_max:.4f}"
            )
        ]
        
        # Results dictionary
        results = {
            'As_required_mm2': As_required or 0,
            'reinforcement_ratio': rho_provided if As_required else 0,
            'section_type': section_type if feasible else "over-reinforced",
            'strength_reduction_factor': phi_actual if feasible else 0,
            'moment_capacity_kNm': Mn_provided / 1e6 if Mn_provided else 0,
            'capacity_ratio': capacity_ratio,
            'concrete_strength_MPa': self.fc,
            'steel_yield_MPa': self.fy,
            'warnings': warnings
        }
        
        return DesignResult(
            member_type="beam",
            design_method="ACI 318M-25 Flexural",
            overall_status=DesignStatus.PASS if feasible else DesignStatus.FAIL,
            utilization_ratio=1/capacity_ratio if capacity_ratio > 0 else float('inf'),
            strength_checks=checks,
            design_forces={'moment_ultimate': Mu/1e6},
            design_capacities={'moment_capacity': Mn_provided/1e6 if Mn_provided else 0},
            required_reinforcement={'As_required_mm2': As_required or 0},
            warnings=warnings
        )
    
    def design_shear_reinforcement(self,
                                 geometry: BeamGeometry,
                                 shear_ultimate: float,
                                 longitudinal_steel: float) -> DesignResult:
        """
        Design shear reinforcement (stirrups)
        
        Parameters:
        -----------
        geometry : BeamGeometry
            Beam geometry
        shear_ultimate : float
            Ultimate shear force (kN)
        longitudinal_steel : float
            Area of longitudinal tension reinforcement (mm²)
            
        Returns:
        --------
        DesignResult
            Shear design results
        """
        # Convert to consistent units
        Vu = shear_ultimate * 1000  # kN to N
        
        b = geometry.width  # mm
        d = geometry.effective_depth  # mm
        
        # Validate inputs
        validate_positive(Vu, "Ultimate shear")
        validate_positive(longitudinal_steel, "Longitudinal steel area")
        
        # Concrete shear strength (ACI 318M-25 Section 22.5)
        lambda_factor = 1.0  # Normal weight concrete
        sqrt_fc = math.sqrt(self.fc)  # MPa^0.5
        
        # Vc = 0.17⋅λ⋅√fc'⋅bw⋅d  (Table 22.5.5.1(a), SI: MPa·mm·mm = N)
        Vc = 0.17 * lambda_factor * sqrt_fc * b * d  # N
        
        # Design shear strength
        phi_Vc = self.phi_shear * Vc
        
        # Required shear strength from reinforcement
        Vs_required = max(0, Vu - phi_Vc)  # N
        
        # Check if shear reinforcement is required
        if Vs_required <= 0:
            # Minimum shear reinforcement (ACI 318M-25 Section 9.6.3)
            Av_min = self.minimum_shear_reinforcement_area(b)  # mm²
            s_max = min(d/2, 600)  # mm
            
            stirrup_area = Av_min
            stirrup_spacing = s_max
            shear_reinforcement_required = False
            
        else:
            # Design shear reinforcement
            # Vs = Av⋅fy⋅d/s
            # Therefore: Av/s = Vs/(fy⋅d)
            
            Av_over_s_required = Vs_required / (self.fy * d)  # mm²/mm
            
            # Assume stirrup size (can be optimized)
            stirrup_diameter = 10  # mm (DB10)
            Av_stirrup = 2 * math.pi * (stirrup_diameter/2)**2  # 2-leg stirrup, mm²
            
            # Required spacing
            s_required = Av_stirrup / Av_over_s_required  # mm
            
            # Maximum spacing limits (ACI 318M-25 Section 9.6.3)
            if Vs_required <= 0.33 * sqrt_fc * b * d:  # 25.7.2.1.2
                s_max = min(d/2, 600)  # mm
            else:
                s_max = min(d/4, 300)  # mm
            
            stirrup_spacing = min(s_required, s_max)
            stirrup_area = Av_stirrup
            shear_reinforcement_required = True
        
        # Check maximum shear limit (ACI 318M-25 Section 22.5)
        Vs_max = 0.66 * sqrt_fc * b * d  # N, 22.5.1.2: Vn ≤ Vc + 0.66√fc' bw d
        phi_Vs_max = self.phi_shear * Vs_max
        
        # Total shear capacity
        phi_Vn = phi_Vc + min(self.phi_shear * Vs_required / max(Vs_required, 1), phi_Vs_max - phi_Vc)
        
        # Design checks
        checks = [
            DesignCheck("Shear Strength", phi_Vn >= Vu,
                       f"φVn = {phi_Vn/1000:.1f} kN ≥ Vu = {Vu/1000:.1f} kN"),
            DesignCheck("Maximum Shear", Vs_required <= Vs_max,
                       f"Vs = {Vs_required/1000:.1f} kN ≤ Vs,max = {Vs_max/1000:.1f} kN"),
            DesignCheck("Stirrup Spacing", stirrup_spacing <= s_max,
                       f"s = {stirrup_spacing:.0f} mm ≤ s,max = {s_max:.0f} mm")
        ]
        
        # Results
        feasible = all(check.passes for check in checks)
        capacity_ratio = phi_Vn / Vu if Vu > 0 else float('inf')
        
        results = {
            'concrete_shear_kN': phi_Vc / 1000,
            'steel_shear_required_kN': Vs_required / 1000,
            'stirrup_area_mm2': stirrup_area,
            'stirrup_spacing_mm': stirrup_spacing,
            'shear_capacity_kN': phi_Vn / 1000,
            'capacity_ratio': capacity_ratio,
            'shear_reinforcement_required': shear_reinforcement_required,
            'stirrup_diameter_mm': stirrup_diameter if shear_reinforcement_required else 0
        }
        
        return DesignResult(
            is_adequate=feasible,
            capacity_ratio=capacity_ratio,
            governing_check="Shear Strength",
            design_details=results,
            checks=checks
        )
    
    def check_deflection(self,
                        geometry: BeamGeometry,
                        loads: BeamLoads,
                        reinforcement: BeamReinforcement,
                        beam_type: BeamType = BeamType.SIMPLY_SUPPORTED) -> DesignResult:
        """
        Check deflection according to ACI 318M-25
        
        Parameters:
        -----------
        geometry : BeamGeometry
            Beam geometry
        loads : BeamLoads
            Applied loads
        reinforcement : BeamReinforcement
            Provided reinforcement
        beam_type : BeamType
            Beam support conditions
            
        Returns:
        --------
        DesignResult
            Deflection check results
        """
        b = geometry.width  # mm
        h = geometry.height  # mm
        d = geometry.effective_depth  # mm
        L = geometry.span_length  # mm
        
        # Service loads
        w_dead = loads.dead_load  # kN/m
        w_live = loads.live_load  # kN/m
        w_total = w_dead + w_live  # kN/m
        
        # Convert to N/mm
        w_dead_per_mm = w_dead * 1000 / 1000  # N/mm
        w_live_per_mm = w_live * 1000 / 1000  # N/mm
        w_total_per_mm = w_total * 1000 / 1000  # N/mm
        
        # Gross moment of inertia
        Ig = b * h**3 / 12  # mm⁴
        
        # Calculate cracking moment
        fr = self.concrete.modulus_of_rupture()  # MPa
        yt = h / 2  # mm (distance to extreme tension fiber)
        Mcr = fr * Ig / yt  # N⋅mm  (MPa·mm⁴/mm = N·mm)
        
        # Service moments
        if beam_type == BeamType.SIMPLY_SUPPORTED:
            M_dead = w_dead_per_mm * L**2 / 8  # N⋅mm
            M_live = w_live_per_mm * L**2 / 8  # N⋅mm
            M_total = w_total_per_mm * L**2 / 8  # N⋅mm
        elif beam_type == BeamType.CONTINUOUS:
            # Approximate for continuous beams
            M_dead = w_dead_per_mm * L**2 / 10  # N⋅mm
            M_live = w_live_per_mm * L**2 / 10  # N⋅mm
            M_total = w_total_per_mm * L**2 / 10  # N⋅mm
        else:  # Cantilever
            M_dead = w_dead_per_mm * L**2 / 2  # N⋅mm
            M_live = w_live_per_mm * L**2 / 2  # N⋅mm
            M_total = w_total_per_mm * L**2 / 2  # N⋅mm
        
        # Calculate effective moment of inertia using ACI approach
        # Assume tension reinforcement area for cracked section analysis
        As = 1000  # mm² (placeholder - should come from actual reinforcement)
        
        # Cracked moment of inertia (simplified)
        n = self.Es / self.Ec  # Modular ratio
        rho = As / (b * d)
        k = math.sqrt(2*rho*n + (rho*n)**2) - rho*n
        Icr = b * d**3 * k**3 / 3 + n * As * (d - k*d)**2  # mm⁴
        
        # Effective moment of inertia (ACI 318M-25 Section 24.2.3)
        if M_total <= Mcr:
            Ie = Ig
        else:
            Ie = Icr + (Ig - Icr) * (Mcr / M_total)**3
            Ie = max(Ie, Icr)  # Ie should not be less than Icr
        
        # Calculate deflections
        if beam_type == BeamType.SIMPLY_SUPPORTED:
            # Immediate deflection
            delta_immediate = 5 * w_total_per_mm * L**4 / (384 * self.Ec * Ie)  # mm
            
            # Long-term deflection
            # Sustained load deflection
            delta_sustained = 5 * w_dead_per_mm * L**4 / (384 * self.Ec * Ie)  # mm
            
        elif beam_type == BeamType.CONTINUOUS:
            # Approximate for continuous beams
            delta_immediate = w_total_per_mm * L**4 / (384 * self.Ec * Ie)  # mm
            delta_sustained = w_dead_per_mm * L**4 / (384 * self.Ec * Ie)  # mm
            
        else:  # Cantilever
            delta_immediate = w_total_per_mm * L**4 / (8 * self.Ec * Ie)  # mm
            delta_sustained = w_dead_per_mm * L**4 / (8 * self.Ec * Ie)  # mm
        
        # Time-dependent factor for sustained loads (ACI 318M-25 Section 24.2.4)
        xi = 2.0  # For 5 years or more
        # Compression reinforcement factor (simplified)
        rho_prime = 0  # Assume no compression reinforcement
        lambda_delta = xi / (1 + 50 * rho_prime)
        
        # Total long-term deflection
        delta_longterm = delta_immediate + lambda_delta * delta_sustained
        
        # Deflection limits (ACI 318M-25 Table 24.2.2)
        if beam_type == BeamType.CANTILEVER:
            delta_limit_immediate = L / 180  # mm
            delta_limit_longterm = L / 90   # mm
        else:
            delta_limit_immediate = L / 360  # mm
            delta_limit_longterm = L / 240  # mm
        
        # Design checks
        checks = [
            DesignCheck("Immediate Deflection", delta_immediate <= delta_limit_immediate,
                       f"Δi = {delta_immediate:.1f} mm ≤ L/{int(L/delta_limit_immediate)} = {delta_limit_immediate:.1f} mm"),
            DesignCheck("Long-term Deflection", delta_longterm <= delta_limit_longterm,
                       f"Δlt = {delta_longterm:.1f} mm ≤ L/{int(L/delta_limit_longterm)} = {delta_limit_longterm:.1f} mm")
        ]
        
        # Results
        feasible = all(check.passes for check in checks)
        
        results = {
            'immediate_deflection_mm': delta_immediate,
            'longterm_deflection_mm': delta_longterm,
            'deflection_limit_immediate_mm': delta_limit_immediate,
            'deflection_limit_longterm_mm': delta_limit_longterm,
            'effective_moment_inertia_mm4': Ie,
            'gross_moment_inertia_mm4': Ig,
            'cracked_moment_inertia_mm4': Icr,
            'cracking_moment_Nmm': Mcr,
            'service_moment_Nmm': M_total
        }
        
        return DesignResult(
            is_adequate=feasible,
            capacity_ratio=min(delta_limit_immediate/delta_immediate, 
                             delta_limit_longterm/delta_longterm) if feasible else 0,
            governing_check="Deflection",
            design_details=results,
            checks=checks
        )
    
    def minimum_flexural_reinforcement_ratio(self, b: float, d: float) -> float:
        """
        Calculate minimum flexural reinforcement ratio
        ACI 318M-25 Section 9.6.1
        """
        # ρ_min = max(1.4/fy, √fc/(4⋅fy))
        sqrt_fc = math.sqrt(self.fc)  # MPa^0.5
        rho_min1 = 1.4 / self.fy  # For fy in MPa
        rho_min2 = sqrt_fc / (4 * self.fy)  # For fc in MPa, fy in MPa
        
        return max(rho_min1, rho_min2)
    
    def maximum_flexural_reinforcement_ratio(self) -> float:
        """
        Calculate maximum flexural reinforcement ratio
        ACI 318M-25 Section 21.2.2
        """
        # For tension-controlled sections (ε_t ≥ 0.005)
        beta1 = self.concrete.beta1()
        rho_max = 0.75 * beta1 * 0.85 * self.fc / self.fy * \
                  (600 / (600 + self.fy))
        
        return rho_max
    
    def minimum_shear_reinforcement_area(self, b: float) -> float:
        """
        Calculate minimum shear reinforcement area
        ACI 318M-25 Section 9.6.3
        """
        # Av,min = max(0.35⋅b⋅s/fy, 0.083⋅√fc⋅b⋅s/fy)
        # Return Av,min per unit spacing (Av,min/s)
        sqrt_fc = math.sqrt(self.fc)
        Av_min_over_s_1 = 0.35 * b / self.fy
        Av_min_over_s_2 = 0.083 * sqrt_fc * b / self.fy
        
        # Return for unit spacing (s = 1 mm)
        return max(Av_min_over_s_1, Av_min_over_s_2)
    
    def flexural_capacity(self, b: float, d: float, As: float, phi: float) -> float:
        """
        Calculate flexural capacity of section
        
        Returns:
        --------
        float
            Nominal moment capacity (N⋅mm)
        """
        # Rectangular stress block analysis
        a = As * self.fy / (0.85 * self.fc * b)  # mm
        Mn = As * self.fy * (d - a/2)  # N⋅mm
        
        return phi * Mn
    
    def design(self, **kwargs) -> DesignResult:
        """
        Main design method - wrapper for specific design types
        
        Parameters:
        -----------
        **kwargs : dict
            Design parameters
            
        Returns:
        --------
        DesignResult
            Design results
        """
        if 'geometry' in kwargs and 'moment_ultimate' in kwargs:
            return self.design_flexural_reinforcement(
                kwargs['geometry'],
                kwargs['moment_ultimate'],
                kwargs.get('moment_service')
            )
        else:
            raise ValueError("Insufficient parameters for beam design")
    
    def check_strength(self, **kwargs) -> List[DesignCheck]:
        """
        Check strength requirements
        
        Parameters:
        -----------
        **kwargs : dict
            Check parameters
            
        Returns:
        --------
        List[DesignCheck]
            Strength check results
        """
        if 'geometry' in kwargs and 'shear_ultimate' in kwargs and 'longitudinal_steel' in kwargs:
            result = self.design_shear_reinforcement(
                kwargs['geometry'],
                kwargs['shear_ultimate'],
                kwargs['longitudinal_steel']
            )
            return result.checks
        else:
            raise ValueError("Insufficient parameters for strength check")
    
    def check_serviceability(self, **kwargs) -> List[DesignCheck]:
        """
        Check serviceability requirements
        
        Parameters:
        -----------
        **kwargs : dict
            Serviceability parameters
            
        Returns:
        --------
        List[DesignCheck]
            Serviceability check results
        """
        if all(k in kwargs for k in ['geometry', 'loads', 'reinforcement']):
            result = self.check_deflection(
                kwargs['geometry'],
                kwargs['loads'],
                kwargs['reinforcement'],
                kwargs.get('beam_type', BeamType.SIMPLY_SUPPORTED)
            )
            return result.checks
        else:
            raise ValueError("Insufficient parameters for serviceability check")