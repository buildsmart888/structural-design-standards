"""
Structural Design Standards Package
===================================

A comprehensive library for structural design standards implementation.

โปรแกรมมาตรฐานการออกแบบโครงสร้าง
ห้องสมุดที่ครอบคลุมสำหรับการดำเนินการตามมาตรฐานการออกแบบโครงสร้าง
"""

__version__ = '1.0.0'
__author__ = 'Structural Design Standards Team'

# Available standard modules
__all__ = [
    'aci',       # ACI standards
    'thai',      # Thai standards
    'base',      # Base classes
    'utils'      # Utilities
]

def get_version():
    """Get package version"""
    return __version__

def get_available_standards():
    """Get list of available design standards"""
    return {
        'aci': 'American Concrete Institute Standards',
        'thai': 'Thai Building Code Standards'
    }
