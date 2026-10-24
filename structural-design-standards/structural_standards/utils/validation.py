"""
Input Validation Utilities
==========================

Enhanced validation system for structural design parameters.
Based on the existing twoWaySlab validation with improvements.

ระบบตรวจสอบข้อมูลนำเข้าที่ปรับปรุงแล้วสำหรับพารามิเตอร์การออกแบบโครงสร้าง
พัฒนาจากระบบ validation ของ twoWaySlab ที่มีอยู่
"""

import math
import re
from typing import Any, List, Optional, Union, Tuple
from enum import Enum

class ValidationError(ValueError):
    """Custom exception for validation errors"""
    pass

class ValidationLevel(Enum):
    """Validation strictness levels"""
    STRICT = "strict"      # Fail on any violation
    WARNING = "warning"    # Allow with warnings
    PERMISSIVE = "permissive"  # Allow most values

class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, 
                 is_valid: bool, 
                 value: Any = None,
                 error_message: str = "",
                 warning_message: str = "",
                 code_reference: str = ""):
        self.is_valid = is_valid
        self.value = value
        self.error_message = error_message
        self.warning_message = warning_message
        self.code_reference = code_reference
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def __str__(self) -> str:
        if self.is_valid:
            return f"Valid: {self.value}"
        else:
            return f"Invalid: {self.error_message}"

# Basic validation functions
def validate_positive(value: Union[int, float], 
                     name: str = "value",
                     allow_zero: bool = False) -> float:
    """
    Validate that a value is positive
    
    Parameters:
    -----------
    value : Union[int, float]
        Value to validate
    name : str
        Parameter name for error messages
    allow_zero : bool
        Whether to allow zero values
        
    Returns:
    --------
    float
        Validated value
        
    Raises:
    -------
    ValidationError
        If value is not positive
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")
    
    if math.isnan(value):
        raise ValidationError(f"{name} cannot be NaN")
    
    if math.isinf(value):
        raise ValidationError(f"{name} cannot be infinite")
    
    if allow_zero:
        if value < 0:
            raise ValidationError(f"{name} must be >= 0, got {value}")
    else:
        if value <= 0:
            raise ValidationError(f"{name} must be > 0, got {value}")
    
    return float(value)

def validate_range(value: Union[int, float],
                  min_val: Optional[float] = None,
                  max_val: Optional[float] = None,
                  name: str = "value") -> float:
    """
    Validate that a value is within a specified range
    
    Parameters:
    -----------
    value : Union[int, float]
        Value to validate
    min_val : float, optional
        Minimum allowed value
    max_val : float, optional
        Maximum allowed value
    name : str
        Parameter name for error messages
        
    Returns:
    --------
    float
        Validated value
        
    Raises:
    -------
    ValidationError
        If value is outside range
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")
    
    if math.isnan(value):
        raise ValidationError(f"{name} cannot be NaN")
    
    if math.isinf(value):
        raise ValidationError(f"{name} cannot be infinite")
    
    if min_val is not None and value < min_val:
        raise ValidationError(f"{name} must be >= {min_val}, got {value}")
    
    if max_val is not None and value > max_val:
        raise ValidationError(f"{name} must be <= {max_val}, got {value}")
    
    return float(value)

def validate_type(value: Any, 
                 expected_type: type,
                 name: str = "value") -> Any:
    """
    Validate that a value is of expected type
    
    Parameters:
    -----------
    value : Any
        Value to validate
    expected_type : type
        Expected type
    name : str
        Parameter name for error messages
        
    Returns:
    --------
    Any
        Validated value
        
    Raises:
    -------
    ValidationError
        If value is not of expected type
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"{name} must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
    
    return value

def validate_in_list(value: Any,
                    allowed_values: List[Any],
                    name: str = "value") -> Any:
    """
    Validate that a value is in a list of allowed values
    
    Parameters:
    -----------
    value : Any
        Value to validate
    allowed_values : List[Any]
        List of allowed values
    name : str
        Parameter name for error messages
        
    Returns:
    --------
    Any
        Validated value
        
    Raises:
    -------
    ValidationError
        If value is not in allowed list
    """
    if value not in allowed_values:
        raise ValidationError(
            f"{name} must be one of {allowed_values}, got {value}"
        )
    
    return value

class StructuralValidator:
    """
    Enhanced validator for structural engineering parameters
    
    ตัวตรวจสอบที่ปรับปรุงแล้วสำหรับพารามิเตอร์วิศวกรรมโครงสร้าง
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.WARNING):
        """
        Initialize validator
        
        Parameters:
        -----------
        validation_level : ValidationLevel
            Level of validation strictness
        """
        self.validation_level = validation_level
        
        # Standard ranges for structural parameters
        self.ranges = {
            # Dimensions (meters)
            'slab_length': (0.5, 50.0),
            'beam_span': (1.0, 30.0),
            'column_height': (2.0, 20.0),
            
            # Thickness/Depth (mm)
            'slab_thickness': (50, 1000),
            'beam_depth': (150, 2000),
            'beam_width': (100, 1000),
            'column_dimension': (200, 2000),
            'wall_thickness': (100, 500),
            
            # Material properties
            'concrete_strength': (10, 150),   # MPa
            'steel_strength': (200, 800),     # MPa
            'unit_weight_concrete': (15, 35), # kN/m³
            'unit_weight_steel': (70, 85),    # kN/m³
            
            # Loads (kN/m² or kN/m)
            'dead_load': (0.5, 50.0),
            'live_load': (0.5, 25.0),
            'wind_load': (0.1, 10.0),
            'seismic_load': (0.1, 15.0),
            
            # Design parameters
            'cover': (10, 100),               # mm
            'bar_spacing': (50, 500),         # mm
            'creep_factor': (1.0, 5.0),
            'safety_factor': (1.0, 3.0),
            
            # Ratios and factors
            'deflection_limit': (150, 500),   # L/x
            'span_depth_ratio': (10, 30),
            'reinforcement_ratio': (0.001, 0.05),
        }
        
        # Standard material grades
        self.concrete_grades = {
            'aci': ['FC14', 'FC17', 'FC21', 'FC28', 'FC35', 'FC42', 'FC50', 'FC70', 'FC100'],
            'thai': ['Fc180', 'Fc210', 'Fc240', 'Fc280', 'Fc350'],
            'japanese': ['Fc15', 'Fc18', 'Fc21', 'Fc24', 'Fc27', 'Fc30', 'Fc36', 'Fc42']
        }
        
        self.steel_grades = {
            'aci': ['GRADE280', 'GRADE420', 'GRADE520'],
            'thai': ['SR24', 'SD40', 'SD50'],
            'japanese': ['SD295A', 'SD345', 'SD390', 'SD490']
        }
        
        self.rebar_designations = {
            'aci': ['10M', '15M', '20M', '25M', '30M', '35M', '45M', '55M'],
            'thai': ['DB10', 'DB12', 'DB20', 'DB25', 'DB32', 'DB36', 'DB40', 'RB6', 'RB9'],
            'japanese': ['D10', 'D13', 'D16', 'D19', 'D22', 'D25', 'D29', 'D32', 'D35', 'D38', 'D41']
        }
    
    def validate_dimension(self, 
                          value: Union[str, float],
                          dimension_type: str,
                          name: str = "") -> ValidationResult:
        """
        Validate structural dimensions
        
        Parameters:
        -----------
        value : Union[str, float]
            Dimension value to validate
        dimension_type : str
            Type of dimension ('slab_length', 'beam_depth', etc.)
        name : str
            Custom name for error messages
            
        Returns:
        --------
        ValidationResult
            Validation result
        """
        if name == "":
            name = dimension_type.replace('_', ' ').title()
        
        # Convert string to float if needed
        try:
            if isinstance(value, str):
                float_value = float(value.strip())
            else:
                float_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult(
                False, None, 
                f"{name} must be a valid number, got '{value}'"
            )
        
        # Check for special values
        if math.isnan(float_value):
            return ValidationResult(False, None, f"{name} cannot be NaN")
        
        if math.isinf(float_value):
            return ValidationResult(False, None, f"{name} cannot be infinite")
        
        # Get range for this dimension type
        if dimension_type not in self.ranges:
            return ValidationResult(False, None, f"Unknown dimension type: {dimension_type}")
        
        min_val, max_val = self.ranges[dimension_type]
        
        # Check range
        if float_value < min_val:
            return ValidationResult(
                False, None,
                f"{name} must be >= {min_val}, got {float_value}"
            )
        
        if float_value > max_val:
            error_msg = f"{name} must be <= {max_val}, got {float_value}"
            if self.validation_level == ValidationLevel.PERMISSIVE:
                return ValidationResult(
                    True, float_value, "", 
                    f"Large {name.lower()} ({float_value}) - verify if realistic"
                )
            else:
                return ValidationResult(False, None, error_msg)
        
        # Generate warnings for unusual values
        warning = ""
        if dimension_type == 'slab_thickness':
            if float_value < 100:
                warning = f"Thin slab ({float_value}mm) - check deflection limits"
            elif float_value > 400:
                warning = f"Thick slab ({float_value}mm) - verify economic feasibility"
        
        elif dimension_type in ['slab_length', 'beam_span']:
            if float_value > 12.0:
                warning = f"Long span ({float_value}m) - may require special analysis"
        
        return ValidationResult(True, float_value, "", warning)
    
    def validate_material_grade(self,
                               grade: str,
                               material_type: str,
                               standard: str = 'aci') -> ValidationResult:
        """
        Validate material grade designation
        
        Parameters:
        -----------
        grade : str
            Material grade designation
        material_type : str
            'concrete' or 'steel' or 'rebar'
        standard : str
            Design standard ('aci', 'thai', 'japanese')
            
        Returns:
        --------
        ValidationResult
            Validation result
        """
        if not isinstance(grade, str):
            return ValidationResult(
                False, None,
                f"Grade must be a string, got {type(grade).__name__}"
            )
        
        grade = grade.strip()
        if not grade:
            return ValidationResult(False, None, "Grade cannot be empty")
        
        # Get valid grades for this material type and standard
        if material_type == 'concrete':
            valid_grades = self.concrete_grades.get(standard, [])
        elif material_type == 'steel':
            valid_grades = self.steel_grades.get(standard, [])
        elif material_type == 'rebar':
            valid_grades = self.rebar_designations.get(standard, [])
        else:
            return ValidationResult(
                False, None,
                f"Unknown material type: {material_type}"
            )
        
        if not valid_grades:
            return ValidationResult(
                False, None,
                f"No grades defined for {material_type} in {standard} standard"
            )
        
        # Case-insensitive check
        grade_upper = grade.upper()
        valid_grades_upper = [g.upper() for g in valid_grades]
        
        if grade_upper in valid_grades_upper:
            # Return the correctly formatted grade
            correct_index = valid_grades_upper.index(grade_upper)
            return ValidationResult(True, valid_grades[correct_index])
        
        # Generate suggestions for similar grades
        suggestions = []
        for valid_grade in valid_grades:
            if grade_upper in valid_grade.upper() or valid_grade.upper() in grade_upper:
                suggestions.append(valid_grade)
        
        error_msg = f"Invalid {material_type} grade '{grade}' for {standard} standard."
        if suggestions:
            error_msg += f" Did you mean: {', '.join(suggestions)}?"
        else:
            error_msg += f" Valid grades: {', '.join(valid_grades[:5])}{'...' if len(valid_grades) > 5 else ''}"
        
        return ValidationResult(False, None, error_msg)
    
    def validate_load_combination(self,
                                loads: dict,
                                combination_type: str = 'ultimate') -> ValidationResult:
        """
        Validate load combination inputs
        
        Parameters:
        -----------
        loads : dict
            Dictionary of load values
        combination_type : str
            'ultimate' or 'service'
            
        Returns:
        --------
        ValidationResult
            Validation result
        """
        if not isinstance(loads, dict):
            return ValidationResult(
                False, None,
                f"Loads must be a dictionary, got {type(loads).__name__}"
            )
        
        if not loads:
            return ValidationResult(False, None, "Load dictionary cannot be empty")
        
        valid_load_types = ['dead', 'live', 'wind', 'seismic', 'snow', 'thermal']
        validated_loads = {}
        warnings = []
        
        for load_type, value in loads.items():
            # Validate load type
            if load_type.lower() not in valid_load_types:
                return ValidationResult(
                    False, None,
                    f"Invalid load type '{load_type}'. Valid types: {valid_load_types}"
                )
            
            # Validate load value
            try:
                float_value = float(value)
            except (ValueError, TypeError):
                return ValidationResult(
                    False, None,
                    f"Load value for '{load_type}' must be a number, got '{value}'"
                )
            
            if float_value < 0:
                return ValidationResult(
                    False, None,
                    f"Load value for '{load_type}' cannot be negative, got {float_value}"
                )
            
            # Check realistic ranges
            load_key = f"{load_type.lower()}_load"
            if load_key in self.ranges:
                min_val, max_val = self.ranges[load_key]
                if float_value > max_val:
                    warnings.append(f"High {load_type} load ({float_value} kN/m²)")
            
            validated_loads[load_type.lower()] = float_value
        
        warning_msg = "; ".join(warnings) if warnings else ""
        return ValidationResult(True, validated_loads, "", warning_msg)
    
    def validate_geometry_consistency(self,
                                    width: float,
                                    depth: float,
                                    effective_depth: float,
                                    cover: float) -> ValidationResult:
        """
        Validate geometric consistency
        
        Parameters:
        -----------
        width : float
            Member width
        depth : float
            Total depth
        effective_depth : float
            Effective depth
        cover : float
            Concrete cover
            
        Returns:
        --------
        ValidationResult
            Validation result
        """
        # Check basic geometric relationship: d = h - cover - bar_diameter/2
        # Assuming typical bar diameter of 20mm
        typical_bar_radius = 10.0  # mm
        expected_d = depth - cover - typical_bar_radius
        
        tolerance = 5.0  # mm tolerance
        
        if abs(effective_depth - expected_d) > tolerance:
            return ValidationResult(
                False, None,
                f"Geometric inconsistency: effective depth ({effective_depth}mm) "
                f"should be approximately {expected_d:.1f}mm "
                f"(total depth - cover - bar radius)"
            )
        
        # Check if cover is reasonable
        if cover < 15:
            warning = f"Small cover ({cover}mm) - check durability requirements"
        elif cover > 75:
            warning = f"Large cover ({cover}mm) - verify if necessary"
        else:
            warning = ""
        
        return ValidationResult(True, {
            'width': width,
            'depth': depth, 
            'effective_depth': effective_depth,
            'cover': cover
        }, "", warning)