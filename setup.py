"""Packaging.

Still setup.py rather than a declarative file. It has worked since the
beginning and there is nothing here that needs anything cleverer.
"""

from setuptools import find_packages, setup

setup(
    name="blueline",
    version="0.2.0",
    description="Change ringing method analysis and composition proving",
    author="Fredrik Ahman",
    author_email="fredrik.fullstackdev@gmail.com",
    packages=find_packages(include=["blueline", "blueline.*"]),
    python_requires=">=3.11",
    install_requires=[
        "SQLAlchemy>=2.0.52",
        "alembic>=1.19.1",
        "click>=8.5.0",
        "structlog>=26.1.0",
    ],
    extras_require={"dev": ["pytest", "pytest-cov", "mypy", "flake8"]},
    entry_points={"console_scripts": ["blueline = blueline.cli.main:app"]},
)
