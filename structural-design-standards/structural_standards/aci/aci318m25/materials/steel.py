"""
ACI 318M-25 Steel Material Models
=================================

Implementation of reinforcement steel and structural steel properties 
per ACI 318M-25 Building Code Requirements for Structural Concrete.

Based on:
- ACI 318M-25 Chapter 20: Reinforcement
- ACI 318M-25 Chapter 26: Structural Steel in Composite Members
- ASTM A615/A615M: Deformed and Plain Carbon-Steel Bars

การใช้งานเหล็กเสริมและเหล็กโครงสร้างตาม ACI 318M-25
"""

import math
from typing import Dict, Optional, Tuple, List
from structural_standards.base.material_base import SteelMaterial, ReinforcementSteel, SteelType
from structural_standards.utils.validation import validate_positive, validate_range

class ACI318M25Steel(SteelMaterial):
    """
    ACI 318M-25 Structural Steel Material
    
    Implementation of structural steel properties according to ACI 318M-25
    for use in composite members and structural steel elements.
    
    เหล็กโครงสร้างตาม ACI 318M-25
    """
    
    # Standard steel grades per ASTM specifications
    STANDARD_GRADES = {
        'GRADE280': {
            'fy': 280.0,     # MPa - ASTM A615 Grade 280
            'fu': 420.0,     # MPa
            'description': 'Grade 280 Reinforcing Steel'
        },
        'GRADE420': {
            'fy': 420.0,     # MPa - ASTM A615 Grade 420 (most common)
            'fu': 620.0,     # MPa
            'description': 'Grade 420 Reinforcing Steel'
        },
        'GRADE520': {
            'fy': 520.0,     # MPa - ASTM A615 Grade 520
            'fu': 690.0,     # MPa
            'description': 'Grade 520 High-Strength Reinforcing Steel'
        },
        'A36': {
            'fy': 250.0,     # MPa - ASTM A36 Structural Steel
            'fu': 400.0,     # MPa
            'description': 'A36 Structural Steel'
        },
        'A572_50': {
            'fy': 345.0,     # MPa - ASTM A572 Grade 50
            'fu': 450.0,     # MPa
            'description': 'A572 Grade 50 High-Strength Steel'
        }
    }
    
    def __init__(self, 
                 grade: Optional[str] = None,
                 fy: Optional[float] = None,
                 fu: Optional[float] = None,
                 steel_type: SteelType = SteelType.MILD_STEEL,
                 unit_weight: float = 77.0):
        """
        Initialize ACI 318M-25 steel material
        
        Parameters:
        -----------
        grade : str, optional
            Standard steel grade (e.g., 'GRADE420')
        fy : float, optional
            Yield strength (MPa)
        fu : float, optional
            Ultimate tensile strength (MPa)
        steel_type : SteelType
            Type of steel
        unit_weight : float
            Unit weight (kN/m³), default 77.0
            
        Note:
        -----
        Either grade or fy must be provided
        """
        # Determine properties from grade or direct input
        if grade is not None:
            if grade not in self.STANDARD_GRADES:
                raise ValueError(f"Unknown steel grade: {grade}")
            
            grade_props = self.STANDARD_GRADES[grade]
            fy = grade_props['fy']
            fu = grade_props['fu']
            
        elif fy is not None:
            validate_positive(fy, "fy")
            if fu is None:
                fu = fy * 1.5  # Typical assumption if not provided
        else:
            raise ValueError("Either grade or fy must be provided")
        
        # Initialize base class
        super().__init__(
            fy=fy,
            fu=fu,
            steel_type=steel_type,
            unit_weight=unit_weight,
            standard="ACI 318M-25"
        )
        
        self.grade = grade
        
        # ACI 318M-25 specific properties
        self.Es = 200000.0  # MPa - ACI 318M-25 Section 20.2.2.2
        self._validate_aci_requirements()
    
    def _validate_aci_requirements(self) -> None:
        """Structural steel != rebar: A36 fy=250MPa is an allowed steel grade.

        Steel member design still requires the applicable structural steel code.
        """
        if (not math.isfinite(self.fy) or not math.isfinite(self.fu)
                or self.fy <= 0 or self.fu < self.fy):
            raise ValueError("Structural steel must have finite Fu >= Fy > 0")

    def elastic_modulus(self) -> float:
        """
        Get elastic modulus per ACI 318M-25
        
        ACI 318M-25 Section 20.2.2.2: Es = 200,000 MPa
        
        Returns:
        --------
        float
            Elastic modulus (MPa)
        """
        return self.Es
    
    def get_development_length_factors(self) -> Dict[str, float]:
        """
        Get development length factors per ACI 318M-25 Chapter 25
        
        Returns:
        --------
        Dict[str, float]
            Development length modification factors
        """
        # ACI 318M-25 Section 25.4.2 - Basic development length factors
        factors = {
            'bar_location_top': 1.3,      # Top reinforcement factor
            'bar_location_other': 1.0,    # Other reinforcement
            'concrete_density': 1.0,      # Normal weight concrete
            'bar_coating': 1.0,           # Uncoated bars
            'bar_size': 1.0,              # For bars ≤ 22M
            'concrete_cover': 1.0,        # Adequate cover and spacing
            'transverse_reinforcement': 1.0,  # Minimum stirrups/ties provided
            'excess_reinforcement': 1.0   # As,required / As,provided
        }
        
        return factors
    
    def calculate_development_length(
            self, bar_diameter: float, concrete_strength: float,
            bar_location: str = "other",
            bar_coating: str = "uncoated") -> float:
        """Disabled: previous implementation assumed max confinement=2.5.

        (cb+Ktr)/db=2.5 is an UPPER LIMIT, not a conservative assumed
        input. Without cover/spacing and transverse details the answer could
        dangerously UNDERESTIMATE required anchorage.
        """
        raise NotImplementedError(
            "ACI 318-25 ld NOT VERIFIED: provide actual bar center cover, "
            "center spacing, confinement reinforcement, concrete density, "
            "coating, grade and bar position; no assumed maximum confinement."
        )

    @staticmethod
    def evaluate_development_expression_si(
            fy_mpa: float, fc_mpa: float, db_mm: float,
            cb_mm: float, ktr_mm: float, lambda_factor: float,
            psi_t: float, psi_e: float, psi_s: float,
            psi_g: float) -> Dict[str, float]:
        """Dimensioned SI evaluation of fully EXPLICIT GENERAL ld expression.

        This arithmetic helper is NOT ACI code compliance: all psi modifiers,
        their applicability, the chosen edition, the confinement index and
        required minimum length must be externally verified. It does NOT
        choose any of those values. Per general equation denominator 1.1.
        """
        values={"fy":fy_mpa,"fc":fc_mpa,"db":db_mm,"cb":cb_mm,
                "Ktr":ktr_mm,"lambda":lambda_factor,"psi_t":psi_t,
                "psi_e":psi_e,"psi_s":psi_s,"psi_g":psi_g}
        if any(not math.isfinite(v) for v in values.values()):
            raise ValueError("All anchorage variables must be finite")
        if any(v <= 0 for k,v in values.items() if k not in ("Ktr",)):
            raise ValueError("All non-Ktr anchorage variables must be positive")
        if ktr_mm < 0:
            raise ValueError("Ktr must be nonnegative mm")
        confinement_ratio=min((cb_mm+ktr_mm)/db_mm,2.5)
        ld=fy_mpa*psi_t*psi_e*psi_s*psi_g*db_mm / (
            1.1*lambda_factor*math.sqrt(fc_mpa)*confinement_ratio)
        return {
            "general_expression_length_mm": ld,
            "confinement_ratio_capped": confinement_ratio,
            "not_code_compliant_without_detail_checks": True,
        }

    def get_splice_length(self, bar_diameter: float,
                         concrete_strength: float,
                         splice_type: str = "tension") -> float:
        """No automatic Class A lap or unsupported compression-splice equation."""
        raise NotImplementedError(
            "ACI lap splice NOT VERIFIED: Class A/B applicability, bar continuity "
            "and spacing, tension/compression state, cover/confinement and "
            "seismic requirements must be specified."
        )

    def get_design_properties(self) -> Dict[str, float]:
        """
        Get comprehensive design properties for ACI 318M-25
        
        Returns:
        --------
        Dict[str, float]
            All relevant design properties
        """
        base_props = super().get_design_properties()
        
        aci_props = {
            'elastic_modulus': self.elastic_modulus(),
            'elongation_min': 9.0 if self.fy <= 420 else 7.0,  # % (ASTM requirements)
            'bend_diameter_factor': 6.0 if self.fy <= 420 else 8.0,  # For 90° bends
            'max_spacing_factor': 3.0,  # Maximum spacing = 3h or 500mm
        }
        
        return {**base_props, **aci_props}
    
    def __str__(self) -> str:
        """String representation"""
        grade_str = f" {self.grade}" if self.grade else ""
        return f"ACI 318M-25 Steel{grade_str} (fy = {self.fy} MPa)"

class ACI318M25ReinforcementSteel(ReinforcementSteel):
    """
    ACI 318M-25 Reinforcement Steel (Rebar)
    
    Implementation of reinforcement steel properties according to ACI 318M-25
    and ASTM A615/A615M specifications.
    
    เหล็กเสริมตาม ACI 318M-25
    """
    
    # Standard bar designations and properties per ASTM A615M
    STANDARD_BARS = {
        # Metric bar designations (ASTM A615M)
        '10M': {'diameter': 11.3, 'area': 100, 'mass': 0.785},    # mm, mm², kg/m
        '15M': {'diameter': 16.0, 'area': 200, 'mass': 1.570},
        '20M': {'diameter': 19.5, 'area': 300, 'mass': 2.355},
        '25M': {'diameter': 25.2, 'area': 500, 'mass': 3.925},
        '30M': {'diameter': 29.9, 'area': 700, 'mass': 5.495},
        '35M': {'diameter': 35.7, 'area': 1000, 'mass': 7.850},
        '45M': {'diameter': 43.7, 'area': 1500, 'mass': 11.775},
        '55M': {'diameter': 56.4, 'area': 2500, 'mass': 19.625},
        
        # Imperial equivalents for reference (ASTM A615)
        '#3': {'diameter': 9.5, 'area': 71, 'mass': 0.560},      # ≈ 10M
        '#4': {'diameter': 12.7, 'area': 129, 'mass': 1.043},    # Between 10M-15M
        '#5': {'diameter': 15.9, 'area': 200, 'mass': 1.552},    # ≈ 15M
        '#6': {'diameter': 19.1, 'area': 284, 'mass': 2.235},    # ≈ 20M
        '#7': {'diameter': 22.2, 'area': 387, 'mass': 3.042},    # Between 20M-25M
        '#8': {'diameter': 25.4, 'area': 510, 'mass': 3.973},    # ≈ 25M
        '#9': {'diameter': 28.7, 'area': 645, 'mass': 5.060},    # Between 25M-30M
        '#10': {'diameter': 32.3, 'area': 819, 'mass': 6.404},   # Between 30M-35M
        '#11': {'diameter': 35.8, 'area': 1006, 'mass': 7.907},  # ≈ 35M
        '#14': {'diameter': 43.0, 'area': 1452, 'mass': 11.38},  # ≈ 45M
        '#18': {'diameter': 57.3, 'area': 2581, 'mass': 20.24}   # ≈ 55M
    }
    
    def __init__(self,
                 bar_designation: str,
                 grade: str = 'GRADE420',
                 surface_condition: str = 'deformed'):
        """
        Initialize ACI 318M-25 reinforcement steel
        
        Parameters:
        -----------
        bar_designation : str
            Bar designation (e.g., '20M', '#6')
        grade : str
            Steel grade ('GRADE280', 'GRADE420', 'GRADE520')
        surface_condition : str
            'deformed' or 'plain'
        """
        if bar_designation not in self.STANDARD_BARS:
            raise ValueError(f"Unknown bar designation: {bar_designation}")
        
        # Get steel properties from grade
        if grade in ACI318M25Steel.STANDARD_GRADES:
            fy = ACI318M25Steel.STANDARD_GRADES[grade]['fy']
        else:
            raise ValueError(f"Unknown steel grade: {grade}")
        
        # Initialize base class
        super().__init__(
            fy=fy,
            bar_designation=bar_designation,
            surface_condition=surface_condition,
            standard="ACI 318M-25"
        )
        
        self.grade = grade
        self.bar_properties = self.STANDARD_BARS[bar_designation]
    
    def bar_area(self) -> float:
        """
        Get cross-sectional area of the bar
        
        Returns:
        --------
        float
            Bar area (mm²)
        """
        return self.bar_properties['area']
    
    def bar_diameter(self) -> float:
        """
        Get nominal diameter of the bar
        
        Returns:
        --------
        float
            Nominal diameter (mm)
        """
        return self.bar_properties['diameter']
    
    def bar_mass(self) -> float:
        """
        Get mass per unit length of the bar
        
        Returns:
        --------
        float
            Mass per unit length (kg/m)
        """
        return self.bar_properties['mass']
    
    def get_minimum_bend_diameter(self, bend_angle: float = 90.0) -> float:
        """ACI longitudinal STANDARD hook bend; not ties/seismic hooks.

        #3-#8: 6db; #9-#11: 8db; #14-#18: 10db.
        Extension length must be checked separately.
        """
        if bend_angle not in (90.0, 180.0):
            raise NotImplementedError("Tie/seismic hook bend needs its own rule")
        db = self.bar_diameter()
        if db <= 25.4:
            return 6 * db
        elif db <= 35.8:
            return 8 * db
        return 10 * db

    def get_maximum_spacing(self, member_thickness: float) -> float:
        """No universal ACI max spacing without slab type and reinforcement role."""
        raise NotImplementedError("Spacing requires slab system, layer, cover and design checks")

    def calculate_area_per_meter(self, spacing: float) -> float:
        """
        Calculate reinforcement area per meter width
        
        Parameters:
        -----------
        spacing : float
            Bar spacing (mm)
            
        Returns:
        --------
        float
            Area per meter (mm²/m)
        """
        if not math.isfinite(spacing) or spacing <= 0:
            raise ValueError("Spacing must be a finite positive mm value")
        return (self.bar_area() * 1000.0) / spacing
    
    def get_design_properties(self) -> Dict[str, float]:
        """
        Get comprehensive design properties
        
        Returns:
        --------
        Dict[str, float]
            All relevant design properties
        """
        base_props = super().get_design_properties()
        
        aci_props = {
            'bar_area': self.bar_area(),
            'bar_diameter': self.bar_diameter(),
            'bar_mass': self.bar_mass(),
            'min_bend_diameter_90': self.get_minimum_bend_diameter(90.0),
            'min_bend_diameter_180': self.get_minimum_bend_diameter(180.0)
        }
        
        return {**base_props, **aci_props}
    
    def __str__(self) -> str:
        """String representation"""
        return f"ACI 318M-25 Rebar {self.bar_designation} {self.grade} (fy = {self.fy} MPa)"

def create_aci_reinforcement_database() -> Dict[str, ACI318M25ReinforcementSteel]:
    """
    Create a complete database of ACI reinforcement steel
    
    Returns:
    --------
    Dict[str, ACI318M25ReinforcementSteel]
        Database of all standard reinforcement bars
    """
    database = {}
    
    # Create all standard metric bars with Grade 420
    metric_bars = ['10M', '15M', '20M', '25M', '30M', '35M', '45M', '55M']
    
    for bar in metric_bars:
        database[bar] = ACI318M25ReinforcementSteel(
            bar_designation=bar,
            grade='GRADE420'
        )
    
    # Create Grade 280 alternatives
    for bar in metric_bars[:4]:  # Common sizes for Grade 280
        key = f"{bar}_G280"
        database[key] = ACI318M25ReinforcementSteel(
            bar_designation=bar,
            grade='GRADE280'
        )
    
    return database