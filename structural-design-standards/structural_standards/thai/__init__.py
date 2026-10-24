"""
Thai Building Code Standards Package
====================================

Implementation of Thai building code standards including:
- Ministry Regulation B.E. 2566 (2023)
- Thai Industrial Standards (TIS)
- Thai wind and seismic loads

การใช้งานมาตรฐานการออกแบบโครงสร้างของไทย รวมถึง:
- กฎกระทรวง พ.ศ. 2566
- มาตรฐานอุตสาหกรรมไทย (มอก.)
- แรงลมและแรงแผ่นดินไหวไทย
"""

from . import ministry_2566

__version__ = '1.0.0'
__author__ = 'Thai Structural Design Standards Team'

__all__ = [
    'ministry_2566'  # Thai Ministry Regulation B.E. 2566
]

def get_thai_standards():
    """Get available Thai standards"""
    return {
        'ministry_2566': 'Thai Ministry Regulation B.E. 2566 (2023)',
        'description': 'Comprehensive Thai building code implementation'
    }

