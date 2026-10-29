"""
Thai Ministry Regulation B.E. 2566 Material Models Package
==========================================================

Concrete and steel material models according to the Thai Ministry
Regulation on Structural Building Design B.E. 2566 (กฎกระทรวง พ.ศ. 2566).

แพ็กรวมโมเดลวัสดุคอนกรีตและเหล็กตามกฎกระทรวง พ.ศ. 2566
"""

from .concrete import (
    ThaiConcrete,
    ThaiConcreteGrade,
    ThaiConcreteProperties,
    create_fc180,
    create_fc210,
    create_fc240,
    create_fc280,
    create_fc350,
    mpa_to_ksc,
    ksc_to_mpa
)

from .steel import (
    ThaiSteel,
    ThaiSteelGrade,
    ThaiRebarDesignation,
    ThaiSteelProperties,
    ThaiRebarProperties,
    ThaiReinforcementSteel,
    create_sd40,
    create_sd50,
    create_sr24,
    create_db20_sd40,
    create_db25_sd40,
    create_rb6_sr24
)

__version__ = '1.0.0'
__standard__ = 'Thai Ministry Regulation B.E. 2566'

__all__ = [
    # Concrete
    'ThaiConcrete',
    'ThaiConcreteGrade',
    'ThaiConcreteProperties',
    'create_fc180',
    'create_fc210',
    'create_fc240',
    'create_fc280',
    'create_fc350',
    'mpa_to_ksc',
    'ksc_to_mpa',
    # Steel
    'ThaiSteel',
    'ThaiSteelGrade',
    'ThaiRebarDesignation',
    'ThaiSteelProperties',
    'ThaiRebarProperties',
    'ThaiReinforcementSteel',
    'create_sd40',
    'create_sd50',
    'create_sr24',
    'create_db20_sd40',
    'create_db25_sd40',
    'create_rb6_sr24',
]
