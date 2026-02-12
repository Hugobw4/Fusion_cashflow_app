# PyFECONS Full Port — Implementation Plan

> **Goal:** Strip out the simplified costing module and replace it with a full-depth port of [PyFECONS](https://github.com/Woodruff-Scientific-Ltd/PyFECONS), preserving backward compatibility with the rest of the application via an adapter layer.

---

## Current State

### Files to Replace (7 simplified costing files)

| File | Purpose | Issues |
|------|---------|--------|
| `costing/total_cost.py` | Main entry `compute_total_epc_cost(config)` | Hardcoded $200M tritium, $85M instr., $150M materials; missing CAS 25/28/50/60/70/80/90/LCOE |
| `costing/geometry.py` | `ReactorGeometry` volume calcs | Only torus (MFE) and sphere (IFE); no mirror cylinder |
| `costing/power_balance.py` | `PowerBalance` class | No neutron multiplication, simplified LCOE with no discount rate |
| `costing/materials.py` | Material DB (~20 materials) | Missing manufacturing factors, incomplete properties |
| `costing/reactor_equipment.py` | CAS 22.01 reactor core | Missing CAS 22.04–22.07 sub-accounts |
| `costing/magnets.py` | CAS 22.03 magnets | Limited to 3 magnet types, no PF/central solenoid split |
| `costing/buildings.py` | CAS 21 + CAS 23/24/26 | Only 5 building types vs PyFECONS 17; percentage-based turbine/electrical |
| `costing/enums.py` | Enums | Missing blanket coolant, neutron multiplier, structure PGA, region enums |

### Integration Points (must remain working)

| Consumer File | What It Uses | Key Lines |
|---------------|-------------|-----------|
| `core/power_to_epc.py` | `compute_total_epc_cost(config) → dict` | L13 import, L173 call, L113-168 config build, L178-252 result translation |
| `core/cashflow_engine.py` | `compute_epc(config)` → `total_epc`, `power_balance.q_eng` | L23 import, L712-717 usage |
| `ui/dashboard.py` | `compute_epc`, `compute_total_epc_cost`, `detailed_result` dict keys | L860-895, L976/1648 |
| `ui/costing_panel.py` | `create_costing_panel(epc_results, config)`, all CAS keys | L27 entry, L194-259 tree, L410-488 levers |
| `visualization/bokeh_plots.py` | Cost breakdown dict for charts | Various |

### Required Output Dict Keys (backward compat)

```python
{
    "power_balance": {...},
    "q_eng": float,
    "volumes": {...},
    "cas_2201": float,       # CAS 22.01 reactor equipment
    "cas_2203": float,       # CAS 22.03 magnets
    "heating_systems": float,
    "coolant_system": float,
    "tritium_systems": float,
    "instrumentation": float,
    "cas_21_total": float,
    "cas_22_total": float,
    "cas_23_turbine": float,
    "cas_24_electrical": float,
    "cas_26_cooling": float,
    "cas_27_materials": float,
    "cas_29_contingency": float,
    "cas_30_indirect": float,
    "cas_10_preconstruction": float,
    "cas_40_owner_costs": float,
    "total_capital_cost": float,
    "total_epc_cost": float,
    "cost_per_kw_net": float,
    "epc_per_kw_net": float,
}
```

---

## Target Architecture

```
src/fusion_cashflow/costing/
├── __init__.py                  # re-exports compute_total_epc_cost (adapter)
├── adapter.py                   # backward-compat wrapper
├── units.py                     # M_USD, USD, MW, Meters, etc.
├── enums.py                     # full PyFECONS enums
├── materials.py                 # full material database
├── costing_data.py              # CostingData master dataclass
├── inputs/                      # input dataclasses per CAS
│   ├── __init__.py
│   ├── basic.py                 # BasicInputs (p_nrl, p_et, etc.)
│   ├── power_balance.py         # PowerBalanceInputs
│   ├── cas10.py                 # CAS 10 inputs
│   ├── cas21.py                 # CAS 21 inputs
│   ├── cas220101.py             # CAS 22.01.01 inputs
│   ├── cas220102.py             # CAS 22.01.02 inputs
│   ├── cas220103.py             # CAS 22.01.03 inputs
│   ├── cas220104.py             # CAS 22.01.04 inputs
│   ├── cas220105.py             # CAS 22.01.05 inputs
│   ├── cas220106.py             # CAS 22.01.06 inputs
│   ├── cas220107.py             # CAS 22.01.07 inputs
│   ├── cas2202.py               # CAS 22.02 main heat transfer
│   ├── cas2203.py               # CAS 22.03 magnets
│   ├── cas2204.py               # CAS 22.04 supplementary heating
│   ├── cas2205.py               # CAS 22.05 primary structure
│   ├── cas2206.py               # CAS 22.06 vacuum system
│   ├── cas2207.py               # CAS 22.07 power supplies
│   ├── cas23.py                 # CAS 23 turbine
│   ├── cas24.py                 # CAS 24 electrical
│   ├── cas25.py                 # CAS 25 heat rejection (misc)
│   ├── cas26.py                 # CAS 26 heat rejection
│   ├── cas27.py                 # CAS 27 fuel handling
│   ├── cas28.py                 # CAS 28 instrumentation
│   ├── cas29.py                 # CAS 29 contingency
│   ├── cas30.py                 # CAS 30 indirect (construction)
│   ├── cas40.py                 # CAS 40 owner costs
│   ├── cas50.py                 # CAS 50 capitalized supplementary
│   ├── cas60.py                 # CAS 60 capitalized O&M
│   ├── cas70.py                 # CAS 70 annualized O&M
│   ├── cas80.py                 # CAS 80 annualized fuel
│   └── cas90.py                 # CAS 90 annualized financial
├── categories/                  # output dataclasses per CAS
│   ├── __init__.py
│   ├── cas10.py
│   ├── cas21.py
│   ├── cas22.py                 # + all sub-accounts
│   ├── cas23.py
│   ├── cas24.py
│   ├── cas25.py
│   ├── cas26.py
│   ├── cas27.py
│   ├── cas28.py
│   ├── cas29.py
│   ├── cas30.py
│   ├── cas40.py
│   ├── cas50.py
│   ├── cas60.py
│   ├── cas70.py
│   ├── cas80.py
│   ├── cas90.py
│   └── lcoe.py
├── calculations/                # actual calculation modules
│   ├── __init__.py
│   ├── volume.py                # radial build → volumes
│   ├── conversions.py           # k_to_m_usd, unit helpers
│   ├── thermal.py               # blanket gain, thermal cycle
│   ├── cas10.py
│   ├── cas21.py
│   ├── cas220101.py             # first wall / blanket / shield
│   ├── cas220102.py             # high-temp shield
│   ├── cas220103.py             # magnet calcs (TF, PF, CS)
│   ├── cas220104.py             # supplementary heating (MFE)
│   ├── cas220105.py             # primary structure
│   ├── cas220106.py             # vacuum system
│   ├── cas220107.py             # power supplies
│   ├── cas2202.py               # main heat transfer
│   ├── cas23.py
│   ├── cas24.py
│   ├── cas25.py
│   ├── cas26.py
│   ├── cas27.py
│   ├── cas28.py
│   ├── cas29.py
│   ├── cas30.py
│   ├── cas40.py
│   ├── cas50.py
│   ├── cas60.py
│   ├── cas70.py
│   ├── cas80.py
│   ├── cas90.py
│   └── lcoe.py
├── mfe/                         # MFE-specific overrides
│   ├── __init__.py
│   ├── power_balance.py
│   ├── cas220103_tokamak.py     # tokamak magnet coils
│   ├── cas220103_mirror.py      # mirror magnet coils
│   ├── cas220104.py             # supplementary heating
│   ├── cas220106.py             # vacuum system
│   └── cas220107.py             # power supplies
└── ife/                         # IFE-specific overrides
    ├── __init__.py
    ├── power_balance.py
    ├── cas220104.py             # target factory
    ├── cas220106.py             # vacuum (IFE)
    └── cas2207.py               # fuel handling (IFE)
```

---

## Phase 1 — Foundation (units, enums, materials, dataclasses)

### 1.1 Create `units.py`

Type aliases for dimensional safety:

```python
from typing import NewType

M_USD = NewType("M_USD", float)   # millions of USD
USD   = NewType("USD", float)
MW    = NewType("MW", float)
Meters = NewType("Meters", float)
Kg    = NewType("Kg", float)
KgM3  = NewType("KgM3", float)   # density
Kelvin = NewType("Kelvin", float)
```

### 1.2 Rewrite `enums.py`

Full PyFECONS enums:

```python
from enum import Enum

class ReactorType(Enum):
    MFE_TOKAMAK = "tokamak"
    MFE_MIRROR  = "mirror"
    IFE_LASER   = "laser"

class FuelType(Enum):
    DT  = "DT"
    DD  = "DD"
    DHe3 = "DHe3"
    pB11 = "pB11"

class BlanketPrimaryCoolant(Enum):
    WATER = "H2O"
    HELIUM = "He"
    FLIBE = "FLiBe"
    PBLI  = "PbLi"
    DUAL_COOLANT = "Dual"

class BlanketSecondaryCoolant(Enum):
    WATER = "H2O"
    HELIUM = "He"
    NONE = "None"

class BlanketNeutronMultiplier(Enum):
    BE = "Be"
    PB = "Pb"
    NONE = "None"

class MagnetType(Enum):
    HTS = "HTS"
    LTS = "LTS"
    COPPER = "Copper"
    RESISTIVE = "Resistive"

class MagnetMaterialType(Enum):
    REBCO = "REBCO"       # YBCO/HTS
    NB3SN = "Nb3Sn"       # LTS
    NBTI  = "NbTi"        # LTS
    COPPER = "Copper"

class StructurePga(Enum):
    LOW  = "low"           # 0.1g
    MED  = "medium"        # 0.3g
    HIGH = "high"          # 0.5g

class Region(Enum):
    US = "US"
    EU = "EU"
    ASIA = "Asia"

class LSALevel(Enum):
    LSA1 = 1   # least safety assurance (commercial)
    LSA2 = 2
    LSA3 = 3
    LSA4 = 4   # most safety assurance (experimental)
```

### 1.3 Rewrite `materials.py`

Full PyFECONS material database with dataclass:

```python
@dataclass
class Material:
    name: str
    code: str
    rho: KgM3           # density kg/m³
    c_raw: float         # raw cost $/kg
    m: float             # manufacturing multiplier
    t_max: Kelvin = 0.0  # max operating temp (K)

    @property
    def unit_cost(self) -> float:
        """Manufactured cost per kg ($/kg)"""
        return self.c_raw * self.m

    def volume_cost_m_usd(self, volume_m3: float) -> M_USD:
        """Cost for given volume in M$"""
        return M_USD(volume_m3 * self.rho * self.c_raw * self.m / 1e6)
```

**Material constants from PyFECONS:**

| Code | Name | rho (kg/m³) | c_raw ($/kg) | m |
|------|------|------------|-------------|---|
| FS | Ferritic Steel | 7470 | 10 | 3 |
| W | Tungsten | 19300 | 100 | 3 |
| Be | Beryllium | 1850 | 5750 | 3 |
| Li | Lithium | 534 | 70 | 1.5 |
| Li4SiO4 | Lithium Orthosilicate | 2390 | 1 | 2 |
| Li2TiO3 | Lithium Metatitanate | 3430 | 1297.05 | 3 |
| FliBe | FLiBe (molten salt) | 1900 | 1000 | 1 |
| SiC | Silicon Carbide | 3200 | 14.49 | 3 |
| SS316 | Stainless Steel 316 | 7860 | 2 | 2 |
| Cu | Copper | 7300 | 10.2 | 3 |
| YBCO | YBCO (HTS) | 6200 | 55 | 1 |
| Nb3Sn | Niobium-Tin (LTS) | — | 5 | 1 |
| Concrete | Concrete | 2300 | 0.013 (13/1000) | 2 |
| BFS | Borated FS | 7800 | 30 | 2 |
| Inconel | Inconel 718 | 8440 | 46 | 3 |
| Pb | Lead | 9400 | 2.4 | 1.5 |
| PbLi | Lead-Lithium | blended (Pb:Li = 10:1 molar) | calc | 1.5 |
| V | Vanadium alloy | 6100 | 220 | 3 |

### 1.4 Create Input Dataclasses (`inputs/`)

Each CAS account gets an input dataclass. Example `inputs/basic.py`:

```python
@dataclass
class BasicInputs:
    p_nrl: MW = MW(500.0)           # net rated load (electrical)
    p_et: MW = MW(0.0)              # total thermal power (computed)
    n_mod: int = 1                   # number of power core modules
    reactor_type: ReactorType = ReactorType.MFE_TOKAMAK
    fuel_type: FuelType = FuelType.DT
    lsa_level: LSALevel = LSALevel.LSA1
    availability: float = 0.75       # plant availability factor
    construction_time_years: int = 6
    plant_lifetime_years: int = 40
    is_foak: bool = False            # first-of-a-kind
```

Example `inputs/cas220101.py`:

```python
@dataclass
class CAS220101Inputs:
    # Radial build (meters from plasma center)
    r_plasma: Meters = Meters(2.0)
    a_plasma: Meters = Meters(0.5)    # minor radius
    elon: float = 1.7                  # elongation
    # Layer thicknesses
    first_wall_thickness: Meters = Meters(0.02)
    blanket_thickness: Meters = Meters(0.50)
    shield_thickness: Meters = Meters(0.50)
    # Material selections
    first_wall_material: str = "FS"
    blanket_structural_material: str = "FS"
    blanket_breeder_material: str = "Li4SiO4"
    blanket_coolant: BlanketPrimaryCoolant = BlanketPrimaryCoolant.WATER
    blanket_multiplier: BlanketNeutronMultiplier = BlanketNeutronMultiplier.BE
    shield_material: str = "BFS"
```

### 1.5 Create Output Dataclasses (`categories/`)

Each CAS account gets an output dataclass. Example `categories/cas21.py`:

```python
@dataclass
class CAS21Output:
    C210100: M_USD = M_USD(0.0)   # Reactor building
    C210200: M_USD = M_USD(0.0)   # Turbine building
    C210300: M_USD = M_USD(0.0)   # Reactor maintenance building
    C210400: M_USD = M_USD(0.0)   # Warm shop
    C210500: M_USD = M_USD(0.0)   # Tritium building
    C210600: M_USD = M_USD(0.0)   # Electrical equipment building
    C210700: M_USD = M_USD(0.0)   # Hot cell building
    C210800: M_USD = M_USD(0.0)   # Reactor service building
    C210900: M_USD = M_USD(0.0)   # Service water building
    C211000: M_USD = M_USD(0.0)   # Fuel storage building
    C211100: M_USD = M_USD(0.0)   # Control room building
    C211200: M_USD = M_USD(0.0)   # On-site AC power building
    C211300: M_USD = M_USD(0.0)   # Admin building
    C211400: M_USD = M_USD(0.0)   # Site services building
    C211500: M_USD = M_USD(0.0)   # Cryogenics building
    C211600: M_USD = M_USD(0.0)   # Security building
    C211700: M_USD = M_USD(0.0)   # Ventilation stack
    C211800: M_USD = M_USD(0.0)   # Spare (not used)
    C211900: M_USD = M_USD(0.0)   # Contingency (FOAK only)
    C210000: M_USD = M_USD(0.0)   # TOTAL CAS 21

    def compute_total(self):
        self.C210000 = M_USD(sum([
            self.C210100, self.C210200, self.C210300, self.C210400,
            self.C210500, self.C210600, self.C210700, self.C210800,
            self.C210900, self.C211000, self.C211100, self.C211200,
            self.C211300, self.C211400, self.C211500, self.C211600,
            self.C211700, self.C211900
        ]))
```

### 1.6 Create `costing_data.py`

Master container holding all inputs + outputs:

```python
@dataclass
class CostingData:
    basic: BasicInputs = field(default_factory=BasicInputs)
    power_balance_in: PowerBalanceInputs = field(default_factory=PowerBalanceInputs)
    cas10_in: CAS10Inputs = field(default_factory=CAS10Inputs)
    cas21_in: CAS21Inputs = field(default_factory=CAS21Inputs)
    cas220101_in: CAS220101Inputs = field(default_factory=CAS220101Inputs)
    # ... all other inputs ...
    
    # Outputs
    cas10_out: CAS10Output = field(default_factory=CAS10Output)
    cas21_out: CAS21Output = field(default_factory=CAS21Output)
    cas22_out: CAS22Output = field(default_factory=CAS22Output)
    # ... all other outputs ...
    
    total_capital_cost: M_USD = M_USD(0.0)
    total_epc_cost: M_USD = M_USD(0.0)
    lcoe: float = 0.0  # $/MWh
```

---

## Phase 2 — Shared Calculations

### 2.1 `calculations/conversions.py`

```python
def k_to_m_usd(k_factor: float) -> M_USD:
    """Convert $/kW factor to M$ (divide by 1000)"""
    return M_USD(k_factor / 1000.0)
```

### 2.2 `calculations/volume.py`

Full radial build → volume computation:

```python
def compute_inner_radii(data: CostingData) -> dict:
    """Stack layer thicknesses to get inner radii"""
    # r0 = R_plasma + a_plasma (outer edge of plasma)
    # r_first_wall_inner = r0
    # r_blanket_inner = r0 + first_wall_thickness
    # r_shield_inner = r_blanket_inner + blanket_thickness
    # r_magnet_inner = r_shield_inner + shield_thickness
    pass

def compute_outer_radii(data: CostingData) -> dict:
    """Add thicknesses to get outer radii"""
    pass

def calc_volume_outer_hollow_torus(R: float, r_outer: float, r_inner: float) -> float:
    """V = 2π²R(r_outer² - r_inner²) for tokamak"""
    return 2 * math.pi**2 * R * (r_outer**2 - r_inner**2)

def calc_volume_ring(length: float, r_inner: float, r_outer: float) -> float:
    """V = πL(r_outer² - r_inner²) for mirror"""
    return math.pi * length * (r_outer**2 - r_inner**2)

def calc_volume_sphere(r_inner: float, r_outer: float) -> float:
    """V = 4/3 π (r_outer³ - r_inner³) for IFE"""
    return (4/3) * math.pi * (r_outer**3 - r_inner**3)

def compute_volumes(data: CostingData) -> dict:
    """Dispatch to correct geometry based on reactor_type"""
    if data.basic.reactor_type == ReactorType.MFE_TOKAMAK:
        # Use hollow torus with elongation multiplier
        pass
    elif data.basic.reactor_type == ReactorType.MFE_MIRROR:
        # Use cylindrical ring
        pass
    elif data.basic.reactor_type == ReactorType.IFE_LASER:
        # Use spherical shell
        pass
```

### 2.3 `calculations/cas21.py` — Buildings

PyFECONS formula: `C21xxxx = k_to_m_usd(factor) × p_et`

| Sub-account | Factor ($/kW) | Name | Fuel Scaling |
|-------------|--------------|------|-------------|
| C210100 | 268.0 | Reactor building | Yes (0.5× non-DT) |
| C210200 | 186.8 | Turbine building | Yes |
| C210300 | 54.0 | Reactor maintenance bldg | No |
| C210400 | 37.8 | Warm shop | No |
| C210500 | 10.8 | Tritium building | No |
| C210600 | 5.4 | Electrical equipment bldg | No |
| C210700 | 93.4 | Hot cell building | Yes |
| C210800 | 18.7 | Reactor service bldg | No |
| C210900 | 0.3 | Service water bldg | No |
| C211000 | 1.1 | Fuel storage bldg | No |
| C211100 | 0.9 | Control room bldg | No |
| C211200 | 0.8 | On-site AC power bldg | No |
| C211300 | 4.4 | Admin bldg | No |
| C211400 | 1.6 | Site services bldg | No |
| C211500 | 2.4 | Cryogenics bldg | No |
| C211600 | 0.9 | Security bldg | No |
| C211700 | 27.0 | Ventilation stack | No |

- **Fuel scaling**: For non-DT fuel (DD/DHe3/pB11), reduce buildings C210100, C210200, C210700 by 0.5× (smaller tritium handling).
- **FOAK contingency** (C211900): 10% of sum(C210100..C211700) when `is_foak=True`.

### 2.4 `calculations/cas220101.py` — First Wall / Blanket / Shield

```
C22010101 (First Wall)  = first_wall_volume × material_cost
C22010102 (Blanket)     = blanket_volume × material_cost (structural + breeder + multiplier)
C22010103 (Shield)      = shield_volume × material_cost
C22010100 (Total)       = sum of above

material_cost(vol, mat) = vol × mat.rho × mat.c_raw × mat.m / 1e6  [M$]
```

Blanket material dispatch (by BlanketPrimaryCoolant):
- **WATER**: structural=FS, breeder=Li4SiO4, multiplier=Be
- **HELIUM**: structural=FS, breeder=Li4SiO4 or Li2TiO3, multiplier=Be
- **FLIBE**: structural=FS or SiC, breeder=FliBe (self-breeding), multiplier=none
- **PBLI**: structural=FS, breeder=PbLi (self-breeding), multiplier=Pb inherent
- **DUAL_COOLANT**: structural=FS, first coolant=He, second coolant=PbLi

### 2.5 `calculations/cas220103.py` — Magnets

TF coil cost = magnet_volume × material_cost
- HTS (YBCO): `vol × 6200 × 55 × 1 / 1e6`
- LTS Nb3Sn: Uses superconductor fraction + copper stabilizer
- Copper: `vol × 7300 × 10.2 × 3 / 1e6`

Plus structure (Inconel 718 or SS316) and cryostat.

### 2.6 Remaining CAS Calculations

| CAS | Formula | Notes |
|-----|---------|-------|
| 10 | Pre-construction | Land, site prep, permits |
| 22.02 | Main heat transfer | Primary loop piping, heat exchangers |
| 22.04 | Supplementary heating | NBI/RF/ECRH (MFE); Target factory (IFE) |
| 22.05 | Primary structure | Reactor support, seismic isolation |
| 22.06 | Vacuum system | Pumps, vessel |
| 22.07 | Power supplies | Magnet PS, heating PS |
| 23 | Turbine plant | `k_to_m_usd(79) × p_et` |
| 24 | Electric plant | `k_to_m_usd(47) × p_et` |
| 25 | Misc plant equip | `k_to_m_usd(30) × p_et` |
| 26 | Heat rejection | `k_to_m_usd(29) × p_et` |
| 27 | Fuel handling | `k_to_m_usd(46) × p_et` (DT), scaled for non-DT |
| 28 | Instrumentation | `k_to_m_usd(19) × p_et` |
| 29 | Contingency | 0% NOAK, 10% FOAK of sum(CAS 21–28) |
| 30 | Indirect / Construction | `(p_net/150)^-0.5 × p_net × factor × construction_time` |
| 40 | Owner costs | `fac_91[LSA] × C200000`; LSA factors: [0.07, 0.10, 0.14, 0.18] |
| 50 | Capitalized supplementary | Minor additional capitalized costs |
| 60 | Capitalized O&M | Spare parts, initial inventory |
| 70 | Annualized O&M | `60 × p_net × 1000 / 1e6` M_USD/yr |
| 80 | Annualized fuel | `(fuel_cost_per_kg × annual_burn) / 1e6` |
| 90 | Annualized financial | `CRF × TCC`; default CRF = 0.09 |
| LCOE | | `(C90×1e6 + (C70+C80)×1e6×(1+i)^L) / (8760 × p_net × n_mod × availability)` $/MWh |

---

## Phase 3 — MFE / IFE Specific Modules

### 3.1 `mfe/power_balance.py`

```python
def compute_power_balance_mfe(data: CostingData) -> PowerBalanceOutput:
    # P_fusion from Q_plasma × P_heating
    # P_neutron = P_fusion × (14.06 / 17.58) for DT
    # P_alpha = P_fusion × (3.52 / 17.58) for DT
    # P_neutron_wall = P_neutron × neutron_multiplication (mn)
    # P_thermal = P_neutron_wall + P_alpha + P_heating
    # P_electric_gross = P_thermal × eta_th
    # P_recirculating = P_magnets + P_cryo + P_heating_wall + P_pumps + P_aux
    # P_net = P_electric_gross - P_recirculating
    # Q_eng = P_net / P_recirculating
```

### 3.2 `ife/power_balance.py`

```python
def compute_power_balance_ife(data: CostingData) -> PowerBalanceOutput:
    # P_fusion from target yield × rep rate
    # No magnetic confinement power
    # Driver (laser) recirculating power
    # P_net = P_gross - P_driver - P_aux
```

### 3.3 Tokamak vs Mirror Magnets

- `mfe/cas220103_tokamak.py`: TF coils (D-shaped), PF coils, central solenoid
- `mfe/cas220103_mirror.py`: Solenoidal coils, mirror coils, no CS

---

## Phase 4 — Delete Old Files

Remove the 7 simplified costing files:
- [x] `costing/total_cost.py`
- [x] `costing/geometry.py`
- [x] `costing/power_balance.py`
- [x] `costing/materials.py` (replaced)
- [x] `costing/reactor_equipment.py`
- [x] `costing/magnets.py`
- [x] `costing/buildings.py`
- [x] `costing/enums.py` (replaced)

---

## Phase 5 — Adapter Layer

### 5.1 `adapter.py`

Maintains the exact same `compute_total_epc_cost(config: dict) -> dict` signature:

```python
def compute_total_epc_cost(config: dict) -> dict:
    """Backward-compatible wrapper.
    
    1. Converts flat config dict → CostingData dataclass
    2. Runs full PyFECONS calculation pipeline
    3. Converts CostingData outputs → flat result dict
    """
    data = _config_to_costing_data(config)
    _run_calculations(data)
    return _costing_data_to_result_dict(data)
```

**Config mapping** (existing keys → CostingData fields):

| Config Key | CostingData Field |
|-----------|-------------------|
| `"thermal_power_mw"` | `basic.p_et` |
| `"net_electric_mw"` | `basic.p_nrl` |
| `"q_plasma"` | `power_balance_in.q_plasma` |
| `"reactor_type"` | `basic.reactor_type` |
| `"major_radius"` | `cas220101_in.r_plasma` |
| `"minor_radius"` | `cas220101_in.a_plasma` |
| `"elongation"` | `cas220101_in.elon` |
| `"blanket_thickness"` | `cas220101_in.blanket_thickness` |
| `"shield_thickness"` | `cas220101_in.shield_thickness` |
| `"first_wall_material"` | `cas220101_in.first_wall_material` |
| `"magnet_type"` | `cas2203_in.magnet_type` |
| ... | ... |

**Result mapping** (CostingData → output dict):

| Output Key | Source |
|-----------|--------|
| `"cas_21_total"` | `cas21_out.C210000` |
| `"cas_22_total"` | `cas22_out.C220000` |
| `"cas_2201"` | `cas22_out.C220100` |
| `"cas_2203"` | `cas22_out.C220300` |
| `"cas_23_turbine"` | `cas23_out.C230000` |
| `"total_epc_cost"` | `data.total_epc_cost` |
| ... | ... |

### 5.2 Update `costing/__init__.py`

```python
from .adapter import compute_total_epc_cost
```

---

## Phase 6 — Update Integration Points

### 6.1 `core/power_to_epc.py`

- Import stays the same (`from ..costing import compute_total_epc_cost`)
- Adapter handles all translation
- May need to add new CAS keys to `detailed_result` dict for expanded breakdown
- Add new sub-accounts to `detailed_result["CAS 22 - Reactor Equipment"]`

### 6.2 `ui/costing_panel.py`

- Expand `_build_enhanced_cost_tree()` with all 17 building sub-accounts
- Add CAS 25, 28, 50, 60, 70, 80, 90, LCOE display
- Update `_compute_reduction_levers()` to work with new keys

### 6.3 `ui/dashboard.py`

- Add LCOE display widget
- Expand cost breakdown visualization with new CAS accounts
- May add reactor type selector if not already present

---

## Phase 7 — Tests

### 7.1 Rewrite `test_embedded_costing.py`

- Test full pipeline: config → adapter → results
- Verify all output dict keys present
- Verify numeric ranges are physically reasonable

### 7.2 `test_pyfecons_parity.py`

- Compare our calculations against known PyFECONS reference values
- Test each CAS account individually
- Test MFE tokamak, MFE mirror, and IFE laser configurations

### 7.3 Integration Tests

- `compute_epc(config)` still returns expected structure
- Dashboard renders without errors
- Costing panel tree builds correctly

---

## Reference Data

### Power Balance Constants

| Parameter | DT | DD | DHe3 | pB11 |
|-----------|----|----|------|------|
| Alpha fraction | 3.52/17.58 | varies | 3.67/18.35 | 8.68/8.68 |
| Neutron fraction | 14.06/17.58 | varies | 14.68/18.35 | 0/8.68 |
| Fuel scaling (buildings) | 1.0 | 0.5 | 0.5 | 0.5 |

### CAS 30 LSA Factors

| LSA Level | Factor 91 | Factor 92 | Factor 93 | Factor 94 |
|-----------|-----------|-----------|-----------|-----------|
| LSA-1 | 0.07 | 0.22 | 0.049 | 0.077 |
| LSA-2 | 0.10 | 0.22 | 0.049 | 0.077 |
| LSA-3 | 0.14 | 0.22 | 0.049 | 0.077 |
| LSA-4 | 0.18 | 0.22 | 0.049 | 0.077 |

### CAS 40 Owner Cost Factors (by LSA)

| LSA | Factor |
|-----|--------|
| 1 | 0.07 |
| 2 | 0.10 |
| 3 | 0.14 |
| 4 | 0.18 |

---

## Execution Order

1. **Phase 1** — Foundation files (no breaking changes, additive only)
2. **Phase 2** — Calculation modules (no breaking changes, additive only)
3. **Phase 3** — MFE/IFE specifics (additive only)
4. **Phase 4** — Delete old files + **Phase 5** — Adapter (atomic swap)
5. **Phase 6** — Update UI/integration (use new CAS sub-accounts)
6. **Phase 7** — Tests (verify everything works)

> **Critical:** Phases 4+5 must be done together as an atomic operation to avoid breaking the app. The adapter must be in place before old files are deleted.
