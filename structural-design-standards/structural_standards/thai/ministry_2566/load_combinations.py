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
        if ThaiLoadType.DEAD not in loads:
            raise ValueError("D (permanent load EFFECT) is required, even if zero")
        for kind, magnitude in loads.items():
            if not isinstance(kind, ThaiLoadType):
                raise TypeError(f"Unknown Thai load key: {kind!r}")
            if not isinstance(magnitude, (int, float)) or not math.isfinite(magnitude):
                raise ValueError(f"Non-finite/non-numeric load effect: {kind}")
        return sum(f * loads.get(t, 0.0) for t, f in self.factors.items())

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
    
    def __init__(self, good_quality_control: bool = False):
        """Select phi using explicit evidence of construction quality.

        Section 8 has TWO columns. Without a documented quality-control program
        the conservative (second) column is used. This is NOT ACI phi.
        """
        self.validator = StructuralValidator()
        self.good_quality_control = good_quality_control

        # Structural strength-design load factors, not EC2 material gammas.
        self.safety_factors = {
            "dead_load": 1.4,
            "live_load": 1.7,
            "wind_load": 1.6,
            "seismic_load": 1.0,
            "lateral_earth": 1.7,
            "fluid": 1.4,
            "thermal": 1.4,
        }
        # Thai Ministerial Regulation B.E. 2566 Section 8:
        # (good documented quality control, not demonstrated).
        quality = {
            "flexure_tension_controlled": (0.90, 0.75),
            "axial_tension": (0.90, 0.75),
            "axial_compression_spiral": (0.75, 0.625),
            "axial_compression_tied": (0.70, 0.60),
            "shear_and_torsion": (0.85, 0.70),
            "bearing_on_concrete": (0.70, 0.60),
        }
        self.phi_factors = {
            key: pair[0] if good_quality_control else pair[1]
            for key, pair in quality.items()
        }
        self._ultimate_combinations = self._create_ultimate_combinations()
        self._serviceability_combinations = self._create_serviceability_combinations()

    @staticmethod
    def _expand_lateral(name: str, kind: ThaiCombinationType,
                        factors: Dict[ThaiLoadType, float],
                        clause: str) -> List[ThaiLoadCombination]:
        """Evaluate BOTH opposite signs of every present lateral load.

        The signed effects for each direction (Wx, Wy, Ex, Ey) still have to be
        passed as separate analyses; this routine never creates their geometry.
        """
        lateral = [key for key in (ThaiLoadType.WIND, ThaiLoadType.EARTHQUAKE)
                   if key in factors]
        if not lateral:
            return [ThaiLoadCombination(name=name, combination_type=kind,
                                        factors=factors.copy(), reference=clause)]
        if len(lateral) != 1:
            raise ValueError("Wind and earthquake must not be combined by this helper")
        key = lateral[0]
        return [
            ThaiLoadCombination(
                name=name + suffix, combination_type=kind,
                factors={**factors, key: factors[key] * sign},
                description_english="Signed lateral load effect; analyze each direction",
                reference=clause,
            )
            for sign, suffix in ((1.0, "+"), (-1.0, "-"))
        ]

    def _create_ultimate_combinations(self) -> List[ThaiLoadCombination]:
        """EXACT load factors of Ministerial Regulation B.E. 2566, clause 7.

        W/E lateral components expanded to +/-; load shapes/directions and
        the applicability of each clause remain responsibilities of the caller.
        """
        D = ThaiLoadType.DEAD
        L = ThaiLoadType.LIVE
        W = ThaiLoadType.WIND
        E = ThaiLoadType.EARTHQUAKE
        H = ThaiLoadType.LATERAL_EARTH
        F = ThaiLoadType.FLUID
        T = ThaiLoadType.THERMAL
        S = ThaiLoadType.SETTLEMENT
        rows = [
            ("ULS-7.1",    {D: 1.4, L: 1.7}),
            ("ULS-7.2a",   {D: 1.05, L: 1.275, W: 1.6}),
            ("ULS-7.2b",   {D: 0.9, W: 1.6}),
            ("ULS-7.3a",   {D: 1.05, L: 1.275, E: 1.0}),
            ("ULS-7.3b",   {D: 0.9, E: 1.0}),
            ("ULS-7.4aH",  {D: 1.4, L: 1.7, H: 1.7}),
            ("ULS-7.4bH",  {D: 0.9, H: 1.7}),
            ("ULS-7.4aF",  {D: 1.4, L: 1.7, F: 1.4}),
            ("ULS-7.4bF",  {D: 0.9, F: 1.4}),
            ("ULS-7.5a",   {D: 1.05, L: 1.275, T: 1.05, S: 1.05}),
            ("ULS-7.5b",   {D: 1.4, T: 1.4, S: 1.4}),
        ]
        result = []
        for name, factors in rows:
            result.extend(self._expand_lateral(
                name, ThaiCombinationType.ULTIMATE_LIMIT_STATE,
                factors, "Ministry Regulation B.E. 2566 clause 7"
            ))
        return result

    def _create_serviceability_combinations(self) -> List[ThaiLoadCombination]:
        """ASD/service load effects in clause 6, NOT ASCE 7 combinations."""
        D = ThaiLoadType.DEAD
        L = ThaiLoadType.LIVE
        W = ThaiLoadType.WIND
        E = ThaiLoadType.EARTHQUAKE
        H = ThaiLoadType.LATERAL_EARTH
        F = ThaiLoadType.FLUID
        T = ThaiLoadType.THERMAL
        S = ThaiLoadType.SETTLEMENT
        rows = [
            ("ASD-6.1",  {D: 1.0, L: 1.0}),
            ("ASD-6.2a", {D: 1.0, L: 0.75, W: 0.75}),
            ("ASD-6.2b", {D: 0.6, W: 1.0}),
            ("ASD-6.3a", {D: 1.0, E: 0.7}),
            ("ASD-6.3b", {D: 1.0, L: 0.75, E: 0.525}),
            ("ASD-6.3c", {D: 0.6, E: 0.7}),
            ("ASD-6.4",  {D: 1.0, L: 1.0, H: 1.0, F: 1.0,
                          T: 1.0, S: 1.0}),
        ]
        result = []
        for name, factors in rows:
            result.extend(self._expand_lateral(
                name, ThaiCombinationType.SERVICEABILITY_LIMIT_STATE,
                factors, "Ministry Regulation B.E. 2566 clause 6"
            ))
        return result

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
        if material_or_load not in self.safety_factors:
            raise KeyError(f"Unverified or unknown Thai safety factor: {material_or_load}")
        return self.safety_factors[material_or_load]
    
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
        """Signed internal-force effects are allowed; NaN/Inf are NEVER valid."""
        return (ThaiLoadType.DEAD in loads
                and all(isinstance(k, ThaiLoadType)
                        and isinstance(v, (float, int))
                        and math.isfinite(v) for k,v in loads.items()))

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