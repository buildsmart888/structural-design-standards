"""
ACI 318M-25 Load Combinations
============================

Implementation of load combinations and strength reduction factors
according to ACI 318M-25 and ASCE 7.

การคำนวณการรวมแรง และค่าลดกำลัง ตามมาตรฐาน ACI 318M-25
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ...utils.validation import StructuralValidator


class LoadType(Enum):
    """Load type classification"""
    DEAD = "dead"
    LIVE = "live"
    ROOF_LIVE = "roof_live"
    SNOW = "snow"
    WIND = "wind"
    EARTHQUAKE = "earthquake"
    RAIN = "rain"
    SOIL = "soil"
    FLUID = "fluid"
    THERMAL = "thermal"


class LoadDuration(Enum):
    """Load duration for service loads"""
    PERMANENT = "permanent"
    SUSTAINED = "sustained"
    TRANSIENT = "transient"
    IMPACT = "impact"


class CombinationType(Enum):
    """Load combination type"""
    STRENGTH = "strength"
    SERVICE = "service"
    DEFLECTION = "deflection"


@dataclass
class Load:
    """Individual load component"""
    name: str
    magnitude: float
    load_type: LoadType
    duration: LoadDuration = LoadDuration.PERMANENT
    direction: str = "vertical"  # "vertical", "horizontal_x", "horizontal_y"
    location: str = "uniform"  # "uniform", "concentrated", "distributed"
    
    def __post_init__(self):
        """Validate load parameters"""
        if self.magnitude < 0:
            raise ValueError(f"Load magnitude must be non-negative: {self.magnitude}")


@dataclass
class LoadCombination:
    """Load combination with factors"""
    name: str
    combination_type: CombinationType
    factors: Dict[LoadType, float] = field(default_factory=dict)
    description: str = ""
    
    def calculate_load_effect(self, loads: Dict[LoadType, float]) -> float:
        """
        Calculate total load effect for this combination
        
        Parameters:
        -----------
        loads : Dict[LoadType, float]
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
        for load_type, factor in self.factors.items():
            if factor != 0:
                if factor == 1.0:
                    terms.append(f"{load_type.value.upper()}")
                elif factor == -1.0:
                    terms.append(f"-{load_type.value.upper()}")
                else:
                    terms.append(f"{factor:.2g}{load_type.value.upper()}")
        
        return " + ".join(terms) if terms else "0"


class ACI318M25LoadCombinations:
    """
    ACI 318M-25 Load Combinations Implementation
    
    การรวมแรงตาม ACI 318M-25
    """
    
    def __init__(self):
        """Initialize load combinations"""
        self.validator = StructuralValidator()
        
        # Strength reduction factors (ACI 318M-25 Section 21.2)
        self.phi_factors = {
            'flexure_tension_controlled': 0.90,
            'flexure_compression_controlled_ties': 0.65,
            'flexure_compression_controlled_spiral': 0.75,
            'shear_and_torsion': 0.75,
            'compression_axial_ties': 0.65,
            'compression_axial_spiral': 0.75,
            'bearing_on_concrete': 0.65,            # Table 21.2.1(d)
            'post_tensioned_anchorage': 0.85,       # Table 21.2.1(h)
            # Table 21.2.1(g): one value for struts, ties, nodal zones and
            # bearing areas designed with the strut-and-tie model of Ch. 23
            'strut_and_tie_nodal_zones': 0.75,
            'strut_and_tie_struts': 0.75,
            'strut_and_tie_ties': 0.75
        }
        
        # Initialize standard combinations
        self._strength_combinations = self._create_strength_combinations()
        self._service_combinations = self._create_service_combinations()
    
    def _create_strength_combinations(self) -> List[LoadCombination]:
        """
        Create strength design load combinations per ASCE 7 and ACI 318M-25
        """
        combinations = []
        
        # Basic strength combinations (ASCE 7 Section 2.3.2)
        combinations.extend([
            LoadCombination(
                name="1.4D",
                combination_type=CombinationType.STRENGTH,
                factors={LoadType.DEAD: 1.4},
                description="Dead load only"
            ),
            
            LoadCombination(
                name="1.2D + 1.6L + (0.5Lr or 0.3S or 0.5R)",
                combination_type=CombinationType.STRENGTH,
                factors={
                    LoadType.DEAD: 1.2,
                    LoadType.LIVE: 1.6,
                    LoadType.ROOF_LIVE: 0.5,
                    LoadType.SNOW: 0.3,
                    LoadType.RAIN: 0.5
                },
                description="Dead + Live + (0.5Roof Live or 0.3Snow or 0.5Rain) - Eq. (5.3.1b)"
            ),
            
            LoadCombination(
                name="1.2D + (1.6Lr or 1.0S or 1.6R) + (1.0L or 0.5W)",
                combination_type=CombinationType.STRENGTH,
                factors={
                    LoadType.DEAD: 1.2,
                    LoadType.ROOF_LIVE: 1.6,
                    LoadType.SNOW: 1.0,
                    LoadType.RAIN: 1.6,
                    LoadType.LIVE: 1.0,
                    LoadType.WIND: 0.5
                },
                description="Dead + (1.6Roof Live or 1.0Snow or 1.6Rain) + (Live or 0.5Wind) - Eq. (5.3.1c)"
            ),
            
            LoadCombination(
                name="1.2D + 1.0W + 1.0L + (0.5Lr or 0.3S or 0.5R)",
                combination_type=CombinationType.STRENGTH,
                factors={
                    LoadType.DEAD: 1.2,
                    LoadType.WIND: 1.0,
                    LoadType.LIVE: 1.0,
                    LoadType.ROOF_LIVE: 0.5,
                    LoadType.SNOW: 0.3,
                    LoadType.RAIN: 0.5
                },
                description="Dead + Wind + Live + (0.5Roof Live or 0.3Snow or 0.5Rain) - Eq. (5.3.1d)"
            ),
            
            LoadCombination(
                name="1.2D + 1.0E + 1.0L + 0.15S",
                combination_type=CombinationType.STRENGTH,
                factors={
                    LoadType.DEAD: 1.2,
                    LoadType.EARTHQUAKE: 1.0,
                    LoadType.LIVE: 1.0,
                    LoadType.SNOW: 0.15
                },
                description="Dead + Earthquake + Live + 0.15Snow - Eq. (5.3.1e)"
            ),
            
            LoadCombination(
                name="0.9D + 1.0W",
                combination_type=CombinationType.STRENGTH,
                factors={
                    LoadType.DEAD: 0.9,
                    LoadType.WIND: 1.0
                },
                description="Reduced Dead + Wind (uplift/overturn check)"
            ),
            
            LoadCombination(
                name="0.9D + 1.0E",
                combination_type=CombinationType.STRENGTH,
                factors={
                    LoadType.DEAD: 0.9,
                    LoadType.EARTHQUAKE: 1.0
                },
                description="Reduced Dead + Earthquake (uplift/overturn check)"
            )
        ])
        
        return combinations
    
    def _create_service_combinations(self) -> List[LoadCombination]:
        """
        Create service load combinations for deflection and crack control
        """
        combinations = []
        
        combinations.extend([
            LoadCombination(
                name="D",
                combination_type=CombinationType.SERVICE,
                factors={LoadType.DEAD: 1.0},
                description="Dead load only"
            ),
            
            LoadCombination(
                name="D + L",
                combination_type=CombinationType.SERVICE,
                factors={
                    LoadType.DEAD: 1.0,
                    LoadType.LIVE: 1.0
                },
                description="Dead + Live load"
            ),
            
            LoadCombination(
                name="D + 0.75L + 0.75(Lr or S or R)",
                combination_type=CombinationType.SERVICE,
                factors={
                    LoadType.DEAD: 1.0,
                    LoadType.LIVE: 0.75,
                    LoadType.ROOF_LIVE: 0.75,
                    LoadType.SNOW: 0.75,
                    LoadType.RAIN: 0.75
                },
                description="Dead + 0.75Live + 0.75(Roof Live or Snow or Rain)"
            ),
            
            LoadCombination(
                name="D + 0.6W",
                combination_type=CombinationType.SERVICE,
                factors={
                    LoadType.DEAD: 1.0,
                    LoadType.WIND: 0.6
                },
                description="Dead + 0.6Wind"
            ),
            
            LoadCombination(
                name="D + 0.7E",
                combination_type=CombinationType.SERVICE,
                factors={
                    LoadType.DEAD: 1.0,
                    LoadType.EARTHQUAKE: 0.7
                },
                description="Dead + 0.7Earthquake"
            ),
            
            # Deflection combinations
            LoadCombination(
                name="D + L (Immediate)",
                combination_type=CombinationType.DEFLECTION,
                factors={
                    LoadType.DEAD: 1.0,
                    LoadType.LIVE: 1.0
                },
                description="Immediate deflection under full service load"
            ),
            
            LoadCombination(
                name="D (Sustained)",
                combination_type=CombinationType.DEFLECTION,
                factors={LoadType.DEAD: 1.0},
                description="Long-term deflection under sustained loads"
            )
        ])
        
        return combinations
    
    def get_strength_combinations(self) -> List[LoadCombination]:
        """Get all strength design load combinations"""
        return self._strength_combinations.copy()
    
    def get_service_combinations(self) -> List[LoadCombination]:
        """Get all service load combinations"""
        return self._service_combinations.copy()
    
    def get_deflection_combinations(self) -> List[LoadCombination]:
        """Get deflection-specific load combinations"""
        return [combo for combo in self._service_combinations 
                if combo.combination_type == CombinationType.DEFLECTION]
    
    def find_critical_combination(self, 
                                loads: Dict[LoadType, float],
                                combination_type: CombinationType = CombinationType.STRENGTH) -> Tuple[LoadCombination, float]:
        """
        Find the critical (maximum) load combination
        
        Parameters:
        -----------
        loads : Dict[LoadType, float]
            Applied loads by type
        combination_type : CombinationType
            Type of combinations to consider
            
        Returns:
        --------
        Tuple[LoadCombination, float]
            Critical combination and its load effect
        """
        if combination_type == CombinationType.STRENGTH:
            combinations = self._strength_combinations
        else:
            combinations = self._service_combinations
        
        max_effect = -float('inf')
        critical_combo = None
        
        for combo in combinations:
            effect = combo.calculate_load_effect(loads)
            if effect > max_effect:
                max_effect = effect
                critical_combo = combo
        
        return critical_combo, max_effect
    
    def calculate_all_combinations(self, 
                                 loads: Dict[LoadType, float],
                                 combination_type: CombinationType = CombinationType.STRENGTH) -> Dict[str, float]:
        """
        Calculate load effects for all combinations of specified type
        
        Parameters:
        -----------
        loads : Dict[LoadType, float]
            Applied loads by type
        combination_type : CombinationType
            Type of combinations to calculate
            
        Returns:
        --------
        Dict[str, float]
            Load effects for each combination
        """
        if combination_type == CombinationType.STRENGTH:
            combinations = self._strength_combinations
        else:
            combinations = self._service_combinations
        
        results = {}
        for combo in combinations:
            effect = combo.calculate_load_effect(loads)
            results[combo.name] = effect
        
        return results
    
    def get_strength_reduction_factor(self, failure_mode: str) -> float:
        """
        Get strength reduction factor (φ) for specified failure mode
        
        Parameters:
        -----------
        failure_mode : str
            Failure mode key (see phi_factors)
            
        Returns:
        --------
        float
            Strength reduction factor
        """
        if failure_mode in self.phi_factors:
            return self.phi_factors[failure_mode]
        else:
            raise ValueError(f"Unknown failure mode: {failure_mode}")
    
    def get_transition_phi_factor(self, 
                                net_tensile_strain: float,
                                reinforcement_type: str = "ties",
                                fy: float = 420.0) -> float:
        """
        Calculate φ factor for sections in transition zone
        ACI 318M-25 Section 21.2.2
        
        Parameters:
        -----------
        net_tensile_strain : float
            Net tensile strain in extreme tension steel
        reinforcement_type : str
            "ties" or "spiral"
        fy : float
            Specified yield strength of the reinforcement (MPa), used for
            epsilon_ty = fy / Es per 21.2.2.1. Grade 420 -> 0.0021.
            
        Returns:
        --------
        float
            Interpolated φ factor
        """
        # Strain limits per ACI 318M-25 21.2.2.1 and Table 21.2.2:
        # compression-controlled at epsilon_ty, tension-controlled at epsilon_ty + 0.003
        ES = 200000.0  # Modulus of elasticity of reinforcement steel (MPa)
        epsilon_ty = fy / ES
        epsilon_t_limit = epsilon_ty + 0.003  # Tension-controlled limit
        
        if net_tensile_strain >= epsilon_t_limit:
            # Tension-controlled
            return self.phi_factors['flexure_tension_controlled']
        elif net_tensile_strain <= epsilon_ty:
            # Compression-controlled
            if reinforcement_type == "spiral":
                return self.phi_factors['flexure_compression_controlled_spiral']
            else:
                return self.phi_factors['flexure_compression_controlled_ties']
        else:
            # Transition zone - linear interpolation
            if reinforcement_type == "spiral":
                phi_compression = self.phi_factors['flexure_compression_controlled_spiral']
            else:
                phi_compression = self.phi_factors['flexure_compression_controlled_ties']
            
            phi_tension = self.phi_factors['flexure_tension_controlled']
            
            # Linear interpolation
            ratio = (net_tensile_strain - epsilon_ty) / (epsilon_t_limit - epsilon_ty)
            return phi_compression + ratio * (phi_tension - phi_compression)
    
    def create_custom_combination(self, 
                                name: str,
                                factors: Dict[LoadType, float],
                                combination_type: CombinationType,
                                description: str = "") -> LoadCombination:
        """
        Create a custom load combination
        
        Parameters:
        -----------
        name : str
            Combination name
        factors : Dict[LoadType, float]
            Load factors by type
        combination_type : CombinationType
            Type of combination
        description : str
            Description of combination
            
        Returns:
        --------
        LoadCombination
            Custom load combination
        """
        return LoadCombination(
            name=name,
            combination_type=combination_type,
            factors=factors,
            description=description
        )
    
    def validate_loads(self, loads: Dict[LoadType, float]) -> bool:
        """
        Validate load dictionary
        
        Parameters:
        -----------
        loads : Dict[LoadType, float]
            Load values to validate
            
        Returns:
        --------
        bool
            True if all loads are valid
        """
        try:
            for load_type, value in loads.items():
                if not isinstance(load_type, LoadType):
                    raise ValueError(f"Invalid load type: {load_type}")
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Load value must be numeric: {value}")
                if value < 0:
                    raise ValueError(f"Load value cannot be negative: {value}")
            return True
        except ValueError as e:
            print(f"Load validation error: {e}")
            return False
    
    def get_combination_summary(self) -> Dict[str, List[str]]:
        """
        Get summary of all available combinations
        
        Returns:
        --------
        Dict[str, List[str]]
            Summary by combination type
        """
        summary = {
            'strength': [combo.name for combo in self._strength_combinations],
            'service': [combo.name for combo in self._service_combinations 
                       if combo.combination_type == CombinationType.SERVICE],
            'deflection': [combo.name for combo in self._service_combinations 
                          if combo.combination_type == CombinationType.DEFLECTION]
        }
        return summary
    
    def print_combination_table(self, combination_type: CombinationType = CombinationType.STRENGTH):
        """
        Print formatted table of load combinations
        
        Parameters:
        -----------
        combination_type : CombinationType
            Type of combinations to print
        """
        if combination_type == CombinationType.STRENGTH:
            combinations = self._strength_combinations
            title = "ACI 318M-25 Strength Design Load Combinations"
        else:
            combinations = [combo for combo in self._service_combinations 
                           if combo.combination_type == combination_type]
            title = f"ACI 318M-25 {combination_type.value.title()} Load Combinations"
        
        print(f"\n{title}")
        print("=" * len(title))
        
        for i, combo in enumerate(combinations, 1):
            print(f"{i:2d}. {combo.name}")
            print(f"    Equation: {combo.get_equation()}")
            if combo.description:
                print(f"    Description: {combo.description}")
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
            'strength_combinations': [
                {
                    'name': combo.name,
                    'factors': {load_type.value: factor for load_type, factor in combo.factors.items()},
                    'equation': combo.get_equation(),
                    'description': combo.description
                }
                for combo in self._strength_combinations
            ],
            'service_combinations': [
                {
                    'name': combo.name,
                    'factors': {load_type.value: factor for load_type, factor in combo.factors.items()},
                    'equation': combo.get_equation(),
                    'description': combo.description,
                    'type': combo.combination_type.value
                }
                for combo in self._service_combinations
            ],
            'phi_factors': self.phi_factors
        }