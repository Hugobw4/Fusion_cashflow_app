"""
Fusion Cashflow - Fusion Energy Financial Modeling Engine
"""

__version__ = "1.0.0"
__author__ = "Hugo"

# Core imports
from .core.cashflow_engine import run_cashflow_scenario, get_default_config
from .core import cashflow_engine
from .core import power_to_epc
from .core import q_model

__all__ = [
    "run_cashflow_scenario",
    "get_default_config",
    "cashflow_engine",
    "power_to_epc", 
    "q_model"
]