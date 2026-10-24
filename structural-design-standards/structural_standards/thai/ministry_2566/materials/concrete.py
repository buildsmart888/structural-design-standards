"""
Thai Concrete Materials - Ministry Regulation B.E. 2566
=======================================================

Implementation of Thai concrete materials according to:
- Ministry Regulation B.E. 2566 (2023) for structural design standards
- มยผ. 1103 for concrete specifications
- มยผ. 1101 for structural concrete design

การใช้งานวัสดุคอนกรีตไทยตาม:
- กฎกระทรวง พ.ศ. 2566 สำหรับมาตรฐานการออกแบบโครงสร้าง
- มยผ. 1103 สำหรับข้อกำหนดคอนกรีต
- มยผ. 1101 สำหรับการออกแบบคอนกรีตเสริมเหล็ก
"""

import math
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from ....base.material_base import ConcreteMaterial, ConcreteType
from ....utils.validation import validate_positive, validate_range


class ThaiConcreteGrade(Enum):
    """Thai concrete grade designations"""
    FC180 = "Fc180"  # 18.0 MPa (180 ksc)
    FC210 = "Fc210"  # 21.0 MPa (210 ksc) 
    FC240 = "Fc240"  # 24.0 MPa (240 ksc)
    FC280 = "Fc280"  # 28.0 MPa (280 ksc)
    FC350 = "Fc350"  # 35.0 MPa (350 ksc)


@dataclass
class ThaiConcreteProperties:
    """Properties of Thai concrete grades"""
    grade: str
    fc_mpa: float          # Compressive strength (MPa)
    fc_ksc: float          # Compressive strength (ksc)
    min_cement_content: float  # kg/m³
    max_water_cement_ratio: float
    min_slump: float       # cm
    max_slump: float       # cm
    description_thai: str
    description_english: str


class ThaiConcrete(ConcreteMaterial):
    """
    Thai concrete material implementation
    
    วัสดุคอนกรีตไทยตามมาตรฐาน มยผ.
    """
    
    # Standard Thai concrete grades
    THAI_CONCRETE_GRADES = {
        ThaiConcreteGrade.FC180: ThaiConcreteProperties(
            grade="Fc180",
            fc_mpa=18.0,
            fc_ksc=180.0,
            min_cement_content=280,
            max_water_cement_ratio=0.65,
            min_slump=5.0,
            max_slump=15.0,
            description_thai="คอนกรีตเกรด 180 กิโลกรัมต่อตารางเซนติเมตร",
            description_english="Concrete Grade 180 ksc"
        ),
        
        ThaiConcreteGrade.FC210: ThaiConcreteProperties(
            grade="Fc210", 
            fc_mpa=21.0,
            fc_ksc=210.0,
            min_cement_content=300,
            max_water_cement_ratio=0.60,
            min_slump=5.0,
            max_slump=15.0,
            description_thai="คอนกรีตเกรด 210 กิโลกรัมต่อตารางเซนติเมตร",
            description_english="Concrete Grade 210 ksc"
        ),
        
        ThaiConcreteGrade.FC240: ThaiConcreteProperties(
            grade="Fc240",
            fc_mpa=24.0,
            fc_ksc=240.0,
            min_cement_content=320,
            max_water_cement_ratio=0.55,
            min_slump=5.0,
            max_slump=12.0,
            description_thai="คอนกรีตเกรด 240 กิโลกรัมต่อตารางเซนติเมตร",
            description_english="Concrete Grade 240 ksc"
        ),
        
        ThaiConcreteGrade.FC280: ThaiConcreteProperties(
            grade="Fc280",
            fc_mpa=28.0,
            fc_ksc=280.0,
            min_cement_content=350,
            max_water_cement_ratio=0.50,
            min_slump=5.0,
            max_slump=12.0,
            description_thai="คอนกรีตเกรด 280 กิโลกรัมต่อตารางเซนติเมตร",
            description_english="Concrete Grade 280 ksc"
        ),
        
        ThaiConcreteGrade.FC350: ThaiConcreteProperties(
            grade="Fc350",
            fc_mpa=35.0,
            fc_ksc=350.0,
            min_cement_content=400,
            max_water_cement_ratio=0.45,
            min_slump=5.0,
            max_slump=10.0,
            description_thai="คอนกรีตเกรด 350 กิโลกรัมต่อตารางเซนติเมตร",
            description_english="Concrete Grade 350 ksc"
        )
    }
    
    def __init__(self,
                 grade: Optional[str] = None,
                 fc_prime: Optional[float] = None,
                 unit_weight: float = 24.0,
                 concrete_type: ConcreteType = ConcreteType.NORMAL_WEIGHT,
                 aggregate_size: float = 25.0):
        """
        Initialize Thai concrete
        
        Parameters:
        -----------
        grade : str, optional
            Thai concrete grade (e.g., 'Fc210', 'Fc280')
        fc_prime : float, optional
            Compressive strength in MPa
        unit_weight : float
            Unit weight (kN/m³), default 24.0
        concrete_type : ConcreteType
            Type of concrete
        aggregate_size : float
            Maximum aggregate size (mm)
        """
        # Determine strength from grade or direct input
        if grade is not None:
            grade_enum = self._parse_grade(grade)
            if grade_enum not in self.THAI_CONCRETE_GRADES:
                raise ValueError(f"Unknown Thai concrete grade: {grade}")
            
            props = self.THAI_CONCRETE_GRADES[grade_enum]
            fc_prime = props.fc_mpa
            
        elif fc_prime is not None:
            validate_positive(fc_prime, "fc_prime")
            grade = self._determine_grade_from_strength(fc_prime)
        else:
            raise ValueError("Either grade or fc_prime must be provided")
        
        # Initialize base class
        super().__init__(
            fc_prime=fc_prime,
            unit_weight=unit_weight,
            concrete_type=concrete_type,
            aggregate_size=aggregate_size,
            standard="Thai Ministry B.E. 2566"
        )
        
        self.grade = grade
        self.grade_properties = self._get_grade_properties()
        
        # Validate Thai requirements
        self._validate_thai_requirements()
    
    def _parse_grade(self, grade: str) -> ThaiConcreteGrade:
        """Parse grade string to enum, case-insensitively.

        Accepts 'Fc210', 'FC210' and 'fc210'. The previous implementation
        re-cased the upper-cased string back to 'Fc210' and then compared it
        against an upper-cased enum value, so no spelling ever matched and
        every create_fcXXX() factory raised ValueError.
        """
        grade_upper = grade.upper()
        
        for thai_grade in ThaiConcreteGrade:
            if thai_grade.value.upper() == grade_upper:
                return thai_grade
        
        raise ValueError(f"Invalid Thai concrete grade: {grade}")
    
    def _determine_grade_from_strength(self, fc: float) -> str:
        """Determine Thai grade from strength"""
        for grade_enum, props in self.THAI_CONCRETE_GRADES.items():
            if abs(fc - props.fc_mpa) < 0.5:  # Allow small tolerance
                return props.grade
        
        # If no exact match, find closest
        closest_grade = min(
            self.THAI_CONCRETE_GRADES.values(),
            key=lambda p: abs(p.fc_mpa - fc)
        )
        return closest_grade.grade
    
    def _get_grade_properties(self) -> Optional[ThaiConcreteProperties]:
        """Get properties for current grade"""
        for grade_enum, props in self.THAI_CONCRETE_GRADES.items():
            if props.grade == self.grade:
                return props
        return None
    
    def _validate_thai_requirements(self) -> None:
        """Validate according to Thai standards"""
        if self.fc_prime < 15.0:
            raise ValueError("Thai standard: Minimum fc' is 15.0 MPa")
        
        if self.fc_prime > 50.0:
            raise ValueError("Thai standard: fc' > 50.0 MPa requires special approval")
        
        # Unit weight validation
        if self.concrete_type == ConcreteType.NORMAL_WEIGHT:
            if not (22.0 <= self.unit_weight <= 26.0):
                raise ValueError("Thai standard: Normal concrete unit weight should be 22-26 kN/m³")
    
    def elastic_modulus(self) -> float:
        """
        Calculate elastic modulus per Thai standards
        
        Thai formula: Ec = 4700√fc (MPa) for normal weight concrete
        Based on modified ACI approach used in Thai codes
        
        Returns:
        --------
        float
            Elastic modulus (MPa)
        """
        if self.concrete_type == ConcreteType.NORMAL_WEIGHT:
            return 4700 * math.sqrt(self.fc_prime)
        else:
            # For lightweight concrete
            wc = self.unit_weight * 1000 / 9.81  # Convert to kg/m³
            return (wc**1.5) * 0.043 * math.sqrt(self.fc_prime)
    
    def modulus_of_rupture(self) -> float:
        """
        Calculate modulus of rupture per Thai standards
        
        Thai formula: fr = 0.62√fc (MPa) for normal weight concrete
        
        Returns:
        --------
        float
            Modulus of rupture (MPa)
        """
        if self.concrete_type == ConcreteType.NORMAL_WEIGHT:
            return 0.62 * math.sqrt(self.fc_prime)
        else:
            return 0.5 * math.sqrt(self.fc_prime)
    
    def beta1_factor(self) -> float:
        """
        Calculate β₁ factor for Thai concrete design
        
        Thai standards follow modified ACI approach:
        - β₁ = 0.85 for fc' ≤ 28 MPa
        - β₁ = 0.85 - 0.05(fc' - 28)/7 for 28 < fc' ≤ 55 MPa
        - β₁ = 0.65 for fc' > 55 MPa
        
        Returns:
        --------
        float
            β₁ factor
        """
        if self.fc_prime <= 28.0:
            return 0.85
        elif self.fc_prime <= 55.0:
            return 0.85 - 0.05 * (self.fc_prime - 28.0) / 7.0
        else:
            return 0.65
    
    def strength_in_ksc(self) -> float:
        """
        Get compressive strength in ksc (Thai traditional unit)
        
        Returns:
        --------
        float
            Compressive strength (ksc)
        """
        return self.fc_prime * 1000 / 98.0665  # MPa -> ksc; 1 ksc = 1 kgf/cm2 = 0.0980665 MPa
    
    def get_mix_requirements(self) -> Dict[str, Any]:
        """
        Get concrete mix requirements per Thai standards
        
        Returns:
        --------
        Dict[str, Any]
            Mix design requirements
        """
        if not self.grade_properties:
            return {}
        
        props = self.grade_properties
        return {
            'min_cement_content_kg_m3': props.min_cement_content,
            'max_water_cement_ratio': props.max_water_cement_ratio,
            'slump_range_cm': (props.min_slump, props.max_slump),
            'min_curing_days': 28,
            'required_compressive_strength_28_days_mpa': props.fc_mpa,
            'required_compressive_strength_28_days_ksc': props.fc_ksc
        }
    
    def get_design_properties(self) -> Dict[str, float]:
        """
        Get comprehensive design properties for Thai concrete
        
        Returns:
        --------
        Dict[str, float]
            All relevant design properties
        """
        base_props = super().get_design_properties()
        
        thai_props = {
            'elastic_modulus_thai': self.elastic_modulus(),
            'modulus_of_rupture_thai': self.modulus_of_rupture(),
            'beta1_factor': self.beta1_factor(),
            'strength_ksc': self.strength_in_ksc(),
            'density_kg_m3': self.unit_weight * 1000 / 9.81,
        }
        
        if self.grade_properties:
            thai_props.update({
                'min_cement_content': self.grade_properties.min_cement_content,
                'max_wc_ratio': self.grade_properties.max_water_cement_ratio
            })
        
        return {**base_props, **thai_props}
    
    def get_strength_reduction_factors(self) -> Dict[str, float]:
        """
        Get strength reduction factors per Thai standards
        
        Based on Thai adoption of modified ACI factors
        
        Returns:
        --------
        Dict[str, float]
            φ factors for different failure modes
        """
        return {
            'flexure_tension_controlled': 0.90,      # งานโค้งควบคุมด้วยแรงดึง
            'flexure_compression_controlled': 0.65,   # งานโค้งควบคุมด้วยแรงอัด
            'shear_and_torsion': 0.75,               # แรงเฉือนและแรงบิด
            'axial_compression_tied': 0.65,          # แรงอัดตามแนวแกนด้วยเหล็กปลอก
            'axial_compression_spiral': 0.70,        # แรงอัดตามแนวแกนด้วยเหล็กเกลียว
            'bearing_on_concrete': 0.65,             # แรงรองรับบนคอนกรีต
        }
    
    def __str__(self) -> str:
        """String representation"""
        if self.grade_properties:
            return f"Thai Concrete {self.grade} (fc = {self.fc_prime:.1f} MPa = {self.strength_in_ksc():.0f} ksc)"
        else:
            return f"Thai Concrete fc = {self.fc_prime:.1f} MPa"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"ThaiConcrete(grade='{self.grade}', fc_prime={self.fc_prime}, "
                f"unit_weight={self.unit_weight})")
    
    @classmethod
    def get_available_grades(cls) -> List[str]:
        """Get list of available Thai concrete grades"""
        return [props.grade for props in cls.THAI_CONCRETE_GRADES.values()]
    
    @classmethod
    def get_grade_info(cls, grade: str) -> Optional[ThaiConcreteProperties]:
        """Get detailed information about a specific grade"""
        try:
            grade_enum = cls._parse_grade_static(grade)
            return cls.THAI_CONCRETE_GRADES.get(grade_enum)
        except ValueError:
            return None
    
    @staticmethod
    def _parse_grade_static(grade: str) -> ThaiConcreteGrade:
        """Static version of grade parsing"""
        grade_upper = grade.upper()
        if grade_upper.startswith('FC'):
            grade_upper = grade_upper.replace('FC', 'Fc')
        
        for thai_grade in ThaiConcreteGrade:
            if thai_grade.value.upper() == grade_upper:
                return thai_grade
        
        raise ValueError(f"Invalid Thai concrete grade: {grade}")
    
    @classmethod
    def create_standard_concrete(cls, grade: str) -> 'ThaiConcrete':
        """
        Create standard Thai concrete with typical properties
        
        Parameters:
        -----------
        grade : str
            Thai concrete grade (e.g., 'Fc210', 'Fc280')
            
        Returns:
        --------
        ThaiConcrete
            Thai concrete instance
        """
        return cls(grade=grade)


# Convenience functions for common grades
def create_fc180() -> ThaiConcrete:
    """Create Fc180 concrete (18.0 MPa)"""
    return ThaiConcrete(grade="Fc180")

def create_fc210() -> ThaiConcrete:
    """Create Fc210 concrete (21.0 MPa) - Most common grade"""
    return ThaiConcrete(grade="Fc210")

def create_fc240() -> ThaiConcrete:
    """Create Fc240 concrete (24.0 MPa)"""
    return ThaiConcrete(grade="Fc240")

def create_fc280() -> ThaiConcrete:
    """Create Fc280 concrete (28.0 MPa) - High strength"""
    return ThaiConcrete(grade="Fc280")

def create_fc350() -> ThaiConcrete:
    """Create Fc350 concrete (35.0 MPa) - Premium grade"""
    return ThaiConcrete(grade="Fc350")


# Unit conversion utilities
def mpa_to_ksc(mpa: float) -> float:
    """Convert MPa to ksc (Thai traditional unit); 1 ksc = 1 kgf/cm2 = 0.0980665 MPa"""
    return mpa * 1000 / 98.0665

def ksc_to_mpa(ksc: float) -> float:
    """Convert ksc to MPa; 1 ksc = 1 kgf/cm2 = 0.0980665 MPa"""
    return ksc * 98.0665 / 1000