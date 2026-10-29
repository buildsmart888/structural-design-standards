"""
Thai Seismic/Earthquake Load Calculations per TIS 1301/1302-61
=============================================================

Implementation of Thai seismic load calculations according to:
- TIS 1301/1302-61 (Revised Edition 1) - Standard for Earthquake Resistant Building Design
- Ministry Regulation B.E. 2566

การคำนวณแรงแผ่นดินไหวประเทศไทยตาม:
- มยผ. 1301/1302-61 (ฉบับปรับปรุงครั้งที่ 1) มาตรฐานการออกแบบอาคารต้านทานการสั่นสะเทือนของแผ่นดินไหว
- กฎกระทรวง พ.ศ. 2566
"""

import math
from typing import Dict, Tuple, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum

from ....utils.validation import StructuralValidator, validate_positive


class ThaiSeismicZone(Enum):
    """Thai seismic zones per TIS 1301/1302-61"""
    ZONE_A = "A"  # Low risk areas (PGA = 0.15g)
    ZONE_B = "B"  # Moderate risk areas (PGA = 0.25g)
    ZONE_C = "C"  # High risk areas (PGA = 0.40g)


class ThaiSoilType(Enum):
    """Thai soil types per TIS 1301/1302-61"""
    TYPE_A = "A"  # Hard rock
    TYPE_B = "B"  # Rock
    TYPE_C = "C"  # Very dense soil
    TYPE_D = "D"  # Stiff soil
    TYPE_E = "E"  # Soft soil
    TYPE_F = "F"  # Special soil (requires site-specific study)


class ThaiSeismicImportance(Enum):
    """Building importance categories for seismic design"""
    STANDARD = "I"    # Standard buildings (I = 1.0)
    IMPORTANT = "II"  # Important buildings (I = 1.25)
    ESSENTIAL = "III" # Essential facilities (I = 1.5)


class ThaiStructuralSystem(Enum):
    """Structural systems for seismic resistance"""
    MOMENT_FRAME = "moment_frame"      # Moment resisting frame
    SHEAR_WALL = "shear_wall"          # Shear wall system
    DUAL_SYSTEM = "dual_system"        # Dual system
    BRACED_FRAME = "braced_frame"      # Braced frame system


@dataclass
class ThaiSeismicForces:
    """Thai seismic force results"""
    base_shear: float                    # Design base shear (kN)
    seismic_coefficient: float          # Seismic coefficient Cs
    fundamental_period: float           # Fundamental period Ta (sec)
    peak_ground_acceleration: float     # PGA (g)
    site_coefficient_fa: float          # Site coefficient Fa
    site_coefficient_fv: float          # Site coefficient Fv
    importance_factor: float            # Importance factor I
    response_modification: float        # Response modification factor R
    story_forces: Dict[int, float]      # Story forces by floor (kN)
    calculation_method: str = "TIS 1301/1302-61 Equivalent Lateral Force Method"


@dataclass
class ThaiBuildingGeometry:
    """Thai building geometry for seismic analysis"""
    total_height: float                    # Total height (m)
    story_heights: List[float]             # Story heights (m)
    story_weights: List[float]             # Story weights (kN)
    structural_system: ThaiStructuralSystem
    structural_material: str = "concrete"  # "concrete", "steel"


class ThaiSeismicLoads:
    """
    Thai Seismic/Earthquake Load Calculations per TIS 1301/1302-61
    
    ไลบรารีการคำนวณแรงแผ่นดินไหวประเทศไทยตาม มยผ. 1301/1302-61
    """
    
    def __init__(self):
        """Initialize Thai seismic loads calculator"""
        self.validator = StructuralValidator()
        
        # Peak ground accelerations by seismic zone
        self.peak_ground_accelerations = {
            ThaiSeismicZone.ZONE_A: 0.15,  # Low risk - 0.15g
            ThaiSeismicZone.ZONE_B: 0.25,  # Moderate risk - 0.25g
            ThaiSeismicZone.ZONE_C: 0.40   # High risk - 0.40g
        }
        
        # Site coefficient Fa (short period) tables
        self.site_coefficient_fa = {
            ThaiSoilType.TYPE_A: {0.15: 0.8, 0.25: 0.8, 0.40: 0.8},
            ThaiSoilType.TYPE_B: {0.15: 1.0, 0.25: 1.0, 0.40: 1.0},
            ThaiSoilType.TYPE_C: {0.15: 1.2, 0.25: 1.2, 0.40: 1.1},
            ThaiSoilType.TYPE_D: {0.15: 1.6, 0.25: 1.4, 0.40: 1.2},
            ThaiSoilType.TYPE_E: {0.15: 2.5, 0.25: 1.7, 0.40: 1.2}
        }
        
        # Site coefficient Fv (long period) tables
        self.site_coefficient_fv = {
            ThaiSoilType.TYPE_A: {0.15: 0.8, 0.25: 0.8, 0.40: 0.8},
            ThaiSoilType.TYPE_B: {0.15: 1.0, 0.25: 1.0, 0.40: 1.0},
            ThaiSoilType.TYPE_C: {0.15: 1.8, 0.25: 1.6, 0.40: 1.5},
            ThaiSoilType.TYPE_D: {0.15: 2.4, 0.25: 2.0, 0.40: 1.8},
            ThaiSoilType.TYPE_E: {0.15: 3.5, 0.25: 3.2, 0.40: 3.0}
        }
        
        # Importance factors by building category
        self.importance_factors = {
            ThaiSeismicImportance.STANDARD: 1.0,
            ThaiSeismicImportance.IMPORTANT: 1.25,
            ThaiSeismicImportance.ESSENTIAL: 1.5
        }
        
        # Structural system factors (R and Cd values)
        self.structural_system_factors = {
            ThaiStructuralSystem.MOMENT_FRAME: {
                'steel': {'R': 8, 'Cd': 5.5},
                'concrete': {'R': 8, 'Cd': 5.5}
            },
            ThaiStructuralSystem.SHEAR_WALL: {
                'concrete': {'R': 5, 'Cd': 5.0},
                'masonry': {'R': 2, 'Cd': 2.5}
            },
            ThaiStructuralSystem.DUAL_SYSTEM: {
                'steel': {'R': 8, 'Cd': 6.5},
                'concrete': {'R': 7, 'Cd': 5.5}
            },
            ThaiStructuralSystem.BRACED_FRAME: {
                'steel': {'R': 6, 'Cd': 5.0},
                'concrete': {'R': 6, 'Cd': 5.0}
            }
        }
        
        # Provincial seismic zone mapping
        self.provincial_zones = {
            # Northern Thailand - Higher seismic risk
            'เชียงใหม่': ThaiSeismicZone.ZONE_C, 'เชียงราย': ThaiSeismicZone.ZONE_C,
            'ลำปาง': ThaiSeismicZone.ZONE_B, 'ลำพูน': ThaiSeismicZone.ZONE_B,
            'แม่ฮ่องสอน': ThaiSeismicZone.ZONE_C, 'น่าน': ThaiSeismicZone.ZONE_B,
            'พะเยา': ThaiSeismicZone.ZONE_B, 'แพร่': ThaiSeismicZone.ZONE_B,
            
            # Western Thailand - Moderate to high risk  
            'กาญจนบุรี': ThaiSeismicZone.ZONE_B, 'ตาก': ThaiSeismicZone.ZONE_B,
            'สุพรรณบุรี': ThaiSeismicZone.ZONE_B, 'ราชบุรี': ThaiSeismicZone.ZONE_A,
            'เพชรบุรี': ThaiSeismicZone.ZONE_A, 'ประจวบคีรีขันธ์': ThaiSeismicZone.ZONE_A,
            
            # Central Thailand - Lower seismic risk
            'กรุงเทพมหานคร': ThaiSeismicZone.ZONE_A, 'นนทบุรี': ThaiSeismicZone.ZONE_A,
            'ปทุมธานี': ThaiSeismicZone.ZONE_A, 'สมุทรปราการ': ThaiSeismicZone.ZONE_A,
            'นครปฐม': ThaiSeismicZone.ZONE_A, 'สมุทรสาคร': ThaiSeismicZone.ZONE_A,
            
            # Eastern Thailand - Low risk
            'ชลบุรี': ThaiSeismicZone.ZONE_A, 'ระยอง': ThaiSeismicZone.ZONE_A,
            'จันทบุรี': ThaiSeismicZone.ZONE_A, 'ตราด': ThaiSeismicZone.ZONE_A,
            
            # Southern Thailand - Low risk
            'ภูเก็ต': ThaiSeismicZone.ZONE_A, 'สงขลา': ThaiSeismicZone.ZONE_A,
            'สุราษฎร์ธานี': ThaiSeismicZone.ZONE_A, 'นครศรีธรรมราช': ThaiSeismicZone.ZONE_A
        }
    
def get_seismic_zone_data(self, location: Union[str, ThaiSeismicZone]) -> Dict[str, Any]:
        """Province/PGA lookup is an unsupported placeholder, NOT official hazard."""
        raise NotImplementedError(
            "Unverified province-to-PGA map is disabled. Thai seismic design "
            "requires official location-specific Ss/S1, site classification and "
            "the applicable earthquake regulation; province name or guessed "
            "PGA 0.15/0.25/0.40 g is insufficient."
        )

def get_site_coefficients(self, pga: float,
                              soil_type: ThaiSoilType) -> Tuple[float, float]:
        """Nearest-neighbor interpolation on unverified PGA tables is unsafe."""
        raise NotImplementedError(
            "Fa/Fv cannot be selected from nearest PGA. Use code-required "
            "site-adjusted Ss/S1 and the correct site tables, with site study "
            "for exceptional soil classes."
        )

def calculate_fundamental_period(self,
                                    building_geometry: ThaiBuildingGeometry) -> float:
        """Structural period method must be chosen per governing seismic code."""
        raise NotImplementedError(
            "Unverified Ct and exponent table; exact structural system and "
            "current code period upper bounds are required."
        )

def calculate_seismic_coefficient(self, sds: float, r_factor: float,
                                     importance_factor: float,
                                     ta: Optional[float] = None,
                                     sd1: Optional[float] = None) -> float:
        """Incomplete Cs with default 0.01 and SdS/2 limits is disabled."""
        raise NotImplementedError(
            "Seismic Cs requires validated Ss/S1, SDS/SD1, period limits, "
            "R and importance factors, site class and minimum shear provisions."
        )

    @staticmethod
    def base_shear_from_verified_coefficient(
            seismic_coefficient: float, effective_weight_kN: float) -> float:
        """Arithmetic only: V=Cs*W with EXTERNALLY verified Cs and W."""
        for name, value in (("Cs", seismic_coefficient),
                            ("seismic effective weight", effective_weight_kN)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        return seismic_coefficient * effective_weight_kN

    @staticmethod
    def distribute_base_shear(
            base_shear_kN: float, story_heights_m: List[float],
            story_weights_kN: List[float], exponent_k: float) -> Dict[int, float]:
        """Pure normalization Fi=V*wi*hi**k / sum(wj*hj**k).

        The code-specific k, vertical force exceptions, top force, and dynamic
        requirements must be established separately. This is NOT seismic design.
        Heights are elevations above base, NOT incremental story heights.
        """
        if not story_heights_m or len(story_heights_m) != len(story_weights_kN):
            raise ValueError("Non-empty matching story arrays are required")
        for name, x in [("V", base_shear_kN), ("k", exponent_k)]:
            if not math.isfinite(x) or x <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if (any(not math.isfinite(h) or h <= 0 for h in story_heights_m)
                or any(not math.isfinite(w) or w <= 0 for w in story_weights_kN)):
            raise ValueError("All elevations and weights must be positive finite")
        if any(story_heights_m[i] >= story_heights_m[i+1]
               for i in range(len(story_heights_m)-1)):
            raise ValueError("Elevations must strictly increase above base")
        weights = [w*h**exponent_k for w,h in zip(story_weights_kN, story_heights_m)]
        sumw = sum(weights)
        if not math.isfinite(sumw) or sumw <= 0:
            raise ValueError("Invalid lateral force distribution denominator")
        return {i: base_shear_kN*wk/sumw for i,wk in enumerate(weights,1)}

def calculate_complete_seismic_analysis(
            self, location: Union[str, ThaiSeismicZone],
            building_geometry: ThaiBuildingGeometry,
            soil_type: ThaiSoilType,
            importance_category: ThaiSeismicImportance) -> ThaiSeismicForces:
        """No automatic seismic certification from the unverified PGA lookup."""
        raise NotImplementedError(
            "Complete Thai seismic model NOT VERIFIED: use current government "
            "site-specific spectrum, ground class, R, period, Cs limits, torsion, "
            "drift, vertical distribution and required modal/dynamic checks."
        )

    def generate_seismic_report(self, result: ThaiSeismicForces, 
                              project_info: Dict[str, str]) -> str:
        """Generate seismic load calculation report"""
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                     รายงานการคำนวณแรงแผ่นดินไหว                             ║
║                   THAI SEISMIC LOAD CALCULATION REPORT                        ║
║                     ตาม มยผ. 1301/1302-61 (ฉบับปรับปรุง)                      ║
╚════════════════════════════════════════════════════════════════════════════════╝

ข้อมูลโครงการ / Project Information:
{'-'*80}
ชื่อโครงการ / Project: {project_info.get('project_name', 'N/A')}
ตำแหน่ง / Location: {project_info.get('location', 'N/A')}
วันที่ / Date: {project_info.get('date', 'N/A')}

พารามิเตอร์แผ่นดินไหว / Seismic Parameters:
{'-'*80}
ความเร่งพื้นดินสูงสุด / PGA: {result.peak_ground_acceleration:.3f} g
ค่าสัมประสิทธิ์ดิน Fa: {result.site_coefficient_fa:.2f}
ค่าสัมประสิทธิ์ดิน Fv: {result.site_coefficient_fv:.2f}
ค่าประกอบความสำคัญ I: {result.importance_factor:.2f}
ค่าปรับลดแรง R: {result.response_modification:.1f}

ผลการวิเคราะห์ / Analysis Results:
{'-'*80}
คาบธรรมชาติ Ta: {result.fundamental_period:.3f} วินาที
ค่าสัมประสิทธิ์แผ่นดินไหว Cs: {result.seismic_coefficient:.4f}
แรงเฉือนฐาน V: {result.base_shear:.1f} kN

แรงด้านข้างแต่ละชั้น / Story Forces:
{'-'*80}
{'ชั้น':<8} {'แรงแผ่นดินไหว (kN)':<20}
{'Floor':<8} {'Seismic Force (kN)':<20}
{'-'*30}"""

        for floor, force in sorted(result.story_forces.items()):
            report += f"\n{floor:<8} {force:<20.1f}"
        
        report += f"""

วิธีการคำนวณ / Method: {result.calculation_method}

หมายเหตุ / Notes:
{'-'*80}
1. การคำนวณตาม มยผ. 1301/1302-61 (ฉบับปรับปรุงครั้งที่ 1)
2. ใช้วิธี Equivalent Lateral Force Method
3. ควรตรวจสอบด้วยโปรแกรมวิเคราะห์โครงสร้าง
4. Based on TIS 1301/1302-61 (Revised Edition 1)
5. Equivalent Lateral Force Method used
6. Detailed structural analysis software recommended

รายงานสร้างโดย Thai Seismic Loads v1.0
Generated by Thai Seismic Loads v1.0
{'-'*80}
"""
        return report


# Convenience functions for quick calculations
def get_seismic_zone(province: str) -> ThaiSeismicZone:
    """Legacy API disabled: a provincial PGA guess cannot certify a building."""
    raise NotImplementedError("Official site-specific seismic parameters required")


def quick_seismic_analysis(location: str, building_height: float,
                           total_weight: float,
                           soil_type: ThaiSoilType = ThaiSoilType.TYPE_C) -> Dict[str, float]:
    """No automatic default concrete R=8 and default soil class C."""
    raise NotImplementedError(
        "Quick Thai seismic analysis NOT VERIFIED: provide official site "
        "parameters and approved structural system; do not default R or soil"
    )
