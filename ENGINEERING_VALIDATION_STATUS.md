# Engineering Validation Status — 2026-10-29

> **RELEASE BLOCKED — NOT FOR STRUCTURAL DESIGN APPROVAL**
>
> This repository is experimental. A passing sectional check does not certify
> compliance with ACI CODE-318-25, Thai law, or a real structural member.
> Legacy calculations and many modules remain unverified.

## Authoritative sources and applicability
- ACI CODE-318-25 overview:
  https://www.concrete.org/newsandevents/news/newsdetail.aspx?f=51745596
- Thai Ministerial Regulation B.E.2566, Royal Gazette (6 September 2023):
  https://ratchakitcha.soc.go.th/documents/140A054N0000000000400.pdf
- Thai Clauses 6-7 (ASD / strength load combinations), 8 (quality-based phi)
  and 17 (simplified eligible wind-pressure minimum tables).
- Project-specific editions, governing government notices, exposures, wind and
  seismic maps still require independent confirmation.

## Engineering coverage matrix

| Domain | Limited calculation provided | NOT VERIFIED / prohibited from certifying |
| --- | --- | --- |
| ACI beam | Rectangular tension-controlled sectional flexure, preliminary shear with minimum stirrups | Whole member, torsion, T-beams, bar layout/anchorage, seismic, deflection |
| ACI column | Concentric axial upper bound from actual As | Factored P-M-M, interaction, slenderness, second order, detailing |
| ACI slab | Simple one-way uniform strip statics | DDM/EFM, punching, shear, RC flexure, serviceability |
| ACI footing | Full-contact elastic service soil bearing with biaxial eccentricities | Partial contact, geotechnical settlement, sliding, strength, detailing |
| ACI walls/diaphragms | No full member verified | All limit states and load paths |
| ACI load combinations | Alternatives are exclusive; signed wind/seismic envelope helper | Complete 3D code applicability, vertical E, all analysis directions |
| Thai combinations | 2566 clause 6/7 factors, clause 8 phi quality distinction | Member acceptance and project-specific code/quality determination |
| Thai wind | Clause 17 limited simplified minimum for eligible rectangular main systems | Province m/s, building Cp, internal pressures, facade and uplift |
| Thai earthquake | V=CsW arithmetic and normalized story allocation with explicit inputs | All provincial PGA, site spectra, R, k and complete seismic analysis |
| Legacy root modules | Retained for migration/reference | Unverified; DO NOT use to approve structural design |

## Important corrections already committed to audit PR

1. Repaired 1000x shear unit error and inconsistent Vu/Vc/Vs comparison.
2. Compare Mu with phi*Mn, never with phi*Mn against Mu/phi.
3. Removed false deflection approvals based on guessed As=1000 mm2.
4. Thai ksc/MPa factor repaired by initial PR; Thai basic strength load is
   1.4D+1.7L (not 1.4D+1.6L).
5. Thai phi for shear is 0.85 / 0.70 and bearing 0.70 / 0.60 in the two
   construction quality classes, NOT default ACI values.
6. Disabled unsupported province wind and earthquake lookups that guessed a
   minimum zone or used an unverified PGA as a full spectrum.
7. Footing settlement, shallow auto-sizing and 400mm assumed column disabled.
8. ACI column/wall/diaphragm/slab complete-design PASS blocked.
9. DesignResult needs explicit all_required_checks_performed=True for adequacy.
10. The licensed ACI PDF was removed from the audit branch tip, but it remains
    in existing git history until an explicitly authorized history rewrite.

## Required release acceptance checks

- Execute Python compileall, all safety regressions and the entire existing
  pytest suite; zero errors and zero regressions.
- Build/install wheel on supported Python versions and verify all imports.
- Prove no direct or wrapper API can return complete-member PASS without checks.
- For each implemented code clause: citation, full units, manual reference
  example, edge/failure cases, code applicability and engineering review.
- Validate Thai statutory amendments and local authorities as applicable.
- Verify actual loads, soil data, support conditions, geometry, reinforcement,
  material properties, and seismic/wind spatial inputs.
- Run CI with a working GitHub Actions runner. No runner/step logs means tests
  have NOT executed, regardless of workflow presence.
- Independent reviewer acceptance and formal signoff are still required.
- Remove restricted PDF content from old public git history if rights prohibit
  redistribution, only following owner's history rewrite approval.

**The audit PR remains open and should not be merged or released as a fully
code-compliant structural-design package until these blockers are cleared.**
