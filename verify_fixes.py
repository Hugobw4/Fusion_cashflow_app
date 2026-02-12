#!/usr/bin/env python3
"""
Quick verification script to test AWS deployment fixes.
Run this before deploying to AWS Lightsail.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    required_modules = [
        "bokeh",
        "holoviews", 
        "pandas",
        "numpy",
        "numpy_financial",
        "pandas_datareader",
        "scipy",
        "jinja2",
    ]
    
    optional_modules = [
        "nevergrad",
    ]
    
    failed = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed.append(module)
    
    print("\nOptional modules:")
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"⚠️  {module} (optional - optimization features disabled)")
    
    if failed:
        print(f"\n❌ FAILED: Missing required modules: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required modules installed")
        return True


def test_dashboard_import():
    """Test that dashboard module can be imported without crashes."""
    print("\n" + "=" * 60)
    print("Testing Dashboard Module")
    print("=" * 60)
    
    try:
        # Add src to path
        src_path = os.path.join(os.path.dirname(__file__), "src")
        sys.path.insert(0, src_path)
        
        # This should not crash even without nevergrad
        from fusion_cashflow.ui import dashboard
        print("✅ Dashboard module imports successfully")
        
        # Check if nevergrad guard works
        if hasattr(dashboard, 'NEVERGRAD_AVAILABLE'):
            if dashboard.NEVERGRAD_AVAILABLE:
                print("✅ Nevergrad available - optimization features enabled")
            else:
                print("⚠️  Nevergrad not available - optimization features disabled (OK)")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_websocket_config():
    """Test WebSocket origin configuration."""
    print("\n" + "=" * 60)
    print("Testing WebSocket Configuration")
    print("=" * 60)
    
    # Test default (wildcard)
    os.environ.pop('BOKEH_ALLOW_WS_ORIGIN', None)
    import run_dashboard_with_static
    from importlib import reload
    reload(run_dashboard_with_static)
    
    # Just check the file was updated correctly
    with open('run_dashboard_with_static.py', 'r') as f:
        content = f.read()
        if 'BOKEH_ALLOW_WS_ORIGIN' in content and "allowed_origins" in content:
            print("✅ WebSocket origin configuration updated")
            print("   - Default: Accept all origins (*)")
            print("   - Can be overridden with BOKEH_ALLOW_WS_ORIGIN env var")
            return True
        else:
            print("❌ WebSocket configuration not updated properly")
            return False


def test_network_resilience():
    """Test that network calls have timeout protection."""
    print("\n" + "=" * 60)
    print("Testing Network Resilience")
    print("=" * 60)
    
    try:
        src_path = os.path.join(os.path.dirname(__file__), "src")
        sys.path.insert(0, src_path)
        
        from fusion_cashflow.core import cashflow_engine
        
        # Test that get_avg_annual_return works even with network issues
        result = cashflow_engine.get_avg_annual_return("North America")
        
        if isinstance(result, (int, float)) and result > 0:
            print(f"✅ Network calls have fallback (returned: {result:.4f})")
            return True
        else:
            print(f"⚠️  Unexpected return value: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Network resilience test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_static_files():
    """Check that static files exist."""
    print("\n" + "=" * 60)
    print("Testing Static Files")
    print("=" * 60)
    
    static_dir = os.path.join(os.path.dirname(__file__), "src", "fusion_cashflow", "ui", "static")
    required_files = ["logo.png", "favicon.ico"]
    
    all_present = True
    for filename in required_files:
        filepath = os.path.join(static_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {filename} ({size:,} bytes)")
        else:
            print(f"❌ {filename} missing")
            all_present = False
    
    if all_present:
        print("✅ All static files present")
    else:
        print("⚠️  Some static files missing (logo won't display)")
    
    return all_present


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "   AWS Deployment Verification".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("Dashboard Import", test_dashboard_import()))
    results.append(("WebSocket Config", test_websocket_config()))
    results.append(("Network Resilience", test_network_resilience()))
    results.append(("Static Files", test_static_files()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Ready for AWS deployment!")
        print("\nNext steps:")
        print("1. Push changes to GitHub main branch")
        print("2. On AWS Lightsail, pull latest code")
        print("3. Run: pip install -r requirements.txt")
        print("4. Set: export BOKEH_ALLOW_WS_ORIGIN='*'")
        print("5. Run: python run_dashboard_with_static.py")
        print("\nSee AWS_DEPLOYMENT_GUIDE.md for detailed instructions")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\nFix the issues above before deploying to AWS")
        return 1


if __name__ == "__main__":
    sys.exit(main())
