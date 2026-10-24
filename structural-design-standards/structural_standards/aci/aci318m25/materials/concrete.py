"""
ACI 318M-25 Concrete Material Model
===================================

Implementation of concrete material properties per ACI 318M-25
Building Code Requirements for Structural Concrete (International System of Units).

Based on:
- ACI 318M-25 Chapter 19: Concrete
- ACI 318M-25 Chapter 20: Reinforcement
- ACI 318M-25 Chapter 21: Strength Reduction Factors

การใช้งานคุณสมบัติวัสดุคอนกรีตตาม ACI 318M-25
"""

import math
from typing import Dict, Optional, Tuple
from structural_standards.base.material_base import ConcreteMaterial, ConcreteType
from structural_standards.utils.validation import validate_positive, validate_range

class ACI318M25Concrete(ConcreteMaterial):
    """
    ACI 318M-25 Concrete Material Implementation
    
    Implements concrete properties and behavior according to ACI 318M-25
    including compressive strength, elastic modulus, and various design
    parameters required for structural concrete design.
    
    การใช้งานวัสดุคอนกรีตตาม ACI 318M-25
    """
    
    # Standard concrete strength classes - ACI 318M-25
    STANDARD_STRENGTHS = {
        'FC14': 14.0,    # 14 MPa
        'FC17': 17.0,    # 17 MPa  
        'FC21': 21.0,    # 21 MPa
        'FC28': 28.0,    # 28 MPa (most common)
        'FC35': 35.0,    # 35 MPa
        'FC42': 42.0,    # 42 MPa
        'FC50': 50.0,    # 50 MPa
        'FC70': 70.0,    # 70 MPa (high strength)
        'FC100': 100.0   # 100 MPa (ultra high strength)
    }
    
    def __init__(self, 
                 fc_prime: Optional[float] = None,
                 strength_class: Optional[str] = None,
                 unit_weight: float = 24.0,
                 concrete_type: ConcreteType = ConcreteType.NORMAL_WEIGHT,
                 aggregate_size: float = 25.0):
        """
        Initialize ACI 318M-25 concrete material
        
        Parameters:
        -----------
        fc_prime : float, optional
            Specified compressive strength (MPa)
        strength_class : str, optional
            Standard strength class (e.g., 'FC28')
        unit_weight : float
            Unit weight of concrete (kN/m³), default 24.0
        concrete_type : ConcreteType
            Type of concrete (normal, lightweight, etc.)
        aggregate_size : float
            Maximum aggregate size (mm), default 25.0
            
        Note:
        -----
        Either fc_prime or strength_class must be provided
        """
        # Determine fc_prime from inputs
        if strength_class is not None:
            if strength_class not in self.STANDARD_STRENGTHS:
                raise ValueError(f"Unknown strength class: {strength_class}")
            fc_prime = self.STANDARD_STRENGTHS[strength_class]
            grade = strength_class
        elif fc_prime is not None:
            validate_positive(fc_prime, "fc_prime")
            grade = f"FC{int(fc_prime)}"
        else:
            raise ValueError("Either fc_prime or strength_class must be provided")
        
        # Initialize base class
        super().__init__(
            fc_prime=fc_prime,
            unit_weight=unit_weight,
            concrete_type=concrete_type,
            aggregate_size=aggregate_size,
            standard="ACI 318M-25"
        )
        
        self.strength_class = strength_class if strength_class else grade
        
        # ACI 318M-25 specific properties
        self._validate_aci_requirements()
    
    def _validate_aci_requirements(self) -> None:
        """Validate inputs according to ACI 318M-25 requirements"""
        # ACI 318M-25 Section 19.2.1.1 - minimum strength
        if self.fc_prime < 17.0:
            raise ValueError("ACI 318M-25: Minimum fc' is 17 MPa (Section 19.2.1.1)")
        
        # Practical upper limit
        if self.fc_prime > 100.0:
            raise ValueError("fc' > 100 MPa requires special provisions")
        
        # Unit weight validation for concrete type
        if self.concrete_type == ConcreteType.NORMAL_WEIGHT:
            if not (22.0 <= self.unit_weight <= 26.0):
                raise ValueError("Normal weight concrete: unit weight should be 22-26 kN/m³")
        elif self.concrete_type == ConcreteType.LIGHTWEIGHT:
            if not (14.0 <= self.unit_weight <= 22.0):
                raise ValueError("Lightweight concrete: unit weight should be 14-22 kN/m³")
    
    def elastic_modulus(self) -> float:
        """
        Calculate modulus of elasticity per ACI 318M-25
        
        ACI 318M-25 Eq. 19.2.2.1b: Ec = 4700√f'c (MPa)
        For normal weight concrete
        
        Returns:
        --------
        float
            Elastic modulus (MPa)
        """
        if self.concrete_type == ConcreteType.NORMAL_WEIGHT:
            # ACI 318M-25 Eq. 19.2.2.1b
            return 4700 * math.sqrt(self.fc_prime)
        else:
            # ACI 318M-25 Eq. 19.2.2.1c for lightweight concrete
            wc = self.unit_weight * 1000 / 9.81  # Convert to kg/m³
            return (wc**1.5) * 0.043 * math.sqrt(self.fc_prime)
    
    def modulus_of_rupture(self) -> float:
        """
        Calculate modulus of rupture per ACI 318M-25
        
        ACI 318M-25 Eq. 19.2.3.1: fr = 0.62√f'c (MPa)
        For normal weight concrete
        
        Returns:
        --------
        float
            Modulus of rupture (MPa)
        """
        if self.concrete_type == ConcreteType.NORMAL_WEIGHT:
            # ACI 318M-25 Eq. 19.2.3.1
            return 0.62 * math.sqrt(self.fc_prime)
        else:
            # ACI 318M-25 Eq. 19.2.3.2 for lightweight concrete
            return 0.5 * math.sqrt(self.fc_prime)
    
    def beta1(self) -> float:
        """
        Calculate β₁ factor for equivalent rectangular stress block
        
        ACI 318M-25 Section 22.2.2.4.3:
        - β₁ = 0.85 for f'c ≤ 28 MPa
        - β₁ = 0.85 - 0.05(f'c - 28)/7 for 28 < f'c ≤ 55 MPa  
        - β₁ = 0.65 for f'c > 55 MPa
        
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
    
    def alpha1(self) -> float:
        """
        Calculate α₁ factor for equivalent rectangular stress block
        
        ACI 318M-25 Section 22.2.2.4.1:
        α₁ = 0.85
        
        Returns:
        --------
        float
            α₁ factor
        """
        return 0.85
    
    def shear_strength_factor(self) -> float:
        """
        Get shear strength factor for concrete
        
        ACI 318M-25 Section 22.5.5.1:
        λ = 1.0 for normal weight concrete
        λ = 0.75 for all-lightweight concrete
        λ = interpolated for sand-lightweight concrete
        
        Returns:
        --------
        float
            Shear strength factor λ
        """
        if self.concrete_type == ConcreteType.NORMAL_WEIGHT:
            return 1.0
        elif self.concrete_type == ConcreteType.LIGHTWEIGHT:
            return 0.75
        else:
            # Conservative assumption for other types
            return 0.75
    
    def maximum_aggregate_size_factor(self) -> float:
        """
        Get factor for maximum aggregate size effects
        
        Returns:
        --------
        float
            Aggregate size factor
        """
        # Simplified implementation - can be enhanced based on specific requirements
        if self.aggregate_size >= 20.0:
            return 1.0
        else:
            return 0.95
    
    def tensile_strength(self) -> float:
        """
        Calculate tensile strength of concrete
        
        Approximate relationship: ft ≈ 0.35√f'c (MPa)
        
        Returns:
        --------
        float
            Tensile strength (MPa)
        """
        return 0.35 * math.sqrt(self.fc_prime)
    
    def get_strength_reduction_factors(self) -> Dict[str, float]:
        """
        Get strength reduction factors (φ factors) per ACI 318M-25 Chapter 21
        
        Returns:
        --------
        Dict[str, float]
            Dictionary of φ factors for different failure modes
        """
        return {
            'tension_controlled': 0.90,            # Table 21.2.2
            'compression_controlled_tied': 0.65,   # Table 21.2.2
            'compression_controlled_spiral': 0.75, # Table 21.2.2
            'shear_and_torsion': 0.75,             # Table 21.2.1(b), (c)
            'bearing': 0.65,                       # Table 21.2.1(d)
            'post_tensioned_anchorage': 0.85,      # Table 21.2.1(h)
            # Table 21.2.1(g): struts, ties, nodal zones and bearing areas
            # designed with the strut-and-tie model of Ch. 23 all use 0.75
            'strut_and_tie_struts': 0.75,
            'strut_and_tie_ties': 0.75,
            'strut_and_tie_nodal': 0.75
        }
    
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
            'beta1': self.beta1(),
            'alpha1': self.alpha1(), 
            'lambda_factor': self.shear_strength_factor(),
            'tensile_strength': self.tensile_strength(),
            'aggregate_factor': self.maximum_aggregate_size_factor()
        }
        
        # Merge and return
        return {**base_props, **aci_props}
    
    def validate_grade(self, grade: str) -> bool:
        """
        Validate ACI concrete grade
        
        Parameters:
        -----------
        grade : str
            Concrete grade designation
            
        Returns:
        --------
        bool
            True if valid
        """
        return grade.upper() in self.STANDARD_STRENGTHS
    
    def get_minimum_cover_requirements(self, 
                                     exposure_condition: str = 'normal',
                                     bar_size: float = 20.0) -> Dict[str, float]:
        """
        Get minimum concrete cover requirements per ACI 318M-25
        
        Parameters:
        -----------
        exposure_condition : str
            'normal', 'corrosive', 'severe'
        bar_size : float
            Reinforcement bar diameter (mm)
            
        Returns:
        --------
        Dict[str, float]
            Cover requirements for different members (mm)
        """
        # ACI 318M-25 Table 20.5.1.3.1 - simplified version
        if exposure_condition == 'normal':
            base_covers = {
                'slab': max(20, bar_size),
                'beam': max(40, bar_size),
                'column': max(40, bar_size),
                'footing_cast_against_ground': 75,
                'footing_formed': max(40, bar_size)
            }
        elif exposure_condition == 'corrosive':
            base_covers = {
                'slab': max(40, bar_size),
                'beam': max(50, bar_size), 
                'column': max(50, bar_size),
                'footing_cast_against_ground': 75,
                'footing_formed': max(50, bar_size)
            }
        else:  # severe
            base_covers = {
                'slab': max(65, bar_size),
                'beam': max(65, bar_size),
                'column': max(65, bar_size), 
                'footing_cast_against_ground': 100,
                'footing_formed': max(65, bar_size)
            }
        
        return base_covers
    
    def __str__(self) -> str:
        """String representation"""
        return f"ACI 318M-25 Concrete {self.strength_class} (f'c = {self.fc_prime} MPa)"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"ACI318M25Concrete(fc_prime={self.fc_prime}, "
                f"strength_class='{self.strength_class}', "
                f"unit_weight={self.unit_weight}, "
                f"concrete_type={self.concrete_type})")