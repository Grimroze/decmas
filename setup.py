from setuptools import setup, find_packages
import os

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="decmas",
    version="0.1.1", # Changed version to 0.1.1 for PyPI update
    description="A Python framework for Decentralized Multi-Agent Systems (DeMAS)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Goldi Soni",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pydantic",
        "langchain",
        "langchain-core"
    ],
)
