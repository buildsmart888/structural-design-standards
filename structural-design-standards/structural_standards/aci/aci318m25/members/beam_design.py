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
        
def design_flexural_reinforcement(self, geometry: BeamGeometry,
                                    moment_ultimate: float,
                                    moment_service: Optional[float] = None) -> DesignResult:
        """Rectangular singly-reinforced, tension-controlled SECTIONAL flexure.

        b, h, d in mm, fc' and fy in MPa, Mu in kN.m, As in mm2.
        ACI 318M-25 9.3.3, 9.6.1, 21.2.2, 22.2. Not a complete beam design.
        """
        validate_positive(moment_ultimate, "Factored moment magnitude (kN.m)")
        b, h, d = geometry.width, geometry.height, geometry.effective_depth
        for name, v in (("b", b), ("h", h), ("d", d)):
            validate_positive(v, name)
        if d >= h:
            raise ValueError("Effective depth must be smaller than beam height")
        Mu = moment_ultimate * 1e6
        phi = self.phi_flexure
        As_min = self.minimum_flexural_reinforcement_ratio(b, d) * b * d
        As_max = self.maximum_flexural_reinforcement_ratio() * b * d
        if As_min > As_max:
            raise ValueError("Minimum steel exceeds tension-controlled limit")
        # Mn = As*fy*d - (As**2 * fy**2)/(2*0.85*fc'*b).
        a = self.fy**2 / (2 * 0.85 * self.fc * b)
        bb = self.fy * d
        target_Mn = Mu / phi
        disc = bb**2 - 4 * a * target_Mn
        As_trial = 2 * target_Mn / (bb + math.sqrt(disc)) if disc >= 0 else None
        max_phiMn = self.flexural_capacity(b, d, As_max, phi)
        feasible = (As_trial is not None
                    and As_trial <= As_max * (1 + 1e-9)
                    and Mu <= max_phiMn * (1 + 1e-9))
        warnings = []
        if feasible:
            As_req = max(As_trial, As_min)
            if As_trial < As_min:
                warnings.append("Minimum longitudinal steel controls")
            As_checked = As_req
        else:
            As_req = None
            As_checked = As_max  # Report limit capacity, NOT a usable design
            warnings.append("Tension-controlled singly reinforced section is insufficient; "
                            "increase section or use a separately verified method")
        phiMn = self.flexural_capacity(b, d, As_checked, phi)
        utilization = Mu / phiMn if phiMn > 0 else float("inf")
        ok = feasible and utilization <= 1 + 1e-9
        checks = [
            DesignCheck(name="Flexural Strength",
                        status=DesignStatus.PASS if ok else DesignStatus.FAIL,
                        value=moment_ultimate, limit=phiMn / 1e6, ratio=utilization,
                        units="kN.m", code_reference="ACI 318M-25 9.3.3, 22.2"),
            DesignCheck(name="Minimum Reinforcement",
                        status=DesignStatus.PASS if As_checked >= As_min else DesignStatus.FAIL,
                        value=As_checked, limit=As_min,
                        ratio=As_min / As_checked if As_checked else float("inf"),
                        units="mm2", code_reference="ACI 318M-25 9.6.1"),
            DesignCheck(name="Tension-Controlled Maximum Steel",
                        status=DesignStatus.PASS if feasible else DesignStatus.FAIL,
                        value=As_checked, limit=As_max,
                        ratio=As_checked / As_max if As_max else float("inf"),
                        units="mm2", code_reference="ACI 318M-25 9.3.3, 21.2.2"),
        ]
        if moment_service is not None:
            warnings.append("Service cracking/deflection NOT CHECKED; moment_service unused")
        return DesignResult(
            member_type="beam", design_method="ACI 318M-25",
            overall_status=DesignStatus.NOT_CHECKED if ok else DesignStatus.FAIL,
            utilization_ratio=utilization, strength_checks=checks[:1],
            detailing_checks=checks[1:],
            design_forces={"moment_ultimate_kNm": moment_ultimate},
            design_capacities={"phi_Mn_kNm": phiMn / 1e6,
                               "maximum_phi_Mn_kNm": max_phiMn / 1e6},
            required_reinforcement={"As_required_mm2": As_req,
                                    "required_steel_area": As_req,
                                    "As_min_mm2": As_min,
                                    "As_max_tension_controlled_mm2": As_max},
            warnings=warnings,
            notes=["Strength check may PASS, but complete member is NOT VERIFIED until "
                   "all required limit states and detailing have been checked."],
        )

def design_shear_reinforcement(self, geometry: BeamGeometry,
                                 shear_ultimate: float,
                                 longitudinal_steel: float) -> DesignResult:
        """Preliminary nonprestressed rectangular BEAM shear WITH min stirrups.

        Assumes no torsion, axial load, prestressing or seismic ductility demands.
        2-leg 10 mm stirrups, fyt = min(rebar fy, 420 MPa). b,d mm, fc' MPa.
        ACI 318M-25 9.6.3, 9.7.6, 22.5. Cross-width detailing not checked.
        """
        validate_positive(shear_ultimate, "Shear demand magnitude (kN)")
        validate_positive(longitudinal_steel, "Longitudinal steel area (mm2)")
        b, h, d = geometry.width, geometry.height, geometry.effective_depth
        for name, v in (("b", b), ("h", h), ("d", d)):
            validate_positive(v, name)
        if d >= h:
            raise ValueError("Effective depth must be smaller than beam height")
        Vu = shear_ultimate * 1000  # kN -> N
        phi = self.phi_shear
        fyt = min(self.fy, 420.0)
        sqrt_fc = math.sqrt(self.fc)
        lam = self.concrete.shear_strength_factor()
        # Vc branch applies ONLY when Av >= Av,min (N = MPa*mm2).
        Vc = 0.17 * lam * sqrt_fc * b * d
        Vs_required = max(0.0, Vu / phi - Vc)
        Vs_max = 0.66 * sqrt_fc * b * d
        avs_min = self.minimum_shear_reinforcement_area(b, fyt)
        avs_strength = Vs_required / (fyt * d)
        avs = max(avs_min, avs_strength)
        db = 10.0  # mm
        Av = 2 * math.pi * (db / 2)**2  # two-legged stirrup area, mm2
        s_max = (min(d / 4, 300.0) if Vs_required > 0.33 * sqrt_fc * b * d
                 else min(d / 2, 600.0))
        s = min(Av / avs, s_max)
        Vs_provided = Av * fyt * d / s
        phiVn = phi * (Vc + min(Vs_provided, Vs_max))
        utilization = Vu / phiVn
        strength_ok = utilization <= 1 + 1e-9 and Vs_required <= Vs_max * (1 + 1e-9)
        # This 50mm lower bound is a construction screening rule, NOT a code limit.
        spacing_ok = 50.0 <= s <= s_max + 1e-9
        checks = [
            DesignCheck(name="Shear Strength",
                        status=DesignStatus.PASS if strength_ok else DesignStatus.FAIL,
                        value=shear_ultimate, limit=phiVn / 1000, ratio=utilization,
                        units="kN", code_reference="ACI 318M-25 22.5"),
            DesignCheck(name="Max Shear Steel Contribution",
                        status=DesignStatus.PASS if Vs_required <= Vs_max else DesignStatus.FAIL,
                        value=Vs_required / 1000, limit=Vs_max / 1000,
                        ratio=Vs_required / Vs_max, units="kN",
                        code_reference="ACI 318M-25 22.5"),
            DesignCheck(name="Preliminary Stirrup Spacing",
                        status=DesignStatus.PASS if spacing_ok else DesignStatus.FAIL,
                        value=s, limit=s_max, ratio=s / s_max, units="mm",
                        code_reference="ACI 318M-25 9.7.6"),
        ]
        warnings = ["Sectional shear only: torsion, axial forces, seismic detailing, "
                    "support critical sections and cross-width stirrup layout NOT CHECKED"]
        if not strength_ok:
            warnings.append("Section exceeds maximum shear strength")
        if not spacing_ok:
            warnings.append("Stirrup spacing below 50 mm constructability screening limit")
        return DesignResult(
            member_type="beam", design_method="ACI 318M-25",
            overall_status=(DesignStatus.NOT_CHECKED if strength_ok and spacing_ok
                            else DesignStatus.FAIL),
            utilization_ratio=utilization, strength_checks=checks[:2],
            detailing_checks=checks[2:],
            design_forces={"shear_ultimate_kN": shear_ultimate},
            design_capacities={"phi_Vn_kN": phiVn / 1000,
                               "phi_Vc_kN": phi * Vc / 1000,
                               "Vs_max_nominal_kN": Vs_max / 1000},
            required_reinforcement={"stirrup_diameter_mm": db, "stirrup_legs": 2,
                                    "stirrup_area_mm2": Av, "stirrup_spacing_mm": s,
                                    "stirrup_fyt_MPa": fyt,
                                    "Av_over_s_min_mm2_per_mm": avs_min,
                                    "Av_over_s_strength_mm2_per_mm": avs_strength,
                                    "shear_reinforcement_required": Vu > 0.5 * phi * Vc,
                                    "minimum_stirrups_provided": True},
            warnings=warnings,
        )

def check_deflection(self, geometry: BeamGeometry, loads: BeamLoads,
                         reinforcement: BeamReinforcement,
                         beam_type: BeamType = BeamType.SIMPLY_SUPPORTED) -> DesignResult:
        """Do NOT report fictitious passing deflection with placeholder As=1000."""
        raise NotImplementedError(
            "ACI 318M-25 deflection NOT VERIFIED: actual tension/compression bar "
            "areas, cracked stiffness, serviceability combinations and sustained "
            "load history are required; no placeholder reinforcement is allowed"
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
        """Tension-controlled limit: epsilon_t >= fy/Es + 0.003, ACI 21.2.2."""
        eps_limit = self.epsilon_ty + 0.003
        c_over_d = self.epsilon_cu / (self.epsilon_cu + eps_limit)
        return 0.85 * self.fc * self.concrete.beta1() * c_over_d / self.fy

def minimum_shear_reinforcement_area(self, b: float,
                                         stirrup_fy: Optional[float] = None) -> float:
        """Av,min/s in mm2/mm, ACI 318M-25 Table 9.6.3.4, not Av per stirrup."""
        validate_positive(b, "Web width")
        fyt = min(self.fy, 420.0) if stirrup_fy is None else stirrup_fy
        validate_positive(fyt, "Stirrup yield strength")
        return max(0.062 * math.sqrt(self.fc) * b / fyt,
                   0.35 * b / fyt)

    def flexural_capacity(self, b: float, d: float, As: float, phi: float) -> float:
        """
        Calculate flexural capacity of section
        
        Returns:
        --------
        float
            Design moment strength phi*Mn (N.mm)
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
            return result.strength_checks + result.detailing_checks
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
            return result.serviceability_checks
        else:
            raise ValueError("Insufficient parameters for serviceability check")