"""
ACI 318M-25 Structural Members Package
=====================================

Complete implementation of structural member design according to ACI 318M-25.
Includes beams, columns, slabs, walls, footings, and diaphragms.

แพ็คเกจการออกแบบสมาชิกโครงสร้างตาม ACI 318M-25
รวมคาน เสา พื้น กำแพง ฐานราก และแผ่นรับแรงในระนาบ
"""

# Import all member design classes
from .beam_design import (
    ACI318M25BeamDesign,
    BeamGeometry,
    BeamLoads,
    BeamReinforcement,
    BeamType,
    LoadType
)

from .column_design import (
    ACI318M25ColumnDesign,
    ColumnGeometry,
    ColumnLoads,
    ColumnReinforcement,
    ColumnType,
    ReinforcementPattern
)

from .slab_design import (
    ACI318M25SlabDesign,
    SlabGeometry,
    SlabLoads,
    SlabReinforcement,
    SlabType,
    SupportCondition
)

from .wall_design import (
    ACI318M25WallDesign,
    WallGeometry,
    WallLoads,
    WallReinforcement,
    WallType,
    WallBoundaryCondition
)

from .footing_design import (
    ACI318M25FootingDesign,
    FootingGeometry,
    ColumnLoads as FootingColumnLoads,
    SoilProperties,
    FootingReinforcement,
    FootingType,
    SoilCondition
)

from .diaphragm_design import (
    ACI318M25DiaphragmDesign,
    DiaphragmGeometry,
    DiaphragmLoads,
    DiaphragmReinforcement,
    DiaphragmType,
    DiaphragmBehavior,
    LoadingType
)

__version__ = '1.0.0'
__author__ = 'ACI 318M-25 Implementation Team'

# All available design classes
__all__ = [
    # Beam Design
    'ACI318M25BeamDesign',
    'BeamGeometry',
    'BeamLoads', 
    'BeamReinforcement',
    'BeamType',
    'LoadType',
    
    # Column Design
    'ACI318M25ColumnDesign',
    'ColumnGeometry',
    'ColumnLoads',
    'ColumnReinforcement',
    'ColumnType',
    'ReinforcementPattern',
    
    # Slab Design
    'ACI318M25SlabDesign',
    'SlabGeometry',
    'SlabLoads',
    'SlabReinforcement',
    'SlabType',
    'SupportCondition',
    
    # Wall Design
    'ACI318M25WallDesign',
    'WallGeometry',
    'WallLoads',
    'WallReinforcement',
    'WallType',
    'WallBoundaryCondition',

    
    # Footing Design
    'ACI318M25FootingDesign',
    'FootingGeometry',
    'FootingColumnLoads',
    'SoilProperties',
    'FootingReinforcement',
    'FootingType',
    'SoilCondition',
    
    # Diaphragm Design
    'ACI318M25DiaphragmDesign',
    'DiaphragmGeometry',
    'DiaphragmLoads',
    'DiaphragmReinforcement',
    'DiaphragmType',
    'DiaphragmBehavior',
    'LoadingType'
]


def get_available_members():
    """
    Get list of available structural member design classes
    
    Returns:
    --------
    dict
        Dictionary of member types and their design classes
    """
    return {
        'beam': ACI318M25BeamDesign,
        'column': ACI318M25ColumnDesign,
        'slab': ACI318M25SlabDesign,
        'wall': ACI318M25WallDesign,
        'footing': ACI318M25FootingDesign,
        'diaphragm': ACI318M25DiaphragmDesign
    }


def create_member_designer(member_type: str, concrete, reinforcement):
    """
    Factory function to create member designer instances
    
    Parameters:
    -----------
    member_type : str
        Type of structural member ('beam', 'column', 'slab', 'wall', 'footing', 'diaphragm')
    concrete : ACI318M25Concrete
        Concrete material
    reinforcement : ACI318M25ReinforcementSteel
        Reinforcement steel material
        
    Returns:
    --------
    MemberDesign
        Appropriate member design instance
        
    Raises:
    -------
    ValueError
        If member_type is not supported
    """
    available_members = get_available_members()
    
    if member_type.lower() not in available_members:
        supported_types = ', '.join(available_members.keys())
        raise ValueError(f"Unsupported member type '{member_type}'. "
                        f"Supported types: {supported_types}")
    
    design_class = available_members[member_type.lower()]
    return design_class(concrete, reinforcement)


def validate_member_imports():
    """
    Validate that all member design modules can be imported successfully
    
    Returns:
    --------
    dict
        Dictionary with import status for each module
    """
    import_status = {}
    
    # Test each member type
    member_modules = {
        'beam': 'beam_design',
        'column': 'column_design', 
        'slab': 'slab_design',
        'wall': 'wall_design',
        'footing': 'footing_design',
        'diaphragm': 'diaphragm_design'
    }
    
    for member_type, module_name in member_modules.items():
        try:
            # Try to import the module
            exec(f'from . import {module_name}')
            import_status[member_type] = {
                'status': 'success',
                'module': module_name,
                'error': None
            }
        except Exception as e:
            import_status[member_type] = {
                'status': 'failed',
                'module': module_name,
                'error': str(e)
            }
    
    return import_status


def get_member_capabilities():
    """
    Get capabilities summary for each member type
    
    Returns:
    --------
    dict
        Dictionary describing capabilities of each member type
    """
    return {
        'beam': {
            'description': 'Flexural, shear, and deflection design for beams',
            'design_methods': ['flexural_reinforcement', 'shear_reinforcement', 'deflection_check'],
            'load_types': ['distributed', 'concentrated', 'moments'],
            'support_types': ['simply_supported', 'continuous', 'cantilever'],
            'code_sections': ['ACI 318M-25 Sections 7, 8, 9, 24']
        },
        'column': {
            'description': 'Axial-moment interaction design for columns',
            'design_methods': ['axial_reinforcement', 'interaction_diagram', 'slenderness_effects'],
            'load_types': ['axial', 'moments', 'combined'],
            'cross_sections': ['rectangular', 'circular'],
            'code_sections': ['ACI 318M-25 Sections 6, 10, 22']
        },
        'slab': {
            'description': 'One-way and two-way slab design including punching shear',
            'design_methods': ['flexural_reinforcement', 'punching_shear', 'deflection_check'],
            'slab_types': ['one_way', 'two_way', 'flat_slab'],
            'support_conditions': ['simply_supported', 'fixed', 'continuous'],
            'code_sections': ['ACI 318M-25 Sections 7, 8, 22']
        },
        'wall': {
            'description': 'Bearing walls, shear walls, and out-of-plane design',
            'design_methods': ['axial_design', 'flexural_design', 'shear_design'],
            'wall_types': ['bearing', 'shear', 'non_bearing'],
            'boundary_conditions': ['pinned', 'fixed', 'cantilever'],
            'code_sections': ['ACI 318M-25 Section 14']
        },
        'footing': {
            'description': 'Isolated, combined, and mat foundation design',
            'design_methods': ['bearing_pressure', 'flexural_design', 'punching_shear'],
            'footing_types': ['isolated', 'combined', 'strap', 'mat'],
            'soil_conditions': ['allowable_stress', 'ultimate_bearing'],
            'code_sections': ['ACI 318M-25 Section 13']
        },
        'diaphragm': {
            'description': 'In-plane shear design for concrete diaphragms',
            'design_methods': ['in_plane_shear', 'chord_design', 'collector_design'],
            'diaphragm_types': ['cast_in_place', 'precast', 'composite'],
            'behavior_types': ['flexible', 'rigid', 'semi_rigid'],
            'code_sections': ['ACI 318M-25 Section 12']
        }
    }


# Module information
