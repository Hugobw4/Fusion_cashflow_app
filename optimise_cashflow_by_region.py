#!/usr/bin/env python3
"""
Optimise fusion-plant KPIs by region

Multi-objective optimization script that runs separately for every region
supported by cashflow_engine.py and writes one CSV per region containing
that region's 15 best scenarios (ranked by IRR ↓ then LCOE ↑).

Optimizes:
- Maximize project IRR
- Minimize after-tax LCOE  
- Maximize project NPV

Author: Generated for Fusion Advisory Services
Date: July 10, 2025
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import warnings

# Suppress nevergrad warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="nevergrad")
warnings.filterwarnings("ignore", message=".*inf.*")
warnings.filterwarnings("ignore", message=".*BadLossWarning.*")
warnings.filterwarnings("ignore", message=".*LossTooLargeWarning.*")

import numpy as np
import pandas as pd
import nevergrad as ng
from slugify import slugify

# Import the cashflow engine
try:
    from fusion_cashflow_app import cashflow_engine
except ImportError:
    import cashflow_engine

# Set random seed for reproducibility
np.random.seed(42)


def get_supported_regions() -> List[str]:
    """Get all supported regions from the cashflow engine."""
    return sorted(cashflow_engine.REGION_MAP.keys())


def get_representative_location(region: str) -> str:
    """Get a representative location string for a region."""
    location_map = {
        "North America": "United States",
        "Europe": "France", 
        "MENA": "Saudi Arabia",
        "Southern Africa": "South Africa",
        "Sub-Saharan Africa": "Nigeria",
        "China": "China",
        "India": "India", 
        "Southeast Asia": "Thailand",
        "Latin America": "Brazil",
        "Russia & CIS": "Russia",
        "Oceania": "Australia",
    }
    return location_map.get(region, region)


def create_instrumentation():
    """Create the nevergrad instrumentation for optimization variables."""
    return ng.p.Instrumentation(
        total_epc_cost=ng.p.Scalar(lower=8.0e9, upper=18.0e9),
        electricity_price=ng.p.Scalar(lower=90, upper=101),
        net_electric_power_mw=ng.p.Scalar(lower=200, upper=1000),
        capacity_factor=ng.p.Scalar(lower=0.90, upper=0.95),
        input_debt_pct=ng.p.Scalar(lower=0.20, upper=0.90),
        cost_of_debt=ng.p.Scalar(lower=0.03, upper=0.09),
        years_construction=ng.p.Scalar(lower=15, upper=40),
        plant_lifetime=ng.p.Scalar(lower=20, upper=50),
    )


def assemble_config(x: Dict[str, float], region: str) -> Dict[str, Any]:
    """Assemble configuration dictionary from optimization variables and region."""
    base = cashflow_engine.get_default_config()
    
    # Set the project location for this region
    base["project_location"] = get_representative_location(region)
    
    # Overwrite the eight tunables with vector values
    base["total_epc_cost"] = x["total_epc_cost"]
    base["electricity_price"] = x["electricity_price"]
    base["net_electric_power_mw"] = x["net_electric_power_mw"]
    base["capacity_factor"] = x["capacity_factor"]
    base["input_debt_pct"] = x["input_debt_pct"]
    base["cost_of_debt"] = x["cost_of_debt"]
    
    # Construction and plant lifetime parameters
    base["years_construction"] = int(round(x["years_construction"]))
    base["plant_lifetime"] = int(round(x["plant_lifetime"]))
    
    # Set construction start year to a reasonable baseline (2025) 
    # The years_construction will determine when energy production starts
    base["construction_start_year"] = 2025
    base["project_energy_start_year"] = base["construction_start_year"] + base["years_construction"]
    
    # Also set loan_rate to match cost_of_debt for consistency
    base["loan_rate"] = x["cost_of_debt"]
    
    return base


def fitness(x: Dict[str, float], region: str) -> Tuple[float, float, float]:
    """
    Fitness function for multi-objective optimization.
    
    Returns:
        Tuple of (negative_irr, lcoe, negative_npv) for minimization
    """
    try:
        cfg = assemble_config(x, region)
        out = cashflow_engine.run_cashflow_scenario(cfg)
        
        # Extract metrics with robust handling of inf/nan values
        try:
            irr = out["irr"] if out["irr"] is not None and np.isfinite(out["irr"]) else -0.5
            lcoe = out["lcoe_val"] if out["lcoe_val"] is not None and np.isfinite(out["lcoe_val"]) else 10000.0
            npv = out["npv"] if out["npv"] is not None and np.isfinite(out["npv"]) else -1e10
        except KeyError as e:
            # Fallback in case metric names are different
            print(f"KeyError in fitness function: {e}")
            print(f"Available keys: {list(out.keys())}")
            # Use fallback values
            irr = -0.5
            lcoe = 10000.0
            npv = -1e10
        
        # Clamp values to prevent inf/nan issues in optimizer
        irr = np.clip(irr, -1.0, 1.0)  # IRR between -100% and 100%
        lcoe = np.clip(lcoe, -1000.0, 50000.0)  # Allow negative LCOE but cap it
        npv = np.clip(npv, -1e11, 1e11)  # NPV between -$100B and +$100B
        
        return (-irr, lcoe, -npv)  # Negative IRR and NPV for maximization
        
    except Exception as e:
        print(f"Error in fitness function for region {region}: {e}")
        # Return bad but finite fitness values
        return (0.5, 10000.0, 1e10)


def optimize_region(region: str, budget: int = 400) -> pd.DataFrame:
    """
    Run optimization for a single region using multiple single-objective optimizations
    to ensure we find the true best solutions for each metric.
    
    Args:
        region: Region name
        budget: Total optimization budget (split across objectives)
        
    Returns:
        DataFrame with optimization results
    """
    print(f"Optimizing region: {region}")
    
    # Split budget across three single-objective optimizations
    budget_per_objective = max(budget // 3, 50)  # Minimum 50 iterations per objective
    
    all_candidates = []
    
    # 1. Optimize for maximum IRR
    print(f"  Optimizing for IRR ({budget_per_objective} iterations)...")
    candidates_irr = optimize_single_objective(region, "IRR", budget_per_objective)
    all_candidates.extend(candidates_irr)
    
    # 2. Optimize for minimum LCOE
    print(f"  Optimizing for LCOE ({budget_per_objective} iterations)...")
    candidates_lcoe = optimize_single_objective(region, "LCOE", budget_per_objective)
    all_candidates.extend(candidates_lcoe)
    
    # 3. Optimize for maximum NPV
    print(f"  Optimizing for NPV ({budget_per_objective} iterations)...")
    candidates_npv = optimize_single_objective(region, "NPV", budget_per_objective)
    all_candidates.extend(candidates_npv)
    
    # Convert to DataFrame and remove duplicates
    df = pd.DataFrame(all_candidates)
    
    # Remove near-duplicate rows (within 1% tolerance)
    df = remove_duplicate_scenarios(df)
    
    # Sort by IRR descending, then LCOE ascending, then NPV descending
    df = df.sort_values(['IRR', 'LCOE_after_tax', 'NPV_project'], ascending=[False, True, False])
    
    print(f"  Found {len(df)} unique scenarios")
    return df


def optimize_single_objective(region: str, objective: str, budget: int) -> List[Dict]:
    """Optimize for a single objective to find the true best solution."""
    
    # Create instrumentation
    instrumentation = create_instrumentation()
    
    # Use faster optimizer - OnePlusOne is much quicker for single objectives
    optimizer = ng.optimizers.OnePlusOne(parametrization=instrumentation, budget=budget)
    
    candidates = []
    best_value = float('inf') if objective in ['LCOE'] else float('-inf')
    
    for i in range(budget):
        x = optimizer.ask()
        
        # Extract parameter values
        if hasattr(x.value, 'items'):
            params = x.value
        else:
            if isinstance(x.value, tuple) and len(x.value) == 2:
                args, kwargs = x.value
                params = kwargs
            else:
                param_names = ['total_epc_cost', 'electricity_price', 'net_electric_power_mw', 
                              'capacity_factor', 'input_debt_pct', 'cost_of_debt',
                              'years_construction', 'plant_lifetime']
                if isinstance(x.value, (list, tuple)):
                    params = dict(zip(param_names, x.value))
                else:
                    params = x.value
        
        # Calculate single objective fitness
        fitness_value = single_objective_fitness(params, region, objective)
        
        # Tell optimizer the result
        optimizer.tell(x, fitness_value)
        
        # Store candidate with full metrics
        try:
            cfg = assemble_config(params, region)
            out = cashflow_engine.run_cashflow_scenario(cfg)
            
            candidate = {
                'total_epc_cost': params['total_epc_cost'],
                'electricity_price': params['electricity_price'],
                'net_electric_power_mw': params['net_electric_power_mw'],
                'capacity_factor': params['capacity_factor'],
                'input_debt_pct': params['input_debt_pct'],
                'cost_of_debt': params['cost_of_debt'],
                'years_construction': int(round(params['years_construction'])),
                'plant_lifetime': int(round(params['plant_lifetime'])),
                'IRR': out.get('irr', 0.0),
                'LCOE_after_tax': out.get('lcoe_val', 10000.0),
                'NPV_project': out.get('npv', -1e10),
                'Payback_years': out.get('payback', 50.0),
                'region': region,
                'optimization_target': objective
            }
            
            # Track if this is the best for this objective
            current_value = candidate[{'IRR': 'IRR', 'LCOE': 'LCOE_after_tax', 'NPV': 'NPV_project'}[objective]]
            
            if objective == 'LCOE':
                if current_value < best_value:
                    best_value = current_value
            else:
                if current_value > best_value:
                    best_value = current_value
            
            candidates.append(candidate)
            
        except Exception as e:
            print(f"    Error in iteration {i}: {e}")
            continue
    
    print(f"    Best {objective}: {best_value}")
    return candidates


def single_objective_fitness(params: Dict[str, float], region: str, objective: str) -> float:
    """Calculate fitness for a single objective."""
    try:
        cfg = assemble_config(params, region)
        out = cashflow_engine.run_cashflow_scenario(cfg)
        
        if objective == "IRR":
            irr = out.get("irr", -0.5)
            irr = np.clip(irr, -1.0, 1.0) if np.isfinite(irr) else -0.5
            return -irr  # Negative for minimization
            
        elif objective == "LCOE":
            lcoe = out.get("lcoe_val", 10000.0)
            lcoe = np.clip(lcoe, 0.0, 50000.0) if np.isfinite(lcoe) else 10000.0
            return lcoe  # Positive for minimization
            
        elif objective == "NPV":
            npv = out.get("npv", -1e10)
            npv = np.clip(npv, -1e11, 1e11) if np.isfinite(npv) else -1e10
            return -npv  # Negative for minimization
            
    except Exception:
        # Return bad fitness
        if objective == "IRR":
            return 0.5  # Bad IRR
        elif objective == "LCOE":
            return 10000.0  # Bad LCOE
        elif objective == "NPV":
            return 1e10  # Bad NPV (remember this gets negated)


def remove_duplicate_scenarios(df: pd.DataFrame, tolerance: float = 0.01) -> pd.DataFrame:
    """Remove near-duplicate scenarios within tolerance."""
    if df.empty:
        return df
        
    # Create a simplified version for comparison
    numeric_cols = ['total_epc_cost', 'electricity_price', 'net_electric_power_mw', 
                   'capacity_factor', 'input_debt_pct', 'cost_of_debt',
                   'years_construction', 'plant_lifetime']
    
    unique_scenarios = []
    
    for idx, row in df.iterrows():
        is_duplicate = False
        
        for i, existing_row in enumerate(unique_scenarios):
            # Check if scenarios are similar within tolerance
            similar = True
            for col in numeric_cols:
                if col in row and col in existing_row:
                    # Handle both Series and dict-like objects
                    row_val = row[col] if hasattr(row, 'iloc') else row.get(col, 0)
                    existing_val = existing_row[col] if hasattr(existing_row, 'iloc') else existing_row.get(col, 0)
                    
                    if abs(existing_val) > 1e-10:  # Avoid division by very small numbers
                        relative_diff = abs(row_val - existing_val) / abs(existing_val)
                        if relative_diff > tolerance:
                            similar = False
                            break
                    elif abs(row_val - existing_val) > tolerance:  # Absolute difference for small values
                        similar = False
                        break
            
            if similar:
                # Keep the one with better IRR
                row_irr = row['IRR'] if hasattr(row, 'iloc') else row.get('IRR', 0)
                existing_irr = existing_row['IRR'] if hasattr(existing_row, 'iloc') else existing_row.get('IRR', 0)
                
                if row_irr > existing_irr:
                    unique_scenarios[i] = row.to_dict() if hasattr(row, 'to_dict') else dict(row)
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_scenarios.append(row.to_dict() if hasattr(row, 'to_dict') else dict(row))
    
    return pd.DataFrame(unique_scenarios)


def optimize_single_region_for_parallel(args_tuple):
    """Wrapper function for parallel processing."""
    region, budget, outdir = args_tuple
    try:
        print(f"\n{'='*60}")
        print(f"Region: {region}")
        print(f"{'='*60}")
        
        df = optimize_region(region, budget)
        top_15 = df.head(15)
        
        # Save to CSV
        slug = slugify(region, separator="_").lower()
        csv_path = outdir / f"best_15_scenarios_{slug}.csv"
        top_15.to_csv(csv_path, index=False)
        
        best = top_15.iloc[0]
        
        return {
            'region': region,
            'best_irr': best['IRR'],
            'best_lcoe': best['LCOE_after_tax'],
            'best_npv': best['NPV_project'],
            'best_payback': best['Payback_years'],
            'csv_file': str(csv_path)
        }
    except Exception as e:
        print(f"Error optimizing region {region}: {e}")
        return None


def main():
    """Main optimization loop."""
    parser = argparse.ArgumentParser(description="Optimize fusion plant KPIs by region")
    parser.add_argument("--budget", type=int, default=400, help="Optimization budget per region")
    parser.add_argument("--outdir", type=str, default=".", help="Output directory")
    parser.add_argument("--regions", nargs="*", help="Specific regions to optimize (default: all)")
    parser.add_argument("--parallel", action="store_true", help="Use parallel processing")
    args = parser.parse_args()
    
    # Setup output directory
    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)
    
    # Get supported regions
    if args.regions:
        regions = [r for r in get_supported_regions() if r in args.regions]
        print(f"Optimizing selected regions: {regions}")
    else:
        regions = get_supported_regions()
        print(f"Found {len(regions)} supported regions: {regions}")
    
    # Summary results
    summary_results = []
    
    # Optimize each region
    if args.parallel:
        # Parallel processing 
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing as mp
        
        # Create arguments tuples for parallel processing
        args_tuples = [(region, args.budget, outdir) for region in regions]
        
        with ProcessPoolExecutor(max_workers=min(4, len(regions))) as executor:
            results = list(executor.map(optimize_single_region_for_parallel, args_tuples))
        
        summary_results = [r for r in results if r is not None]
        
    else:
        # Sequential processing (original logic)
        for region in regions:
            try:
                print(f"\n{'='*60}")
                print(f"Region: {region}")
                print(f"{'='*60}")
                
                # Run optimization
                df = optimize_region(region, args.budget)
                
                # Get top 15 scenarios
                top_15 = df.head(15)
                
                # Save to CSV
                slug = slugify(region, separator="_").lower()
                csv_path = outdir / f"best_15_scenarios_{slug}.csv"
                top_15.to_csv(csv_path, index=False)
                
                # Get best scenario
                best = top_15.iloc[0]
                
                # Console output - show best overall and best for each objective
                print(f"Region: {region}")
                print(f"  Best Overall IRR: {best['IRR']:.4f} ({best['IRR']*100:.2f}%)")
                print(f"  Best Overall LCOE: ${best['LCOE_after_tax']:.2f}/MWh")
                print(f"  Best Overall NPV: ${best['NPV_project']:,.0f}")
                print(f"  Payback: {best['Payback_years']:.1f} years")
                
                # Show best for each individual objective
                if len(top_15) > 0:
                    best_irr_idx = top_15['IRR'].idxmax()
                    best_lcoe_idx = top_15['LCOE_after_tax'].idxmin()
                    best_npv_idx = top_15['NPV_project'].idxmax()
                    
                    best_irr = top_15.loc[best_irr_idx]
                    best_lcoe = top_15.loc[best_lcoe_idx] 
                    best_npv = top_15.loc[best_npv_idx]
                    
                    print(f"  Best IRR Only: {best_irr['IRR']*100:.2f}% (LCOE: ${best_irr['LCOE_after_tax']:.0f}, NPV: ${best_irr['NPV_project']:,.0f})")
                    print(f"  Best LCOE Only: ${best_lcoe['LCOE_after_tax']:.0f}/MWh (IRR: {best_lcoe['IRR']*100:.2f}%, NPV: ${best_lcoe['NPV_project']:,.0f})")
                    print(f"  Best NPV Only: ${best_npv['NPV_project']:,.0f} (IRR: {best_npv['IRR']*100:.2f}%, LCOE: ${best_npv['LCOE_after_tax']:.0f})")
                print(f"  Saved to: {csv_path}")
                
                # Store summary
                summary_results.append({
                    'region': region,
                    'best_irr': best['IRR'],
                    'best_lcoe': best['LCOE_after_tax'],
                    'best_npv': best['NPV_project'],
                    'best_payback': best['Payback_years'],
                    'csv_file': str(csv_path)
                })
                
            except Exception as e:
                print(f"Error optimizing region {region}: {e}")
                continue
    
    # Save summary results
    if summary_results:
        summary_df = pd.DataFrame(summary_results)
        summary_path = outdir / "optimization_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSummary saved to: {summary_path}")
        
        # Print final summary
        print(f"\n{'='*60}")
        print("OPTIMIZATION SUMMARY")
        print(f"{'='*60}")
        print(f"{'Region':<20} {'IRR':<8} {'LCOE':<10} {'NPV':<15} {'Payback':<10}")
        print("-" * 70)
        for _, row in summary_df.iterrows():
            print(f"{row['region']:<20} {row['best_irr']*100:>6.2f}% ${row['best_lcoe']:>8.2f} ${row['best_npv']:>12,.0f} {row['best_payback']:>8.1f}")
    
    print(f"\nOptimization complete!")


if __name__ == "__main__":
    main()
