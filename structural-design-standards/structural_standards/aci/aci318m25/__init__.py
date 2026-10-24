"""
ACI 318M-25 Building Code Requirements for Structural Concrete
=============================================================

Complete implementation of ACI 318M-25 (Metric) standard for:
- Material properties and behavior models
- Member design (beams, columns, slabs, walls, footings)
- Load combinations and strength reduction factors
- Serviceability requirements and detailing

การใช้งานมาตรฐาน ACI 318M-25 (เมตริก) สำหรับ:
- คุณสมบัติและพฤติกรรมของวัสดุ
- การออกแบบส่วนประกอบ (คาน เสา พื้น ผนัง ฐานราก)
- การรวมแรงและค่าลดกำลัง
- ข้อกำหนดการใช้งานและรายละเอียดการเสริม
"""

# Material imports
from .materials.concrete import ACI318M25Concrete
from .materials.steel import (
    ACI318M25Steel,
    ACI318M25ReinforcementSteel
)

# Member design imports
from .members.slab_design import (
    ACI318M25SlabDesign,
    SlabType,
    SupportCondition,
    SlabGeometry,
    SlabLoads,
    SlabReinforcement
)

from .members.beam_design import (
    ACI318M25BeamDesign,
    BeamType,
    LoadType as BeamLoadType,
    BeamGeometry,
    BeamLoads,
    BeamReinforcement
)

from .members.column_design import (
    ACI318M25ColumnDesign,
    ColumnType,
    ReinforcementPattern,
    ColumnGeometry,
    ColumnLoads,
    ColumnReinforcement
)

# Load combinations
from .load_combinations import (
    ACI318M25LoadCombinations,
    LoadType as CombinationLoadType,
    LoadDuration,
    CombinationType,
    Load,
    LoadCombination
)

# Version info
__version__ = "1.0.0"
__standard__ = "ACI 318M-25"
__metric_units__ = True

# Package metadata
__all__ = [
    # Materials
    'ACI318M25Concrete',
    'ACI318M25Steel',
    'ACI318M25ReinforcementSteel',
    
    # Member Design
    'ACI318M25SlabDesign',
    'ACI318M25BeamDesign',
    'ACI318M25ColumnDesign',
    
    # Geometry and Loading
    'SlabGeometry',
    'SlabLoads',
    'SlabReinforcement',
    'BeamGeometry',
    'BeamLoads',
    'BeamReinforcement',
    'ColumnGeometry',
    'ColumnLoads',
    'ColumnReinforcement',
    
    # Enums
    'SlabType',
    'SupportCondition',
    'BeamType',
    'BeamLoadType',
    'ColumnType',
    'ReinforcementPattern',
    
    # Load Combinations
    'ACI318M25LoadCombinations',
    'CombinationLoadType',
    'LoadDuration',
    'CombinationType',
    'Load',
    'LoadCombination',
    
    # Package metadata
    '__version__',
    '__standard__',
    '__metric_units__'
]

# Create convenience functions for common operations
def create_concrete(fc_prime: float, unit_weight: float = 24.0) -> ACI318M25Concrete:
    """
    Create ACI 318M-25 concrete with specified strength
    
    Parameters:
    -----------
    fc_prime : float
        Specified compressive strength (MPa)
    unit_weight : float
        Unit weight (kN/m³), default 24.0
        
    Returns:
    --------
    ACI318M25Concrete
        Concrete material object
    """
    return ACI318M25Concrete(fc_prime=fc_prime, unit_weight=unit_weight)

def create_reinforcement(bar_designation: str, fy: float = 420.0) -> ACI318M25ReinforcementSteel:
    """
    Create ACI 318M-25 reinforcement steel
    
    Parameters:
    -----------
    bar_designation : str
        Bar designation (e.g., "DB20", "#8")
    fy : float
        Yield strength (MPa), default 420.0
        
    Returns:
    --------
    ACI318M25ReinforcementSteel
        Reinforcement steel object
    """
    return ACI318M25ReinforcementSteel(bar_designation=bar_designation)

# def create_load_combinations() -> ACI318M25LoadCombinations:
#     """
#     Create ACI 318M-25 load combinations object
#     
#     Returns:
#     --------
#     ACI318M25LoadCombinations
#         Load combinations calculator
#     """
#     return ACI318M25LoadCombinations()

# Standard material combinations
def get_standard_concrete_grades() -> dict:
    """Get dictionary of standard concrete grades with their properties"""
    return {
        'fc21': create_concrete(21.0),
        'fc28': create_concrete(28.0),
        'fc35': create_concrete(35.0),
        'fc42': create_concrete(42.0),
        'fc50': create_concrete(50.0),
        'fc60': create_concrete(60.0)
    }

def get_standard_reinforcement_grades() -> dict:
    """Get dictionary of standard reinforcement grades"""
    return {
        'grade420': create_reinforcement("20M"),
        'grade520': create_reinforcement("25M"),
        'grade620': create_reinforcement("30M")
    }

# Usage examples
def example_beam_design():
    """Example beam design workflow"""
    # Create materials
    concrete = create_concrete(28.0)  # 28 MPa concrete
    steel = create_reinforcement("20M")  # 20M steel
    
    # Create beam designer
    beam_designer = ACI318M25BeamDesign(concrete, steel)
    
    # Define geometry
    geometry = BeamGeometry(
        width=300.0,  # mm
        height=500.0,  # mm
        effective_depth=450.0,  # mm
        span_length=6000.0  # mm
    )
    
    # Design for moment
    result = beam_designer.design_flexural_reinforcement(
        geometry=geometry,
        moment_ultimate=150.0  # kN⋅m
    )
    
    return result

def example_column_design():
    """Example column design workflow"""
    # Create materials
    concrete = create_concrete(28.0)  # 28 MPa concrete
    steel = create_reinforcement("25M")  # 25M steel
    
    # Create column designer
    column_designer = ACI318M25ColumnDesign(concrete, steel)
    
    # Define geometry
    geometry = ColumnGeometry(
        width=400.0,  # mm
        depth=400.0,  # mm
        length=3000.0,  # mm
        cross_section="rectangular"
    )
    
    # Define loads
    loads = ColumnLoads(
        axial_dead=500.0,  # kN
        axial_live=300.0,  # kN
        moment_x_dead=50.0,  # kN⋅m
        moment_x_live=30.0  # kN⋅m
    )
    
    # Design reinforcement
    result = column_designer.design_axial_reinforcement(
        geometry=geometry,
        loads=loads,
        reinforcement_ratio=0.02
    )
    
    return result

# def example_load_combinations():
#     """Example load combinations usage"""
#     # Create load combinations
#     load_combos = create_load_combinations()
#     
#     # Define loads
#     loads = {
#         LoadType.DEAD: 10.0,  # kN/m²
#         LoadType.LIVE: 5.0,   # kN/m²
#         LoadType.WIND: 2.0    # kN/m²
#     }
#     
#     # Find critical combination
#     critical_combo, max_load = load_combos.find_critical_combination(loads)
#     
#     return critical_combo, max_load

# Package information
def get_package_info():
    """Get package information"""
    return {
        'name': 'ACI 318M-25 Implementation',
        'version': __version__,
        'standard': __standard__,
        'units': 'SI (Metric)',
        'modules': [
            'Materials (Concrete, Steel, Reinforcement)',
            'Member Design (Slabs, Beams, Columns)',
            'Load Combinations',
            'Serviceability Checks'
        ],
        'capabilities': [
            'Flexural design and analysis',
            'Shear design and analysis',
            'Axial-moment interaction',
            'Deflection calculations',
            'Crack control',
            'Development length',
            'Detailing requirements'
        ]
    }