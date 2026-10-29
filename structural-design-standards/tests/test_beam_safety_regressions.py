"""Independent numerical regression checks for ACI rectangular beam sections.

The numerical oracle is calculated from equilibrium, not another implementation.
Not a validation of the entire code or the entire ACI 318M-25 standard.
"""
import math
import pytest
from structural_standards.base.design_base import DesignStatus
from structural_standards.aci.aci318m25.materials.concrete import ACI318M25Concrete
from structural_standards.aci.aci318m25.materials.steel import ACI318M25ReinforcementSteel
from structural_standards.aci.aci318m25.members.beam_design import (
    ACI318M25BeamDesign, BeamGeometry, BeamLoads, BeamReinforcement)


def designer():
    return ACI318M25BeamDesign(
        ACI318M25Concrete(fc_prime=28.0),
        ACI318M25ReinforcementSteel(bar_designation="20M", grade="GRADE420"))


def geometry():
    return BeamGeometry(width=300, height=600, effective_depth=550,
                        span_length=6000)


def test_manual_flexural_150knm_equilibrium():
    """Independent bisection oracle for Mu=phi As fy (d-a/2)."""
    c = designer()
    b, d, fc, fy, phi = 300.0, 550.0, 28.0, 420.0, 0.9
    mu_nmm = 150.0 * 1e6
    lo, hi = 0.0, 5000.0
    for _ in range(100):
        mid = (lo + hi) / 2
        a = mid * fy / (0.85 * fc * b)
        if phi * mid * fy * (d - a / 2) < mu_nmm:
            lo = mid
        else:
            hi = mid
    result = c.design_flexural_reinforcement(geometry(), 150.0)
    assert result.overall_status is DesignStatus.PASS
    assert result.required_reinforcement["As_required_mm2"] == pytest.approx(
        (lo + hi) / 2, rel=1e-9)
    assert result.strength_checks[0].status is DesignStatus.PASS
    assert result.utilization_ratio == pytest.approx(1.0, rel=1e-8)


def test_minimum_steel_recalculates_capacity():
    c = designer()
    result = c.design_flexural_reinforcement(geometry(), 1.0)
    amin = max(1.4 / 420.0, math.sqrt(28.0)/(4*420.0)) * 300 * 550
    assert result.required_reinforcement["As_required_mm2"] == pytest.approx(amin)
    a = amin * 420.0 / (0.85 * 28.0 * 300.0)
    expected = 0.9 * amin * 420.0 * (550.0 - a / 2) / 1e6
    assert result.design_capacities["phi_Mn_kNm"] == pytest.approx(expected)
    assert result.utilization_ratio == pytest.approx(1.0 / expected)


def test_excessive_moment_cannot_pass():
    result = designer().design_flexural_reinforcement(geometry(), 1200.0)
    assert result.overall_status is DesignStatus.FAIL
    assert result.required_reinforcement["As_required_mm2"] is None
    assert result.strength_checks[0].status is DesignStatus.FAIL


def test_maximum_steel_based_on_strain_compatibility():
    c = designer()
    epsilon_ty = 420.0 / 200000.0
    c_over_d = 0.003 / (0.003 + epsilon_ty + 0.003)
    expected = 0.85 * 28 * 0.85 * c_over_d / 420
    assert c.maximum_flexural_reinforcement_ratio() == pytest.approx(expected)


def test_shear_in_newtons_and_capacity_in_kn():
    c = designer()
    result = c.design_shear_reinforcement(geometry(), 200.0, 1000.0)
    vc = 0.17 * math.sqrt(28.0) * 300.0 * 550.0 / 1000.0
    assert result.design_capacities["phi_Vc_kN"] == pytest.approx(0.75*vc)
    assert result.overall_status is DesignStatus.PASS
    assert result.strength_checks[0].status is DesignStatus.PASS
    assert result.required_reinforcement["minimum_stirrups_provided"] is True


def test_low_shear_still_includes_minimum_stirrups():
    result = designer().design_shear_reinforcement(geometry(), 10.0, 1000.0)
    d = result.required_reinforcement
    assert d["minimum_stirrups_provided"] is True
    assert d["stirrup_area_mm2"] > 100.0
    assert d["stirrup_spacing_mm"] <= 275.0


def test_excessive_shear_fails():
    result = designer().design_shear_reinforcement(geometry(), 5000.0, 1000.0)
    assert result.overall_status is DesignStatus.FAIL


def test_invalid_geometry_rejected():
    beam = BeamGeometry(width=300, height=450, effective_depth=500,
                        span_length=6000)
    with pytest.raises(ValueError):
        designer().design_flexural_reinforcement(beam, 100.0)


def test_deflection_does_not_certify_placeholder_steel():
    with pytest.raises(NotImplementedError, match="NOT VERIFIED"):
        designer().check_deflection(geometry(), BeamLoads(dead_load=5, live_load=8),
                                    BeamReinforcement())


def test_shear_design_returns_standard_design_result():
    result = designer().design_shear_reinforcement(geometry(), 100, 1000)
    assert isinstance(result.strength_checks, list)
    assert isinstance(result.detailing_checks, list)
    assert result.member_type == "beam"
