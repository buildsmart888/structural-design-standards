"""
Thai Wind Loads - TIS 1311-50 & Ministry Regulation B.E. 2566
=============================================================

Implementation of Thai wind load calculations according to:
- TIS 1311-50: Thai Industrial Standard for Wind Load Calculation and Building Response
- Ministry Regulation B.E. 2566 Chapter 4: Wind Load Requirements
- Provincial wind zones with specific wind speeds

การคำนวณแรงลมประเทศไทยตาม:
- มยผ. 1311-50: มาตรฐานการคำนวณแรงลมและการตอบสนองของอาคาร
- กฎกระทรวง พ.ศ. 2566 หมวด 4: ข้อกำหนดแรงลม
- โซนลมตามจังหวัดพร้อมความเร็วลมเฉพาะ
"""

import math
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class ThaiWindZone(Enum):
    """Thai wind zones according to TIS 1311-50"""
    ZONE_1 = "1"  # ภาคเหนือ / Northern regions
    ZONE_2 = "2"  # ภาคกลาง / Central regions  
    ZONE_3 = "3"  # ภาคใต้ / Southern regions
    ZONE_4 = "4"  # พื้นที่ชายฝั่ง / Coastal areas


class ThaiTerrainCategory(Enum):
    """Thai terrain categories according to TIS 1311-50"""
    CATEGORY_I = "I"      # ภูมิประเทศเปิด / Open terrain
    CATEGORY_II = "II"    # ภูมิประเทศขรุขระ / Rough terrain
    CATEGORY_III = "III"  # ภูมิประเทศเมือง / Urban terrain
    CATEGORY_IV = "IV"    # ภูมิประเทศเมืองหนาแน่น / Dense urban terrain


class ThaiBuildingImportance(Enum):
    """Thai building importance categories per Ministry Regulation B.E. 2566"""
    STANDARD = "standard"      # อาคารทั่วไป / Standard buildings
    IMPORTANT = "important"    # อาคารสำคัญ / Important buildings
    ESSENTIAL = "essential"    # อาคารจำเป็น / Essential facilities
    HAZARDOUS = "hazardous"    # อาคารอันตราย / Hazardous facilities


class ThaiTopographyType(Enum):
    """Thai topography types for wind calculations"""
    FLAT = "flat"              # ที่ราบ / Flat terrain
    HILL = "hill"              # เนินเขา / Hill
    RIDGE = "ridge"            # สันเขา / Ridge
    ESCARPMENT = "escarpment"  # หน้าผา / Escarpment
    VALLEY = "valley"          # หุบเขา / Valley


@dataclass
class ThaiBuildingGeometry:
    """Thai building geometry parameters for wind analysis"""
    height: float                           # ความสูง m / Height (m)
    width: float                           # ความกว้าง m / Width (m)
    depth: float                           # ความลึก m / Depth (m)
    roof_angle: float = 0.0                # มุมหลังคา องศา / Roof angle (degrees)
    building_type: str = "rectangular"     # ประเภทอาคาร / Building type
    exposure_category: ThaiTerrainCategory = ThaiTerrainCategory.CATEGORY_III


@dataclass
class ThaiWindLoadResult:
    """Thai wind load calculation result"""
    design_wind_pressure: float         # แรงดันลมออกแบบ Pa / Design wind pressure (Pa)
    design_wind_speed: float           # ความเร็วลมออกแบบ m/s / Design wind speed (m/s)
    basic_wind_speed: float            # ความเร็วลมพื้นฐาน m/s / Basic wind speed (m/s)
    terrain_factor: float              # ค่าประกอบภูมิประเทศ / Terrain factor
    topographic_factor: float          # ค่าประกอบภูมิทัศน์ / Topographic factor
    importance_factor: float           # ค่าประกอบความสำคัญ / Importance factor
    pressure_coefficients: Dict[str, float]  # ค่าสัมประสิทธิ์แรงดัน / Pressure coefficients
    total_wind_force: float            # แรงลมรวม N / Total wind force (N)
    wind_zone: str                     # โซนลม / Wind zone
    province: str                      # จังหวัด / Province
    description_thai: str              # คำอธิบายไทย / Thai description
    description_english: str           # คำอธิบายอังกฤษ / English description
    calculation_method: str            # วิธีการคำนวณ / Calculation method
    reference: str                     # อ้างอิง / Reference standard


class ThaiWindLoads:
    """
    Thai Wind Loads Calculator - TIS 1311-50 & Ministry Regulation B.E. 2566
    
    เครื่องคำนวณแรงลมไทย - มยผ. 1311-50 และกฎกระทรวง พ.ศ. 2566
    """
    
    def __init__(self):
        """Initialize Thai wind loads calculator"""
        
        # Basic wind speeds by zone (m/s) according to TIS 1311-50
        self.basic_wind_speeds = {
            ThaiWindZone.ZONE_1: 30.0,  # ภาคเหนือ / Northern Thailand
            ThaiWindZone.ZONE_2: 25.0,  # ภาคกลาง / Central Thailand
            ThaiWindZone.ZONE_3: 35.0,  # ภาคใต้ / Southern Thailand
            ThaiWindZone.ZONE_4: 40.0   # พื้นที่ชายฝั่ง / Coastal areas
        }
        
        # Terrain parameters according to TIS 1311-50
        self.terrain_parameters = {
            ThaiTerrainCategory.CATEGORY_I: {
                'name_thai': 'ภูมิประเทศเปิด',
                'name_english': 'Open terrain',
                'description_thai': 'แหล่งน้ำขนาดใหญ่ พื้นที่เปิดโล่ง',
                'description_english': 'Large water bodies, open flat terrain',
                'z0': 0.03, 'zmin': 10, 'alpha': 0.12
            },
            ThaiTerrainCategory.CATEGORY_II: {
                'name_thai': 'ภูมิประเทศขรุขระ',
                'name_english': 'Rough terrain',
                'description_thai': 'ที่โล่งมีสิ่งกีดขวางกระจายอยู่',
                'description_english': 'Open terrain with scattered obstructions',
                'z0': 0.3, 'zmin': 15, 'alpha': 0.16
            },
            ThaiTerrainCategory.CATEGORY_III: {
                'name_thai': 'ภูมิประเทศเมือง',
                'name_english': 'Urban terrain',
                'description_thai': 'ชานเมือง เมืองเล็ก',
                'description_english': 'Suburban areas, small towns',
                'z0': 1.0, 'zmin': 20, 'alpha': 0.22
            },
            ThaiTerrainCategory.CATEGORY_IV: {
                'name_thai': 'ภูมิประเทศเมืองหนาแน่น',
                'name_english': 'Dense urban terrain',
                'description_thai': 'เขตเมืองหนาแน่น ใจกลางเมือง',
                'description_english': 'Dense urban areas, city centers',
                'z0': 2.5, 'zmin': 30, 'alpha': 0.30
            }
        }
        
        # Importance factors according to Ministry Regulation B.E. 2566
        self.importance_factors = {
            ThaiBuildingImportance.STANDARD: {
                'factor': 1.0,
                'description_thai': 'อาคารทั่วไป',
                'description_english': 'Standard buildings',
                'examples_thai': 'อาคารที่อยู่อาศัย อาคารสำนักงาน',
                'examples_english': 'Residential buildings, office buildings'
            },
            ThaiBuildingImportance.IMPORTANT: {
                'factor': 1.15,
                'description_thai': 'อาคารสำคัญ',
                'description_english': 'Important buildings',
                'examples_thai': 'โรงเรียน โรงพยาบาล อาคารชุมนุม',
                'examples_english': 'Schools, hospitals, assembly buildings'
            },
            ThaiBuildingImportance.ESSENTIAL: {
                'factor': 1.25,
                'description_thai': 'อาคารจำเป็น',
                'description_english': 'Essential facilities',
                'examples_thai': 'สิ่งอำนวยความสะดวกฉุกเฉิน โรงไฟฟ้า',
                'examples_english': 'Emergency facilities, power plants'
            },
            ThaiBuildingImportance.HAZARDOUS: {
                'factor': 1.25,
                'description_thai': 'อาคารอันตราย',
                'description_english': 'Hazardous facilities',
                'examples_thai': 'โรงงานเคมี คลังเก็บสารพิษ',
                'examples_english': 'Chemical plants, toxic storage facilities'
            }
        }
        
        # Pressure coefficients for different building shapes
        self.pressure_coefficients = {
            'rectangular_building': {
                'windward_wall': 0.8, 'leeward_wall': -0.5,
                'side_walls': -0.7, 'flat_roof': -0.7
            },
            'low_rise_building': {
                'windward_wall': 0.8, 'leeward_wall': -0.5,
                'side_walls': -0.7, 'roof_windward': -0.7, 'roof_leeward': -0.3
            }
        }
        
        # Topographic factors
        self.topographic_factors = {
            ThaiTopographyType.FLAT: 1.0, ThaiTopographyType.HILL: 1.1,
            ThaiTopographyType.RIDGE: 1.15, ThaiTopographyType.ESCARPMENT: 1.2,
            ThaiTopographyType.VALLEY: 0.9
        }
        
        # Thai provinces and their wind zones
        self.province_wind_zones = self._initialize_province_zones()
    
    def _initialize_province_zones(self) -> Dict[str, ThaiWindZone]:
        """Initialize Thai province wind zone mapping"""
        return {
            # Northern Thailand (Zone 1)
            'เชียงใหม่': ThaiWindZone.ZONE_1, 'เชียงราย': ThaiWindZone.ZONE_1,
            'ลำปาง': ThaiWindZone.ZONE_1, 'ลำพูน': ThaiWindZone.ZONE_1,
            'แม่ฮ่องสอน': ThaiWindZone.ZONE_1, 'น่าน': ThaiWindZone.ZONE_1,
            # Central Thailand (Zone 2)
            'กรุงเทพมหานคร': ThaiWindZone.ZONE_2, 'นนทบุรี': ThaiWindZone.ZONE_2,
            'ปทุมธานี': ThaiWindZone.ZONE_2, 'สมุทรปราการ': ThaiWindZone.ZONE_2,
            # Northeastern Thailand (Zone 2)
            'นครราชสีมา': ThaiWindZone.ZONE_2, 'ขอนแก่น': ThaiWindZone.ZONE_2,
            'อุดรธานี': ThaiWindZone.ZONE_2, 'อุบลราชธานี': ThaiWindZone.ZONE_2,
            # Eastern & Southern Thailand
            'ชลบุรี': ThaiWindZone.ZONE_4, 'ระยอง': ThaiWindZone.ZONE_4,
            'ภูเก็ต': ThaiWindZone.ZONE_4, 'สงขลา': ThaiWindZone.ZONE_4,
            'สุราษฎร์ธานี': ThaiWindZone.ZONE_3, 'นครศรีธรรมราช': ThaiWindZone.ZONE_3
        }
    
def get_wind_zone_for_province(self, province: str) -> Tuple[ThaiWindZone, float, str]:
        """Unverified province -> m/s mapping must not be used for design."""
        raise NotImplementedError(
            "Province-to-wind-speed lookup is NOT VERIFIED against the current "
            "official DPT wind map. Never default an unknown province to 25 m/s. "
            "For qualifying buildings, use calculate_statutory_minimum_pressure "
            "with explicit terrain and geometry; it is a statutory minimum only."
        )

    @staticmethod
    def calculate_statutory_minimum_pressure(
            building_height_m: float, least_width_m: float,
            terrain: str, is_public_building: bool = False,
            total_floor_area_m2: float = 0.0,
            rectangular_plan: bool = True) -> Dict[str, float]:
        """Ministerial Regulation 2566 clause 17: LIMITED wind-pressure option.

        Applies only to rectangular/similar MAIN structural systems at H <= 40m
        and H <= 3 * least width. Does NOT cover facade components, cladding,
        internal pressure, shape coefficients, uplift, topography, or a complete
        multi-direction wind load analysis. Returns the statutory minimum only.
        """
        for name, val in (("height", building_height_m),
                          ("least width", least_width_m)):
            if not math.isfinite(val) or val <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if (not rectangular_plan or building_height_m > 40
                or building_height_m > 3 * least_width_m):
            raise ValueError("Clause 17 simplified option is NOT applicable")
        if terrain not in ("urban", "open"):
            raise ValueError("terrain must explicitly be urban or open/coastal")
        if not math.isfinite(total_floor_area_m2) or total_floor_area_m2 < 0:
            raise ValueError("total_floor_area_m2 must be >= 0")
        if building_height_m <= 10:
            i = 0
        elif building_height_m <= 20:
            i = 1
        else:
            i = 2
        table = {"urban": (0.6, 0.8, 1.2),
                 "open": (1.0, 1.2, 1.6)}  # kN/m2, clause 17
        factor = 1.15 if is_public_building and total_floor_area_m2 >= 1000 else 1.0
        value = table[terrain][i] * factor
        return {
            "minimum_pressure_kN_m2": value,
            "minimum_pressure_kPa": value,
            "public_building_factor": factor,
            "maximum_applicable_height_m": 40.0,
            "applicability_checked": True,
            "reference": "Thai Ministerial Regulation B.E.2566 clause 17, Tables 1-2",
        }

def calculate_terrain_factor(self, height: float,
                                 terrain: ThaiTerrainCategory) -> float:
        """Site exposure model is NOT verified against DPT wind standard."""
        raise NotImplementedError(
            "Unverified terrain multipliers: official DPT exposure category "
            "and site-specific gust factors are required."
        )

def calculate_design_wind_pressure(self, basic_wind_speed: float,
                                     height: float, terrain: ThaiTerrainCategory,
                                     building_importance: ThaiBuildingImportance,
                                     topography: ThaiTopographyType = ThaiTopographyType.FLAT) -> float:
        """Do not use a guessed wind speed/exposure factor as a design pressure."""
        raise NotImplementedError(
            "Design wind pressure NOT VERIFIED: use the official wind standard "
            "and all applicable external/internal pressures, direction, exposure "
            "and topography factors. A static q=0.5*rho*V^2 is not a building load."
        )

def analyze_building_wind_loads(self, province: str,
                                    building_geometry: ThaiBuildingGeometry,
                                    building_importance: ThaiBuildingImportance,
                                    topography: ThaiTopographyType = ThaiTopographyType.FLAT) -> ThaiWindLoadResult:
        """Full wind analysis unavailable: do not report the old Cp=0.8-only result."""
        raise NotImplementedError(
            "Thai full building wind loads NOT VERIFIED: unverified wind speeds, "
            "windward-only Cp=0.8, missing leeward/internal pressures and uplift. "
            "No force may be automatically certified from a province name."
        )


    def get_wind_load_summary(self, province: str, building_height: float,
                            building_importance: ThaiBuildingImportance = ThaiBuildingImportance.STANDARD) -> Dict[str, Any]:
        """Deprecated 'quick summary' must not imply a fully calculated wind load."""
        raise NotImplementedError(
            "Province-based wind load summary is NOT VERIFIED. Supply terrain, "
            "least width and public status to the clause-17 minimum-pressure API."
        )
