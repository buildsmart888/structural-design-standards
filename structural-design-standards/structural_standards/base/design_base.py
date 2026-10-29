"""
Base Design Classes
===================

Abstract base classes for structural member design.
Provides common interface for beam, column, slab, and other member design.

คลาสฐานสำหรับการออกแบบสมาชิกโครงสร้าง
มี interface ร่วมสำหรับการออกแบบคาน เสา พื้น และสมาชิกอื่นๆ
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from structural_standards.base.material_base import ConcreteMaterial, SteelMaterial, ReinforcementSteel

class DesignStatus(Enum):
    """Design status enumeration"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_CHECKED = "not_checked"

class FailureMode(Enum):
    """Failure modes for structural members"""
    FLEXURE = "flexure"
    SHEAR = "shear"
    COMPRESSION = "compression"
    TENSION = "tension"
    TORSION = "torsion"
    BUCKLING = "buckling"
    PUNCHING_SHEAR = "punching_shear"
    DEFLECTION = "deflection"
    CRACK_WIDTH = "crack_width"

@dataclass
class DesignCheck:
    """Individual design check result"""
    name: str
    status: DesignStatus
    value: float
    limit: float
    ratio: float
    units: str
    description: str = ""
    code_reference: str = ""

@dataclass
class DesignResult:
    """
    Complete design result for a structural member
    
    ผลลัพธ์การออกแบบที่สมบูรณ์สำหรับสมาชิกโครงสร้าง
    """
    member_type: str
    design_method: str
    overall_status: DesignStatus
    utilization_ratio: float
    
    # Design checks
    strength_checks: List[DesignCheck] = field(default_factory=list)
    serviceability_checks: List[DesignCheck] = field(default_factory=list)
    detailing_checks: List[DesignCheck] = field(default_factory=list)
    
    # Design outputs
    required_reinforcement: Dict[str, Any] = field(default_factory=dict)
    provided_reinforcement: Dict[str, Any] = field(default_factory=dict)
    design_forces: Dict[str, float] = field(default_factory=dict)
    design_capacities: Dict[str, float] = field(default_factory=dict)
    
    # Additional information
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    def add_strength_check(self, check: DesignCheck) -> None:
        """Add a strength design check"""
        self.strength_checks.append(check)
        
    def add_serviceability_check(self, check: DesignCheck) -> None:
        """Add a serviceability check"""
        self.serviceability_checks.append(check)
        
    def add_detailing_check(self, check: DesignCheck) -> None:
        """Add a detailing check"""
        self.detailing_checks.append(check)
    
    def get_critical_ratio(self) -> float:
        """Get the most critical (highest) utilization ratio"""
        all_ratios = []
        for checks in [self.strength_checks, self.serviceability_checks, self.detailing_checks]:
            all_ratios.extend([check.ratio for check in checks])
        
        return max(all_ratios) if all_ratios else 0.0
    
    def get_governing_check(self) -> Optional[DesignCheck]:
        """Get the governing (most critical) design check"""
        all_checks = self.strength_checks + self.serviceability_checks + self.detailing_checks
        if not all_checks:
            return None
        
        return max(all_checks, key=lambda x: x.ratio)
    
    def is_adequate(self) -> bool:
        """Fail closed: an empty or incomplete list of checks is NOT adequate.

        WARNING and NOT_CHECKED are not PASS. Subsystems must explicitly set
        their overall_status to NOT_CHECKED when required checks are absent;
        passing one isolated check does not certify the complete member.
        """
        all_checks = self.strength_checks + self.serviceability_checks + self.detailing_checks
        return bool(all_checks) and all(check.status is DesignStatus.PASS for check in all_checks)

class StructuralMember(ABC):
    """
    Abstract base class for structural members
    
    คลาสฐานนามธรรมสำหรับสมาชิกโครงสร้าง
    """
    
    def __init__(self, 
                 member_id: str,
                 member_type: str):
        """
        Initialize structural member
        
        Parameters:
        -----------
        member_id : str
            Unique identifier for the member
        member_type : str
            Type of member (beam, column, slab, etc.)
        """
        self.member_id = member_id
        self.member_type = member_type
    
    @abstractmethod
    def get_geometry_properties(self) -> Dict[str, float]:
        """Get geometric properties of the member"""
        pass
    
    @abstractmethod
    def validate_geometry(self) -> bool:
        """Validate member geometry"""
        pass

class MemberDesign(ABC):
    """
    Abstract base class for member design
    
    คลาสฐานนามธรรมสำหรับการออกแบบสมาชิก
    """
    
    def __init__(self, 
                 concrete: ConcreteMaterial,
                 steel: ReinforcementSteel,
                 design_standard: str):
        """
        Initialize member design
        
        Parameters:
        -----------
        concrete : ConcreteMaterial
            Concrete material
        steel : ReinforcementSteel
            Reinforcement steel material
        design_standard : str
            Design standard reference
        """
        self.concrete = concrete
        self.steel = steel
        self.design_standard = design_standard
        
    @abstractmethod
    def design(self, *args, **kwargs) -> DesignResult:
        """Perform complete member design"""
        pass
    
    @abstractmethod
    def check_strength(self, *args, **kwargs) -> List[DesignCheck]:
        """Check strength requirements"""
        pass
    
    @abstractmethod
    def check_serviceability(self, *args, **kwargs) -> List[DesignCheck]:
        """Check serviceability requirements"""
        pass
    
    def create_design_check(self,
                          name: str,
                          actual_value: float,
                          limit_value: float,
                          units: str,
                          description: str = "",
                          code_reference: str = "",
                          is_lower_bound: bool = False) -> DesignCheck:
        """
        Create a design check
        
        Parameters:
        -----------
        name : str
            Check name
        actual_value : float
            Actual calculated value
        limit_value : float
            Limit value per code
        units : str
            Units
        description : str
            Description of the check
        code_reference : str
            Code section reference
        is_lower_bound : bool
            True if actual_value should be >= limit_value
            
        Returns:
        --------
        DesignCheck
            Design check result
        """
        if (not math.isfinite(actual_value) or not math.isfinite(limit_value)
                or actual_value < 0 or limit_value <= 0):
            return DesignCheck(
                name=name, status=DesignStatus.NOT_CHECKED,
                value=actual_value, limit=limit_value, ratio=float('inf'),
                units=units, description="Invalid, absent or nonpositive check input: "
                + description, code_reference=code_reference,
            )

        if is_lower_bound:
            # Required / provided, the SAME utilization convention as upper bounds.
            ratio = limit_value / actual_value if actual_value > 0 else float('inf')
            status = (DesignStatus.PASS if actual_value >= limit_value
                      else DesignStatus.FAIL)
        else:
            ratio = actual_value / limit_value
            status = (DesignStatus.PASS if actual_value <= limit_value
                      else DesignStatus.FAIL)
        
        return DesignCheck(
            name=name,
            status=status,
            value=actual_value,
            limit=limit_value,
            ratio=ratio,
            units=units,
            description=description,
            code_reference=code_reference
        )

class BeamDesign(MemberDesign):
    """
    Base class for beam design
    
    คลาสฐานสำหรับการออกแบบคาน
    """
    
    def __init__(self, 
                 concrete: ConcreteMaterial,
                 steel: ReinforcementSteel,
                 design_standard: str):
        super().__init__(concrete, steel, design_standard)
        
    @abstractmethod
    def design_flexural_reinforcement(self,
                                    moment_ultimate: float,
                                    beam_width: float,
                                    beam_depth: float,
                                    **kwargs) -> Dict[str, Any]:
        """Design flexural reinforcement"""
        pass
    
    @abstractmethod
    def design_shear_reinforcement(self,
                                 shear_ultimate: float,
                                 beam_width: float,
                                 beam_depth: float,
                                 **kwargs) -> Dict[str, Any]:
        """Design shear reinforcement"""
        pass
    
    @abstractmethod
    def check_deflection(self,
                        service_moment: float,
                        span_length: float,
                        **kwargs) -> DesignCheck:
        """Check deflection limits"""
        pass

class ColumnDesign(MemberDesign):
    """
    Base class for column design
    
    คลาสฐานสำหรับการออกแบบเสา
    """
    
    def __init__(self, 
                 concrete: ConcreteMaterial,
                 steel: ReinforcementSteel,
                 design_standard: str):
        super().__init__(concrete, steel, design_standard)
        
    @abstractmethod
    def design_reinforcement(self,
                           axial_force: float,
                           moment_x: float,
                           moment_y: float,
                           column_width: float,
                           column_depth: float,
                           **kwargs) -> Dict[str, Any]:
        """Design column reinforcement"""
        pass
    
    @abstractmethod
    def check_slenderness(self,
                         unbraced_length: float,
                         column_width: float,
                         column_depth: float,
                         **kwargs) -> DesignCheck:
        """Check slenderness limits"""
        pass
    
    @abstractmethod
    def interaction_diagram(self,
                          column_width: float,
                          column_depth: float,
                          **kwargs) -> Dict[str, List[float]]:
        """Generate P-M interaction diagram"""
        pass

class SlabDesign(MemberDesign):
    """
    Base class for slab design
    
    คลาสฐานสำหรับการออกแบบพื้น
    """
    
    def __init__(self, 
                 concrete: ConcreteMaterial,
                 steel: ReinforcementSteel,
                 design_standard: str):
        super().__init__(concrete, steel, design_standard)
        
    @abstractmethod
    def design_one_way_slab(self,
                          moment_ultimate: float,
                          slab_thickness: float,
                          slab_width: float,
                          **kwargs) -> Dict[str, Any]:
        """Design one-way slab"""
        pass
    
    @abstractmethod
    def design_two_way_slab(self,
                          moment_x: float,
                          moment_y: float,
                          slab_thickness: float,
                          **kwargs) -> Dict[str, Any]:
        """Design two-way slab"""
        pass
    
    @abstractmethod
    def check_punching_shear(self,
                           punching_force: float,
                           column_width: float,
                           column_depth: float,
                           slab_thickness: float,
                           **kwargs) -> DesignCheck:
        """Check punching shear"""
        pass
    
    @abstractmethod
    def check_minimum_thickness(self,
                              span_length: float,
                              support_conditions: str,
                              **kwargs) -> DesignCheck:
        """Check minimum thickness requirements"""
        pass

class WallDesign(MemberDesign):
    """
    Base class for wall design
    
    คลาสฐานสำหรับการออกแบบกำแพง
    """
    
    def __init__(self, 
                 concrete: ConcreteMaterial,
                 steel: ReinforcementSteel,
                 design_standard: str):
        super().__init__(concrete, steel, design_standard)
        
    @abstractmethod
    def design_bearing_wall(self,
                          axial_force: float,
                          wall_thickness: float,
                          wall_height: float,
                          **kwargs) -> Dict[str, Any]:
        """Design bearing wall"""
        pass
    
    @abstractmethod
    def design_shear_wall(self,
                        shear_force: float,
                        moment: float,
                        wall_thickness: float,
                        wall_length: float,
                        **kwargs) -> Dict[str, Any]:
        """Design shear wall"""
        pass

class FootingDesign(MemberDesign):
    """
    Base class for footing design
    
    คลาสฐานสำหรับการออกแบบฐานราก
    """
    
    def __init__(self, 
                 concrete: ConcreteMaterial,
                 steel: ReinforcementSteel,
                 design_standard: str):
        super().__init__(concrete, steel, design_standard)
        
    @abstractmethod
    def design_isolated_footing(self,
                              axial_force: float,
                              moment_x: float,
                              moment_y: float,
                              soil_bearing_capacity: float,
                              **kwargs) -> Dict[str, Any]:
        """Design isolated footing"""
        pass
    
    @abstractmethod
    def check_bearing_pressure(self,
                             applied_pressure: float,
                             allowable_pressure: float,
                             **kwargs) -> DesignCheck:
        """Check bearing pressure"""
        pass