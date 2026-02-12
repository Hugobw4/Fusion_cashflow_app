"""Direct test of detailed power balance functions."""

from fusion_cashflow.costing.costing_data import CostingData
from fusion_cashflow.costing.enums_new import ReactorType, FuelType, MagnetType, BlanketPrimaryCoolant
from fusion_cashflow.costing.units import MW, Meters
from fusion_cashflow.costing.calculations.power_balance import compute_power_balance, USE_DETAILED_CALCULATIONS

# Check if detailed calculations are available
print(f"USE_DETAILED_CALCULATIONS: {USE_DETAILED_CALCULATIONS}")

# Create test data
data = CostingData()
data.basic.reactor_type = ReactorType.MFE_TOKAMAK
data.basic.fuel_type = FuelType.DT
data.basic.p_et = MW(2000.0)

# Power balance inputs
data.power_balance_in.q_plasma = 10.0
data.power_balance_in.p_heating = MW(50.0)
data.power_balance_in.neutron_multiplication = 1.15
data.power_balance_in.eta_th = 0.40
data.power_balance_in.p_magnets = MW(0.0)  # Will be computed
data.power_balance_in.p_cryo = MW(20.0)
data.power_balance_in.p_pumps = MW(10.0)
data.power_balance_in.p_aux = MW(15.0)

# Magnet config
data.cas2203_in.magnet_type = MagnetType.HTS

# Run power balance
print("\n" + "="*60)
print("Running compute_power_balance()...")
print("="*60)

compute_power_balance(data)

# Check outputs
pb = data.power_balance_out
print(f"\nOutputs:")
print(f"  p_fusion:         {pb.p_fusion} MW")
print(f"  p_thermal:        {pb.p_thermal} MW")
print(f"  p_electric_gross: {pb.p_electric_gross} MW")
print(f"  p_recirculating:  {pb.p_recirculating} MW")
print(f"  p_net:            {pb.p_net} MW")
print(f"  q_eng:            {pb.q_eng}")
print(f"  q_eng type:       {type(pb.q_eng)}")

# Check computed recirculating components
print(f"\nRecirculating Power Components:")
print(f"  p_magnets:        {data.power_balance_in.p_magnets} MW")
print(f"  p_cryo:           {data.power_balance_in.p_cryo} MW")
print(f"  p_heating:        {data.power_balance_in.p_heating} MW")
print(f"  p_pumps:          {data.power_balance_in.p_pumps} MW")
print(f"  p_aux:            {data.power_balance_in.p_aux} MW")

# Manually compute Q_eng
if pb.p_recirculating > 0:
    manual_q_eng = pb.p_net / pb.p_recirculating
    print(f"\nManual Q_eng calculation:")
    print(f"  Q_eng = {pb.p_net} / {pb.p_recirculating} = {manual_q_eng:.2f}")
