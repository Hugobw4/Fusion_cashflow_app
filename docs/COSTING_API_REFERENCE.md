# Costing Module API Reference

## Main Entry Point

```python
from src.fusion_cashflow.costing import compute_total_epc_cost

result = compute_total_epc_cost(config)
```

## Configuration Dictionary

### Required Parameters

```python
config = {
    # Reactor Type
    "reactor_type": "MFE" | "IFE",
    "confinement_type": "tokamak" | "mirror" | "laser",  # Optional, defaults based on reactor_type
    "fuel_type": "DT" | "DD" | "DHe3" | "pB11",
    "noak": True | False,  # True = Nth-of-a-kind (10% contingency), False = FOAK (20%)
    
    # Power Parameters
    "p_nrl_fusion_power_mw": float,      # Fusion power (MW)
    "auxiliary_power_mw": float,          # Auxiliary heating/driver power (MW)
    "thermal_efficiency": float,          # Thermal-to-electric (typically 0.46)
}
```

### MFE-Specific Parameters

```python
config = {
    # ... base parameters ...
    
    # Geometry (all in meters)
    "major_radius_m": float,              # Plasma major radius
    "plasma_t": float,                    # Plasma thickness (minor radius)
    "vacuum_t": float,                    # Vacuum gap thickness
    "firstwall_t": float,                 # First wall thickness
    "blanket_t": float,                   # Blanket thickness
    "reflector_t": float,                 # Reflector/multiplier thickness
    "ht_shield_t": float,                 # High-temperature shield thickness
    "structure_t": float,                 # Structure thickness
    "gap_t": float,                       # Gap between structure and vessel
    "vessel_t": float,                    # Vacuum vessel thickness
    "coil_t": float,                      # Magnet coil thickness
    "elongation": float,                  # Plasma elongation (typically 1.6-2.0)
    
    # Materials
    "first_wall_material": "tungsten" | "beryllium" | "lithium" | "flibe",
    "blanket_type": "solid_breeder" | "flowing_breeder",
    "structure_material": "SS" | "FMS" | "ODS" | "V",
    
    # Magnets
    "magnet_technology": "HTS" | "LTS" | "copper",
    "toroidal_field_tesla": float,        # On-axis field strength
    "n_tf_coils": int,                    # Number of TF coils
    "tape_width_m": float,                # HTS tape width (typically 0.004m)
    "coil_thickness_m": float,            # Radial thickness of coil pack
}
```

### IFE-Specific Parameters

```python
config = {
    # ... base parameters ...
    
    # Geometry (spherical chamber)
    "chamber_radius_m": float,            # Inner chamber radius
    "firstwall_t": float,                 # First wall thickness
    "blanket_t": float,                   # Blanket thickness
    "reflector_t": float,                 # Reflector thickness
    "ht_shield_t": float,                 # Shield thickness
    "structure_t": float,                 # Structure thickness
    "vessel_t": float,                    # Vessel thickness
    
    # Materials
    "first_wall_material": "tungsten" | "beryllium" | "lithium" | "flibe",
    "blanket_type": "solid_breeder" | "flowing_breeder",
    "structure_material": "SS" | "FMS" | "ODS" | "V",
    
    # Driver
    "driver_energy_mj": float,            # Driver energy per pulse
}
```

## Return Value Structure

```python
result = {
    # Power Balance
    "power_balance": {
        "p_fusion": float,              # MW
        "p_neutron": float,             # MW
        "p_charged": float,             # MW
        "p_thermal": float,             # MW
        "p_electric_gross": float,      # MW
        "p_auxiliary": float,           # MW
        "p_recirculating": float,       # MW
        "p_electric_net": float,        # MW
        "q_plasma": float,              # P_fusion / P_aux
        "q_eng": float,                 # P_net / P_aux
    },
    "q_eng": float,                     # Also at top level
    
    # Geometry
    "volumes": {
        "plasma": float,                # m³
        "vacuum": float,                # m³
        "firstwall": float,             # m³
        "blanket": float,               # m³
        "reflector": float,             # m³
        "ht_shield": float,             # m³
        "structure": float,             # m³
        "vessel": float,                # m³
        "coils": float,                 # m³ (MFE only)
        # ... plus _radii dict with ir/or for each layer
    },
    
    # CAS 22.01 - Reactor Core Components (M$)
    "firstwall": float,
    "blanket": float,
    "structure": float,
    "shield": float,
    "vessel": float,
    "total_reactor_equipment": float,
    "divertor": float,                  # MFE only
    "vacuum_system": float,
    "power_supplies": float,
    "cas_2201": float,                  # Subtotal
    
    # CAS 22.03 - Magnets (M$, MFE only)
    "magnet_tf_conductor": float,
    "magnet_tf_structure": float,
    "magnet_tf_manufacturing": float,
    "magnet_pf_coils": float,
    "magnet_cryogenic": float,
    "magnet_total_magnets": float,
    "cas_2203": float,                  # Subtotal
    
    # CAS 22 - Other Reactor Systems (M$)
    "heating_systems": float,
    "coolant_system": float,
    "tritium_systems": float,
    "instrumentation": float,
    "cas_22_total": float,              # CAS 22 total
    
    # CAS 21 - Buildings (M$)
    "building_reactor_building": float,
    "building_turbine_building": float,
    "building_auxiliary_buildings": float,
    "cas_21_total": float,
    
    # CAS 23-27 - Balance of Plant (M$)
    "cas_23_turbine": float,
    "cas_24_electrical": float,
    "cas_26_cooling": float,
    "cas_27_materials": float,
    
    # Indirect Costs (M$)
    "cas_10_preconstruction": float,    # 5% of direct
    "cas_30_indirect": float,           # 15% of direct
    "cas_40_owner_costs": float,        # 10% of direct
    "cas_29_contingency": float,        # 10% NOAK or 20% FOAK
    
    # Totals (M$)
    "total_capital_cost": float,        # M$ (includes owner costs)
    "total_epc_cost": float,            # M$ (excludes owner costs)
    
    # Metrics ($/kW)
    "cost_per_kw_net": float,           # total_capital_cost per net kW
    "epc_per_kw_net": float,            # total_epc_cost per net kW
}
```

## Example Usage

### MFE Tokamak

```python
from src.fusion_cashflow.costing import compute_total_epc_cost

config = {
    "reactor_type": "MFE",
    "fuel_type": "DT",
    "noak": True,
    "p_nrl_fusion_power_mw": 500.0,
    "auxiliary_power_mw": 50.0,
    "thermal_efficiency": 0.46,
    "major_radius_m": 3.0,
    "plasma_t": 0.5,
    "vacuum_t": 0.1,
    "firstwall_t": 0.02,
    "blanket_t": 0.6,
    "reflector_t": 0.05,
    "ht_shield_t": 0.4,
    "structure_t": 0.3,
    "gap_t": 0.05,
    "vessel_t": 0.1,
    "coil_t": 0.8,
    "elongation": 1.8,
    "first_wall_material": "tungsten",
    "blanket_type": "solid_breeder",
    "structure_material": "ODS",
    "magnet_technology": "HTS",
    "toroidal_field_tesla": 9.0,
    "n_tf_coils": 18,
    "tape_width_m": 0.004,
    "coil_thickness_m": 0.8,
}

result = compute_total_epc_cost(config)

print(f"Q_eng: {result['q_eng']:.2f}")
print(f"Net Power: {result['power_balance']['p_electric_net']:.0f} MW")
print(f"Total EPC: ${result['total_epc_cost']:.0f}M")
print(f"Cost/kW: ${result['epc_per_kw_net']:.0f}/kW")
```

### IFE Laser

```python
config = {
    "reactor_type": "IFE",
    "fuel_type": "DT",
    "noak": True,
    "p_nrl_fusion_power_mw": 1000.0,
    "auxiliary_power_mw": 100.0,
    "thermal_efficiency": 0.46,
    "chamber_radius_m": 5.0,
    "firstwall_t": 0.5,
    "blanket_t": 0.8,
    "reflector_t": 0.1,
    "ht_shield_t": 0.6,
    "structure_t": 0.4,
    "vessel_t": 0.15,
    "first_wall_material": "tungsten",
    "blanket_type": "solid_breeder",
    "structure_material": "FMS",
    "driver_energy_mj": 2.0,
}

result = compute_total_epc_cost(config)
```

## Cost Scaling Rules

### Power Scaling
- Buildings: `P^0.6` (economies of scale)
- Material-based: Linear with volume/mass
- Turbine: `$600/kW` thermal
- Electrical: `$200/kW`

### Material Costs
- First wall: tungsten @ $750/kg, beryllium @ $750/kg
- Blanket breeder: Li2TiO3 @ $25/kg, PbLi @ $3.5/kg
- Structure: ODS steel @ $280/kg, FMS @ $60/kg
- Magnets: REBCO @ $50/kA·m

### Contingency
- NOAK (Nth-of-a-kind): 10%
- FOAK (First-of-a-kind): 20%

## Helper Functions

```python
from src.fusion_cashflow.costing.total_cost import format_cost_summary

# Get readable summary
summary_text = format_cost_summary(result)
print(summary_text)
```

Output:
```
=== Fusion Reactor Cost Summary ===

Power Performance:
  Fusion Power:        500 MW
  Thermal Power:       540 MW
  Gross Electric:      248 MW
  Net Electric:        173 MW
  Q_eng:              3.47

Capital Costs (M$):
  CAS 21 Buildings:         $537M
  CAS 22 Reactor Equipment: $1595M
    - Reactor Core:         $1204M
    - Magnets:             $34M
    - Heating:             $100M
    - Coolant:             $270M
  ...
```

## Notes

- All costs in **million USD (M$)**
- All power values in **MW**
- All lengths in **meters**
- Cost per kW in **$/kW** (converted from M$/MW internally)
- Regional cost factors should be applied externally (in power_to_epc.py)
