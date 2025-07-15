# Dynamic Q-Engineering Logic

## Overview

The Dynamic Q-Engineering Model replaces hard-coded engineering gain (Q_eng) assumptions with data-driven estimates based on literature review and scaling relationships. This provides realistic power balance calculations across pilot, demonstration, and commercial fusion plant scales.

## Engineering Q Definition

**Engineering Q (Q_eng)** represents the ratio of useful electric output to total power consumption:

```
Q_eng = (Thermal Electric + Direct Electric) / Total Plant Consumption
```

This is distinct from **plasma Q**, which is the ratio of fusion power to heating power. Engineering Q accounts for:
- Thermal conversion efficiency losses
- Auxiliary system power consumption (cryogenics, tritium, cooling, controls)
- Power conversion and transmission losses
- Plant parasitic loads

## Mathematical Formulation

The PNRL (fusion power) calculation uses the following relationship:

```
PNET = (1 - 1/Q_eng) × PET
```

Where:
- `PNET` = Net electric power output (MW)
- `PET` = Gross electric power (thermal + direct conversion)
- `Q_eng` = Engineering gain from dynamic model

The dynamic Q model provides `Q_eng = f(net_mw, technology)` using:

1. **Linear interpolation** between literature anchor points
2. **Sigmoid capping** at maximum achievable Q values
3. **Technology-specific curves** for MFE vs IFE

## Literature Anchor Points

### Magnetic Fusion Energy (MFE)

| Net MW | Q_eng | Source | Study Type |
|-------:|------:|:-------|:-----------|
| 50     | 1.2   | GA FPP pilot study | Pilot plant concept |
| 100    | 1.5   | MIT SPARC-scale pilot | Near-term demonstration |
| 300    | 3.0   | EU DEMO pre-concept | Demonstration reactor |
| 500    | 4.0   | Korean K-DEMO study | Large demonstration |
| 1000   | 5.0   | ARIES-AT commercial | Commercial design |

<!-- citation: General Atomics Fusion Power Plant Study, 2019 -->
<!-- citation: MIT SPARC-scale economics, Commonwealth Fusion Systems -->
<!-- citation: European DEMO Conceptual Design Report, EUROfusion -->
<!-- citation: K-DEMO Conceptual Design, Korean National Fusion Program -->
<!-- citation: ARIES-AT Advanced Tokamak Design, UCSD/ANL -->

### Inertial Fusion Energy (IFE)

| Net MW | Q_eng | Source | Notes |
|-------:|------:|:-------|:------|
| 50     | 1.4   | IFE pilot concepts | Higher efficiency potential |
| 100    | 1.8   | NIF-scale commercial pilot | Direct drive advantages |
| 300    | 3.5   | IFE DEMO concepts | No steady-state auxiliary loads |
| 500    | 4.5   | IFE mid-scale commercial | Target factory efficiency |
| 1000   | 5.5   | Large IFE commercial | Economies of scale |

<!-- citation: IFE Commercial Power Plant Studies, LLNL -->
<!-- citation: NIF and Photon Science Strategic Plan -->

## Model Parameters

### Q Limits
- **Q_MIN**: 1.05 (minimum viable net power production)
- **Q_MAX_MFE**: 5.0 (thermodynamic and practical ceiling for MFE)
- **Q_MAX_IFE**: 6.0 (higher potential due to direct conversion)

### Sigmoid Transition
For very large plants (>800-900 MW), Q approaches maximum values using:

```
Q_final = Q_base + (Q_max - Q_base) × sigmoid(MW - MW_midpoint)
```

This prevents unrealistic Q values while maintaining smooth derivatives for optimization.

## Usage Examples

### Basic Q Estimation
```python
from q_model import estimate_q_eng

# ITER-scale MFE plant
q_iter = estimate_q_eng(500, "MFE")  # Returns ~4.0

# MIT SPARC-scale pilot
q_sparc = estimate_q_eng(100, "MFE")  # Returns ~1.5

# Large IFE commercial
q_ife = estimate_q_eng(1000, "IFE")  # Returns ~5.5
```

### Integration with Power Balance
```python
from power_to_epc import _calculate_fusion_power_balance

# Power balance automatically uses dynamic Q
power_balance = _calculate_fusion_power_balance(500, "MFE")
print(f"Q_eng: {power_balance['QENG']:.2f}")
print(f"PNRL: {power_balance['PNRL']:.0f} MW")
```

## Validation Results

The model passes all validation criteria:

- ✅ **Monotonicity**: Q increases with plant size for both MFE and IFE
- ✅ **Anchor Accuracy**: All literature points within ±5% error
- ✅ **Technology Ranking**: IFE consistently achieves higher Q than MFE
- ✅ **Boundary Conditions**: Q stays within physical limits
- ✅ **Smoothness**: No discontinuities in interpolation regions

## Key Citations

1. **ITER Physics Basis**: Nucl. Fusion 39, 2137-2664 (1999)
2. **EU DEMO Design**: Fusion Eng. Des. 146, 2552-2566 (2019)  
3. **SPARC Economics**: J. Fusion Energy 39, 427-436 (2020)
4. **ARIES Studies**: Fusion Eng. Des. 80, 3-23 (2006)
5. **IFE Power Plants**: Fusion Sci. Tech. 60, 19-27 (2011)
6. **K-DEMO Design**: Fusion Eng. Des. 109-111, 1072-1078 (2016)

## Implementation Notes

- Model uses `@lru_cache` for performance in optimization loops
- Warns for plants below 25 MW (outside validated range)
- Defaults to MFE curves for unknown technology types
- Maintains backward compatibility with manual Q override
