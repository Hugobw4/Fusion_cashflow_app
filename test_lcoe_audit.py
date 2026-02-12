"""Comprehensive audit of all 7 LCOE vector inputs."""
from fusion_cashflow.core.cashflow_engine import get_default_config, run_cashflow_scenario

config = get_default_config()
config.update({
    "power_method": "MFE",
    "fuel_type": "DT",
    "fuel_type_code": "DT",
    "reactor_type": "MFE Tokamak",
    "reactor_type_code": "MFE",
    "fusion_power_mw": 500,
    "q_plasma": 10,
    "auxiliary_power_mw": 50,  # = 500 / 10
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

result = run_cashflow_scenario(config)

SEP = "=" * 70
print(SEP)
print("LCOE INPUT VECTOR AUDIT")
print(SEP)
print(f"LCOE:              ${result['lcoe_val']:.2f}/MWh")
print(f"Discount rate:     {result['discount_rate']*100:.2f}% (WACC)")
print(f"Plant lifetime:    {result['plant_lifetime']} years")
print(f"Construction:      {result['years_construction']} years")

epc = result.get("epc_breakdown", {})
pb = epc.get("power_balance", {})
p_net = pb.get("p_net", 0)
costing_om = epc.get("costing_fixed_om_per_mw", 0)
costing_fuel = epc.get("costing_annual_fuel_cost", 0)
n = len(result['energy_vec'])
yc = result['years_construction']

# 1. CAPEX
print(f"\n1. CAPEX (construction period)")
print(f"   Total EPC:      ${result['total_epc_cost']/1e9:.3f}B")
print(f"   TOC (w/ IDC):   ${result['toc']/1e9:.3f}B")
print(f"   Source:          Costing CAS 10-40 (geometry+physics)")

# 2. OPEX (om_vec in result = fixed_om + variable_om per year)
om = result['om_vec']
op_om = om[yc:] if len(om) > yc else []
print(f"\n2. OPEX (O&M vector)")
if op_om:
    print(f"   Year 1 O&M:     ${op_om[0]/1e6:.1f}M")
    print(f"   Steady-state:   ${op_om[-1]/1e6:.1f}M")
    print(f"   Fixed O&M/MW:   ${costing_om:,.0f}/MW/yr  (CAS 70 / P_net)")
    print(f"   P_net:          {p_net:.1f} MW")
    print(f"   Expected base:  ${costing_om * p_net / 1e6:.1f}M/yr")
    print(f"   Source:          CAS 70 annualized O&M (physics-based)")

# 3. FUEL (fuel_vec in result)
fuel = result['fuel_vec']
op_fuel = fuel[yc:] if len(fuel) > yc else []
print(f"\n3. FUEL VECTOR")
if op_fuel and any(f > 0 for f in op_fuel):
    print(f"   Year 1 fuel:    ${op_fuel[0]/1e6:.3f}M")
    print(f"   Steady-state:   ${op_fuel[-1]/1e6:.3f}M")
    print(f"   CAS 80 base:    ${costing_fuel/1e6:.3f}M/yr")
    print(f"   Source:          CAS 80 (costing-derived fuel cost)")
else:
    print(f"   Fuel costs:     $0 (check CAS 80)")

# 4. DECOMMISSIONING
print(f"\n4. DECOMMISSIONING")
decom_cost = config.get("decommissioning_cost", 0)
print(f"   Decom cost:     ${decom_cost/1e9:.2f}B")
print(f"   Decom year:     {result.get('decommissioning_year', 'N/A')}")
print(f"   Source:          Config (% of EPC could be better)")

# 5. ENERGY
energy = result['energy_vec']
op_energy = [v for v in energy if v > 0]
cf = config.get("capacity_factor", 0.92)
expected_mwh = p_net * 8760 * cf
print(f"\n5. ENERGY VECTOR")
if op_energy:
    print(f"   Year 1 energy:  {op_energy[0]:,.0f} MWh")
    print(f"   Steady-state:   {op_energy[-1]:,.0f} MWh")
    print(f"   Expected:       {expected_mwh:,.0f} MWh")
    print(f"   Match:          {'YES' if abs(op_energy[-1] - expected_mwh)/expected_mwh < 0.01 else 'NO'}")
    print(f"   Source:          P_net (costing physics) x 8760h x CF={cf}")

# 6. TAX
tax = result['tax_vec']
op_tax = [v for v in tax if v > 0]
print(f"\n6. TAX VECTOR")
if op_tax:
    print(f"   Year 1 tax:     ${op_tax[0]/1e6:.1f}M")
    print(f"   Avg annual:     ${sum(op_tax)/len(op_tax)/1e6:.1f}M")
    print(f"   Tax rate:       {result['tax_rate']*100:.1f}%")
    print(f"   Source:          max(0, profit - depreciation) x tax_rate")

# 7. DISCOUNT RATE
print(f"\n7. DISCOUNT RATE")
print(f"   WACC:           {result['discount_rate']*100:.2f}%")
print(f"   CoE:            {result['cost_of_equity']*100:.2f}%")
print(f"   CoD:            {result['cost_of_debt']*100:.2f}%")
print(f"   Equity%:        {result['input_equity_pct']*100:.0f}%")
print(f"   Source:          CAPM (region={result['region']})")

# HEALTH CHECK
print(f"\n{SEP}")
print("HEALTH CHECK")
print(SEP)
issues = []

if abs(result['total_epc_cost'] - 5_000_000_000) < 1:
    issues.append("FAIL: EPC is default $5B — costing module failed!")
else:
    print(f"  [OK] EPC from costing: ${result['total_epc_cost']/1e9:.3f}B")

if p_net > 0:
    print(f"  [OK] P_net = {p_net:.1f} MW (physics-derived)")
else:
    issues.append("FAIL: P_net = 0")

if costing_om > 0:
    print(f"  [OK] O&M from CAS 70: ${costing_om:,.0f}/MW/yr")
else:
    issues.append("WARN: No CAS 70 O&M")

if costing_fuel > 0:
    print(f"  [OK] Fuel from CAS 80: ${costing_fuel/1e6:.3f}M/yr")
else:
    issues.append("WARN: No CAS 80 fuel cost")

if op_energy and expected_mwh > 0 and abs(op_energy[-1] - expected_mwh)/expected_mwh < 0.01:
    print(f"  [OK] Energy consistent: {op_energy[-1]:,.0f} MWh")
else:
    issues.append(f"WARN: Energy mismatch")

lcoe = result['lcoe_val']
if 20 < lcoe < 500:
    print(f"  [OK] LCOE ${lcoe:.2f}/MWh in reasonable range")
else:
    issues.append(f"WARN: LCOE ${lcoe:.2f}/MWh outside expected range")

# Check decom is reasonable
if 0 < decom_cost < result['total_epc_cost']:
    print(f"  [OK] Decom ${decom_cost/1e9:.2f}B < EPC")
elif decom_cost == 0:
    issues.append("WARN: No decommissioning cost set")
else:
    issues.append(f"WARN: Decom (${decom_cost/1e9:.2f}B) seems high")

if issues:
    print(f"\nISSUES ({len(issues)}):")
    for i in issues:
        print(f"  {i}")
else:
    print("\n  ALL CHECKS PASSED")
print(SEP)
