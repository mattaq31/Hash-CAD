""" Setup script for package. """
from setuptools import setup, find_packages

setup(
    name="Crisscross",
    author="Matthew Aquilina, Siyuan Stella Wang, Corey Becker, Florian Katzmeier",
    description="TBC",
    version="1.0.0",
    url="https://github.com/mattaq31/Crisscross-Design",
    packages=find_packages(),
    entry_points='''
    [console_scripts]
    handle_evolve=cli_functions.handle_evolution:handle_evolve
''',
)

