"""Debug CAS 30 calculation."""

from fusion_cashflow.costing.adapter import compute_total_epc_cost

config = {
    "reactor_type": "MFE Tokamak",
    "fuel_type": "DT",
    "plasma_power": 450.0,
   "thermal_power": 2000.0,
    "q_plasma": 10.0,
    "major_radius": 6.2,
    "minor_radius": 2.0,
    "blanket_thickness": 0.85,
    "shield_thickness": 0.75,
    "blanket_type": "Solid Breeder (Li4SiO4)",
    "structure_material": "Ferritic Steel (FMS)",
    "magnet_type": "LTS",
}

result = compute_total_epc_cost(config)

pb = result.get('power_balance', {})
print(f"P_net: {pb.get('p_net', 0)} MW")
print(f"CAS 30: ${result.get('cas_30_indirect', 0):.1f}M")
print(f"Total EPC: ${result.get('total_epc_cost', 0):.1f}M")

# Manual calculation
p_net = pb.get('p_net', 0)
construction_time = 6
factor = 0.22

if p_net > 0:
    manual_cas30 = ((p_net / 150.0) ** -0.5) * p_net * factor * construction_time
    print(f"\nManual CAS 30 calculation:")
    print(f"  ((p_net{p_net}/150)^-0.5) * {p_net} * {factor} * {construction_time}")
    print(f"  = {manual_cas30:.1f} M$")
