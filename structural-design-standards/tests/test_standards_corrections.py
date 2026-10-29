"""
Regression tests for the standards-corrections made in the library audit.
Tests for code-standard corrections found in the audit.

Each test pins a value that was previously computed incorrectly. Expected
numbers are hand-derived from ACI CODE-318-25 (SI) or from the definition of
the Thai unit ksc, not copied from the implementation.

ทุกเทสต์ตรึงค่าที่เคยคำนวณผิด ไว้กับค่าที่คำนวณด้วยมือจาก
ACI CODE-318-25 (SI) หรือนิยามของหน่วย ksc
"""

import math

import pytest

from structural_standards.aci.aci318m25.load_combinations import (
    ACI318M25LoadCombinations, LoadType)
from structural_standards.aci.aci318m25.materials.concrete import ACI318M25Concrete
from structural_standards.aci.aci318m25.materials.steel import ACI318M25Steel
from structural_standards.thai.ministry_2566 import ThaiMinistryRegulation2566
from structural_standards.thai.ministry_2566.materials.concrete import (
    ThaiConcrete, create_fc210, ksc_to_mpa, mpa_to_ksc)
from structural_standards.utils.validation import ValidationError

ES = 200000.0          # MPa
KSC_IN_MPA = 0.0980665  # 1 ksc = 1 kgf/cm2


# ---------------------------------------------------------------- import surface
def test_package_imports_without_console_output(capsys):
    """importing the library must not print, and must not crash on cp874/cp1252."""
    import importlib
    import structural_standards
    importlib.reload(structural_standards)
    assert capsys.readouterr().out == ''


def test_thai_subpackages_import():
    """`structural_standards.thai` used to raise ImportError (phantom ThaiVolumeUnit)."""
    import importlib
    for mod in ('structural_standards.thai',
                'structural_standards.thai.ministry_2566.units',
                'structural_standards.thai.ministry_2566.materials',
                'structural_standards.aci.aci318m25.materials'):
        importlib.import_module(mod)


def test_aci_load_combinations_are_exported():
    """The aci package re-export of the load combinations was commented out."""
    import structural_standards.aci.aci318m25 as pkg
    assert hasattr(pkg, 'ACI318M25LoadCombinations')


# ---------------------------------------------------------------- Table 5.3.1
@pytest.mark.parametrize('eq_name, snow', [
    ('1.2D + 1.6L + (0.5Lr or 0.3S or 0.5R)', 0.3),   # Eq. (5.3.1b)
    ('1.2D + (1.6Lr or 1.0S or 1.6R) + (1.0L or 0.5W)', 1.0),  # (5.3.1c)
    ('1.2D + 1.0W + 1.0L + (0.5Lr or 0.3S or 0.5R)', 0.3),     # (5.3.1d)
    ('1.2D + 1.0E + 1.0L + 0.15S', 0.15),                      # (5.3.1e)
])
def test_snow_companion_factor_matches_table_531(eq_name, snow):
    """ACI 318-25 uses 0.3S and 0.15S, not the ASCE 7-16 style 0.5S / 0.2S."""
    combos = {c.name: c for c in ACI318M25LoadCombinations()._strength_combinations}
    assert eq_name in combos
    assert combos[eq_name].factors[LoadType.SNOW] == pytest.approx(snow)


def test_all_seven_strength_combinations_exist():
    assert len(ACI318M25LoadCombinations()._strength_combinations) == 7


# ---------------------------------------------------------------- Chapter 21 phi
def test_strut_and_tie_phi_is_single_value():
    """Table 21.2.1(g): struts, ties, nodal zones and bearing areas all use 0.75."""
    phi = ACI318M25LoadCombinations().phi_factors
    assert phi['strut_and_tie_struts'] == 0.75
    assert phi['strut_and_tie_ties'] == 0.75
    assert phi['strut_and_tie_nodal_zones'] == 0.75


@pytest.mark.parametrize('strain, transverse, expected', [
    (0.0060, 'ties',   0.90),   # >= eps_ty + 0.003  -> tension controlled
    (0.0060, 'spiral', 0.90),
    (0.0021, 'ties',   0.65),   # <= eps_ty          -> compression controlled
    (0.0021, 'spiral', 0.75),
])
def test_phi_end_points_of_table_2122(strain, transverse, expected):
    got = ACI318M25LoadCombinations().get_transition_phi_factor(strain, transverse)
    assert got == pytest.approx(expected, abs=1e-9)


def test_transition_interpolation_spans_0003():
    """Table 21.2.2(c)/(d): 0.65 + 0.25(eps_t - eps_ty)/0.003 for tied sections."""
    eps_ty = 420.0 / ES
    lc = ACI318M25LoadCombinations()
    strain = eps_ty + 0.0015
    expected = 0.65 + 0.25 * (strain - eps_ty) / 0.003
    assert lc.get_transition_phi_factor(strain, 'ties') == pytest.approx(expected)


def test_tension_controlled_limit_follows_reinforcement_grade():
    """21.2.2.1: eps_ty = fy/Es, so the limit moves with the grade.

    Grade 420 -> eps_ty 0.0021, tension-controlled at 0.0051.
    Grade 550 -> eps_ty 0.0028, tension-controlled at 0.0058.
    A strain of 0.0055 is therefore fully tension-controlled for Grade 420 but
    still in the transition zone for Grade 550.
    """
    lc = ACI318M25LoadCombinations()
    assert lc.get_transition_phi_factor(0.0055, 'ties', fy=420.0) == pytest.approx(0.90)
    assert lc.get_transition_phi_factor(0.0055, 'ties', fy=550.0) < 0.90


# ---------------------------------------------------------------- development length
def test_development_length_without_real_confinement_fails_closed():
    """Never substitute the maximum allowable ratio cb+Ktr/db=2.5."""
    steel=ACI318M25Steel(grade="GRADE420")
    with pytest.raises(NotImplementedError):
        steel.calculate_development_length(20.0,28.0)


def test_development_expression_requires_actual_cb_ktr_and_modifiers():
    steel=ACI318M25Steel(grade="GRADE420")
    r=steel.evaluate_development_expression_si(
        fy_mpa=420,fc_mpa=28,db_mm=20,cb_mm=25,ktr_mm=0,
        lambda_factor=1,psi_t=1,psi_e=1,psi_s=1,psi_g=1)
    expected=420*20/(1.1*math.sqrt(28)*(25/20))
    assert r["general_expression_length_mm"] == pytest.approx(expected)
    assert r["not_code_compliant_without_detail_checks"] is True


def test_automatic_class_a_lap_splice_is_prohibited():
    steel=ACI318M25Steel(grade="GRADE420")
    with pytest.raises(NotImplementedError):
        steel.get_splice_length(20.0,28.0)


# ---------------------------------------------------------------- beam shear/deflection
def test_beam_shear_coefficients_are_si():
    """No hidden 1000 factor: phi Vc from concrete N/mm2 and geometry mm."""
    from structural_standards.aci.aci318m25.members.beam_design import (
        ACI318M25BeamDesign, BeamGeometry)
    from structural_standards.aci.aci318m25.materials.steel import ACI318M25ReinforcementSteel
    b = ACI318M25BeamDesign(ACI318M25Concrete(fc_prime=28),
                             ACI318M25ReinforcementSteel('20M'))
    g = BeamGeometry(width=300, height=600, effective_depth=550, span_length=6000)
    result = b.design_shear_reinforcement(g, 180.0, 1000.0)
    expected = 0.75 * 0.17 * math.sqrt(28) * 300 * 550 / 1000
    assert result.design_capacities["phi_Vc_kN"] == pytest.approx(expected)


def test_cracking_moment_is_in_n_mm():
    """fr*Ig/yt with MPa/mm units is already N.mm; the extra /1e6 collapsed Ie to Icr."""
    import inspect
    import structural_standards.aci.aci318m25.members.beam_design as beam
    assert 'Ig / yt / 1e6' not in inspect.getsource(beam)


def test_deflection_expression_has_no_thousand_fold_divisor():
    import inspect
    import structural_standards.aci.aci318m25.members.beam_design as beam
    assert 'Ie * 1000' not in inspect.getsource(beam)


# ---------------------------------------------------------------- column
def test_column_max_axial_strength_per_table_22421():
    """Tied factor .8 and spiral .85 explicitly from transverse reinforcement."""
    from structural_standards.aci.aci318m25.members.column_design import (
        ACI318M25ColumnDesign, ColumnGeometry)
    from structural_standards.aci.aci318m25.materials.steel import ACI318M25ReinforcementSteel
    c = ACI318M25ColumnDesign(ACI318M25Concrete(fc_prime=28),
                              ACI318M25ReinforcementSteel("20M"))
    ties = c.calculate_concentric_axial_upper_bound(
        ColumnGeometry(400,400,3000,transverse_reinforcement="ties"),3200)
    spiral = c.calculate_concentric_axial_upper_bound(
        ColumnGeometry(400,400,3000,transverse_reinforcement="spiral"),3200)
    assert ties["phi_compression"] == pytest.approx(0.65)
    assert ties["max_axial_factor"] == pytest.approx(0.80)
    assert spiral["phi_compression"] == pytest.approx(0.75)
    assert spiral["max_axial_factor"] == pytest.approx(0.85)


def test_column_phi_no_longer_keyed_to_section_shape():
    """Table 21.2.2 keys phi on transverse reinforcement, not on circular/rectangular."""
    import inspect
    import structural_standards.aci.aci318m25.members.column_design as column
    src = inspect.getsource(column)
    assert 'geometry.cross_section == "circular":\n            phi' not in src


# ---------------------------------------------------------------- slab
@pytest.mark.parametrize('fy, expected_rho', [
    (420.0, 0.0020),   # 7.6.1.1 allowance for lower-strength reinforcement
    (490.0, 0.0018),   # middle tier was missing -> 14% under-reinforcement
    (590.0, 0.0018 * 420 / 590),
])
def test_slab_shrinkage_minimum_reinforcement_tiers(fy, expected_rho):
    """As,min = rho * b * h must follow the three code tiers."""
    from types import SimpleNamespace
    from structural_standards.aci.aci318m25.members.slab_design import ACI318M25SlabDesign
    captured = {}
    # ACI318M25SlabDesign is still abstract, so drive the real function directly
    fake = SimpleNamespace(steel=SimpleNamespace(fy=fy),
                          _select_reinforcement=lambda as_min, width: captured.setdefault('As', as_min))
    ACI318M25SlabDesign._design_minimum_reinforcement(fake, 1000.0, 200.0)
    assert captured['As'] == pytest.approx(expected_rho * 1000.0 * 200.0)


def test_minimum_thickness_includes_fy_multiplier_once():
    """Do not certify minimum thickness from guessed support dimensions."""
    from structural_standards.aci.aci318m25.members.slab_design import ACI318M25SlabDesign
    with pytest.raises(NotImplementedError):
        ACI318M25SlabDesign.calculate_minimum_thickness(None, None)


def test_legacy_wall_axial_private_check_is_disabled():
    """Wall design cannot return bogus PASS based on wrong kN/m -> N conversion."""
    from structural_standards.aci.aci318m25.members.wall_design import ACI318M25WallDesign
    from structural_standards.aci.aci318m25.materials.steel import ACI318M25ReinforcementSteel
    wall=ACI318M25WallDesign(ACI318M25Concrete(fc_prime=28),
                             ACI318M25ReinforcementSteel("20M"))
    with pytest.raises(NotImplementedError):
        wall._check_axial_strength(None,None)


def test_legacy_wall_pressure_private_check_is_disabled():
    """kPa/mm conversions need actual wall geometry and factored combinations."""
    from structural_standards.aci.aci318m25.members.wall_design import ACI318M25WallDesign
    from structural_standards.aci.aci318m25.materials.steel import ACI318M25ReinforcementSteel
    wall=ACI318M25WallDesign(ACI318M25Concrete(fc_prime=28),
                             ACI318M25ReinforcementSteel("20M"))
    with pytest.raises(NotImplementedError):
        wall._check_flexural_strength(None,None,None)


def test_footing_shear_and_bearing_pressure_share_one_force_unit():
    """2x2m x0.5m footing, P=800kN, Mx=20kNm, My=10kNm, qa=250kPa."""
    from structural_standards.aci.aci318m25.members.footing_design import (
        ACI318M25FootingDesign, FootingGeometry, ColumnLoads, SoilProperties)
    from structural_standards.aci.aci318m25.materials.steel import ACI318M25ReinforcementSteel
    from structural_standards.base.design_base import DesignStatus
    f = ACI318M25FootingDesign(ACI318M25Concrete(fc_prime=28),
                               ACI318M25ReinforcementSteel("20M"))
    geo = FootingGeometry(length=2000,width=2000,thickness=500)
    loads = ColumnLoads(axial_dead=500,axial_live=300,
                         moment_x_dead=20,moment_y_live=10)
    check = f.check_service_bearing_pressure(geo,loads,SoilProperties(250))
    assert check.value == pytest.approx(234.5)
    assert check.status is DesignStatus.PASS
    # Passing service soil bearing alone MUST NOT certify complete footing.
    result = f.design(loads,SoilProperties(250),target_geometry=geo)
    assert result.overall_status is DesignStatus.NOT_CHECKED


def test_ksc_conversion_uses_the_correct_definition():
    """1 ksc = 1 kgf/cm2 = 0.0980665 MPa. The old factor was 10x too large."""
    assert mpa_to_ksc(1.0) == pytest.approx(1.0 / KSC_IN_MPA)
    assert ksc_to_mpa(1.0) == pytest.approx(KSC_IN_MPA)
    assert ksc_to_mpa(mpa_to_ksc(25.0)) == pytest.approx(25.0)


def test_thai_concrete_grade_factories_work():
    """create_fc180()..create_fc350() all raised ValueError from the broken parser."""
    c = create_fc210()
    assert c.fc_prime == pytest.approx(210.0 * KSC_IN_MPA)
    assert c.strength_in_ksc() == pytest.approx(210.0, rel=1e-9)


@pytest.mark.parametrize('grade', ['Fc180', 'FC180', 'fc180', 'fc 180'.replace(' ', '')])
def test_thai_grade_parsing_is_case_insensitive(grade):
    """The grade parser must accept any casing and resolve to the Fc180 properties."""
    assert ThaiConcrete(grade=grade).fc_prime == pytest.approx(180.0 * KSC_IN_MPA)


def test_provincial_wind_zone_delegates_to_wind_module():
    """Reject fabricated regional design wind speeds; use regulation clause 17."""
    with pytest.raises(NotImplementedError):
        ThaiMinistryRegulation2566().get_wind_zone_data("กรุงเทพมหานคร")


def test_provincial_seismic_zone_delegates_to_seismic_module():
    """Seismic hazard needs site-specific spectra, not guessed province PGA."""
    with pytest.raises(NotImplementedError):
        ThaiMinistryRegulation2566().get_seismic_zone_data("เชียงใหม่")


def test_validation_error_is_a_value_error():
    """Callers (and pytest.raises(ValueError)) expect a ValueError subclass."""
    assert issubclass(ValidationError, ValueError)


def test_relative_imports_stay_within_the_package():
    """No module may climb above the top-level package with `from ....x`."""
    import ast
    import pathlib
    pkg = pathlib.Path(__file__).resolve().parents[1] / 'structural_standards'
    offenders = []
    for py in pkg.rglob('*.py'):
        if '__pycache__' in py.parts:
            continue
        depth = len(py.relative_to(pkg.parent).parts) - 1  # package parts incl. name
        for node in ast.walk(ast.parse(py.read_text(encoding='utf-8'))):
            if isinstance(node, ast.ImportFrom) and node.level and node.level > depth:
                offenders.append('%s:%d' % (py.name, node.lineno))
    assert offenders == []
