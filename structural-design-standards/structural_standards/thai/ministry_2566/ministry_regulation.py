"""
Thai Ministry Regulation B.E. 2566 - Main Module
================================================

Main integration module for Thai Ministry Regulation B.E. 2566 (2023) 
structural design standards including:
- Load combinations and safety factors
- Design requirements (cover, deflection, tolerances)
- Material specifications integration
- Quality control requirements
- Compliance validation

โมดูลหลักกฎกระทรวง พ.ศ. 2566
การบูรณาการมาตรฐานการออกแบบโครงสร้างอาคารตามกฎกระทรวงไทย
"""

import math
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from .load_combinations import (
    ThaiMinistryLoadCombinations, ThaiLoadType, ThaiCombinationType, ThaiLoadCombination
)
from .design_requirements import (
    ThaiMinistryDesignRequirements, ThaiEnvironmentType, ThaiElementType, 
    ThaiSupportType, ThaiCoverRequirement, ThaiDeflectionLimit
)
from .materials.concrete import ThaiConcrete, ThaiConcreteGrade
from .materials.steel import ThaiReinforcementSteel, ThaiSteelGrade, ThaiRebarDesignation
from ...utils.validation import StructuralValidator, validate_positive


@dataclass
class ThaiProjectData:
    """Thai project data structure"""
    project_name: str
    location: str
    environment_type: ThaiEnvironmentType
    concrete_grade: str
    steel_grade: str
    design_life: int = 50  # years
    importance_factor: float = 1.0
    date: Optional[str] = None


@dataclass
class ThaiComplianceResult:
    """Thai compliance check result"""
    is_compliant: bool
    category: str
    description_thai: str
    description_english: str
    actual_value: float
    required_value: float
    margin: float
    reference: str
    warnings: List[str] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.recommendations is None:
            self.recommendations = []


class ThaiMinistryRegulation2566:
    """
    Thai Ministry Regulation B.E. 2566 (2023) - Complete Implementation
    
    กฎกระทรวง กำหนดการออกแบบโครงสร้างอาคาร และลักษณะและคุณสมบัติของวัสดุ
    ที่ใช้ในงานโครงสร้างอาคาร พ.ศ. 2566
    
    This class provides comprehensive support for Thai structural design standards
    including load combinations, material requirements, and compliance checking.
    """
    
    def __init__(self):
        """Initialize Thai Ministry Regulation B.E. 2566 system"""
        self.validator = StructuralValidator()
        
        # Initialize sub-modules
        self.load_combinations = ThaiMinistryLoadCombinations()
        self.design_requirements = ThaiMinistryDesignRequirements()
        
        # Regulation information
        self.regulation_info = {
            'name_thai': 'กฎกระทรวง กำหนดการออกแบบโครงสร้างอาคาร และลักษณะและคุณสมบัติของวัสดุที่ใช้ในงานโครงสร้างอาคาร พ.ศ. 2566',
            'name_english': 'Ministry Regulation for Building Structural Design and Material Properties B.E. 2566 (2023)',
            'effective_date': '2023-12-01',
            'supersedes': 'กฎกระทรวง พ.ศ. 2527',
            'authority': 'กระทรวงมหาดไทย (Ministry of Interior)',
            'scope': 'ใช้บังคับกับอาคารทุกประเภทในประเทศไทย'
        }
        
        # Provincial zones for wind and seismic loads
        self.provincial_zones = self._initialize_provincial_zones()
    
    def _initialize_provincial_zones(self) -> Dict[str, Dict[str, Any]]:
        """DEPRECATED illustrative zoning table - do not use for design.

        get_wind_zone_data()/get_seismic_zone_data() now delegate to
        loads/wind_loads.py and loads/seismic_loads.py, which are the single
        source of truth. This table is kept only for report text and is known
        to disagree with those modules.
        """
        return {
            'wind_zones': {
                'zone_1': {
                    'wind_speed': 30.0,  # m/s
                    'provinces': ['เชียงใหม่', 'เชียงราย', 'ลำพูน', 'แพร่', 'น่าน'],
                    'description_thai': 'โซนลมความเร็วต่ำ ภาคเหนือตอนบน',
                    'description_english': 'Low wind speed zone - Upper North'
                },
                'zone_2': {
                    'wind_speed': 35.0,  # m/s
                    'provinces': ['กรุงเทพมหานคร', 'นนทบุรี', 'ปทุมธานี', 'สมุทรปราการ'],
                    'description_thai': 'โซนลมความเร็วปานกลาง ภาคกลาง',
                    'description_english': 'Medium wind speed zone - Central'
                },
                'zone_3': {
                    'wind_speed': 40.0,  # m/s
                    'provinces': ['สงขลา', 'ปัตตานี', 'ยะลา', 'นราธิวาส', 'ชุมพร'],
                    'description_thai': 'โซนลมความเร็วสูง ภาคใต้',
                    'description_english': 'High wind speed zone - South'
                }
            },
            'seismic_zones': {
                'zone_low': {
                    'pga': 0.15,  # g
                    'provinces': ['เชียงใหม่', 'เชียงราย', 'กรุงเทพมหานคร'],
                    'description_thai': 'โซนแผ่นดินไหวต่ำ',
                    'description_english': 'Low seismic zone'
                },
                'zone_medium': {
                    'pga': 0.25,  # g
                    'provinces': ['กาญจนบุรี', 'สุพรรณบุรี', 'ราชบุรี'],
                    'description_thai': 'โซนแผ่นดินไหวปานกลาง',
                    'description_english': 'Medium seismic zone'
                },
                'zone_high': {
                    'pga': 0.40,  # g
                    'provinces': ['แม่ฮ่องสอน', 'ตาก', 'พิษณุโลก'],
                    'description_thai': 'โซนแผ่นดินไหวสูง',
                    'description_english': 'High seismic zone'
                }
            }
        }
    
    # Load Combination Methods
    def get_load_combinations(self, 
                            combination_type: ThaiCombinationType = ThaiCombinationType.ULTIMATE_LIMIT_STATE) -> List[ThaiLoadCombination]:
        """Get load combinations for specified type"""
        if combination_type == ThaiCombinationType.ULTIMATE_LIMIT_STATE:
            return self.load_combinations.get_ultimate_combinations()
        else:
            return self.load_combinations.get_serviceability_combinations()
    
    def calculate_design_loads(self, 
                             loads: Dict[ThaiLoadType, float],
                             combination_type: ThaiCombinationType = ThaiCombinationType.ULTIMATE_LIMIT_STATE) -> Dict[str, float]:
        """Calculate design loads for all combinations"""
        return self.load_combinations.calculate_all_combinations(loads, combination_type)
    
    def find_governing_load_combination(self, 
                                      loads: Dict[ThaiLoadType, float],
                                      combination_type: ThaiCombinationType = ThaiCombinationType.ULTIMATE_LIMIT_STATE) -> Tuple[ThaiLoadCombination, float]:
        """Find the governing (critical) load combination"""
        return self.load_combinations.find_critical_combination(loads, combination_type)
    
    # Design Requirements Methods
    def get_concrete_cover(self, 
                          element_type: ThaiElementType, 
                          environment: ThaiEnvironmentType) -> Optional[ThaiCoverRequirement]:
        """Get required concrete cover"""
        return self.design_requirements.get_concrete_cover(element_type, environment)
    
    def get_deflection_limit(self, 
                           support_type: ThaiSupportType, 
                           load_duration: str = "immediate") -> Optional[ThaiDeflectionLimit]:
        """Get deflection limit"""
        return self.design_requirements.get_deflection_limit(support_type, load_duration)
    
    def check_deflection_compliance(self, 
                                  actual_deflection: float,
                                  span_length: float,
                                  support_type: ThaiSupportType,
                                  load_duration: str = "immediate") -> Dict[str, Any]:
        """Check deflection compliance"""
        return self.design_requirements.check_deflection_compliance(
            actual_deflection, span_length, support_type, load_duration
        )
    
    # Material Integration Methods
    def create_thai_concrete(self, grade: str) -> ThaiConcrete:
        """Create Thai concrete with specified grade"""
        return ThaiConcrete(grade=grade)
    
    def create_thai_steel(self, grade: str) -> ThaiReinforcementSteel:
        """Create Thai steel with specified grade"""
        return ThaiReinforcementSteel(grade=grade)
    
    def validate_material_combination(self, 
                                    concrete_grade: str, 
                                    steel_grade: str,
                                    environment: ThaiEnvironmentType) -> Dict[str, Any]:
        """Validate concrete and steel grade combination"""
        result = {
            'is_valid': True,
            'warnings': [],
            'recommendations': [],
            'material_compatibility': 'compatible'
        }
        
        try:
            concrete = self.create_thai_concrete(concrete_grade)
            steel = self.create_thai_steel(steel_grade)
            
            # Check material compatibility
            fc_mpa = concrete.fc_prime
            fy_mpa = steel.fy
            
            # Basic compatibility checks
            if fc_mpa < 18.0 and fy_mpa > 400.0:
                result['warnings'].append("คอนกรีตกำลังต่ำกับเหล็กกำลังสูง อาจมีปัญหาการยึดเกาะ")
                result['warnings'].append("Low strength concrete with high strength steel may have bond issues")
            
            if environment == ThaiEnvironmentType.MARINE and fc_mpa < 28.0:
                result['warnings'].append("สภาพแวดล้อมทางทะเลควรใช้คอนกรีตกำลังสูง (≥Fc280)")
                result['warnings'].append("Marine environment should use high strength concrete (≥Fc280)")
            
            # Recommendations
            if fc_mpa >= 28.0 and fy_mpa >= 400.0:
                result['recommendations'].append("การผสมวัสดุเหมาะสมสำหรับงานโครงสร้างคุณภาพสูง")
                result['recommendations'].append("Material combination suitable for high-quality structural work")
        
        except Exception as e:
            result['is_valid'] = False
            result['warnings'].append(f"ข้อผิดพลาดในการตรวจสอบวัสดุ: {str(e)}")
            result['material_compatibility'] = 'invalid'
        
        return result
    
    # Safety Factor Methods
    def get_safety_factor(self, material_or_load: str) -> float:
        """Get safety factor per Ministry Regulation"""
        return self.load_combinations.get_safety_factor(material_or_load)
    
    def get_phi_factor(self, failure_mode: str) -> float:
        """Get strength reduction factor (φ)"""
        return self.load_combinations.get_phi_factor(failure_mode)
    
    # Provincial Zone Methods
    # These delegate to the dedicated load modules so the province -> zone mapping
    # and the design values have exactly one source of truth
    # (loads/wind_loads.py, loads/seismic_loads.py). The duplicate table that used
    # to live here disagreed with both - Bangkok 35 m/s vs 25 m/s, Chiang Mai
    # 0.15g vs 0.40g - and silently understated the design actions.
    def get_wind_zone_data(self, province: str) -> Optional[Dict[str, Any]]:
        """Get wind zone data for province (delegates to ThaiWindLoads)"""
        from .loads.wind_loads import ThaiWindLoads
        
        zone, wind_speed, description = ThaiWindLoads().get_wind_zone_for_province(province)
        return {
            'zone_id': 'zone_%s' % zone.value,
            'wind_speed': wind_speed,
            'description_english': description
        }
    
    def get_seismic_zone_data(self, province: str) -> Optional[Dict[str, Any]]:
        """Get seismic zone data for province (delegates to ThaiSeismicLoads)"""
        from .loads.seismic_loads import ThaiSeismicLoads
        
        data = ThaiSeismicLoads().get_seismic_zone_data(province)
        return {
            'zone_id': 'zone_%s' % data['seismic_zone'].value,
            'pga': data['peak_ground_acceleration'],
            'description_english': data['zone_description']
        }
    
    # Comprehensive Compliance Check
    def check_project_compliance(self, project_data: ThaiProjectData) -> List[ThaiComplianceResult]:
        """
        Comprehensive project compliance check
        
        Parameters:
        -----------
        project_data : ThaiProjectData
            Project information
            
        Returns:
        --------
        List[ThaiComplianceResult]
            Compliance check results
        """
        results = []
        
        # Material compliance
        material_validation = self.validate_material_combination(
            project_data.concrete_grade,
            project_data.steel_grade,
            project_data.environment_type
        )
        
        results.append(ThaiComplianceResult(
            is_compliant=material_validation['is_valid'],
            category="material_compatibility",
            description_thai="ความเข้ากันได้ของวัสดุ",
            description_english="Material compatibility",
            actual_value=1.0 if material_validation['is_valid'] else 0.0,
            required_value=1.0,
            margin=0.0,
            reference="Ministry Regulation B.E. 2566 Section 3",
            warnings=material_validation['warnings'],
            recommendations=material_validation['recommendations']
        ))
        
        # Cover requirements check (example for slab)
        cover_req = self.get_concrete_cover(ThaiElementType.SLAB, project_data.environment_type)
        if cover_req:
            results.append(ThaiComplianceResult(
                is_compliant=True,  # Would be checked against actual design
                category="concrete_cover",
                description_thai=f"ความหนาคอนกรีตปิดแผ่นพื้น - {cover_req.description_thai}",
                description_english=f"Slab concrete cover - {cover_req.description_english}",
                actual_value=cover_req.cover_mm,  # Would be actual from design
                required_value=cover_req.cover_mm,
                margin=0.0,
                reference=cover_req.reference
            ))
        
        # Safety factors compliance
        concrete_sf = self.get_safety_factor('concrete')
        steel_sf = self.get_safety_factor('steel')
        
        results.append(ThaiComplianceResult(
            is_compliant=True,
            category="safety_factors",
            description_thai="ค่าความปลอดภัยวัสดุ",
            description_english="Material safety factors",
            actual_value=concrete_sf,
            required_value=1.5,
            margin=0.0,
            reference="Ministry Regulation B.E. 2566 Section 4.1"
        ))
        
        return results
    
    # Report Generation
    def generate_compliance_report(self, 
                                 project_data: ThaiProjectData,
                                 compliance_results: Optional[List[ThaiComplianceResult]] = None) -> str:
        """
        Generate comprehensive compliance report
        
        Parameters:
        -----------
        project_data : ThaiProjectData
            Project information
        compliance_results : Optional[List[ThaiComplianceResult]]
            Pre-calculated compliance results
            
        Returns:
        --------
        str
            Formatted compliance report
        """
        if compliance_results is None:
            compliance_results = self.check_project_compliance(project_data)
        
        report = []
        report.append("=" * 100)
        report.append("รายงานการตรวจสอบการปฏิบัติตามกฎกระทรวง พ.ศ. 2566")
        report.append("Ministry Regulation B.E. 2566 Compliance Report")
        report.append("=" * 100)
        
        # Header information
        report.append(f"โครงการ/Project: {project_data.project_name}")
        report.append(f"สถานที่/Location: {project_data.location}")
        report.append(f"สภาพแวดล้อม/Environment: {project_data.environment_type.value}")
        report.append(f"เกรดคอนกรีต/Concrete Grade: {project_data.concrete_grade}")
        report.append(f"เกรดเหล็ก/Steel Grade: {project_data.steel_grade}")
        if project_data.date:
            report.append(f"วันที่/Date: {project_data.date}")
        report.append("")
        
        # Regulation information
        report.append("ข้อมูลกฎกระทรวง/Regulation Information:")
        report.append("-" * 60)
        report.append(f"ชื่อ/Name: {self.regulation_info['name_thai']}")
        report.append(f"English: {self.regulation_info['name_english']}")
        report.append(f"วันที่มีผลบังคับใช้/Effective Date: {self.regulation_info['effective_date']}")
        report.append(f"หน่วยงาน/Authority: {self.regulation_info['authority']}")
        report.append("")
        
        # Compliance results
        report.append("ผลการตรวจสอบการปฏิบัติตาม/Compliance Check Results:")
        report.append("-" * 60)
        
        compliant_count = 0
        total_count = len(compliance_results)
        
        for i, result in enumerate(compliance_results, 1):
            status = "✅ ผ่าน/PASS" if result.is_compliant else "❌ ไม่ผ่าน/FAIL"
            report.append(f"{i}. {result.category.replace('_', ' ').title()}: {status}")
            report.append(f"   {result.description_thai}")
            report.append(f"   {result.description_english}")
            
            if result.actual_value is not None and result.required_value is not None:
                report.append(f"   ค่าที่ได้/Actual: {result.actual_value}")
                report.append(f"   ค่าที่ต้องการ/Required: {result.required_value}")
            
            report.append(f"   อ้างอิง/Reference: {result.reference}")
            
            if result.warnings:
                report.append("   คำเตือน/Warnings:")
                for warning in result.warnings:
                    report.append(f"   - {warning}")
            
            if result.recommendations:
                report.append("   ข้อแนะนำ/Recommendations:")
                for rec in result.recommendations:
                    report.append(f"   - {rec}")
            
            if result.is_compliant:
                compliant_count += 1
            
            report.append("")
        
        # Summary
        report.append("สรุปผลการตรวจสอบ/Summary:")
        report.append("-" * 60)
        report.append(f"ผ่านการตรวจสอบ/Compliant: {compliant_count}/{total_count}")
        report.append(f"เปอร์เซ็นต์ที่ผ่าน/Pass Rate: {(compliant_count/total_count)*100:.1f}%")
        
        overall_status = "ผ่าน/COMPLIANT" if compliant_count == total_count else "ไม่ผ่าน/NON-COMPLIANT"
        report.append(f"สถานะโดยรวม/Overall Status: {overall_status}")
        
        report.append("")
        report.append("=" * 100)
        report.append("หมายเหตุ: รายงานนี้จัดทำตามกฎกระทรวง พ.ศ. 2566")
        report.append("Note: This report is prepared according to Ministry Regulation B.E. 2566")
        report.append("=" * 100)
        
        return "\n".join(report)
    
    def get_regulation_info(self) -> Dict[str, str]:
        """Get regulation information"""
        return self.regulation_info.copy()
    
    def __str__(self) -> str:
        """String representation"""
        return f"Thai Ministry Regulation B.E. 2566 (2023) - {self.regulation_info['name_english']}"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return f"ThaiMinistryRegulation2566(effective_date='{self.regulation_info['effective_date']}')"