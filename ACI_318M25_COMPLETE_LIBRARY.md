> **ENGINEERING SAFETY NOTICE (2026-10-29): UNVERIFIED / DO NOT USE FOR DESIGN APPROVAL.**
> The ACI/Thai calculation library has unresolved code-compliance and integration
> gaps. Numerical fixes are in progress on the audit branch. Only limited,
> explicitly documented statics or sectional calculations are available;
> a "PASS" for one check does not certify a member or building. See
> [ENGINEERING_VALIDATION_STATUS.md](ENGINEERING_VALIDATION_STATUS.md).
> Current 2026 code applicability and site-specific inputs require independent
> licensed-engineer review.

# ACI 318M-25 Complete Member Design Library System
# ระบบไลบรารีการออกแบบสมาชิกโครงสร้างคอนกรีตเสริมเหล็กครบถ้วน ACI 318M-25

## 📋 Overview / ภาพรวม

The **ACI 318M-25 Complete Member Design Library System** is a comprehensive collection of standalone libraries for designing all major reinforced concrete structural members according to the American Concrete Institute's Building Code Requirements for Structural Concrete using the International System of Units (SI).

**ระบบไลบรารีการออกแบบสมาชิกโครงสร้างครบถ้วน ACI 318M-25** เป็นชุดไลบรารีแยกต่างหากที่ครอบคลุมการออกแบบสมาชิกโครงสร้างคอนกรีตเสริมเหล็กทุกประเภทหลักตามมาตรฐาน American Concrete Institute โดยใช้หน่วยระบบสากล (SI)

## 🎯 Key Standards / มาตรฐานหลัก

### ✨ **Based on ACI Standards**
- **ACI CODE-318M-25** - Building Code Requirements for Structural Concrete (International System of Units)
- **ACI 318RM-25** - Commentary on Building Code Requirements for Structural Concrete
- **ASTM A615/A615M** - Standard Specification for Deformed and Plain Carbon-Steel Bars
- **ASCE 7** - Compatible load combinations

## 🏗️ **Complete Member Library System / ระบบไลบรารีสมาชิกโครงสร้างครบถ้วน**

### 📚 **Individual Member Libraries**

| Library File | Member Type | Capabilities | Key Features |
|--------------|-------------|--------------|--------------|
| **`aci318m25_beam.py`** | Beams / คาน | Flexural & Shear Design | Moment capacity, shear reinforcement, deflection |
| **`aci318m25_column.py`** | Columns / เสา | Axial & P-M Interaction | Compression, P-M interaction, confinement |
| **`aci318m25_slab.py`** | Slabs / พื้น | One-way & Two-way Systems | Moment distribution, punching shear, deflection |
| **`aci318m25_footing.py`** | Footings / ฐานราก | Foundation Design | Bearing capacity, shear checks, reinforcement |
| **`aci318m25_wall.py`** | Walls / กำแพง | Bearing & Shear Walls | Stability, shear capacity, boundary elements |
| **`aci318m25_diaphragm.py`** | Diaphragms / ไดอะแฟรม | In-plane Shear Design | Collector elements, flexibility, chord forces |
| **`aci318m25_complete.py`** | Manager / ตัวจัดการ | Complete System | Central access, typical designs, reports |

### 🔧 **Core Base Library**
- **`aci318m25.py`** - Base ACI 318M-25 implementation with material properties, load combinations, and fundamental calculations

## 🌟 **Key Features / คุณสมบัติหลัก**

### ✨ **Comprehensive Design Capabilities**
- **Material Properties** - FC14 to FC100 concrete (14-100 MPa), Grade 280-520 steel
- **Load Combinations** - Complete ACI 318M-25 Section 5.3 combinations
- **Strength Reduction Factors** - φ factors per Section 21.2
- **Development Lengths** - Bar development and splice calculations
- **International SI Units** - Consistent MPa, kN, mm, m throughout

### 🔧 **Individual Member Features**

#### **Beam Design Library (`aci318m25_beam.py`)**
- **Flexural Design**: Rectangular and T-beam sections
- **Shear Design**: Stirrup design and spacing
- **Deflection Control**: Service load deflection calculations
- **Development Lengths**: Bar embedment requirements
- **Support Types**: Simply supported, fixed, continuous

#### **Column Design Library (`aci318m25_column.py`)**
- **Axial Capacity**: Compression design with slenderness effects
- **P-M Interaction**: Combined axial and moment loading
- **Confinement**: Tied and spiral column design
- **Load Conditions**: Uniaxial and biaxial bending
- **Seismic Provisions**: Special detailing requirements

#### **Slab Design Library (`aci318m25_slab.py`)**
- **One-way Slabs**: Simple span and continuous systems
- **Two-way Slabs**: Direct design method and equivalent frame
- **Punching Shear**: Column-slab connections
- **Minimum Thickness**: Deflection control requirements
- **Reinforcement**: Main, shrinkage, and temperature steel

#### **Footing Design Library (`aci318m25_footing.py`)**
- **Bearing Capacity**: Soil pressure distribution
- **Sizing**: Required dimensions for given loads
- **Shear Checks**: One-way and two-way (punching) shear
- **Reinforcement**: Flexural steel and development
- **Soil Conditions**: Various bearing capacity scenarios

#### **Wall Design Library (`aci318m25_wall.py`)**
- **Bearing Walls**: Gravity load design with slenderness
- **Shear Walls**: Lateral force resistance
- **Stability Analysis**: Buckling and second-order effects
- **Boundary Elements**: Special seismic detailing
- **Reinforcement**: Vertical and horizontal steel

#### **Diaphragm Design Library (`aci318m25_diaphragm.py`)**
- **In-plane Shear Design**: Diaphragm force distribution and capacity
- **Flexibility Assessment**: Rigid, semi-rigid, or flexible classification
- **Collector Elements**: Force transfer elements design
- **Chord Reinforcement**: Edge reinforcement for tension/compression
- **Seismic Provisions**: Special detailing for earthquake resistance

## 📊 **Material Properties / คุณสมบัติวัสดุ**

### **Concrete Strength Classes**

| Class | fc' (MPa) | Usage | Applications |
|-------|-----------|-------|--------------|
| **FC14** | 14 | Plain concrete | Non-structural elements |
| **FC21** | 21 | Normal structural | Standard applications |
| **FC28** | 28 | Standard structural | Most common for buildings |
| **FC35** | 35 | High-strength | Important structures |
| **FC50** | 50 | High-strength | High-rise buildings |
| **FC70** | 70 | High-performance | Special applications |
| **FC100** | 100 | Ultra-high-strength | Advanced structures |

### **Reinforcement Grades**

| Grade | fy (MPa) | fu (MPa) | ASTM Standard | Common Use |
|-------|----------|----------|---------------|------------|
| **Grade 280** | 280 | 420 | ASTM A615/A615M | Standard reinforcement |
| **Grade 420** | 420 | 620 | ASTM A615/A615M | Most common grade |
| **Grade 520** | 520 | 690 | ASTM A615/A615M | High-strength applications |

### **Metric Reinforcing Bars**

| Bar Size | Diameter (mm) | Area (mm²) | Imperial Equivalent |
|----------|---------------|------------|-------------------|
| **10M** | 11.3 | 100 | ≈ #3 |
| **15M** | 16.0 | 200 | ≈ #5 |
| **20M** | 19.5 | 300 | ≈ #6 |
| **25M** | 25.2 | 500 | ≈ #8 |
| **30M** | 29.9 | 700 | ≈ #9 |
| **35M** | 35.7 | 1000 | ≈ #11 |
| **45M** | 43.7 | 1500 | ≈ #14 |
| **55M** | 56.4 | 2500 | ≈ #18 |

## 📚 **Usage Examples / ตัวอย่างการใช้งาน**

### **1. Individual Member Design**

```python
# Beam Design
from aci318m25_beam import ACI318M25BeamDesign, BeamGeometry, BeamType
from aci318m25 import ConcreteStrengthClass, ReinforcementGrade

beam_design = ACI318M25BeamDesign()
material_props = beam_design.aci.get_material_properties(
    ConcreteStrengthClass.FC28, ReinforcementGrade.GRADE420
)

beam_geometry = BeamGeometry(
    length=6000, width=300, height=600, effective_depth=540,
    cover=40, flange_width=0, flange_thickness=0,
    beam_type=BeamType.RECTANGULAR
)

result = beam_design.perform_complete_beam_design(
    mu=180.0,  # 180 kN⋅m
    vu=120.0,  # 120 kN
    beam_geometry=beam_geometry,
    material_props=material_props
)

print(f"Main reinforcement: {result.reinforcement.main_bars}")
print(f"Stirrups: {result.reinforcement.stirrups}@{result.reinforcement.stirrup_spacing:.0f}mm")
```

### **2. Complete Building Design**

```python
# Complete Member Library Manager
from aci318m25_complete import ACI318M25MemberLibrary, ProjectInfo

library = ACI318M25MemberLibrary()

# Design typical office building
design_results = library.design_typical_office_building_members(
    building_height=24.0,  # 24m building
    typical_span=7.0       # 7m spans
)

# Generate report
project_info = ProjectInfo(
    project_name="Office Building",
    location="Bangkok, Thailand",
    date="2024-01-15",
    engineer="Professional Engineer"
)

report = library.generate_design_summary_report(design_results, project_info)
```

### **3. Column P-M Interaction**

```python
# Column Design with P-M Interaction
from aci318m25_column import ACI318M25ColumnDesign, ColumnGeometry, ColumnLoads
from aci318m25_column import ColumnType, ColumnShape, LoadCondition

column_design = ACI318M25ColumnDesign()

column_geometry = ColumnGeometry(
    width=400, depth=400, height=3000, cover=40,
    shape=ColumnShape.RECTANGULAR, column_type=ColumnType.TIED,
    effective_length=3000
)

column_loads = ColumnLoads(
    axial_force=1200,      # 1200 kN
    moment_x=180,          # 180 kN⋅m
    moment_y=0, shear_x=0, shear_y=0,
    load_condition=LoadCondition.UNIAXIAL_BENDING
)

result = column_design.perform_complete_column_design(
    column_loads, column_geometry, material_props
)

print(f"Interaction ratio: {result.capacity.interaction_ratio:.2f}")
print(f"Longitudinal bars: {result.reinforcement.longitudinal_bars}")
```

### **4. Two-Way Slab Design**

```python
# Two-Way Slab Design
from aci318m25_slab import ACI318M25SlabDesign, SlabGeometry, SlabLoads
from aci318m25_slab import SlabType, SupportCondition, LoadPattern

slab_design = ACI318M25SlabDesign()

slab_geometry = SlabGeometry(
    length_x=6000, length_y=8000, thickness=200, cover=20,
    effective_depth_x=172, effective_depth_y=165,
    slab_type=SlabType.TWO_WAY_FLAT,
    support_conditions={
        'x1': SupportCondition.CONTINUOUS,
        'x2': SupportCondition.CONTINUOUS,
        'y1': SupportCondition.CONTINUOUS,
        'y2': SupportCondition.CONTINUOUS
    }
)

slab_loads = SlabLoads(
    dead_load=6.0, live_load=3.0, superimposed_dead=1.5,
    load_pattern=LoadPattern.UNIFORM,
    load_factors={'D': 1.4, 'L': 1.6}
)

result = slab_design.perform_complete_slab_design(
    slab_geometry, slab_loads, material_props, column_size=(400, 400)
)

print(f"X-direction: {result.reinforcement.main_bars_x}@{result.reinforcement.main_spacing_x:.0f}mm")
print(f"Y-direction: {result.reinforcement.main_bars_y}@{result.reinforcement.main_spacing_y:.0f}mm")
```

## ⚖️ **Load Combinations (ACI 318M-25 Section 5.3)**

### **Strength Design:**
1. **Eq. (5.3.1a)**: `1.4D`
2. **Eq. (5.3.1b)**: `1.2D + 1.6L + 0.5(Lr or S or R)`
3. **Eq. (5.3.1c)**: `1.2D + 1.6(Lr or S or R) + (1.0L or 0.5W)`
4. **Eq. (5.3.1d)**: `1.2D + 1.0W + 1.0L + 0.5(Lr or S or R)`
5. **Eq. (5.3.1e)**: `1.2D + 1.0E + 1.0L + 0.2S`
6. **Eq. (5.3.1f)**: `0.9D + 1.0W` (uplift)
7. **Eq. (5.3.1g)**: `0.9D + 1.0E` (uplift)

### **Service Load:**
1. **Service-1**: `1.0D + 1.0L`
2. **Service-2**: `1.0D + 1.0W`
3. **Service-3**: `1.0D + 1.0E`

## 🔧 **Strength Reduction Factors (φ)**

| Failure Mode | φ Factor | Application |
|--------------|----------|-------------|
| **Tension-controlled** | 0.90 | Flexural members with adequate ductility |
| **Compression-controlled (tied)** | 0.65 | Tied columns and compression members |
| **Compression-controlled (spiral)** | 0.75 | Spiral columns and confined members |
| **Shear** | 0.75 | Shear and torsion |
| **Bearing** | 0.65 | Bearing on concrete |

## 🧪 **Testing / การทดสอบ**

### **Run Individual Library Tests:**

```bash
# Test individual libraries
python test_aci318m25.py              # Core library
python test_aci318m25_complete.py     # All member libraries

# Test complete system
python aci318m25_complete.py          # Manager with examples
```

### **Test Coverage:**
- ✅ **Material Properties** - All concrete and steel grades
- ✅ **Load Combinations** - Complete ACI 318M-25 combinations
- ✅ **Member Design** - All major structural members
- ✅ **Integration** - Cross-library compatibility
- ✅ **Examples** - Practical design scenarios
- ✅ **Reports** - Comprehensive documentation

## 📦 **Installation & Setup**

### **Requirements:**
```python
python>=3.7
typing      # Type hints
dataclasses # Data structures
enum        # Enumerations
math        # Mathematical functions
```

### **Installation:**
1. Copy all library files to your project:
   - `aci318m25.py` (core library)
   - `aci318m25_beam.py`
   - `aci318m25_column.py`
   - `aci318m25_slab.py`
   - `aci318m25_footing.py`
   - `aci318m25_wall.py`
   - `aci318m25_complete.py` (manager)

2. Import and use:
```python
from aci318m25_complete import ACI318M25MemberLibrary
library = ACI318M25MemberLibrary()
```

## 🌟 **Use Cases / กรณีการใช้งาน**

### **1. Structural Design Offices**
- **Complete Building Design** - All members in one system
- **Code Compliance** - ACI 318M-25 requirements
- **Design Reports** - Professional documentation
- **Quality Assurance** - Consistent methodology

### **2. Engineering Software Integration**
- **CAD Integration** - Export to ETABS, SAP2000, STAAD
- **API Access** - Individual member libraries
- **Batch Processing** - Multiple designs
- **Custom Applications** - Building-specific tools

### **3. Educational Applications**
- **Teaching Tool** - ACI 318M-25 concepts
- **Student Projects** - Hands-on design experience
- **Research** - Advanced analysis capabilities
- **Code Learning** - Step-by-step methodology

### **4. International Projects**
- **SI Unit Projects** - Global compatibility
- **Multi-national Teams** - Common standards
- **Software Compatibility** - International tools
- **Documentation** - English/Thai bilingual

## 🔗 **Integration Examples**

### **Example 1: Complete Building Analysis**

```python
# Integrated building design workflow
from aci318m25_complete import ACI318M25MemberLibrary
from aci318m25_beam import BeamGeometry, BeamType
from aci318m25_column import ColumnGeometry, ColumnLoads

# Initialize complete system
library = ACI318M25MemberLibrary()

# Get standard materials
materials = library.create_standard_material_properties()

# Design complete building
building_results = library.design_typical_office_building_members(
    building_height=30.0,  # 30m building
    typical_span=8.0       # 8m spans
)

# Access individual member results
beam_result = building_results['beam']['design_result']
column_result = building_results['column']['design_result']

print(f"Beam utilization: {beam_result.utilization_ratio:.2f}")
print(f"Column utilization: {column_result.utilization_ratio:.2f}")
```

### **Example 2: Custom Design Workflow**

```python
# Custom workflow using individual libraries
from aci318m25_beam import ACI318M25BeamDesign
from aci318m25_column import ACI318M25ColumnDesign
from aci318m25_footing import ACI318M25FootingDesign

class CustomStructuralDesign:
    def __init__(self):
        self.beam_design = ACI318M25BeamDesign()
        self.column_design = ACI318M25ColumnDesign()
        self.footing_design = ACI318M25FootingDesign()
    
    def design_frame_system(self, geometry, loads):
        """Custom frame design combining multiple members"""
        # Design beams
        beam_result = self.beam_design.perform_complete_beam_design(...)
        
        # Design columns with beam reactions
        column_result = self.column_design.perform_complete_column_design(...)
        
        # Design footings with column loads
        footing_result = self.footing_design.perform_complete_footing_design(...)
        
        return {
            'beam': beam_result,
            'column': column_result,
            'footing': footing_result
        }
```

## 📈 **Comparison with Other Systems**

| Feature | ACI 318M-25 Libraries | Thai Building Code | Eurocode 2 |
|---------|----------------------|-------------------|------------|
| **Units** | SI (MPa, kN, mm) | Mixed (ksc/MPa) | SI (MPa, kN, mm) |
| **Concrete Range** | 14-100 MPa | 180-500 ksc | 12-90 MPa |
| **Steel Grades** | 280-520 MPa | SD40-SD50 | B500A-B500C |
| **Load Combinations** | ASCE 7 based | Ministry Reg. | EN 1990 |
| **Phi Factors** | 0.65-0.90 | Safety factors | γ = 1.15-1.50 |
| **International Use** | Global | Thailand | Europe |

## 🛠️ **Advanced Features**

### **1. P-M Interaction Diagrams**
- Comprehensive column analysis
- Biaxial bending capabilities
- Slenderness effects
- Confinement considerations

### **2. Deflection Control**
- Immediate and long-term deflection
- Cracked section analysis
- Service load calculations
- Code limit checks

### **3. Development Length Calculations**
- Bar size effects
- Concrete strength influence
- Modification factors
- Hook and lap splice requirements

### **4. Seismic Design Provisions**
- Special moment frames
- Shear wall design
- Boundary element requirements
- Ductility considerations

## 📄 **Standards References**

- **ACI 318M-25**: Building Code Requirements for Structural Concrete (Metric)
- **ACI 318RM-25**: Commentary on Building Code Requirements for Structural Concrete
- **ASTM A615/A615M**: Standard Specification for Deformed and Plain Carbon-Steel Bars
- **ASCE 7**: Minimum Design Loads and Associated Criteria for Buildings
- **ACI 301**: Specifications for Structural Concrete
- **ACI 435R**: Control of Deflection in Concrete Structures

## 🔮 **Future Enhancements**

### **Planned Features:**
- **Prestressed Concrete** - Post-tensioned members
- **Advanced Analysis** - Nonlinear capabilities
- **Seismic Detailing** - Enhanced earthquake provisions
- **BIM Integration** - Building Information Modeling
- **Cloud API** - Web-based access
- **Mobile Apps** - Field calculation tools

## 📄 **License**

This comprehensive library system follows the same license terms as the original twoWaySlab project while providing complete ACI 318M-25 functionality for international structural concrete design.

---

**ACI 318M-25 Complete Member Design Library System v1.0** - Comprehensive implementation of ACI Building Code Requirements for Structural Concrete using International System of Units (SI).

**ระบบไลบรารีการออกแบบสมาชิกโครงสร้างครบถ้วน ACI 318M-25 v1.0** - การนำมาตรฐาน ACI สำหรับคอนกรีตเสริมเหล็กมาใช้อย่างครบถ้วนด้วยหน่วยระบบสากล (SI)

Complete structural concrete design capabilities supporting modern international engineering practice with full ACI 318M-25 compliance across all major structural members.