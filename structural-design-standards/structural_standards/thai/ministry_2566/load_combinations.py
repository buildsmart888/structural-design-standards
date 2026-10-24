"""
Thai Ministry Regulation B.E. 2566 Load Combinations
===================================================

Implementation of load combinations and safety factors according to:
- Ministry Regulation B.E. 2566 (2023) for structural design standards
- Thai building code requirements for load combinations
- Safety factors per Thai Ministry specifications

การรวมแรงตามกฎกระทรวง พ.ศ. 2566
ระบบการรวมแรงและค่าความปลอดภัยตามกฎกระทรวงไทย
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ...utils.validation import StructuralValidator


class ThaiLoadType(Enum):
    """Thai load type classification per Ministry Regulation B.E. 2566"""
    DEAD = "dead"           # DL - น้ำหนักบรรทุกตายตัว
    LIVE = "live"           # LL - น้ำหนักบรรจร
    LATERAL_EARTH = "lateral_earth"  # H - แรงดันดินด้านข้าง
    FLUID = "fluid"         # F - แรงดันน้ำ หรือของเหลว
    WIND = "wind"           # W - แรงลม
    EARTHQUAKE = "earthquake"  # E - แรงแผ่นดินไหว
    THERMAL = "thermal"     # T - แรงจากอุณหภูมิ
    SETTLEMENT = "settlement"  # S - แรงจากการทรุดตัว


class ThaiCombinationType(Enum):
    """Thai load combination types"""
    ULTIMATE_LIMIT_STATE = "ultimate"          # สภาวะจำกัดสุดขีด
    SERVICEABILITY_LIMIT_STATE = "serviceability"  # สภาวะจำกัดการใช้งาน
    FATIGUE_LIMIT_STATE = "fatigue"           # สภาวะจำกัดความล้า


@dataclass
class ThaiLoadCombination:
    """Thai load combination with factors"""
    name: str
    combination_type: ThaiCombinationType
    factors: Dict[ThaiLoadType, float] = field(default_factory=dict)
    description_thai: str = ""
    description_english: str = ""
    reference: str = "Ministry Regulation B.E. 2566"
    
    def calculate_load_effect(self, loads: Dict[ThaiLoadType, float]) -> float:
        """
        Calculate total load effect for this combination
        
        Parameters:
        -----------
        loads : Dict[ThaiLoadType, float]
            Dictionary of load values by type
            
        Returns:
        --------
        float
            Combined load effect
        """
        total = 0.0
        for load_type, factor in self.factors.items():
            if load_type in loads:
                total += factor * loads[load_type]
        return total
    
    def get_equation(self) -> str:
        """Get load combination equation as string"""
        terms = []
        thai_symbols = {
            ThaiLoadType.DEAD: "DL",
            ThaiLoadType.LIVE: "LL", 
            ThaiLoadType.LATERAL_EARTH: "H",
            ThaiLoadType.FLUID: "F",
            ThaiLoadType.WIND: "W",
            ThaiLoadType.EARTHQUAKE: "E",
            ThaiLoadType.THERMAL: "T",
            ThaiLoadType.SETTLEMENT: "S"
        }
        
        for load_type, factor in self.factors.items():
            if factor != 0:
                symbol = thai_symbols.get(load_type, load_type.value.upper())
                if factor == 1.0:
                    terms.append(symbol)
                elif factor == -1.0:
                    terms.append(f"-{symbol}")
                else:
                    terms.append(f"{factor:.1f}{symbol}")
        
        return " + ".join(terms) if terms else "0"


class ThaiMinistryLoadCombinations:
    """
    Thai Ministry Regulation B.E. 2566 Load Combinations
    
    การรวมแรงตามกฎกระทรวง พ.ศ. 2566
    """
    
    def __init__(self):
        """Initialize Thai load combinations"""
        self.validator = StructuralValidator()
        
        # Safety factors per Ministry Regulation B.E. 2566
        self.safety_factors = {
            'concrete': 1.5,        # γc สำหรับคอนกรีต
            'steel': 1.15,          # γs สำหรับเหล็ก
            'dead_load': 1.4,       # ค่าตัวคูณน้ำหนักตาย
            'live_load': 1.6,       # ค่าตัวคูณน้ำหนักใช้สอย
            'wind_load': 1.6,       # ค่าตัวคูณแรงลม
            'seismic_load': 1.0     # ค่าตัวคูณแรงแผ่นดินไหว (รวมกับค่าตัวคูณพิเศษ)
        }
        
        # Strength reduction factors (φ factors)
        self.phi_factors = {
            'flexure_tension_controlled': 0.90,      # งานโค้งควบคุมด้วยแรงดึง
            'flexure_compression_controlled': 0.65,   # งานโค้งควบคุมด้วยแรงอัด
            'shear_and_torsion': 0.75,               # แรงเฉือนและแรงบิด
            'axial_compression_tied': 0.65,          # แรงอัดตามแนวแกนด้วยเหล็กปลอก
            'axial_compression_spiral': 0.70,        # แรงอัดตามแนวแกนด้วยเหล็กเกลียว
            'bearing_on_concrete': 0.65,             # แรงรองรับบนคอนกรีต
        }
        
        # Initialize standard combinations
        self._ultimate_combinations = self._create_ultimate_combinations()
        self._serviceability_combinations = self._create_serviceability_combinations()
    
    def _create_ultimate_combinations(self) -> List[ThaiLoadCombination]:
        """
        Create ultimate limit state combinations per B.E. 2566
        """
        combinations = []
        
        combinations.extend([
            ThaiLoadCombination(
                name="ULS-1",
                combination_type=ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                factors={
                    ThaiLoadType.DEAD: 1.4,
                    ThaiLoadType.LIVE: 1.6
                },
                description_thai="น้ำหนักตาย + น้ำหนักใช้สอย",
                description_english="Dead + Live loads",
                reference="Ministry Regulation B.E. 2566 Section 4.2.1"
            ),
            
            ThaiLoadCombination(
                name="ULS-2",
                combination_type=ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                factors={
                    ThaiLoadType.DEAD: 1.2,
                    ThaiLoadType.LIVE: 1.6,
                    ThaiLoadType.WIND: 1.6
                },
                description_thai="น้ำหนักตาย + น้ำหนักใช้สอย + แรงลม",
                description_english="Dead + Live + Wind loads",
                reference="Ministry Regulation B.E. 2566 Section 4.2.2"
            ),
            
            ThaiLoadCombination(
                name="ULS-3",
                combination_type=ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                factors={
                    ThaiLoadType.DEAD: 1.2,
                    ThaiLoadType.LIVE: 1.0,
                    ThaiLoadType.EARTHQUAKE: 1.0
                },
                description_thai="น้ำหนักตาย + น้ำหนักใช้สอย + แรงแผ่นดินไหว",
                description_english="Dead + Live + Earthquake loads",
                reference="Ministry Regulation B.E. 2566 Section 4.2.3"
            ),
            
            ThaiLoadCombination(
                name="ULS-4",
                combination_type=ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                factors={
                    ThaiLoadType.DEAD: 0.9,
                    ThaiLoadType.WIND: 1.6
                },
                description_thai="น้ำหนักตายขั้นต่ำ + แรงลม (ตรวจสอบการเคว้ง)",
                description_english="Minimum Dead + Wind (overturning check)",
                reference="Ministry Regulation B.E. 2566 Section 4.2.4"
            ),
            
            ThaiLoadCombination(
                name="ULS-5",
                combination_type=ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                factors={
                    ThaiLoadType.DEAD: 0.9,
                    ThaiLoadType.EARTHQUAKE: 1.0
                },
                description_thai="น้ำหนักตายขั้นต่ำ + แรงแผ่นดินไหว (ตรวจสอบการเคว้ง)",
                description_english="Minimum Dead + Earthquake (overturning check)",
                reference="Ministry Regulation B.E. 2566 Section 4.2.5"
            ),
            
            ThaiLoadCombination(
                name="ULS-6",
                combination_type=ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                factors={
                    ThaiLoadType.DEAD: 1.2,
                    ThaiLoadType.LIVE: 0.5,
                    ThaiLoadType.WIND: 1.6
                },
                description_thai="น้ำหนักตาย + น้ำหนักใช้สอยลดลง + แรงลม",
                description_english="Dead + Reduced Live + Wind loads",
                reference="Ministry Regulation B.E. 2566 Section 4.2.6"
            )
        ])
        
        return combinations
    
    def _create_serviceability_combinations(self) -> List[ThaiLoadCombination]:
        """
        Create serviceability limit state combinations per Ministry Regulation B.E. 2566
        หน่วยแรงที่ยอมให้ - Allowable Stress Method per Ministry Regulation B.E. 2566
        """
        combinations = []
        
        # Allowable stress combinations (100-122 series)
        combinations.extend([
            # 100: DL
            ThaiLoadCombination(
                name="ASD-100",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 1.0},
                description_thai="น้ำหนักบรรทุกตายตัวเท่านั้น",
                description_english="Dead load only",
                reference="Ministry Regulation B.E. 2566 - 100"
            ),
            
            # 101: DL + LL
            ThaiLoadCombination(
                name="ASD-101",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 1.0, ThaiLoadType.LIVE: 1.0},
                description_thai="น้ำหนักตายตัว + น้ำหนักบรรจร",
                description_english="Dead + Live loads",
                reference="Ministry Regulation B.E. 2566 - 101"
            ),
            
            # Wind combinations (102-109)
            # 102: DL + 0.75(LL + W(X+))
            ThaiLoadCombination(
                name="ASD-102",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 1.0, ThaiLoadType.LIVE: 0.75, ThaiLoadType.WIND: 0.75},
                description_thai="น้ำหนักตายตัว + 0.75(น้ำหนักบรรจร + แรงลม(X+))",
                description_english="Dead + 0.75(Live + Wind(X+))",
                reference="Ministry Regulation B.E. 2566 - 102"
            ),
            
            # 106: 0.6DL + W(X+)
            ThaiLoadCombination(
                name="ASD-106",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 0.6, ThaiLoadType.WIND: 1.0},
                description_thai="0.6×น้ำหนักตายตัว + แรงลม(X+)",
                description_english="0.6×Dead + Wind(X+)",
                reference="Ministry Regulation B.E. 2566 - 106"
            ),
            
            # Earthquake combinations (110-121)
            # 110: DL + 0.7E(X+)
            ThaiLoadCombination(
                name="ASD-110",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 1.0, ThaiLoadType.EARTHQUAKE: 0.7},
                description_thai="น้ำหนักตายตัว + 0.7×แรงแผ่นดินไหว(X+)",
                description_english="Dead + 0.7×Earthquake(X+)",
                reference="Ministry Regulation B.E. 2566 - 110"
            ),
            
            # 114: DL + 0.525E(X+) + 0.75LL
            ThaiLoadCombination(
                name="ASD-114",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 1.0, ThaiLoadType.EARTHQUAKE: 0.525, ThaiLoadType.LIVE: 0.75},
                description_thai="น้ำหนักตายตัว + 0.525×แรงแผ่นดินไหว(X+) + 0.75×น้ำหนักบรรจร",
                description_english="Dead + 0.525×Earthquake(X+) + 0.75×Live",
                reference="Ministry Regulation B.E. 2566 - 114"
            ),
            
            # 118: 0.6DL + 0.7E(X+)
            ThaiLoadCombination(
                name="ASD-118",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 0.6, ThaiLoadType.EARTHQUAKE: 0.7},
                description_thai="0.6×น้ำหนักตายตัว + 0.7×แรงแผ่นดินไหว(X+)",
                description_english="0.6×Dead + 0.7×Earthquake(X+)",
                reference="Ministry Regulation B.E. 2566 - 118"
            ),
            
            # Special combinations
            # 122: DL + LL + H + F
            ThaiLoadCombination(
                name="ASD-122",
                combination_type=ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors={ThaiLoadType.DEAD: 1.0, ThaiLoadType.LIVE: 1.0, ThaiLoadType.LATERAL_EARTH: 1.0, ThaiLoadType.FLUID: 1.0},
                description_thai="น้ำหนักตายตัว + น้ำหนักบรรจร + แรงดันดินด้านข้าง + แรงดันน้ำ",
                description_english="Dead + Live + Lateral earth pressure + Fluid pressure",
                reference="Ministry Regulation B.E. 2566 - 122"
            )
        ])
        
        return combinations
    
    def get_ultimate_combinations(self) -> List[ThaiLoadCombination]:
        """Get all ultimate limit state combinations"""
        return self._ultimate_combinations.copy()
    
    def get_serviceability_combinations(self) -> List[ThaiLoadCombination]:
        """Get all serviceability limit state combinations"""
        return self._serviceability_combinations.copy()
    
    def find_critical_combination(self, 
                                loads: Dict[ThaiLoadType, float],
                                combination_type: ThaiCombinationType = ThaiCombinationType.ULTIMATE_LIMIT_STATE) -> Tuple[ThaiLoadCombination, float]:
        """
        Find the critical (maximum) load combination
        
        Parameters:
        -----------
        loads : Dict[ThaiLoadType, float]
            Applied loads by type (kN, kN/m, etc.)
        combination_type : ThaiCombinationType
            Type of combinations to consider
            
        Returns:
        --------
        Tuple[ThaiLoadCombination, float]
            Critical combination and its load effect
        """
        if combination_type == ThaiCombinationType.ULTIMATE_LIMIT_STATE:
            combinations = self._ultimate_combinations
        else:
            combinations = self._serviceability_combinations
        
        max_effect = -float('inf')
        critical_combo = None
        
        for combo in combinations:
            effect = combo.calculate_load_effect(loads)
            if effect > max_effect:
                max_effect = effect
                critical_combo = combo
        
        return critical_combo, max_effect
    
    def calculate_all_combinations(self, 
                                 loads: Dict[ThaiLoadType, float],
                                 combination_type: ThaiCombinationType = ThaiCombinationType.ULTIMATE_LIMIT_STATE) -> Dict[str, float]:
        """
        Calculate load effects for all combinations of specified type
        
        Parameters:
        -----------
        loads : Dict[ThaiLoadType, float]
            Applied loads by type
        combination_type : ThaiCombinationType
            Type of combinations to calculate
            
        Returns:
        --------
        Dict[str, float]
            Load effects for each combination
        """
        if combination_type == ThaiCombinationType.ULTIMATE_LIMIT_STATE:
            combinations = self._ultimate_combinations
        else:
            combinations = self._serviceability_combinations
        
        results = {}
        for combo in combinations:
            effect = combo.calculate_load_effect(loads)
            results[combo.name] = effect
        
        return results
    
    def get_safety_factor(self, material_or_load: str) -> float:
        """
        Get safety factor per Ministry Regulation B.E. 2566
        
        Parameters:
        -----------
        material_or_load : str
            Material or load type key
            
        Returns:
        --------
        float
            Safety factor value
        """
        return self.safety_factors.get(material_or_load, 1.0)
    
    def get_phi_factor(self, failure_mode: str) -> float:
        """
        Get strength reduction factor (φ) per Thai standards
        
        Parameters:
        -----------
        failure_mode : str
            Failure mode key
            
        Returns:
        --------
        float
            Strength reduction factor
        """
        if failure_mode in self.phi_factors:
            return self.phi_factors[failure_mode]
        else:
            raise ValueError(f"Unknown failure mode: {failure_mode}")
    
    def validate_loads(self, loads: Dict[ThaiLoadType, float]) -> bool:
        """
        Validate load dictionary
        
        Parameters:
        -----------
        loads : Dict[ThaiLoadType, float]
            Load values to validate
            
        Returns:
        --------
        bool
            True if all loads are valid
        """
        try:
            for load_type, value in loads.items():
                if not isinstance(load_type, ThaiLoadType):
                    raise ValueError(f"Invalid load type: {load_type}")
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Load value must be numeric: {value}")
                if value < 0:
                    raise ValueError(f"Load value cannot be negative: {value}")
            return True
        except ValueError as e:
            print(f"Load validation error: {e}")
            return False
    
    def print_combination_table(self, 
                              combination_type: ThaiCombinationType = ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                              language: str = "thai"):
        """
        Print formatted table of load combinations
        
        Parameters:
        -----------
        combination_type : ThaiCombinationType
            Type of combinations to print
        language : str
            Display language ("thai" or "english")
        """
        if combination_type == ThaiCombinationType.ULTIMATE_LIMIT_STATE:
            combinations = self._ultimate_combinations
            if language == "thai":
                title = "การรวมแรงสภาวะจำกัดสุดขีด - กฎกระทรวง พ.ศ. 2566"
            else:
                title = "Ultimate Limit State Load Combinations - Ministry Regulation B.E. 2566"
        else:
            combinations = self._serviceability_combinations
            if language == "thai":
                title = "การรวมแรงสภาวะจำกัดการใช้งาน - กฎกระทรวง พ.ศ. 2566"
            else:
                title = "Serviceability Limit State Load Combinations - Ministry Regulation B.E. 2566"
        
        print(f"\n{title}")
        print("=" * len(title))
        
        for i, combo in enumerate(combinations, 1):
            print(f"{i:2d}. {combo.name}: {combo.get_equation()}")
            if language == "thai":
                print(f"    คำอธิบาย: {combo.description_thai}")
            else:
                print(f"    Description: {combo.description_english}")
            print(f"    อ้างอิง/Reference: {combo.reference}")
            print()
    
    def export_combinations_to_dict(self) -> Dict[str, Any]:
        """
        Export all combinations to dictionary format
        
        Returns:
        --------
        Dict[str, Any]
            All combinations in dictionary format
        """
        return {
            'ultimate_combinations': [
                {
                    'name': combo.name,
                    'factors': {load_type.value: factor for load_type, factor in combo.factors.items()},
                    'equation': combo.get_equation(),
                    'description_thai': combo.description_thai,
                    'description_english': combo.description_english,
                    'reference': combo.reference
                }
                for combo in self._ultimate_combinations
            ],
            'serviceability_combinations': [
                {
                    'name': combo.name,
                    'factors': {load_type.value: factor for load_type, factor in combo.factors.items()},
                    'equation': combo.get_equation(),
                    'description_thai': combo.description_thai,
                    'description_english': combo.description_english,
                    'reference': combo.reference
                }
                for combo in self._serviceability_combinations
            ],
            'safety_factors': self.safety_factors,
            'phi_factors': self.phi_factors
        }