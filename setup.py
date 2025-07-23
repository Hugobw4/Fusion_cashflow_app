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
        "numpy",
        "pandas", 
        "streamlit",
        "bokeh",
        "scipy"
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