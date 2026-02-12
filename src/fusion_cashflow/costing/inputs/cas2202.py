"""CAS 22.02 (Main Heat Transfer) input parameters."""
from dataclasses import dataclass

from ..units import MW, Meters


@dataclass
class CAS2202Inputs:
    """Main heat transfer system inputs."""
    
    # Primary coolant loop
    primary_loop_pressure_mpa: float = 15.0         # Primary coolant pressure [MPa]
    primary_loop_temp_inlet_k: float = 573.0        # Inlet temperature [K]
    primary_loop_temp_outlet_k: float = 823.0       # Outlet temperature [K]
    
    # Heat exchangers
    n_heat_exchangers: int = 4                      # Number of HX units
    heat_exchanger_power_mw: MW = MW(500.0)         # Power per HX [MW]
    heat_exchanger_cost_factor: float = 0.5         # Cost factor [M$/MW]
    
    # Piping
    primary_piping_length: Meters = Meters(500.0)   # Total length [m]
    primary_piping_diameter: Meters = Meters(1.0)   # Pipe diameter [m]
    primary_piping_material: str = "SS316"          # Pipe material
    
    # Pumps
    n_primary_pumps: int = 3                        # Number of pumps
    pump_power_mw: MW = MW(10.0)                    # Power per pump [MW]
    pump_cost_musd: float = 5.0                     # Cost per pump [M$]
