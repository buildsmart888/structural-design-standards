"""
Thai Ministry Regulation B.E. 2566 Design Requirements
======================================================

Implementation of design requirements and parameters according to:
- Ministry Regulation B.E. 2566 (2023) for structural design standards
- Thai building code requirements for cover, deflection, and tolerances
- Quality control and construction requirements

ข้อกำหนดการออกแบบตามกฎกระทรวง พ.ศ. 2566
รวมความหนาคอนกรีตปิด การโก่งตัว และข้อกำหนดการก่อสร้าง
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from ...utils.validation import StructuralValidator, validate_positive


class ThaiEnvironmentType(Enum):
    """Thai environment classification"""
    NORMAL = "normal"           # สภาพแวดล้อมปกติ
    AGGRESSIVE = "aggressive"   # สภาพแวดล้อมรุนแรง
    MARINE = "marine"          # สภาพแวดล้อมทางทะเล
    INDUSTRIAL = "industrial"   # สภาพแวดล้อมอุตสาหกรรม


class ThaiElementType(Enum):
    """Thai structural element types"""
    SLAB = "slab"               # แผ่นพื้น
    BEAM = "beam"               # คาน
    COLUMN = "column"           # เสา
    FOUNDATION = "foundation"   # ฐานราก
    WALL = "wall"              # กำแพง
    FOOTING = "footing"        # ฐานรากแผ่


class ThaiSupportType(Enum):
    """Thai support condition types"""
    SIMPLY_SUPPORTED = "simply_supported"  # รองรับแบบง่าย
    CONTINUOUS = "continuous"              # ต่อเนื่อง
    CANTILEVER = "cantilever"             # จำยื่น
    FIXED = "fixed"                       # ยึดแน่น


@dataclass
class ThaiCoverRequirement:
    """Thai concrete cover requirement"""
    element_type: ThaiElementType
    environment: ThaiEnvironmentType
    cover_mm: float
    description_thai: str
    description_english: str
    reference: str


@dataclass
class ThaiDeflectionLimit:
    """Thai deflection limit"""
    support_type: ThaiSupportType
    limit_ratio: int  # L/x format
    load_duration: str  # "immediate" or "long_term"
    description_thai: str
    description_english: str


class ThaiMinistryDesignRequirements:
    """
    Thai Ministry Regulation B.E. 2566 Design Requirements
    
    ข้อกำหนดการออกแบบตามกฎกระทรวง พ.ศ. 2566
    """
    
    def __init__(self):
        """Initialize Thai design requirements"""
        self.validator = StructuralValidator()
        
        # Concrete cover requirements per B.E. 2566
        self.cover_requirements = self._initialize_cover_requirements()
        
        # Deflection limits per B.E. 2566
        self.deflection_limits = self._initialize_deflection_limits()
        
        # Construction tolerances
        self.construction_tolerances = self._initialize_construction_tolerances()
        
        # Quality control requirements
        self.quality_control = self._initialize_quality_control()
    
    def _initialize_cover_requirements(self) -> List[ThaiCoverRequirement]:
        """Initialize concrete cover requirements"""
        requirements = []
        
        # Normal environment (สภาพแวดล้อมปกติ)
        requirements.extend([
            ThaiCoverRequirement(
                ThaiElementType.SLAB, ThaiEnvironmentType.NORMAL, 20.0,
                "แผ่นพื้นในสภาพแวดล้อมปกติ", "Slab in normal environment",
                "Ministry Regulation B.E. 2566 Table 4.1"
            ),
            ThaiCoverRequirement(
                ThaiElementType.BEAM, ThaiEnvironmentType.NORMAL, 25.0,
                "คานในสภาพแวดล้อมปกติ", "Beam in normal environment",
                "Ministry Regulation B.E. 2566 Table 4.1"
            ),
            ThaiCoverRequirement(
                ThaiElementType.COLUMN, ThaiEnvironmentType.NORMAL, 25.0,
                "เสาในสภาพแวดล้อมปกติ", "Column in normal environment",
                "Ministry Regulation B.E. 2566 Table 4.1"
            ),
            ThaiCoverRequirement(
                ThaiElementType.FOUNDATION, ThaiEnvironmentType.NORMAL, 75.0,
                "ฐานรากในสภาพแวดล้อมปกติ", "Foundation in normal environment",
                "Ministry Regulation B.E. 2566 Table 4.1"
            ),
            ThaiCoverRequirement(
                ThaiElementType.WALL, ThaiEnvironmentType.NORMAL, 20.0,
                "กำแพงในสภาพแวดล้อมปกติ", "Wall in normal environment",
                "Ministry Regulation B.E. 2566 Table 4.1"
            )
        ])
        
        # Aggressive environment (สภาพแวดล้อมรุนแรง)
        requirements.extend([
            ThaiCoverRequirement(
                ThaiElementType.SLAB, ThaiEnvironmentType.AGGRESSIVE, 30.0,
                "แผ่นพื้นในสภาพแวดล้อมรุนแรง", "Slab in aggressive environment",
                "Ministry Regulation B.E. 2566 Table 4.2"
            ),
            ThaiCoverRequirement(
                ThaiElementType.BEAM, ThaiEnvironmentType.AGGRESSIVE, 40.0,
                "คานในสภาพแวดล้อมรุนแรง", "Beam in aggressive environment",
                "Ministry Regulation B.E. 2566 Table 4.2"
            ),
            ThaiCoverRequirement(
                ThaiElementType.COLUMN, ThaiEnvironmentType.AGGRESSIVE, 40.0,
                "เสาในสภาพแวดล้อมรุนแรง", "Column in aggressive environment",
                "Ministry Regulation B.E. 2566 Table 4.2"
            ),
            ThaiCoverRequirement(
                ThaiElementType.FOUNDATION, ThaiEnvironmentType.AGGRESSIVE, 100.0,
                "ฐานรากในสภาพแวดล้อมรุนแรง", "Foundation in aggressive environment",
                "Ministry Regulation B.E. 2566 Table 4.2"
            )
        ])
        
        # Marine environment (สภาพแวดล้อมทางทะเล)
        requirements.extend([
            ThaiCoverRequirement(
                ThaiElementType.SLAB, ThaiEnvironmentType.MARINE, 40.0,
                "แผ่นพื้นในสภาพแวดล้อมทางทะเล", "Slab in marine environment",
                "Ministry Regulation B.E. 2566 Table 4.3"
            ),
            ThaiCoverRequirement(
                ThaiElementType.BEAM, ThaiEnvironmentType.MARINE, 50.0,
                "คานในสภาพแวดล้อมทางทะเล", "Beam in marine environment",
                "Ministry Regulation B.E. 2566 Table 4.3"
            ),
            ThaiCoverRequirement(
                ThaiElementType.COLUMN, ThaiEnvironmentType.MARINE, 50.0,
                "เสาในสภาพแวดล้อมทางทะเล", "Column in marine environment",
                "Ministry Regulation B.E. 2566 Table 4.3"
            ),
            ThaiCoverRequirement(
                ThaiElementType.FOUNDATION, ThaiEnvironmentType.MARINE, 125.0,
                "ฐานรากในสภาพแวดล้อมทางทะเล", "Foundation in marine environment",
                "Ministry Regulation B.E. 2566 Table 4.3"
            )
        ])
        
        return requirements
    
    def _initialize_deflection_limits(self) -> List[ThaiDeflectionLimit]:
        """Initialize deflection limits"""
        limits = []
        
        # Immediate deflection limits
        limits.extend([
            ThaiDeflectionLimit(
                ThaiSupportType.SIMPLY_SUPPORTED, 300, "immediate",
                "รองรับแบบง่าย - การโก่งตัวทันที", "Simply supported - immediate deflection"
            ),
            ThaiDeflectionLimit(
                ThaiSupportType.CONTINUOUS, 350, "immediate",
                "ต่อเนื่อง - การโก่งตัวทันที", "Continuous - immediate deflection"
            ),
            ThaiDeflectionLimit(
                ThaiSupportType.CANTILEVER, 250, "immediate",
                "จำยื่น - การโก่งตัวทันที", "Cantilever - immediate deflection"
            )
        ])
        
        # Long-term deflection limits
        limits.extend([
            ThaiDeflectionLimit(
                ThaiSupportType.SIMPLY_SUPPORTED, 200, "long_term",
                "รองรับแบบง่าย - การโก่งตัวระยะยาว", "Simply supported - long-term deflection"
            ),
            ThaiDeflectionLimit(
                ThaiSupportType.CONTINUOUS, 250, "long_term",
                "ต่อเนื่อง - การโก่งตัวระยะยาว", "Continuous - long-term deflection"
            ),
            ThaiDeflectionLimit(
                ThaiSupportType.CANTILEVER, 125, "long_term",
                "จำยื่น - การโก่งตัวระยะยาว", "Cantilever - long-term deflection"
            )
        ])
        
        return limits
    
    def _initialize_construction_tolerances(self) -> Dict[str, Any]:
        """Initialize construction tolerances"""
        return {
            'dimensional_tolerances': {
                'column_position': {
                    'horizontal': {'value': 12, 'unit': 'mm', 'tolerance': '±'},
                    'vertical': {'value': 6, 'unit': 'mm', 'tolerance': '±'},
                    'description_thai': 'ตำแหน่งเสา',
                    'description_english': 'Column position'
                },
                'beam_position': {
                    'horizontal': {'value': 10, 'unit': 'mm', 'tolerance': '±'},
                    'vertical': {'value': 6, 'unit': 'mm', 'tolerance': '±'},
                    'description_thai': 'ตำแหน่งคาน',
                    'description_english': 'Beam position'
                },
                'slab_thickness': {
                    'value': 10, 'unit': 'mm', 'tolerance': '±',
                    'percentage': 5, 'unit_percent': '%',
                    'description_thai': 'ความหนาแผ่นพื้น',
                    'description_english': 'Slab thickness'
                },
                'concrete_cover': {
                    'positive': {'value': 10, 'unit': 'mm'},
                    'negative': {'value': 5, 'unit': 'mm'},
                    'description_thai': 'ความหนาคอนกรีตปิด',
                    'description_english': 'Concrete cover'
                }
            },
            'reinforcement_tolerances': {
                'bar_spacing': {
                    'value': 10, 'unit': 'mm', 'tolerance': '±',
                    'percentage': 5, 'unit_percent': '%',
                    'description_thai': 'ระยะห่างเหล็กเสริม',
                    'description_english': 'Reinforcement spacing'
                },
                'bar_cutting': {
                    'value': 25, 'unit': 'mm', 'tolerance': '±',
                    'description_thai': 'การตัดเหล็กเสริม',
                    'description_english': 'Bar cutting'
                },
                'lap_length': {
                    'value': 50, 'unit': 'mm', 'tolerance': '±',
                    'description_thai': 'ความยาวการต่อซ้อน',
                    'description_english': 'Lap length'
                }
            }
        }
    
    def _initialize_quality_control(self) -> Dict[str, Any]:
        """Initialize quality control requirements"""
        return {
            'concrete_testing': {
                'cylinder_strength': {
                    'frequency': '1 ชุด ต่อ 100 ลบ.ม. หรือวันละ 1 ชุด',
                    'frequency_english': '1 set per 100 m³ or 1 set per day',
                    'specimens': 3,
                    'test_ages': [7, 28],
                    'acceptance_criteria': 'fc,avg ≥ fc + 1.64σ',
                    'reference': 'มยผ. 1101-61'
                },
                'slump_test': {
                    'frequency': 'ทุกรถ หรือ ทุก 100 ลบ.ม.',
                    'frequency_english': 'Every truck or every 100 m³',
                    'tolerance': '±25 mm จากที่กำหนด',
                    'tolerance_english': '±25 mm from specified',
                    'reference': 'มยผ. 1101-61'
                },
                'air_content': {
                    'normal_concrete': {'max': 6.0, 'unit': '%'},
                    'air_entrained': {'range': (4.0, 8.0), 'unit': '%'},
                    'reference': 'มยผ. 1101-61'
                }
            },
            'steel_testing': {
                'tensile_test': {
                    'frequency': '1 ชุด ต่อ 40 ตัน',
                    'frequency_english': '1 set per 40 tonnes',
                    'specimens': 2,
                    'requirements': ['จุดครากผล', 'กำลังรับแรงดึง', 'การยืดตัว'],
                    'requirements_english': ['yield strength', 'tensile strength', 'elongation'],
                    'reference': 'มยผ. 1103-61'
                },
                'bend_test': {
                    'frequency': '1 ชุด ต่อ 40 ตัน',
                    'frequency_english': '1 set per 40 tonnes',
                    'angle': '180°',
                    'mandrel_diameter': '4d สำหรับ SD40, 5d สำหรับ SD50',
                    'mandrel_diameter_english': '4d for SD40, 5d for SD50',
                    'reference': 'มยผ. 1103-61'
                }
            }
        }
    
    def get_concrete_cover(self, 
                          element_type: ThaiElementType, 
                          environment: ThaiEnvironmentType) -> Optional[ThaiCoverRequirement]:
        """
        Get required concrete cover per Ministry Regulation B.E. 2566
        
        Parameters:
        -----------
        element_type : ThaiElementType
            Type of structural element
        environment : ThaiEnvironmentType
            Environmental condition
            
        Returns:
        --------
        Optional[ThaiCoverRequirement]
            Cover requirement if found
        """
        for req in self.cover_requirements:
            if req.element_type == element_type and req.environment == environment:
                return req
        return None
    
    def get_deflection_limit(self, 
                           support_type: ThaiSupportType, 
                           load_duration: str = "immediate") -> Optional[ThaiDeflectionLimit]:
        """
        Get deflection limit per Ministry Regulation B.E. 2566
        
        Parameters:
        -----------
        support_type : ThaiSupportType
            Support condition
        load_duration : str
            "immediate" or "long_term"
            
        Returns:
        --------
        Optional[ThaiDeflectionLimit]
            Deflection limit if found
        """
        for limit in self.deflection_limits:
            if limit.support_type == support_type and limit.load_duration == load_duration:
                return limit
        return None
    
    def check_deflection_compliance(
            self, actual_deflection: float, span_length: float,
            support_type: ThaiSupportType,
            load_duration: str = "immediate") -> Dict[str, Any]:
        """The previous generic L/300 etc ignored occupancy and damage type.

        No code-compliance result can be given without the legally applicable
        SLS check, brittle finishes, live-load portion, creep, and real member.
        """
        raise NotImplementedError(
            "Thai deflection compliance NOT VERIFIED: provisional L/ratios "
            "are not sufficient; verify governing occupancy and actual "
            "serviceability load case, member stiffness and limit states."
        )

    def get_construction_tolerance(self, component: str, parameter: str) -> Optional[Dict[str, Any]]:
        """
        Get construction tolerance for specific component and parameter
        
        Parameters:
        -----------
        component : str
            Component type (e.g., 'dimensional_tolerances', 'reinforcement_tolerances')
        parameter : str
            Parameter name
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            Tolerance specification if found
        """
        if component in self.construction_tolerances:
            return self.construction_tolerances[component].get(parameter)
        return None
    
    def validate_concrete_mix(self, *args, **kwargs) -> Dict[str, Any]:
        """No compliant concrete mix from a few blanket W/C and slump checks."""
        raise NotImplementedError(
            "Thai concrete mix acceptance requires exposure, concrete "
            "production records, sample testing, project specification "
            "and actual governing material standard; no generic PASS."
        )

    def generate_design_summary(self, project_data: Dict[str, Any]) -> str:
        """
        Generate design requirements summary
        
        Parameters:
        -----------
        project_data : Dict[str, Any]
            Project data dictionary
            
        Returns:
        --------
        str
            Formatted design summary
        """
        summary = []
        summary.append("=" * 80)
        summary.append("สรุปข้อกำหนดการออกแบบตามกฎกระทรวง พ.ศ. 2566")
        summary.append("Design Requirements Summary - Ministry Regulation B.E. 2566")
        summary.append("=" * 80)
        
        # Project information
        if 'project_name' in project_data:
            summary.append(f"โครงการ/Project: {project_data['project_name']}")
        
        summary.append("")
        
        # Cover requirements
        summary.append("1. ความหนาคอนกรีตปิด (Concrete Cover Requirements)")
        summary.append("-" * 60)
        
        environments = [ThaiEnvironmentType.NORMAL, ThaiEnvironmentType.AGGRESSIVE, ThaiEnvironmentType.MARINE]
        elements = [ThaiElementType.SLAB, ThaiElementType.BEAM, ThaiElementType.COLUMN, ThaiElementType.FOUNDATION]
        
        for env in environments:
            env_name = {
                ThaiEnvironmentType.NORMAL: "ปกติ/Normal",
                ThaiEnvironmentType.AGGRESSIVE: "รุนแรง/Aggressive", 
                ThaiEnvironmentType.MARINE: "ทางทะเล/Marine"
            }[env]
            
            summary.append(f"\nสภาพแวดล้อม {env_name}:")
            for elem in elements:
                cover_req = self.get_concrete_cover(elem, env)
                if cover_req:
                    elem_name = {
                        ThaiElementType.SLAB: "แผ่นพื้น/Slab",
                        ThaiElementType.BEAM: "คาน/Beam",
                        ThaiElementType.COLUMN: "เสา/Column",
                        ThaiElementType.FOUNDATION: "ฐานราก/Foundation"
                    }[elem]
                    summary.append(f"  {elem_name}: {cover_req.cover_mm:.0f} mm")
        
        # Deflection limits
        summary.append(f"\n2. ขีดจำกัดการโก่งตัว (Deflection Limits)")
        summary.append("-" * 60)
        
        support_types = [ThaiSupportType.SIMPLY_SUPPORTED, ThaiSupportType.CONTINUOUS, ThaiSupportType.CANTILEVER]
        durations = ["immediate", "long_term"]
        
        for duration in durations:
            duration_name = "ทันที/Immediate" if duration == "immediate" else "ระยะยาว/Long-term"
            summary.append(f"\n{duration_name}:")
            
            for support in support_types:
                limit = self.get_deflection_limit(support, duration)
                if limit:
                    support_name = {
                        ThaiSupportType.SIMPLY_SUPPORTED: "รองรับแบบง่าย/Simply Supported",
                        ThaiSupportType.CONTINUOUS: "ต่อเนื่อง/Continuous",
                        ThaiSupportType.CANTILEVER: "จำยื่น/Cantilever"
                    }[support]
                    summary.append(f"  {support_name}: L/{limit.limit_ratio}")
        
        summary.append("")
        summary.append("=" * 80)
        summary.append("หมายเหตุ: ข้อกำหนดตามกฎกระทรวง พ.ศ. 2566")
        summary.append("Note: Requirements per Ministry Regulation B.E. 2566")
        summary.append("=" * 80)
        
        return "\n".join(summary)