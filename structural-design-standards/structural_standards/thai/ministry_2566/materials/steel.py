"""
Thai Steel Materials - Ministry Regulation B.E. 2566
====================================================

Implementation of Thai steel materials according to:
- Ministry Regulation B.E. 2566 (2023) for structural design standards  
- มยผ. 1103 for steel specifications
- TIS standards for reinforcement steel

การใช้งานวัสดุเหล็กไทยตาม:
- กฎกระทรวง พ.ศ. 2566 สำหรับมาตรฐานการออกแบบโครงสร้าง
- มยผ. 1103 สำหรับข้อกำหนดเหล็ก
- มาตรฐาน TIS สำหรับเหล็กเสริม
"""

import math
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from ....base.material_base import SteelMaterial, ReinforcementSteel, SteelType
from ....utils.validation import validate_positive, validate_range


class ThaiSteelGrade(Enum):
    """Thai steel grade designations"""
    SR24 = "SR24"  # 2400 ksc = 235.4 MPa (round bars)
    SD40 = "SD40"  # 4000 ksc = 392.4 MPa (deformed bars)
    SD50 = "SD50"  # 5000 ksc = 490.5 MPa (deformed bars, high strength)


class ThaiRebarDesignation(Enum):
    """Thai reinforcement bar designations"""
    # Deformed bars (ข้ออ้อย)
    DB10 = "DB10"  # 10mm diameter
    DB12 = "DB12"  # 12mm diameter  
    DB20 = "DB20"  # 20mm diameter
    DB25 = "DB25"  # 25mm diameter
    DB32 = "DB32"  # 32mm diameter
    DB36 = "DB36"  # 36mm diameter
    DB40 = "DB40"  # 40mm diameter
    
    # Round bars (เหล็กกลม)
    RB6 = "RB6"    # 6mm round bar
    RB9 = "RB9"    # 9mm round bar


@dataclass
class ThaiSteelProperties:
    """Properties of Thai steel grades"""
    grade: str
    fy_mpa: float              # Yield strength (MPa)
    fy_ksc: float              # Yield strength (ksc)
    fu_mpa: float              # Ultimate strength (MPa)
    fu_ksc: float              # Ultimate strength (ksc)
    steel_type: str            # "round" or "deformed"
    surface_condition: str     # "plain" or "deformed"
    min_elongation: float      # Minimum elongation (%)
    description_thai: str
    description_english: str


@dataclass
class ThaiRebarProperties:
    """Properties of Thai reinforcement bars"""
    designation: str
    diameter_mm: float         # Nominal diameter (mm)
    area_mm2: float           # Cross-sectional area (mm²)
    mass_kg_m: float          # Mass per meter (kg/m)
    surface_type: str         # "round" or "deformed"
    typical_grade: str        # Typical steel grade used
    description_thai: str
    description_english: str


class ThaiSteel(SteelMaterial):
    """
    Thai steel material implementation
    
    วัสดุเหล็กไทยตามมาตรฐาน มยผ.
    """
    
    # Standard Thai steel grades
    THAI_STEEL_GRADES = {
        ThaiSteelGrade.SR24: ThaiSteelProperties(
            grade="SR24",
            fy_mpa=235.3596,  # exact 2400 kgf/cm2 in MPa
            fy_ksc=2400.0,
            fu_mpa=372.6527,  # exact 3800 kgf/cm2 in MPa
            fu_ksc=3800.0,
            steel_type="round",
            surface_condition="plain",
            min_elongation=25.0,
            description_thai="เหล็กกลม SR24 กำลังครากสู่งที่จุดครางเหล็ก 2400 กก./ตร.ซม.",
            description_english="Round Steel SR24 Yield Strength 2400 ksc"
        ),
        
        ThaiSteelGrade.SD40: ThaiSteelProperties(
            grade="SD40", 
            fy_mpa=392.266,  # exact 4000 kgf/cm2 in MPa
            fy_ksc=4000.0,
            fu_mpa=588.399,  # exact 6000 kgf/cm2 in MPa
            fu_ksc=6000.0,
            steel_type="deformed",
            surface_condition="deformed",
            min_elongation=18.0,
            description_thai="เหล็กข้ออ้อย SD40 กำลังครากสู่งที่จุดครางเหล็ก 4000 กก./ตร.ซม.",
            description_english="Deformed Steel SD40 Yield Strength 4000 ksc"
        ),
        
        ThaiSteelGrade.SD50: ThaiSteelProperties(
            grade="SD50",
            fy_mpa=490.3325,  # exact 5000 kgf/cm2 in MPa
            fy_ksc=5000.0,
            fu_mpa=686.4655,  # exact 7000 kgf/cm2 in MPa
            fu_ksc=7000.0,
            steel_type="deformed",
            surface_condition="deformed",
            min_elongation=16.0,
            description_thai="เหล็กข้ออ้อย SD50 กำลังครากสู่งที่จุดครางเหล็ก 5000 กก./ตร.ซม.",
            description_english="Deformed Steel SD50 Yield Strength 5000 ksc"
        )
    }
    
    def __init__(self,
                 grade: Optional[str] = None,
                 fy: Optional[float] = None,
                 fu: Optional[float] = None,
                 steel_type: SteelType = SteelType.MILD_STEEL,
                 unit_weight: float = 77.0):
        """
        Initialize Thai steel
        
        Parameters:
        -----------
        grade : str, optional
            Thai steel grade (e.g., 'SD40', 'SD50', 'SR24')
        fy : float, optional
            Yield strength (MPa)
        fu : float, optional
            Ultimate tensile strength (MPa)
        steel_type : SteelType
            Type of steel
        unit_weight : float
            Unit weight (kN/m³), default 77.0
        """
        # Determine properties from grade or direct input
        if grade is not None:
            grade_enum = self._parse_grade(grade)
            if grade_enum not in self.THAI_STEEL_GRADES:
                raise ValueError(f"Unknown Thai steel grade: {grade}")
            
            props = self.THAI_STEEL_GRADES[grade_enum]
            fy = props.fy_mpa
            fu = props.fu_mpa
            grade = props.grade  # canonical case, never a mismatched grade key
            
        elif fy is not None:
            validate_positive(fy, "fy")
            if fu is None:
                raise ValueError(
                    "Custom Thai steel fy requires measured/specified Fu; "
                    "an assumed Fu=1.5Fy is not sufficient"
                )
            validate_positive(fu, "fu")
            grade = self._determine_grade_from_strength(fy)
        else:
            raise ValueError("Either grade or fy must be provided")
        
        # Initialize base class
        super().__init__(
            fy=fy,
            fu=fu,
            steel_type=steel_type,
            unit_weight=unit_weight,
            standard="Thai Ministry B.E. 2566"
        )
        
        self.grade = grade
        self.grade_properties = self._get_grade_properties()
        
        # Thai steel specific properties
        self.Es = 200000.0  # MPa - standard for Thai steel
        
        # Validate Thai requirements
        self._validate_thai_requirements()
    
    def _parse_grade(self, grade: str) -> ThaiSteelGrade:
        """Parse grade string to enum"""
        grade_upper = grade.upper()
        
        for thai_grade in ThaiSteelGrade:
            if thai_grade.value.upper() == grade_upper:
                return thai_grade
        
        raise ValueError(f"Invalid Thai steel grade: {grade}")
    
    def _determine_grade_from_strength(self, fy: float) -> str:
        """Do not silently label custom MPa input as a certified TIS grade."""
        if not math.isfinite(fy) or fy <= 0:
            raise ValueError("fy must be finite positive")
        for props in self.THAI_STEEL_GRADES.values():
            if math.isclose(fy, props.fy_mpa, rel_tol=0, abs_tol=1e-6):
                return props.grade
        return "CUSTOM"

    def _get_grade_properties(self) -> Optional[ThaiSteelProperties]:
        """Get properties for current grade"""
        for grade_enum, props in self.THAI_STEEL_GRADES.items():
            if props.grade == self.grade:
                return props
        return None
    
    def _validate_thai_requirements(self) -> None:
        """Validate according to Thai standards"""
        if self.fy < 200.0:
            raise ValueError("Thai standard: Minimum fy is 200 MPa")
        
        if self.fy > 600.0:
            raise ValueError("Thai standard: fy > 600 MPa requires special approval")
        
        # Check fu/fy ratio
        if self.fu / self.fy < 1.25:
            raise ValueError("Thai standard: fu/fy ratio must be ≥ 1.25")
    
    def elastic_modulus(self) -> float:
        """
        Get elastic modulus per Thai standards
        
        Thai standard: Es = 200,000 MPa
        
        Returns:
        --------
        float
            Elastic modulus (MPa)
        """
        return self.Es
    
    def yield_strength_ksc(self) -> float:
        """
        Get yield strength in ksc (Thai traditional unit)
        
        Returns:
        --------
        float
            Yield strength (ksc)
        """
        return self.fy * 1000 / 98.0665  # MPa -> ksc; 1 ksc = 1 kgf/cm2 = 0.0980665 MPa
    
    def ultimate_strength_ksc(self) -> float:
        """
        Get ultimate strength in ksc
        
        Returns:
        --------
        float
            Ultimate strength (ksc)
        """
        return self.fu * 1000 / 98.0665  # MPa -> ksc; 1 ksc = 1 kgf/cm2 = 0.0980665 MPa
    
    def get_design_properties(self) -> Dict[str, float]:
        """
        Get comprehensive design properties for Thai steel
        
        Returns:
        --------
        Dict[str, float]
            All relevant design properties
        """
        base_props = super().get_design_properties()
        
        thai_props = {
            'elastic_modulus_thai': self.elastic_modulus(),
            'yield_strength_ksc': self.yield_strength_ksc(),
            'ultimate_strength_ksc': self.ultimate_strength_ksc(),
            'density_kg_m3': self.unit_weight * 1000 / 9.81,
        }
        
        if self.grade_properties:
            thai_props.update({
                'min_elongation_percent': self.grade_properties.min_elongation,
                'surface_condition': self.grade_properties.surface_condition
            })
        
        return {**base_props, **thai_props}
    
    def __str__(self) -> str:
        """String representation"""
        if self.grade_properties:
            return f"Thai Steel {self.grade} (fy = {self.fy:.0f} MPa = {self.yield_strength_ksc():.0f} ksc)"
        else:
            return f"Thai Steel fy = {self.fy:.0f} MPa"


class ThaiReinforcementSteel(ReinforcementSteel):
    """
    Thai reinforcement steel (rebar) implementation
    
    เหล็กเสริมไทยตามมาตรฐาน TIS
    """
    
    # Standard Thai rebar designations and properties
    THAI_REBAR_DESIGNATIONS = {
        ThaiRebarDesignation.DB10: ThaiRebarProperties(
            designation="DB10",
            diameter_mm=10.0,
            area_mm2=78.5,
            mass_kg_m=0.617,
            surface_type="deformed",
            typical_grade="SD40",
            description_thai="เหล็กข้ออ้อยเบอร์ 10 มิลลิเมตร",
            description_english="Deformed Bar 10mm"
        ),
        
        ThaiRebarDesignation.DB12: ThaiRebarProperties(
            designation="DB12",
            diameter_mm=12.0,
            area_mm2=113.1,
            mass_kg_m=0.888,
            surface_type="deformed",
            typical_grade="SD40",
            description_thai="เหล็กข้ออ้อยเบอร์ 12 มิลลิเมตร",
            description_english="Deformed Bar 12mm"
        ),
        
        ThaiRebarDesignation.DB20: ThaiRebarProperties(
            designation="DB20",
            diameter_mm=20.0,
            area_mm2=314.2,
            mass_kg_m=2.466,
            surface_type="deformed",
            typical_grade="SD40",
            description_thai="เหล็กข้ออ้อยเบอร์ 20 มิลลิเมตร",
            description_english="Deformed Bar 20mm"
        ),
        
        ThaiRebarDesignation.DB25: ThaiRebarProperties(
            designation="DB25",
            diameter_mm=25.0,
            area_mm2=490.9,
            mass_kg_m=3.853,
            surface_type="deformed",
            typical_grade="SD40",
            description_thai="เหล็กข้ออ้อยเบอร์ 25 มิลลิเมตร",
            description_english="Deformed Bar 25mm"
        ),
        
        ThaiRebarDesignation.DB32: ThaiRebarProperties(
            designation="DB32",
            diameter_mm=32.0,
            area_mm2=804.2,
            mass_kg_m=6.313,
            surface_type="deformed",
            typical_grade="SD40",
            description_thai="เหล็กข้ออ้อยเบอร์ 32 มิลลิเมตร",
            description_english="Deformed Bar 32mm"
        ),
        
        ThaiRebarDesignation.DB36: ThaiRebarProperties(
            designation="DB36",
            diameter_mm=36.0,
            area_mm2=1017.9,
            mass_kg_m=7.990,
            surface_type="deformed",
            typical_grade="SD40",
            description_thai="เหล็กข้ออ้อยเบอร์ 36 มิลลิเมตร",
            description_english="Deformed Bar 36mm"
        ),
        
        ThaiRebarDesignation.DB40: ThaiRebarProperties(
            designation="DB40",
            diameter_mm=40.0,
            area_mm2=1256.6,
            mass_kg_m=9.865,
            surface_type="deformed",
            typical_grade="SD50",
            description_thai="เหล็กข้ออ้อยเบอร์ 40 มิลลิเมตร",
            description_english="Deformed Bar 40mm"
        ),
        
        ThaiRebarDesignation.RB6: ThaiRebarProperties(
            designation="RB6",
            diameter_mm=6.0,
            area_mm2=28.3,
            mass_kg_m=0.222,
            surface_type="round",
            typical_grade="SR24",
            description_thai="เหล็กกลมเบอร์ 6 มิลลิเมตร",
            description_english="Round Bar 6mm"
        ),
        
        ThaiRebarDesignation.RB9: ThaiRebarProperties(
            designation="RB9",
            diameter_mm=9.0,
            area_mm2=63.6,
            mass_kg_m=0.499,
            surface_type="round",
            typical_grade="SR24",
            description_thai="เหล็กกลมเบอร์ 9 มิลลิเมตร",
            description_english="Round Bar 9mm"
        )
    }
    
    def __init__(self,
                 bar_designation: str,
                 steel_grade: Optional[str] = None):
        """
        Initialize Thai reinforcement steel
        
        Parameters:
        -----------
        bar_designation : str
            Thai bar designation (e.g., "DB20", "DB25", "RB6")
        steel_grade : str, optional
            Steel grade override (e.g., "SD40", "SD50", "SR24")
        """
        # Parse bar designation
        designation_enum = self._parse_designation(bar_designation)
        if designation_enum not in self.THAI_REBAR_DESIGNATIONS:
            raise ValueError(f"Unknown Thai bar designation: {bar_designation}")
        
        self.rebar_properties = self.THAI_REBAR_DESIGNATIONS[designation_enum]
        
        # Determine steel grade
        if steel_grade is None:
            steel_grade = self.rebar_properties.typical_grade
        
        if self.rebar_properties.surface_type == "round" and steel_grade.upper() != "SR24":
            raise ValueError("Round RB bar requires SR24, not a deformed-bar grade")
        if self.rebar_properties.surface_type == "deformed" and steel_grade.upper() not in ("SD40", "SD50"):
            raise ValueError("Deformed DB bar cannot use the plain-bar SR24 grade")

        # Get steel properties
        thai_steel = ThaiSteel(grade=steel_grade)
        
        # Initialize base class
        super().__init__(
            fy=thai_steel.fy,
            bar_designation=bar_designation,
            surface_condition=self.rebar_properties.surface_type,
            standard="Thai Ministry B.E. 2566"
        )
        
        self.steel_grade = steel_grade
        self.steel_properties = thai_steel.grade_properties
    
    def _parse_designation(self, designation: str) -> ThaiRebarDesignation:
        """Parse designation string to enum"""
        designation_upper = designation.upper()
        
        for thai_designation in ThaiRebarDesignation:
            if thai_designation.value.upper() == designation_upper:
                return thai_designation
        
        raise ValueError(f"Invalid Thai bar designation: {designation}")
    
    def bar_area(self) -> float:
        """
        Get cross-sectional area of the bar
        
        Returns:
        --------
        float
            Cross-sectional area (mm²)
        """
        return self.rebar_properties.area_mm2
    
    def bar_diameter(self) -> float:
        """
        Get nominal diameter of the bar
        
        Returns:
        --------
        float
            Nominal diameter (mm)
        """
        return self.rebar_properties.diameter_mm
    
    def bar_mass(self) -> float:
        """
        Get mass per unit length of the bar
        
        Returns:
        --------
        float
            Mass per meter (kg/m)
        """
        return self.rebar_properties.mass_kg_m
    
    def is_deformed(self) -> bool:
        """Check if bar is deformed (ข้ออ้อย)"""
        return self.rebar_properties.surface_type == "deformed"
    
    def is_round(self) -> bool:
        """Check if bar is round (กลม)"""
        return self.rebar_properties.surface_type == "round"
    
    def get_design_properties(self) -> Dict[str, Any]:
        """
        Get comprehensive design properties
        
        Returns:
        --------
        Dict[str, Any]
            All relevant design properties
        """
        base_props = super().get_design_properties()
        
        thai_props = {
            'bar_area_mm2': self.bar_area(),
            'bar_diameter_mm': self.bar_diameter(), 
            'bar_mass_kg_m': self.bar_mass(),
            'surface_type': self.rebar_properties.surface_type,
            'steel_grade': self.steel_grade,
            'yield_strength_ksc': self.fy * 1000 / 98.0665,
            'description_thai': self.rebar_properties.description_thai,
            'description_english': self.rebar_properties.description_english
        }
        
        return {**base_props, **thai_props}
    
    def __str__(self) -> str:
        """String representation"""
        return f"Thai Rebar {self.bar_designation} {self.steel_grade} (fy = {self.fy:.0f} MPa)"
    
    @classmethod
    def get_available_designations(cls) -> List[str]:
        """Get list of available Thai bar designations"""
        return [props.designation for props in cls.THAI_REBAR_DESIGNATIONS.values()]
    
    @classmethod
    def get_designation_info(cls, designation: str) -> Optional[ThaiRebarProperties]:
        """Get detailed information about a specific designation"""
        try:
            designation_enum = cls._parse_designation_static(designation)
            return cls.THAI_REBAR_DESIGNATIONS.get(designation_enum)
        except ValueError:
            return None
    
    @staticmethod
    def _parse_designation_static(designation: str) -> ThaiRebarDesignation:
        """Static version of designation parsing"""
        designation_upper = designation.upper()
        
        for thai_designation in ThaiRebarDesignation:
            if thai_designation.value.upper() == designation_upper:
                return thai_designation
        
        raise ValueError(f"Invalid Thai bar designation: {designation}")


# Convenience functions for common grades and bars
def create_sd40() -> ThaiSteel:
    """Create SD40 steel (392.4 MPa) - Most common grade"""
    return ThaiSteel(grade="SD40")

def create_sd50() -> ThaiSteel:
    """Create SD50 steel (490.5 MPa) - High strength"""
    return ThaiSteel(grade="SD50")

def create_sr24() -> ThaiSteel:
    """Create SR24 steel (235.4 MPa) - Round bars"""
    return ThaiSteel(grade="SR24")

def create_db20_sd40() -> ThaiReinforcementSteel:
    """Create DB20 with SD40 steel - Very common combination"""
    return ThaiReinforcementSteel("DB20", "SD40")

def create_db25_sd40() -> ThaiReinforcementSteel:
    """Create DB25 with SD40 steel - Common for columns"""
    return ThaiReinforcementSteel("DB25", "SD40")

def create_rb6_sr24() -> ThaiReinforcementSteel:
    """Create RB6 with SR24 steel - Common for stirrups"""
    return ThaiReinforcementSteel("RB6", "SR24")


# Unit conversion utilities for Thai steel
def mpa_to_ksc_steel(mpa: float) -> float:
    """Convert steel strength from MPa to ksc; 1 ksc = 1 kgf/cm2 = 0.0980665 MPa"""
    return mpa * 1000 / 98.0665

def ksc_to_mpa_steel(ksc: float) -> float:
    """Convert steel strength from ksc to MPa; 1 ksc = 1 kgf/cm2 = 0.0980665 MPa"""
    return ksc * 98.0665 / 1000