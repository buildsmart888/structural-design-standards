> **ENGINEERING SAFETY NOTICE (2026-10-29): UNVERIFIED / DO NOT USE FOR DESIGN APPROVAL.**
> The ACI/Thai calculation library has unresolved code-compliance and integration
> gaps. Numerical fixes are in progress on the audit branch. Only limited,
> explicitly documented statics or sectional calculations are available;
> a "PASS" for one check does not certify a member or building. See
> [ENGINEERING_VALIDATION_STATUS.md](ENGINEERING_VALIDATION_STATUS.md).
> Current 2026 code applicability and site-specific inputs require independent
> licensed-engineer review.

# ACI 318M-25 Building Code Library
# Building Code Requirements for Structural Concrete (International System of Units)

## 📋 Overview

The **ACI 318M-25 Building Code Library** is a comprehensive implementation of the American Concrete Institute's Building Code Requirements for Structural Concrete using the International System of Units (SI). This library provides complete structural concrete design capabilities according to the latest ACI 318M-25 standards.

## 🎯 Key Standards

### ✨ **Based on ACI Standards**
- **ACI CODE-318M-25** - Building Code Requirements for Structural Concrete (International System of Units)
- **ACI 318RM-25** - Commentary on Building Code Requirements for Structural Concrete
- **ASTM Standards** - Referenced material specifications
- **ASCE 7** - Compatible load combinations

## 🏗️ **Core Features**

### ✨ **Material Properties**
- **Concrete Strength Classes** - FC14 to FC100 (14 MPa to 100 MPa)
- **Reinforcement Grades** - Grade 280, 420, and 520 (280 to 520 MPa)
- **Modulus Calculations** - Concrete and steel elastic moduli
- **Material Compatibility** - ASTM A615/A615M specifications

### 🔧 **Design Capabilities**
- **Load Combinations** - Complete ACI 318M-25 Section 5.3 combinations
- **Strength Reduction Factors** - φ factors per Section 21.2
- **Reinforcement Design** - Min/max reinforcement ratios
- **Development Length** - Bar development and splice lengths
- **Deflection Control** - Long-term and immediate deflection limits
- **Crack Control** - Service load crack width limitations

### 📊 **International System Features**
- **Consistent SI Units** - MPa, kN, mm, m throughout
- **Metric Bar Sizes** - 10M to 55M designations plus Imperial reference
- **International Compatibility** - Works with global design software
- **Unit Conversion Ready** - Easy integration with other unit systems

## 📚 **Usage Examples**

### Basic Usage:

```python
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade

# Initialize ACI 318M-25 calculator
aci = ACI318M25()

# Get material properties
material_props = aci.get_material_properties(
    ConcreteStrengthClass.FC28, 
    ReinforcementGrade.GRADE420
)

print(f"Concrete: fc' = {material_props.fc_prime} MPa")
print(f"Steel: fy = {material_props.fy} MPa")
print(f"Concrete modulus: Ec = {material_props.ec:.0f} MPa")
```

### Load Combinations:

```python
# Office building loads
loads = {
    'D': 6.5,   # Dead load (kN/m²)
    'L': 2.4,   # Live load (kN/m²)
    'W': 1.8,   # Wind load (kN/m²)
    'E': 1.2    # Earthquake load (kN/m²)
}

# Check strength design combinations
combinations = aci.check_load_combinations(loads, 'strength')

for combo in combinations[:3]:  # Show first 3
    print(f"{combo['name']}: {combo['factored_load']:.2f} kN/m²")

# Find governing combination
governing = max(combinations, key=lambda x: x['factored_load'])
print(f"Governing: {governing['name']} = {governing['factored_load']:.2f} kN/m²")
```

### Reinforcement Design:

```python
# Calculate reinforcement requirements
fc_prime = 28.0  # MPa
fy = 420.0       # MPa

rho_min = aci.calculate_minimum_reinforcement_ratio(fc_prime, fy)
rho_max = aci.calculate_maximum_reinforcement_ratio(fc_prime, fy)
rho_balanced = aci.calculate_balanced_reinforcement_ratio(fc_prime, fy)

print(f"Minimum reinforcement ratio: {rho_min:.4f}")
print(f"Balanced reinforcement ratio: {rho_balanced:.4f}")
print(f"Maximum reinforcement ratio: {rho_max:.4f} (tension-controlled)")

# Development length calculation
bar_size = '20M'
ld = aci.calculate_development_length(bar_size, fc_prime, fy)
print(f"Development length for {bar_size}: {ld:.0f} mm")
```

### Complete Design Report:

```python
# Project information
project_info = {
    'project_name': 'Office Building Slab Design',
    'location': 'Example Project',
    'date': '2024-01-15',
    'engineer': 'Professional Engineer'
}

# Generate comprehensive report
report = aci.generate_design_summary_report(
    project_info, 
    ConcreteStrengthClass.FC28,
    ReinforcementGrade.GRADE420,
    loads
)

# Save report
with open('aci_design_report.txt', 'w') as f:
    f.write(report)
```

## 🏛️ **Concrete Strength Classes**

| Class | fc' (MPa) | Usage | Min Cement (kg/m³) | Max w/c |
|-------|-----------|-------|-------------------|---------|
| **FC14** | 14 | Plain concrete, non-structural | 280 | 0.70 |
| **FC17** | 17 | Plain concrete, footings | 300 | 0.65 |
| **FC21** | 21 | Structural concrete, normal | 320 | 0.60 |
| **FC28** | 28 | Structural concrete, standard | 350 | 0.55 |
| **FC35** | 35 | High-strength applications | 375 | 0.50 |
| **FC42** | 42 | High-strength structural | 400 | 0.45 |
| **FC50** | 50 | High-strength structural | 425 | 0.40 |
| **FC70** | 70 | High-performance concrete | 475 | 0.35 |
| **FC100** | 100 | Ultra-high-strength concrete | 550 | 0.28 |

## 🔩 **Reinforcement Grades**

| Grade | fy (MPa) | fu (MPa) | ASTM Specification | Common Usage |
|-------|----------|----------|-------------------|--------------|
| **Grade 280** | 280 | 420 | ASTM A615/A615M | Standard reinforcement |
| **Grade 420** | 420 | 620 | ASTM A615/A615M | Most common grade |
| **Grade 520** | 520 | 690 | ASTM A615/A615M | High-strength applications |

## 📏 **Metric Reinforcing Bars**

| Bar Size | Diameter (mm) | Area (mm²) | Equivalent Imperial |
|----------|---------------|------------|-------------------|
| **10M** | 11.3 | 100 | #3 (approximately) |
| **15M** | 16.0 | 200 | #5 (approximately) |
| **20M** | 19.5 | 300 | #6 (approximately) |
| **25M** | 25.2 | 500 | #8 (approximately) |
| **30M** | 29.9 | 700 | #9 (approximately) |
| **35M** | 35.7 | 1000 | #11 (approximately) |
| **45M** | 43.7 | 1500 | #14 (approximately) |
| **55M** | 56.4 | 2500 | #18 (approximately) |

## 🛡️ **Concrete Cover Requirements**

### Cast-in-Place Concrete (mm)

| Element | Normal | Corrosive | Severe |
|---------|--------|-----------|--------|
| **Slab** | 20 | 25 | 30 |
| **Beam** | 40 | 50 | 65 |
| **Column** | 40 | 50 | 65 |
| **Wall** | 20 | 25 | 40 |
| **Footing** | 75 | 100 | 150 |

### Precast Concrete (mm)

| Element | Normal | Corrosive | Severe |
|---------|--------|-----------|--------|
| **Slab** | 15 | 20 | 25 |
| **Beam** | 25 | 40 | 50 |

## ⚖️ **Load Combinations (ACI 318M-25 Section 5.3)**

### Strength Design:

1. **Eq. (5.3.1a)**: `1.4D`
2. **Eq. (5.3.1b)**: `1.2D + 1.6L + 0.5(Lr or S or R)`
3. **Eq. (5.3.1c)**: `1.2D + 1.6(Lr or S or R) + (1.0L or 0.5W)`
4. **Eq. (5.3.1d)**: `1.2D + 1.0W + 1.0L + 0.5(Lr or S or R)`
5. **Eq. (5.3.1e)**: `1.2D + 1.0E + 1.0L + 0.2S`
6. **Eq. (5.3.1f)**: `0.9D + 1.0W` (uplift)
7. **Eq. (5.3.1g)**: `0.9D + 1.0E` (uplift)

### Service Load:

1. **Service-1**: `1.0D + 1.0L`
2. **Service-2**: `1.0D + 1.0W`
3. **Service-3**: `1.0D + 1.0E`

## 🔧 **Strength Reduction Factors (φ)**

| Failure Mode | φ Factor |
|--------------|----------|
| Tension-controlled | 0.90 |
| Compression-controlled (tied) | 0.65 |
| Compression-controlled (spiral) | 0.75 |
| Shear | 0.75 |
| Torsion | 0.75 |
| Bearing on concrete | 0.65 |
| Plain concrete | 0.60 |

## 📐 **Deflection Limits (ACI 318M-25 Table 24.2.2)**

### Immediate Deflection:

- **Flat roof**: L/180
- **Floor**: L/360
- **Roof/floor supporting non-structural**: L/240

### Long-term Deflection:

- **Supporting non-structural elements**: L/480
- **Not supporting non-structural**: L/240

## ⚙️ **API Reference**

### Core Classes:

#### `ACI318M25`
Main calculation class for ACI 318M-25 design.

**Key Methods:**
- `get_material_properties(concrete_class, steel_grade)` - Get complete material properties
- `check_load_combinations(loads, combination_type)` - Calculate load combinations
- `get_concrete_cover(element, exposure)` - Get cover requirements
- `calculate_development_length(bar_size, fc_prime, fy)` - Development length
- `calculate_minimum_reinforcement_ratio(fc_prime, fy)` - Minimum reinforcement
- `calculate_maximum_reinforcement_ratio(fc_prime, fy)` - Maximum reinforcement
- `generate_design_summary_report(...)` - Generate comprehensive report

#### `ConcreteStrengthClass`
Enumeration of concrete strength classes.

```python
ConcreteStrengthClass.FC14   # 14 MPa
ConcreteStrengthClass.FC21   # 21 MPa
ConcreteStrengthClass.FC28   # 28 MPa
ConcreteStrengthClass.FC35   # 35 MPa
ConcreteStrengthClass.FC50   # 50 MPa
ConcreteStrengthClass.FC70   # 70 MPa
ConcreteStrengthClass.FC100  # 100 MPa
```

#### `ReinforcementGrade`
Enumeration of reinforcement grades.

```python
ReinforcementGrade.GRADE280  # 280 MPa yield strength
ReinforcementGrade.GRADE420  # 420 MPa yield strength
ReinforcementGrade.GRADE520  # 520 MPa yield strength
```

#### `StructuralElement`
Enumeration of structural elements for cover requirements.

```python
StructuralElement.SLAB
StructuralElement.BEAM
StructuralElement.COLUMN
StructuralElement.WALL
StructuralElement.FOOTING
```

### Data Classes:

#### `MaterialProperties`
```python
@dataclass
class MaterialProperties:
    fc_prime: float        # Specified compressive strength (MPa)
    fy: float             # Specified yield strength (MPa)
    fu: float             # Specified tensile strength (MPa)
    es: float             # Modulus of elasticity of steel (MPa)
    ec: float             # Modulus of elasticity of concrete (MPa)
    gamma_c: float        # Unit weight of concrete (kN/m³)
    description: str
```

## 🧪 **Testing**

### Run Tests:

```bash
# Run comprehensive tests
python test_aci318m25.py
```

**Test Coverage:**
- ✅ Material properties and calculations
- ✅ Load combinations per ACI 318M-25
- ✅ Reinforcement design methods
- ✅ Development length calculations
- ✅ Crack control and deflection
- ✅ Design report generation
- ✅ Integration compatibility

### Expected Output:
```
🎉 ALL TESTS PASSED! ACI 318M-25 Library is ready to use.
📚 The library can now be integrated with existing projects.
```

## 📦 **Installation & Setup**

### Requirements:
```python
# Required packages
python>=3.7
typing      # For type hints
dataclasses # For data structures
enum        # For enumerations
math        # For calculations
```

### Installation:
1. Copy `aci318m25.py` to your project
2. Import and use:

```python
from aci318m25 import ACI318M25
aci = ACI318M25()
```

## 🌟 **Use Cases**

### 1. **Structural Design Software Integration**
- Import into ETABS, SAP2000, STAAD
- Automated concrete design per ACI 318M-25
- International project compatibility

### 2. **Engineering Consulting**
- Quick design checks and calculations
- Client presentations with ACI compliance
- Detailed analysis reports

### 3. **Educational Applications**
- Teaching concrete design principles
- Demonstrating ACI 318M-25 provisions
- Student calculation tools

### 4. **International Projects**
- Projects requiring SI units
- Multi-national design teams
- Global design software compatibility

## 🔗 **Integration Examples**

### Example 1: Integration with Existing twoWaySlab:

```python
# In your main structural analysis
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade
from thiRc import ThaiRc_set

# Initialize both systems
aci = ACI318M25()
thai_rc = ThaiRc_set()

# Compare design approaches
aci_material = aci.get_material_properties(ConcreteStrengthClass.FC28, ReinforcementGrade.GRADE420)
thai_fc = thai_rc.get_concrete_strength('Fc280', 'mpa')  # Similar strength

print(f"ACI 318M-25: fc' = {aci_material.fc_prime} MPa")
print(f"Thai TIS: fc = {thai_fc} MPa")
```

### Example 2: Multi-Code Analysis:

```python
# Create comparative analysis tool
class MultiCodeAnalysis:
    def __init__(self):
        self.aci = ACI318M25()
        
    def compare_reinforcement_ratios(self, fc_prime, fy):
        # ACI 318M-25 approach
        aci_rho_min = self.aci.calculate_minimum_reinforcement_ratio(fc_prime, fy)
        aci_rho_max = self.aci.calculate_maximum_reinforcement_ratio(fc_prime, fy)
        
        results = {
            'aci_318m25': {
                'rho_min': aci_rho_min,
                'rho_max': aci_rho_max,
                'code': 'ACI 318M-25'
            }
        }
        
        return results
```

## 📈 **Comparison with Other Codes**

| Parameter | ACI 318M-25 | Thai TIS | Eurocode 2 |
|-----------|-------------|----------|------------|
| **Units** | SI (MPa, kN, mm) | Mixed (ksc/MPa) | SI (MPa, kN, mm) |
| **Concrete Classes** | FC14-FC100 | Fc180-Fc500 | C12/15-C90/105 |
| **Steel Grades** | 280-520 MPa | SD40-SD50 | B500A-B500C |
| **φ Factors** | 0.65-0.90 | N/A (safety factors) | γ = 1.15-1.50 |
| **Load Combinations** | ASCE 7 based | Ministry Reg. | EN 1990 |

## 🆚 **ACI 318-19 vs ACI 318M-25**

| Feature | ACI 318-19 | ACI 318M-25 |
|---------|-------------|-------------|
| **Units** | US Customary (psi, kips) | International SI (MPa, kN) |
| **Concrete** | 3000-8000+ psi | 14-100+ MPa |
| **Steel** | 40-80 ksi | 280-520 MPa |
| **Bars** | #3-#18 | 10M-55M + Imperial |
| **Cover** | inches | millimeters |
| **Global Use** | US projects | International projects |

## 📄 **Standards References**

- **ACI 318M-25**: Building Code Requirements for Structural Concrete (Metric)
- **ACI 318RM-25**: Commentary on Building Code Requirements for Structural Concrete
- **ASTM A615/A615M**: Standard Specification for Deformed and Plain Carbon-Steel Bars
- **ASCE 7**: Minimum Design Loads and Associated Criteria for Buildings
- **ACI 435R**: Control of Deflection in Concrete Structures

## 🛠️ **License**

This library follows the same license terms as the original twoWaySlab project while providing comprehensive ACI 318M-25 functionality for international structural concrete design.

---

**ACI 318M-25 Building Code Library v1.0** - Complete implementation of ACI Building Code Requirements for Structural Concrete using International System of Units (SI).

Comprehensive structural concrete design capabilities supporting modern international engineering practice with full ACI 318M-25 compliance.