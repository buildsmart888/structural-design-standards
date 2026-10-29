"""Independent safety/regression tests for the 2026 engineering audit.

Checks are small and auditable. A passing suite is NOT a certified ACI/Thai code
implementation; unverified functions must fail closed instead of returning PASS.
"""
import math
import pytest
from structural_standards.base.design_base import DesignResult, DesignStatus, DesignCheck
from structural_standards.aci.aci318m25.materials.concrete import ACI318M25Concrete
from structural_standards.aci.aci318m25.materials.steel import (
    ACI318M25ReinforcementSteel, ACI318M25Steel)
from structural_standards.aci.aci318m25.members.column_design import (
    ACI318M25ColumnDesign, ColumnGeometry)
from structural_standards.aci.aci318m25.members.footing_design import (
    ACI318M25FootingDesign, FootingGeometry, ColumnLoads as FootingLoads,
    SoilProperties, SoilCondition)
from structural_standards.aci.aci318m25.members.slab_design import ACI318M25SlabDesign
from structural_standards.aci.aci318m25.members.wall_design import ACI318M25WallDesign
from structural_standards.aci.aci318m25.members.diaphragm_design import (
    ACI318M25DiaphragmDesign)
from structural_standards.aci.aci318m25.load_combinations import (
    ACI318M25LoadCombinations, LoadType)
from structural_standards.thai.ministry_2566.load_combinations import (
    ThaiMinistryLoadCombinations, ThaiLoadType)
from structural_standards.thai.ministry_2566.loads.wind_loads import ThaiWindLoads
from structural_standards.thai.ministry_2566.loads.seismic_loads import ThaiSeismicLoads


def concrete():
    return ACI318M25Concrete(fc_prime=28.0)


def steel():
    return ACI318M25ReinforcementSteel("20M", "GRADE420")


def test_no_checks_must_not_mean_pass():
    r = DesignResult("footing","partial",DesignStatus.NOT_CHECKED,0.0)
    assert not r.is_adequate()


def test_warning_check_is_not_pass():
    r = DesignResult("beam","partial",DesignStatus.NOT_CHECKED,0.0)
    r.strength_checks.append(DesignCheck("unknown",DesignStatus.WARNING,0,1,0,
                                        "kN"))
    assert not r.is_adequate()


def test_aci_alternatives_must_not_sum_roof_snow_rain():
    combos = ACI318M25LoadCombinations().get_strength_combinations()
    c = next(c for c in combos if c.name.startswith("1.2D + 1.6L"))
    loads = {LoadType.DEAD:10, LoadType.LIVE:4, LoadType.ROOF_LIVE:2,
             LoadType.SNOW:3, LoadType.RAIN:1}
    # 1.2(10)+1.6(4)+max(0.5(2),0.3(3),0.5(1)) = 19.4
    assert c.calculate_load_effect(loads) == pytest.approx(19.4)


def test_aci_signed_envelope_returns_both_extremes():
    res = ACI318M25LoadCombinations().calculate_signed_strength_envelope(
        {LoadType.DEAD:10, LoadType.WIND:30}
    )
    assert res["minimum"] < 0 < res["maximum"]


@pytest.mark.parametrize("name,expected",[
    ("ULS-7.1", {ThaiLoadType.DEAD:1.4, ThaiLoadType.LIVE:1.7}),
    ("ULS-7.2a+", {ThaiLoadType.DEAD:1.05, ThaiLoadType.LIVE:1.275,
                   ThaiLoadType.WIND:1.6}),
    ("ULS-7.3b-", {ThaiLoadType.DEAD:0.9, ThaiLoadType.EARTHQUAKE:-1.0}),
    ("ULS-7.4aH", {ThaiLoadType.DEAD:1.4, ThaiLoadType.LIVE:1.7,
                    ThaiLoadType.LATERAL_EARTH:1.7}),
    ("ULS-7.4aF", {ThaiLoadType.DEAD:1.4, ThaiLoadType.LIVE:1.7,
                    ThaiLoadType.FLUID:1.4}),
    ("ULS-7.5a", {ThaiLoadType.DEAD:1.05,ThaiLoadType.LIVE:1.275,
                   ThaiLoadType.THERMAL:1.05,ThaiLoadType.SETTLEMENT:1.05}),
])
def test_thai_strength_factors_exact_legal_text(name,expected):
    cases = {c.name:c for c in ThaiMinistryLoadCombinations().get_ultimate_combinations()}
    assert cases[name].factors == expected


@pytest.mark.parametrize("name,expected",[
    ("ASD-6.1",{ThaiLoadType.DEAD:1.0,ThaiLoadType.LIVE:1.0}),
    ("ASD-6.2b+",{ThaiLoadType.DEAD:0.6,ThaiLoadType.WIND:1.0}),
    ("ASD-6.3b-",{ThaiLoadType.DEAD:1.0,ThaiLoadType.LIVE:0.75,
                  ThaiLoadType.EARTHQUAKE:-0.525}),
])
def test_thai_service_load_factors_exact_legal_text(name,expected):
    cases = {c.name:c for c in ThaiMinistryLoadCombinations().get_serviceability_combinations()}
    assert cases[name].factors == expected


def test_thai_good_quality_phi_is_not_aci_phi():
    high = ThaiMinistryLoadCombinations(good_quality_control=True)
    low = ThaiMinistryLoadCombinations(good_quality_control=False)
    assert high.get_phi_factor("shear_and_torsion") == pytest.approx(0.85)
    assert low.get_phi_factor("shear_and_torsion") == pytest.approx(0.70)
    assert high.get_phi_factor("bearing_on_concrete") == pytest.approx(0.70)
    assert low.get_phi_factor("bearing_on_concrete") == pytest.approx(0.60)


def test_thai_no_unknown_safety_factor_defaults_to_one():
    with pytest.raises(KeyError):
        ThaiMinistryLoadCombinations().get_safety_factor("unknown")


@pytest.mark.parametrize("height,least,terrain,expected",[
    (8,4,"urban",0.6), (10,4,"open",1.0),
    (11,4,"urban",0.8), (20,7,"open",1.2),
    (21,8,"urban",1.2), (40,15,"open",1.6),
])
def test_thai_wind_clause17_minimum(height,least,terrain,expected):
    res = ThaiWindLoads.calculate_statutory_minimum_pressure(height,least,terrain)
    assert res["minimum_pressure_kN_m2"] == pytest.approx(expected)


def test_thai_public_large_building_increases_pressure_15pct():
    x = ThaiWindLoads.calculate_statutory_minimum_pressure(
        10,4,"urban",True,1000)
    assert x["minimum_pressure_kN_m2"] == pytest.approx(0.69)


@pytest.mark.parametrize("h,b,terrain",[(41,20,"urban"),
    (30,9,"urban"),(12,5,"unknown"),(-2,5,"open")])
def test_thai_wind_rejects_inapplicable_simplified_method(h,b,terrain):
    with pytest.raises(ValueError):
        ThaiWindLoads.calculate_statutory_minimum_pressure(h,b,terrain)


def test_unverified_wind_speed_by_province_refused():
    with pytest.raises(NotImplementedError):
        ThaiWindLoads().get_wind_zone_for_province("กรุงเทพมหานคร")


def test_unverified_seismic_pga_by_province_refused():
    with pytest.raises(NotImplementedError):
        ThaiSeismicLoads().get_seismic_zone_data("กรุงเทพมหานคร")


def test_seismic_statics_pure_base_shear():
    assert ThaiSeismicLoads.base_shear_from_verified_coefficient(0.1,2000) == 200


def test_seismic_vertical_normalization_without_hidden_k():
    forces = ThaiSeismicLoads.distribute_base_shear(
        120, [3,6,9], [100,200,300],1.0)
    assert sum(forces.values()) == pytest.approx(120)
    assert forces[3] > forces[2] > forces[1]


def test_seismic_rejects_mismatched_story_arrays():
    with pytest.raises(ValueError):
        ThaiSeismicLoads.distribute_base_shear(120,[3,6],[100],1.0)


def test_footing_concentric_service_pressure_includes_selfweight():
    f = ACI318M25FootingDesign(concrete(),steel())
    g = FootingGeometry(length=2000,width=2000,thickness=500)
    l = FootingLoads(axial_dead=500,axial_live=300)
    q = f.check_service_bearing_pressure(g,l,SoilProperties(250))
    # 800kN load + 2m3 *24 kN/m3 = 848kN /4m2 = 212 kPa
    assert q.value == pytest.approx(212.0)
    assert q.status is DesignStatus.PASS


def test_footing_biaxial_service_pressure_uses_mm_m_conversion():
    f = ACI318M25FootingDesign(concrete(),steel())
    g = FootingGeometry(length=2000,width=2000,thickness=500)
    l = FootingLoads(axial_dead=500,axial_live=300,
                     moment_x_dead=20,moment_y_live=10)
    q = f.check_service_bearing_pressure(g,l,SoilProperties(250))
    # qavg=212, ΔqMx=15, ΔqMy=7.5
    assert q.value == pytest.approx(234.5)


def test_footing_outside_middle_third_must_not_get_pass():
    f = ACI318M25FootingDesign(concrete(),steel())
    g = FootingGeometry(length=2000,width=2000,thickness=500)
    l = FootingLoads(axial_dead=500,axial_live=300,moment_x_dead=1000)
    with pytest.raises(NotImplementedError):
        f.check_service_bearing_pressure(g,l,SoilProperties(250))


def test_footing_ultimate_soil_strength_not_divided_by_assumed_three():
    f = ACI318M25FootingDesign(concrete(),steel())
    g = FootingGeometry(length=2000,width=2000,thickness=500)
    with pytest.raises(NotImplementedError):
        f.check_service_bearing_pressure(
            g,FootingLoads(axial_dead=100),
            SoilProperties(1000,condition=SoilCondition.ULTIMATE_BEARING)
        )


def test_footing_preliminary_pass_does_not_certify_complete_design():
    f = ACI318M25FootingDesign(concrete(),steel())
    g = FootingGeometry(length=2000,width=2000,thickness=500)
    l = FootingLoads(axial_dead=500,axial_live=300)
    result = f.design(l,SoilProperties(250),target_geometry=g)
    assert result.overall_status is DesignStatus.NOT_CHECKED
    assert not result.is_adequate() or result.overall_status is DesignStatus.NOT_CHECKED


def test_column_axial_upper_bound_uses_correct_tie_spiral_factors():
    c = ACI318M25ColumnDesign(concrete(),steel())
    ties = ColumnGeometry(width=400,depth=400,length=3000,
                          transverse_reinforcement="ties")
    spiral = ColumnGeometry(width=400,depth=400,length=3000,
                            transverse_reinforcement="spiral")
    pt = c.calculate_concentric_axial_upper_bound(ties,3200)
    ps = c.calculate_concentric_axial_upper_bound(spiral,3200)
    Ag, As = 160000.0, 3200.0
    p0 = (0.85*28*(Ag-As)+420*As)/1000
    assert pt["P0_kN"] == pytest.approx(p0)
    assert pt["phi_Pn_max_kN"] == pytest.approx(0.65*0.80*p0)
    assert ps["phi_Pn_max_kN"] == pytest.approx(0.75*0.85*p0)


def test_column_trial_sizing_is_not_an_approved_design():
    from structural_standards.aci.aci318m25.members.column_design import ColumnLoads
    c = ACI318M25ColumnDesign(concrete(),steel())
    r = c.design_axial_reinforcement(
        ColumnGeometry(400,400,3000),ColumnLoads(axial_dead=400,axial_live=200))
    assert r.overall_status is DesignStatus.NOT_CHECKED


def test_slab_wall_diaphragm_do_not_fake_code_compliance():
    for cls,member in ((ACI318M25SlabDesign,"slab"),
                       (ACI318M25WallDesign,"wall"),
                       (ACI318M25DiaphragmDesign,"diaphragm")):
        result = cls(concrete(),steel()).design()
        assert result.member_type == member
        assert result.overall_status is DesignStatus.NOT_CHECKED


def test_structural_steel_a36_is_not_rejected_as_rebar_grade():
    s = ACI318M25Steel(grade="A36")
    assert s.fy == pytest.approx(250.0)


@pytest.mark.parametrize("bar,factor",[
    ("#8",6),("#10",8),("#14",10),
])
def test_longitudinal_hook_diameter_by_bar_class(bar,factor):
    s = ACI318M25ReinforcementSteel(bar)
    assert s.get_minimum_bend_diameter(90) == pytest.approx(factor*s.bar_diameter())


def test_135_degree_tie_hook_must_not_use_longitudinal_hook_table():
    with pytest.raises(NotImplementedError):
        steel().get_minimum_bend_diameter(135)


def test_zero_bar_spacing_cannot_be_used():
    with pytest.raises(ValueError):
        steel().calculate_area_per_meter(0)


def test_thai_grade_210_ksc_is_not_21_mpa():
    from structural_standards.thai.ministry_2566.materials.concrete import (
        ThaiConcrete, create_fc210)
    c = create_fc210()
    expected_mpa = 210.0 * 0.0980665
    assert c.fc_prime == pytest.approx(expected_mpa)
    assert c.strength_in_ksc() == pytest.approx(210.0)
    assert c.grade_properties.fc_mpa == pytest.approx(expected_mpa)


@pytest.mark.parametrize("grade,ksc",[
    ("Fc180",180),("Fc210",210),("Fc240",240),
    ("Fc280",280),("Fc350",350),
])
def test_all_thai_concrete_grades_convert_exactly(grade,ksc):
    from structural_standards.thai.ministry_2566.materials.concrete import ThaiConcrete
    c = ThaiConcrete(grade=grade)
    assert c.fc_prime == pytest.approx(ksc*.0980665,rel=1e-10)
    assert c.strength_in_ksc() == pytest.approx(ksc,rel=1e-10)


def test_custom_concrete_mpa_must_not_be_mislabeled_as_nearest_grade():
    from structural_standards.thai.ministry_2566.materials.concrete import ThaiConcrete
    c = ThaiConcrete(fc_prime=23.0)
    assert c.grade == "CUSTOM"
    assert c.grade_properties is None


@pytest.mark.parametrize("grade,fy_ksc,fu_ksc",[
    ("SR24",2400,3800),("SD40",4000,6000),("SD50",5000,7000),
])
def test_thai_steel_strengths_are_physically_consistent(grade,fy_ksc,fu_ksc):
    from structural_standards.thai.ministry_2566.materials.steel import ThaiSteel
    s=ThaiSteel(grade=grade)
    assert s.fy == pytest.approx(fy_ksc*.0980665,rel=1e-8)
    assert s.fu == pytest.approx(fu_ksc*.0980665,rel=1e-8)
    assert s.yield_strength_ksc() == pytest.approx(fy_ksc,rel=1e-8)


def test_thai_custom_steel_requires_actual_fu():
    from structural_standards.thai.ministry_2566.materials.steel import ThaiSteel
    with pytest.raises(ValueError,match="Fu"):
        ThaiSteel(fy=320)
    c=ThaiSteel(fy=320,fu=500)
    assert c.grade == "CUSTOM"


def test_plain_and_deformed_bar_grade_must_match():
    from structural_standards.thai.ministry_2566.materials.steel import ThaiReinforcementSteel
    with pytest.raises(ValueError):
        ThaiReinforcementSteel("RB9",steel_grade="SD40")
    with pytest.raises(ValueError):
        ThaiReinforcementSteel("DB12",steel_grade="SR24")


def test_thai_phi_single_source_of_truth_from_load_combinations():
    from structural_standards.thai.ministry_2566.materials.concrete import ThaiConcrete
    c=ThaiConcrete(grade="Fc240")
    assert c.get_strength_reduction_factors(
        good_quality_control=False)["shear_and_torsion"] == pytest.approx(.70)
    assert c.get_strength_reduction_factors(
        good_quality_control=True)["shear_and_torsion"] == pytest.approx(.85)


def test_thai_mix_table_not_proven_solely_by_concrete_grade():
    from structural_standards.thai.ministry_2566.materials.concrete import ThaiConcrete
    with pytest.raises(NotImplementedError):
        ThaiConcrete(grade="Fc210").get_mix_requirements()


def test_aci_rebar_factory_honors_fy_and_does_not_fake_620():
    from structural_standards.aci.aci318m25 import (
        create_reinforcement, get_standard_reinforcement_grades)
    assert create_reinforcement("20M",280).fy == pytest.approx(280)
    assert create_reinforcement("20M",520).fy == pytest.approx(520)
    with pytest.raises(ValueError):
        create_reinforcement("20M",620)
    grades=get_standard_reinforcement_grades()
    assert grades["grade280"].fy == pytest.approx(280)
    assert grades["grade520"].fy == pytest.approx(520)


def test_thai_project_compliance_cannot_pass_without_structure():
    from structural_standards.thai.ministry_2566.ministry_regulation import (
        ThaiMinistryRegulation2566, ThaiProjectData)
    from structural_standards.thai.ministry_2566.design_requirements import ThaiEnvironmentType
    # Use an actual enumeration value; the fake compliance routine must not
    # pretend to verify cover or national safety factors from only grade names.
    env = next(iter(ThaiEnvironmentType))
    reg=ThaiMinistryRegulation2566()
    project=ThaiProjectData(project_name="Regression Test",
                            location="Bangkok",environment_type=env,
                            concrete_grade="Fc210",steel_grade="SD40")
    checks=reg.check_project_compliance(project)
    assert checks and all(not c.is_compliant for c in checks)
    report=reg.generate_compliance_report(project,checks)
    assert "NOT VERIFIED" in report
    assert "COMPLIANT" not in report.split("Overall Status:")[-1].split("\n")[0]


def test_thai_deflection_compliance_does_not_certify_generic_ratio():
    from structural_standards.thai.ministry_2566.design_requirements import (
        ThaiMinistryDesignRequirements, ThaiSupportType)
    c=ThaiMinistryDesignRequirements()
    with pytest.raises(NotImplementedError):
        c.check_deflection_compliance(
            actual_deflection=0,span_length=5000,
            support_type=next(iter(ThaiSupportType)))


def test_thai_concrete_mix_validation_no_blanket_pass():
    from structural_standards.thai.ministry_2566.design_requirements import (
        ThaiMinistryDesignRequirements)
    with pytest.raises(NotImplementedError):
        ThaiMinistryDesignRequirements().validate_concrete_mix()


def test_aci_development_length_default_confinement_must_not_be_assumed():
    s=ACI318M25Steel(grade="GRADE420")
    with pytest.raises(NotImplementedError):
        s.calculate_development_length(20,28)
    with pytest.raises(NotImplementedError):
        s.get_splice_length(20,28)


def test_aci_dev_expression_with_explicit_confinement():
    s=ACI318M25Steel(grade="GRADE420")
    x=s.evaluate_development_expression_si(
        fy_mpa=420,fc_mpa=28,db_mm=20,cb_mm=25,ktr_mm=0,
        lambda_factor=1,psi_t=1,psi_e=1,psi_s=1,psi_g=1)
    assert x["confinement_ratio_capped"] == pytest.approx(1.25)
    assert x["general_expression_length_mm"] == pytest.approx(
        420*20/(1.1*math.sqrt(28)*1.25))


def test_thai_signed_loads_allow_negative_internal_moment_but_reject_nan():
    combos=ThaiMinistryLoadCombinations()
    c=next(c for c in combos.get_ultimate_combinations()
           if c.name=="ULS-7.1")
    # Member effects (moments/reactions) may have physical signs.
    assert c.calculate_load_effect({
        ThaiLoadType.DEAD:-2,ThaiLoadType.LIVE:4}) == pytest.approx(4.0)
    with pytest.raises(ValueError):
        c.calculate_load_effect({
            ThaiLoadType.DEAD:float("nan"),ThaiLoadType.LIVE:4})


def test_thai_missing_dead_load_cannot_be_silent_zero():
    c=next(c for c in ThaiMinistryLoadCombinations().get_ultimate_combinations()
           if c.name=="ULS-7.1")
    with pytest.raises(ValueError):
        c.calculate_load_effect({ThaiLoadType.LIVE:4})


def test_material_input_cannot_disagree_with_grade():
    from structural_standards.thai.ministry_2566.materials.concrete import ThaiConcrete
    from structural_standards.thai.ministry_2566.materials.steel import ThaiSteel
    with pytest.raises(ValueError,match="Conflicting"):
        ThaiConcrete(grade="Fc210",fc_prime=21.0)
    with pytest.raises(ValueError,match="Conflicting"):
        ThaiSteel(grade="SD40",fy=400.0)


def test_case_insensitive_grade_has_canonical_properties():
    from structural_standards.thai.ministry_2566.materials.concrete import ThaiConcrete
    from structural_standards.thai.ministry_2566.materials.steel import ThaiSteel
    c=ThaiConcrete(grade="fc210")
    st=ThaiSteel(grade="sd40")
    assert c.grade == "Fc210" and c.grade_properties is not None
    assert st.grade == "SD40" and st.grade_properties is not None


def test_thai_unverified_cover_tolerance_and_summary_are_blocked():
    from structural_standards.thai.ministry_2566.design_requirements import (
        ThaiMinistryDesignRequirements)
    req=ThaiMinistryDesignRequirements()
    for func in (req.get_concrete_cover,req.get_deflection_limit,
                 req.get_construction_tolerance,req.generate_design_summary):
        with pytest.raises(NotImplementedError):
            func()
