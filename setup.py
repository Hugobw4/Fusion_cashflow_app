from setuptools import setup, find_packages

setup(
    name="fusion-cashflow",
    version="1.0.0",
    description="Fusion Energy Financial Cashflow Modeling Engine",
    author="Hugo",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.5.0",
        "bokeh>=3.0.0",
        "holoviews>=1.15.0",
        "scipy>=1.9.0",
        "numpy_financial>=1.0.0",
        # pandas_datareader removed - breaks on Python 3.13, using hardcoded fallbacks
        # "pandas_datareader>=0.10.0",
        "jinja2>=3.0.0"
    ],
    extras_require={
        "dev": [
            "pytest",
            "hypothesis", 
            "memory-profiler",
            "psutil",
            "faker"
        ],
        "test": [
            "pytest",
            "pytest-benchmark",
            "pytest-cov"
        ]
    },
    entry_points={
        "console_scripts": [
            "fusion-cashflow=fusion_cashflow.ui.app:main",
        ],
    },
)