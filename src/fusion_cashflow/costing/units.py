"""
Type aliases for dimensional safety in costing calculations.

These NewType definitions provide type hints that help catch unit errors
at the IDE/type-checker level while having zero runtime overhead.
"""
from typing import NewType

# Currency types
M_USD = NewType("M_USD", float)   # millions of USD
USD = NewType("USD", float)       # USD

# Power types
MW = NewType("MW", float)         # Megawatts
GW = NewType("GW", float)         # Gigawatts

# Dimension types
Meters = NewType("Meters", float)     # meters
Meters2 = NewType("Meters2", float)   # square meters
Meters3 = NewType("Meters3", float)   # cubic meters

# Material property types
Kg = NewType("Kg", float)             # kilograms
KgM3 = NewType("KgM3", float)         # density (kg/m³)

# Temperature types
Kelvin = NewType("Kelvin", float)     # Kelvin
Celsius = NewType("Celsius", float)   # Celsius

# Time types
Years = NewType("Years", float)       # years
Hours = NewType("Hours", float)       # hours


def mw_to_gw(mw: MW) -> GW:
    """Convert MW to GW."""
    return GW(mw / 1000.0)


def gw_to_mw(gw: GW) -> MW:
    """Convert GW to MW."""
    return MW(gw * 1000.0)


def usd_to_m_usd(usd: USD) -> M_USD:
    """Convert USD to millions of USD."""
    return M_USD(usd / 1_000_000.0)


def m_usd_to_usd(m_usd: M_USD) -> USD:
    """Convert millions of USD to USD."""
    return USD(m_usd * 1_000_000.0)


def celsius_to_kelvin(celsius: Celsius) -> Kelvin:
    """Convert Celsius to Kelvin."""
    return Kelvin(celsius + 273.15)


def kelvin_to_celsius(kelvin: Kelvin) -> Celsius:
    """Convert Kelvin to Celsius."""
    return Celsius(kelvin - 273.15)
