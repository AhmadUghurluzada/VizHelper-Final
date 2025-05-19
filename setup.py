# setup.py
from setuptools import setup, find_packages

setup(
    name="vizhelper",
    version="0.1.1",
    packages=find_packages(),
    install_requires=["matplotlib", "pandas", "mplcursors", "openai"],
    author="Ahmad Ughurluzada",
    description="A user-centered visualization helper for Matplotlib",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
)
