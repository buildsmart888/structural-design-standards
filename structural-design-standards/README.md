# Structural Design Standards Library

> [!CAUTION]
> **ENGINEERING VALIDATION INCOMPLETE — NOT FOR CONSTRUCTION DESIGN OR SIGN-OFF.**
> This repository includes experimental implementations and legacy modules with unresolved
> numerical, standards-edition, and integration defects. An earlier release claimed
> full compliance without code-level independent validation. Do not rely on a PASS
> status as evidence that all code checks were performed.
>
> The rectangular beam sectional flexure and preliminary shear methods have been
> revised on the audit branch and supplied with independent regression cases, but
> the entire suite has NOT been verified passing. Beam deflection now raises
> `NotImplementedError` instead of passing on an assumed reinforcement area.
> Column/footing/slab/wall design methods, soil settlement, two-way action, wind
> and seismic maps, detailing and load combinations still need qualified review.
> Confirm the exact governing standard edition and mandatory local provisions.


**ไลบรารี Python สำหรับมาตรฐานการออกแบบโครงสร้างระดับนานาชาติ**  
*Python Library for International Structural Design Standards*

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/your-org/structural-design-standards)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://structural-design-standards.readthedocs.io/)

## 📋 **Overview / ภาพรวม**

A comprehensive Python library implementing international structural design standards including ACI 318M-25 (USA) and Thai Ministry Regulation B.E. 2566. Designed for structural engineers, researchers, and software developers working on concrete and steel structure design.

ไลบรารี Python ที่ครอบคลุมสำหรับมาตรฐานการออกแบบโครงสร้างระดับนานาชาติ รวมถึง ACI 318M-25 (สหรัฐอเมริกา) และกฎกระทรวง พ.ศ. 2566 (ไทย) ออกแบบสำหรับวิศวกรโครงสร้าง นักวิจัย และนักพัฒนาซอฟต์แวร์ที่ทำงานด้านการออกแบบโครงสร้างคอนกรีตและเหล็ก

## 🎯 **Key Features / ฟีเจอร์หลัก**

### 🇺🇸 **ACI 318M-25 (International SI Units)**
- ✅ Complete concrete and steel material models
- ✅ Comprehensive member design (beams, columns, slabs, walls, footings)
- ✅ Load combinations and strength reduction factors
- ✅ Serviceability checks and deflection limits
- ✅ Detailing requirements and reinforcement design

### 🇹🇭 **Thai Standards (กฎกระทรวง พ.ศ. 2566)**
- ✅ Thai concrete grades (Fc180-Fc350) and steel grades (SD40, SD50, SR24)
- ✅ Wind load calculations per TIS 1311-50
- ✅ Seismic loads per TIS 1301/1302-61
- ✅ Thai unit conversions (ksc ↔ MPa, kgf ↔ N)
- ✅ Provincial wind and seismic zones
- ✅ Bilingual documentation (Thai/English)

### 🔧 **Core Features**
- ✅ Modular plugin-based architecture
- ✅ Cross-standard material property comparisons
- ✅ Comprehensive input validation
- ✅ Unit conversion utilities
- ✅ Professional-grade testing suite
- ✅ Type hints and modern Python practices

## 🚀 **Quick Start / เริ่มต้นใช้งาน**

### Installation / การติดตั้ง
```bash
pip install structural-design-standards
```

### Basic Usage / การใช้งานพื้นฐาน

#### ACI 318M-25 Example
```python
from structural_standards.aci.aci318m25 import ACI318M25Concrete, ACI318M25BeamDesign

# Create materials
concrete = ACI318M25Concrete(fc_prime=28.0)  # 28 MPa concrete
steel = ACI318M25Steel(grade='GRADE420')     # 420 MPa steel

# Design beam
beam_designer = ACI318M25BeamDesign(concrete, steel)
result = beam_designer.design_flexural_reinforcement(
    moment_ultimate=150.0,  # kN⋅m
    beam_width=300.0,       # mm
    beam_depth=500.0        # mm
)

print(f"Required reinforcement: {result['As_required_mm2']:.0f} mm²")
```

#### Thai Standards Example / ตัวอย่างมาตรฐานไทย
```python
from structural_standards.thai.ministry_2566 import ThaiConcrete, ThaiWindLoads

# Thai concrete material
concrete = ThaiConcrete(grade='Fc210')  # 210 ksc ≈ 21 MPa

# Wind load calculation
wind_calc = ThaiWindLoads()
wind_pressure = wind_calc.calculate_wind_pressure(
    province='กรุงเทพมหานคร',    # Bangkok
    building_height=30.0,        # meters
    terrain_category='urban'     # Urban terrain
)

print(f"Wind pressure: {wind_pressure['design_pressure']:.2f} kN/m²")
```

## 📖 **Documentation / เอกสาร**

- 📚 [**API Reference**](https://structural-design-standards.readthedocs.io/api/) - Complete API documentation
- 🎓 [**Tutorials**](https://structural-design-standards.readthedocs.io/tutorials/) - Step-by-step guides
- 📝 [**Examples**](https://github.com/your-org/structural-design-standards/tree/main/examples) - Real-world usage examples
- 🔬 [**Theory Manual**](https://structural-design-standards.readthedocs.io/theory/) - Theoretical background

## 🏗️ **Supported Standards / มาตรฐานที่รองรับ**

| Standard | Version | Status | Coverage |
|----------|---------|--------|----------|
| ACI 318M | ACI 318M-25 | ✅ Complete | Concrete structures |
| Thai Ministry Reg. | B.E. 2566 (2023) | ✅ Complete | All structural types |
| Thai Wind Loads | TIS 1311-50 | ✅ Complete | Wind analysis |
| Thai Seismic | TIS 1301/1302-61 | ✅ Complete | Earthquake analysis |
| Eurocode 2 | EN 1992 | 🚧 Planned | Concrete structures |
| Japanese AIJ | Latest | 🚧 Planned | All structural types |

## 🔧 **Installation & Development / การติดตั้งและพัฒนา**

### Requirements / ความต้องการ
- Python 3.8+
- NumPy ≥ 1.20.0
- SciPy ≥ 1.7.0
- Pandas ≥ 1.3.0

### Development Installation / การติดตั้งสำหรับพัฒนา
```bash
git clone https://github.com/your-org/structural-design-standards.git
cd structural-design-standards
pip install -e ".[dev]"
```

### Running Tests / การรันเทส
```bash
pytest tests/ -v
pytest tests/ --cov=structural_standards --cov-report=html
```

### Building Documentation / การสร้างเอกสาร
```bash
cd docs
make html
```

## 🌍 **Standards Coverage Map / แผนที่ความครอบคลุมมาตรฐาน**

```
🇺🇸 United States
├── ACI 318M-25 (SI Units) ✅
├── AISC 360 (Steel) 🚧
└── ASCE 7 (Loads) 🚧

🇹🇭 Thailand
├── Ministry Regulation 2566 ✅
├── TIS 1311-50 (Wind) ✅
├── TIS 1301/1302-61 (Seismic) ✅
└── มยผ. 1103/1104 (Materials) ✅

🇪🇺 Europe
├── Eurocode 2 (Concrete) 🚧
├── Eurocode 3 (Steel) 🚧
└── Eurocode 1 (Actions) 🚧

🇯🇵 Japan
├── AIJ Standards 🚧
└── JIS Standards 🚧
```

## 🤝 **Contributing / การมีส่วนร่วม**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

เรายินดีรับการมีส่วนร่วม! โปรดดู [คู่มือการมีส่วนร่วม](CONTRIBUTING.md) สำหรับรายละเอียด

### Development Workflow / ขั้นตอนการพัฒนา
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 **License / ใบอนุญาต**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

โปรเจกต์นี้อยู่ภายใต้ใบอนุญาต MIT - ดูรายละเอียดในไฟล์ [LICENSE](LICENSE)

## 🙏 **Acknowledgments / กิตติกรรมประกาศ**

- American Concrete Institute (ACI) for ACI 318M-25 standards
- Thai Industrial Standards Institute for TIS standards  
- Ministry of Interior, Thailand for Ministry Regulation B.E. 2566
- All contributors and users of this library

## 📞 **Support / การสนับสนุน**

- 📧 Email: support@structural-standards.org
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/structural-design-standards/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/structural-design-standards/issues)
- 📖 Documentation: [Read the Docs](https://structural-design-standards.readthedocs.io/)

---

**Made with ❤️ by Structural Engineers, for Structural Engineers**  
**สร้างด้วย ❤️ โดยวิศวกรโครงสร้าง เพื่อวิศวกรโครงสร้าง**