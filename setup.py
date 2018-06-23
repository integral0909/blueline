"""Packaging.

setup.py rather than a declarative file: setuptools could not read metadata
out of pyproject.toml until 2022, and in 2018 this is what there was.
"""

from setuptools import find_packages, setup

setup(
    name="blueline",
    version="0.1.0",
    description="Change ringing method analysis and composition proving",
    author="Fredrik Ahman",
    author_email="fredrik.fullstackdev@gmail.com",
    packages=find_packages(include=["blueline", "blueline.*"]),
    python_requires=">=3.7",
    install_requires=[
        "SQLAlchemy==1.2.19",
        "alembic==1.0.5",
        "click==6.7",
        "structlog==18.1.0",
        "toml==0.9.4",
    ],
    extras_require={
        # Not pinned. The test tooling is the one part of this that has to
        # keep working on whatever python is to hand, and pinning it to the
        # versions that were current when the rest of this was written would
        # mean nothing runs at all.
        "dev": ["pytest", "pytest-cov", "mypy", "flake8"],
    },
    entry_points={"console_scripts": ["blueline = blueline.cli.main:app"]},
)
