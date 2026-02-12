"""
Fusion Reactor Costing Module

Full PyFECONS port with backward-compatible adapter layer.
"""

# Main entry point (backward compatible)
from .adapter import compute_total_epc_cost, format_cost_summary

# New PyFECONS architecture (for advanced usage)
from .costing_data import CostingData
from .materials_new import MATERIALS, get_material, normalize_material_code
from .enums_new import (
    ReactorType, FuelType, BlanketPrimaryCoolant,
    MagnetType, LSALevel, Region
)

__all__ = [
    "compute_total_epc_cost",
    "format_cost_summary",
    "CostingData",
    "MATERIALS",
    "get_material",
    "normalize_material_code",
    "ReactorType",
    "FuelType",
    "BlanketPrimaryCoolant",
    "MagnetType",
    "LSALevel",
    "Region",
]
