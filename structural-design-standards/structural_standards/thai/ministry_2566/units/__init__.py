"""
Thai Unit Systems Package
========================

Thai unit conversion systems including:
- ksc ↔ MPa conversions for concrete and steel
- Traditional Thai units (rai, wa, sen, etc.)
- Engineering units commonly used in Thailand
- International metric conversions

ระบบการแปลงหน่วยไทย รวมถึง:
- การแปลง ksc ↔ MPa สำหรับคอนกรีตและเหล็ก
- หน่วยไทยดั้งเดิม (ไร่, วา, เส้น, ฯลฯ)
- หน่วยวิศวกรรมที่ใช้ในประเทศไทย
- การแปลงเมตริกสากล
"""

from .thai_units import (
    ThaiUnitConverter,
    ThaiPressureUnit,
    ThaiLengthUnit,
    ThaiAreaUnit,
    ThaiWeightUnit,
    ksc_to_mpa,
    mpa_to_ksc,
    convert_thai_length,
    convert_thai_area,
    convert_thai_weight
)

__version__ = '1.0.0'
__author__ = 'Thai Structural Design Standards Team'

__all__ = [
    'ThaiUnitConverter',
    'ThaiPressureUnit',
    'ThaiLengthUnit', 
    'ThaiAreaUnit',
    'ThaiWeightUnit',
    'ksc_to_mpa',
    'mpa_to_ksc',
    'convert_thai_length',
    'convert_thai_area', 
    'convert_thai_weight'
]

# Quick conversion factors
KSC_TO_MPA = 9.80665 / 100  # 1 ksc = 0.0980665 MPa
MPA_TO_KSC = 100 / 9.80665  # 1 MPa = 10.197 ksc

