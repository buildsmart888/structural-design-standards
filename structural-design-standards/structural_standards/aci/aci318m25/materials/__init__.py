"""
ACI 318M-25 Material Models Package
===================================

Concrete and steel material models according to ACI 318M-25 (Metric).

แพ็กรวมโมเดลวัสดุคอนกรีตและเหล็กตาม ACI 318M-25 (หน่วยเมตริก)
"""

from .concrete import ACI318M25Concrete

from .steel import (
    ACI318M25Steel,
    ACI318M25ReinforcementSteel,
    create_aci_reinforcement_database
)

__version__ = '1.0.0'
__standard__ = 'ACI 318M-25'

__all__ = [
    'ACI318M25Concrete',
    'ACI318M25Steel',
    'ACI318M25ReinforcementSteel',
    'create_aci_reinforcement_database',
]
