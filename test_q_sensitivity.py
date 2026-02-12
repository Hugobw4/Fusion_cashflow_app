"""Test Q_plasma sensitivity — verify the slider actually changes outputs."""
from fusion_cashflow.core.cashflow_engine import get_default_config, run_cashflow_scenario

base = get_default_config()
base.update({
    "power_method": "MFE",
    "fuel_type": "DT",
    "fuel_type_code": "DT",
    "reactor_type_code": "MFE",
    "fusion_power_mw": 500,
    "thermal_efficiency": 0.46,
    "first_wall_material": "Tungsten",
    "blanket_type": "Solid Breeder (Li2TiO3)",
    "structure_material": "Ferritic Steel (FMS)",
    "magnet_technology": "HTS REBCO",
    "toroidal_field_tesla": 12,
    "n_tf_coils": 12,
    "tape_width_m_actual": 0.004,
    "coil_thickness_m": 0.25,
    "noak": True,
})

print(f"{'Q':>3}  {'P_heat':>7}  {'P_net':>7}  {'Q_eng':>6}  {'EPC':>7}  {'LCOE':>10}")
print("-" * 55)

for q in [5, 10, 20, 40]:
    cfg = dict(base)
    cfg["q_plasma"] = q
    cfg["auxiliary_power_mw"] = 500.0 / q
    r = run_cashflow_scenario(cfg)
    pb = r["epc_breakdown"]["power_balance"]
    print(f"{q:3d}  {500/q:6.1f}MW  {pb['p_net']:6.1f}MW  {pb['q_eng']:6.2f}  ${r['total_epc_cost']/1e9:.2f}B  ${r['lcoe_val']:7.1f}/MWh")
